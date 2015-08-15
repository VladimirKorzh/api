#!/usr/bin/env python

HOST = 'rabbitmq.it4medicine.com'
PREFETCH_COUNT = 10
X_MESSAGE_TTL = 60000

class ApiWorker():
    def __init__(self, workerId):

        if workerId is None:
            import random
            workerId = random.random()*10000

        self.mqConnection = ''
        self.MAIN_QUEUE_NAME = 'api.v2.worker.' + str(workerId)

        self.ENDPOINTS = {'auth': ApiAuth(),
                          'sync': SyncApi(),
                          'ping': PingApi()}
                          # 'catalog': CatalogApi()}

        self.db = db
        self.db.connect()

    def start_service(self, mqconnection=None):
        if mqconnection is None:
            self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST))
        else:
            self.mqConnection = mqconnection

        self.channel = self.mqConnection.channel()
        self.channel.basic_qos(prefetch_count=PREFETCH_COUNT)

        listening_on = self.channel.queue_declare(queue=self.MAIN_QUEUE_NAME,
                                                  durable=False,
                                                  exclusive=False,
                                                  passive=False,
                                                  auto_delete=True,
                                                  arguments={'x-message-ttl': X_MESSAGE_TTL})

        self.channel.basic_consume(self.on_request, queue=listening_on.method.queue)

        print "[!] API Worker " + self.MAIN_QUEUE_NAME + " started."
        self.channel.start_consuming()

    def stop_service(self):
        self.db.close()

    def on_request(self, ch, method, props, body):
        try:
            pkt = NetworkPacket.fromJson(body)
            api2call = pkt.data['api']
            if api2call in self.ENDPOINTS.keys():
                print '~ Executing "' + api2call + '" call for client ' + str(props.correlation_id)
                self.ENDPOINTS[api2call].on_request(ch, method, props, body)
                print '~ Done. '
            else:
                send_error(ch, method, props, 'API call is not valid')

        except KeyError as e:
            send_error(ch, method, props, 'Have you forgot to state which API endpoint you are calling?')

        except Exception as e:
            send_error(ch, method, props, 'ValueError: Packet was not recognized by API SERVICE ' + str(e.message))



def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def send_error(ch, method, props, msg):
    n = NetworkPacket()
    n.data['status'] = 'ERROR'
    n.data['message'] = msg
    payload = n.toJson()

    if props.reply_to != None:
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=payload)

    ch.basic_nack(delivery_tag=method.delivery_tag, multiple=False, requeue=False)

    print "~ Error msg sent to " + str(props.reply_to) + ": " + payload



def send_reply(ch, method, props, payload):
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id,
                                                     expiration=str(X_MESSAGE_TTL)),
                     body=payload)

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print "~ Reply msg sent to " + str(props.reply_to) + ": " + payload


import pika

from NetworkPacket import NetworkPacket
from DatabaseModels import *

from api_auth import ApiAuth
from api_sync import SyncApi
from api_ping import PingApi


def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='workerID')
    args = parser.parse_args()

    api = ApiWorker(args.workerID)
    api.start_service()


if __name__ == '__main__':
    main()

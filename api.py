#!/usr/bin/env python
import pika
import thread
from NetworkPacket import NetworkPacket

HOST = 'rabbitmq.it4medicine.com'
HEARTBEAT = 5
PREFETCH_COUNT = 10
X_MESSAGE_TTL = 60000
MAIN_QUEUE_NAME = 'request-ay'


def auth_handler(props, pkt):
    from api_auth import ApiAuth
    a = ApiAuth()
    a.start(props, pkt)


def sync_handler(props, pkt):
    from api_sync import SyncApi
    a = SyncApi()
    a.start(props, pkt)

def catalog_handler(props, pkt):
    from api_catalog import CatalogApi
    a = CatalogApi()
    a.start(props, pkt)

def pong_handler(props, pkt):
    from api_ping import PingApi
    a = PingApi()
    a.start(props, pkt)


VALID_ENDPOINTS = {}
VALID_ENDPOINTS['auth'] = auth_handler
VALID_ENDPOINTS['sync'] = sync_handler
VALID_ENDPOINTS['ping'] = pong_handler
VALID_ENDPOINTS['catalog'] = catalog_handler

class API_SERVICE():
    def __init__(self):
        self.mqConnection = ''
        pass

    def start_service(self):
        self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST))
        self.channel = self.mqConnection.channel()
        self.channel.basic_qos(prefetch_count=PREFETCH_COUNT)

        listening_on = self.channel.queue_declare(queue=MAIN_QUEUE_NAME,
                                                 durable=True,
                                                 exclusive=False,
                                                 passive=False,
                                                 auto_delete=False,
                                                 arguments={'x-message-ttl': X_MESSAGE_TTL})

        self.channel.basic_consume(self.on_request, queue=listening_on.method.queue)

        print " [!] API SERVICE started"
        self.channel.start_consuming()

    def on_request(self, ch, method, props, body):
        try:
            pkt = NetworkPacket.fromJson(body)

            if pkt.data['api'] in VALID_ENDPOINTS.keys():
                thread.start_new_thread(VALID_ENDPOINTS[pkt.data['api']], (props, pkt))
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print '-- Starting handler for: ', pkt.data['api'], str(props.correlation_id)
                print '-- rcvd msg: ' + body

            else:
                send_error(ch, method, props, body, 'API call is not valid')

        except KeyError as e:
            print "Key error: ",
            send_error(ch, method, props, body, 'Have you forgot to state whice API endpoint you are calling?')

        except ValueError as e:
            print "Value error: ",
            send_error(ch, method, props, body, 'Packet was not recognized by API SERVICE')

        except TypeError as e:
            print "Type error: ",
            send_error(ch, method, props, body, 'Packet was not recognized by API SERVICE')

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def send_error(ch, method, props, body, msg):
    # reject all the misformed packets
    print '-- rcvd misformed packet: ' + str(body)

    n = NetworkPacket()
    n.data['status'] = 'ERROR'
    n.data['message'] = msg
    response = n.toJson()

    ch.basic_nack(delivery_tag=method.delivery_tag,
                  multiple=False,
                  requeue=False)

    if props.reply_to != None:
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=response)



def main():
    api = API_SERVICE()
    api.start_service()


if __name__ == '__main__':
    main()

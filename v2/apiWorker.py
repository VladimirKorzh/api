#!/usr/bin/env python

HOST = 'rabbitmq.it4medicine.com'
PREFETCH_COUNT = 10
X_MESSAGE_TTL = 60000
VERSION = 2
VERSION_PREFIX = '.v' + str(VERSION) + '.'
MAIN_QUEUE_NAME = 'api' + VERSION_PREFIX + 'requests'
THREAD_COUNT = 4

# import datetime
# logFileName = datetime.datetime.now().strftime("%d.%m_at_%H:%M") + '.nml'
# logFile = open('./logs/'+logFileName, 'w')
#


class ApiWorkerHandler():
    def __init__(self, mqconnection=None):
        self.ENDPOINTS = {'auth': ApiAuth(),
                          'sync': SyncApi(),
                          'ping': PingApi(),
                           'catalog': CatalogApi()}

        self.db = db
        self.db.connect()

        if mqconnection is None:
            self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST))
        else:
            self.mqConnection = mqconnection

        self.channel = self.perform_architecture_setup()

    def perform_architecture_setup(self):
        channel = self.mqConnection.channel()
        channel.basic_qos(prefetch_count=PREFETCH_COUNT)

        channel.exchange_declare(exchange='api'+VERSION_PREFIX,
                                        type='direct',
                                        durable=True)

        self.listening_on = channel.queue_declare(queue=MAIN_QUEUE_NAME,
                                                          durable=True,
                                                          exclusive=False,
                                                          passive=False,
                                                          auto_delete=False,
                                                          arguments={'x-message-ttl': X_MESSAGE_TTL})

        channel.queue_bind(exchange='api'+VERSION_PREFIX,
                                   queue=MAIN_QUEUE_NAME)

        return channel


import threading
class ApiWorker(threading.Thread):
    def __init__(self, apiWorkerHandler, threadID, queueName):
        threading.Thread.__init__(self)
        self.apiWorkerHandler = apiWorkerHandler
        self.threadID = threadID
        self.listenQueueName = queueName
        pass

    def run(self):
        channel = self.apiWorkerHandler.perform_architecture_setup()
        channel.basic_consume(self.on_request, queue=self.listenQueueName)

        print "[!] " + str(self.threadID) + " API Worker " + MAIN_QUEUE_NAME + " started."
        channel.start_consuming()

    def stop_service(self):
        print "[!] " + str(self.threadID) + "API Worker " + MAIN_QUEUE_NAME + " stopping..."
        sys.exit(0)

    def on_request(self, ch, method, props, body):
        try:
            pkt = NetworkPacket.fromJson(body)
            # logFile.write(body+'\n')

            api2call = pkt.data['api']
            if api2call in self.apiWorkerHandler.ENDPOINTS.keys():
                print ' ~ Executing "' + api2call + '" call for client ' + str(props.correlation_id) +'. Received packet: '+body
                self.apiWorkerHandler.ENDPOINTS[api2call].on_request(ch, method, props, body)
            else:
                self.send_error(ch, method, props, 'API call is not valid')

        except KeyError as e:
            self.send_error(ch, method, props, 'Have you forgot to state which API endpoint you are calling?')

        except Exception as e:
            self.send_error(ch, method, props, 'ValueError: Packet was not recognized by API SERVICE, ' + str(e.message))

    @staticmethod
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

        print " ~~ Error msg sent to " + str(props.reply_to) + ": " + payload
        # logFile.write(payload+'\n')

    @staticmethod
    def send_reply(ch, method, props, payload):
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id,
                                                         expiration=str(X_MESSAGE_TTL)),
                         body=payload)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print " ~~ Reply msg sent to " + str(props.reply_to) + ": " + payload
        # logFile.write(payload+'\n')




def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def signal_handler(signal, frame):
    if API_HANDLER.channel is not None:
        API_HANDLER.channel.close()
    if API_HANDLER.mqConnection is not None:
        API_HANDLER.mqConnection.close()
    if API_HANDLER.db is not None:
        API_HANDLER.db.close()

import pika
import signal
import sys

from NetworkPacket import NetworkPacket
from DatabaseModels import *

from api_auth import ApiAuth
from api_sync import SyncApi
from api_ping import PingApi
from api_catalog import CatalogApi

API_HANDLER = None
WORKER_LIST = []

def main():
    global API_HANDLER, WORKER_LIST
    API_HANDLER = ApiWorkerHandler()
    signal.signal(signal.SIGINT, signal_handler)

    for i in range(0, THREAD_COUNT):
        worker = ApiWorker(API_HANDLER, "Thread-"+str(i), MAIN_QUEUE_NAME)
        worker.setDaemon(True)
        WORKER_LIST.append(worker)
        worker.start()

    signal.pause()


if __name__ == '__main__':
    main()

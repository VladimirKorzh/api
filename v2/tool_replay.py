__author__ = 'vladimir'

import os
import pika
import argparse
import pprint
import random

from apiWorker import HOST, PREFETCH_COUNT, X_MESSAGE_TTL, byteify
from NetworkPacket import NetworkPacket

REQUEST_TARGET = 'api.v2.'
LISTEN_QUEUE = 'tool.replay.'+str(random.random()*10000)

class LogReplayer():
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(HOST))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=PREFETCH_COUNT)

        self.listening_on = self.channel.queue_declare(queue=LISTEN_QUEUE,
                                                          durable=False,
                                                          exclusive=False,
                                                          passive=False,
                                                          auto_delete=True,
                                                          arguments={'x-message-ttl': X_MESSAGE_TTL})

        self.channel.basic_consume(self.on_response, queue=self.listening_on.method.queue)

    def call(self, payload, expected):
        self.response = None
        self.channel.basic_publish(exchange=REQUEST_TARGET,
                                   routing_key=REQUEST_TARGET+'requests',
                                   properties=pika.BasicProperties(reply_to=LISTEN_QUEUE),
                                   body=payload)
        while self.response is None:
            self.connection.process_data_events()
        return self.response, self.response == expected

    def on_response(self, ch, method, props, body):
        self.response = body
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def start_ddos(self):
        zeros = bytearray(100)
        for i in range(0,10000):
            self.channel.basic_publish(exchange=REQUEST_TARGET,
                               routing_key=REQUEST_TARGET+'requests',
                               properties=pika.BasicProperties(reply_to=LISTEN_QUEUE),
                               body=str(zeros))


    def start(self):
        pp = pprint.PrettyPrinter(indent=4)

        curdir = os.path.dirname(os.path.realpath(__file__))
        logs = os.path.join(curdir, "logs")

        fileList = []
        print "Looking for files in 'logs' directory... ",
        for (dirpath, dirnames, filenames) in os.walk(logs):
            fileList.extend([os.path.join(dirpath, name) for name in filenames])
        print len(fileList), ' files found.'

        print 'Starting replay: '


        for fileName in fileList:
            if fileName[len(fileName)-4:] == ".nml":
                print ' ~ Replaying: ', fileName
                with open(fileName, 'r') as file:
                    request = file.readline().rstrip('\n')
                    response = file.readline().rstrip('\n')
                    if len(request) > 5 and len(response) > 5:
                        print '-----------------------------------'
                        print 'REQUEST: ' + request
                        print '. . . . . . . . . . . . . . . . . .'
                        print 'EXPECTED: ' + response
                        print '-----------------------------------'
                        reply, complete = self.call(request, response)
                        print 'RESULT: ' + reply
                        print '----- correct ' + str(complete)


        print 'Replay complete.'
        self.connection.close()


def main():
    replayer = LogReplayer()
    replayer.start_ddos()

if __name__ == '__main__':
    main()
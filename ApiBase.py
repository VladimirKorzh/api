#!/usr/bin/env python
import json, pika
from api import HOST, HEARTBEAT, X_MESSAGE_TTL


class ApiBase():
    def __init__(self):
        self.map = {}
        self.client_queue = 'cli_listen_q'
        self.server_queue = 'srv_listen_q'
        self.correlation_id = ''
        self.consumer_tag = ''

    def start(self, props, pkt):
        self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST,
                                                                              heartbeat_interval=HEARTBEAT))
        self.mqConnection.add_timeout(10, self.stop)

        self.channel = self.mqConnection.channel()
        self.channel.basic_qos(prefetch_count=1)

        tmp_queue = self.channel.queue_declare(durable=False,
                                               exclusive=False,
                                               passive=False,
                                               auto_delete=True,
                                               arguments={'x-message-ttl': X_MESSAGE_TTL})

        self.map[self.server_queue] = tmp_queue.method.queue
        self.map[self.client_queue] = props.reply_to

        print '-- server side q: ' + str(self.map[self.server_queue])
        print '-- client side q: ' + str(self.map[self.client_queue])

        self.consumer_tag = self.channel.basic_consume(self.on_request, queue=str(self.map[self.server_queue]))

        self.send(str(self.map[self.server_queue]), pkt.toJson())
        self.correlation_id = props.correlation_id

        print " [x] Personal Api worker starts listening"
        self.channel.start_consuming()

    def stop(self):
        self.channel.basic_cancel(consumer_tag=self.consumer_tag)
        self.channel.close()
        self.mqConnection.close()
        print " [x] Api worker has stopped listening for: ", self.consumer_tag

    def send(self, queue, payload):
        self.channel.basic_publish(exchange='',
                                   routing_key=queue,
                                   properties=pika.BasicProperties(correlation_id=self.correlation_id,
                                                                   reply_to=str(self.map[self.server_queue]),
                                                                    expiration=str(X_MESSAGE_TTL)),
                                   body=payload)
        print " -- msg sent into q: "+ queue +": "+ payload




    def on_request(self, ch, method, props, body):
        print 'got msg ' + body.pretty()

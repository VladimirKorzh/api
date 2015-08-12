#!/usr/bin/env python
import json, pika
from api import HOST,HEARTBEAT

class apiBase():
  def __init__(self):
    pass
  
  def start(self, props):
    from api import HOST,HEARTBEAT
    self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST,
									heartbeat_interval=HEARTBEAT))
    self.mqConnection.add_timeout(10, self.stop)
    
    self.channel = self.mqConnection.channel()
    self.channel.basic_qos(prefetch_count=1)
    
    tmp_queue = self.channel.queue_declare(durable=False,
				      exclusive=False,
				      passive=False,
				      auto_delete=True,
				      arguments={'x-message-ttl':60000})

    self.map[self.server_queue] = tmp_queue.method.queue
    self.map[self.client_queue] = props.reply_to
    
    print '-- server side q: ' + str(self.map[self.server_queue])
    print '-- client side q: ' + str(self.map[self.client_queue])
    
    self.consumer_tag = self.channel.basic_consume(self.on_request, queue=str(self.map[self.server_queue]))
 
    print " [x] Personal Api worker starts listening"
    self.channel.start_consuming()    

  def stop(self):
    self.channel.basic_cancel(consumer_tag=self.consumer_tag)
    self.mqConnection.close()
    print " [x] Api worker has stopped listening for: ", self.consumer_tag
    
  def send(self, payload):
    self.channel.basic_publish(exchange='',
			      routing_key=str(self.map[self.client_queue]),
			      properties=pika.BasicProperties(correlation_id = self.correlation_id,
							      reply_to = str(self.map[self.server_queue])),
			      body=payload)    
    print " -- msg sent: " + p.pretty()    
    
    
  def on_request(self, ch, method, props, body):
      print 'got msg ' + str(body)    
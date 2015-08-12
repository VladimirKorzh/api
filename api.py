#!/usr/bin/env python
import pika

HOST = 'rabbitmq.it4medicine.com'
HEARTBEAT = 5
PREFETCH_COUNT = 10 
X_MESSAGE_TTL = 60000

class api():
  def __init__(self):
    pass
  
  def start_service(self):
  self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST,
									heartbeat_interval=HEARTBEAT))
  channel = self.mqConnection.channel()
  channel.basic_qos(prefetch_count=PREFETCH_COUNT)
  
  listening_on = channel.queue_declare(queue="handshake",
				      durable=True,
				      exclusive=False,
				      passive=False,
				      auto_delete=False,
				      arguments={'x-message-ttl':X_MESSAGE_TTL})
  
  channel.basic_consume(self.on_request, queue=listening_on.method.queue)
  
  print " [!] ApiEncryptionHandshake SERVICE started"
  channel.start_consuming() 
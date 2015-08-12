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
    
  def stop(self):
    self.channel.basic_cancel(consumer_tag=self.consumer_tag)
    self.mqConnection.close()
    print " [x] Api worker has stopped listening for: ", self.consumer_tag
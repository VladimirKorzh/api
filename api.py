#!/usr/bin/env python
import pika
import thread
from NetworkPacket import NetworkPacket

"""
    AUTH:
      sign_up - register new user in system
      login - check user authenticity
      connect - join account info    
      
    catalog - get catalog 
    
    sync - sync user db

    reply: 
	  {
	    STATUS:{OK, ERROR}
	    MSG: {}
	  }
"""

HOST = 'rabbitmq.it4medicine.com'
HEARTBEAT = 5
PREFETCH_COUNT = 10
X_MESSAGE_TTL = 10000
MAIN_QUEUE_NAME = 'request'


def auth_handler(props, pkt):
    pass


def sync_handler(props, pkt):
    pass


def pong_handler(props, pkt):
    from ping import PingApi
    a = PingApi()
    a.start(props, pkt)


VALID_ENDPOINTS = {}
VALID_ENDPOINTS['auth'] = auth_handler
VALID_ENDPOINTS['sync'] = sync_handler
VALID_ENDPOINTS['ping'] = pong_handler

class API_SERVICE():
    def __init__(self):
        self.mqConnection = ''
        pass

    def start_service(self):
        self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST,
                                                                              heartbeat_interval=HEARTBEAT))
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
                self.send_error(ch, method, props, body, 'API call is not valid')

        except ValueError as e:
            print "Value error: " + e
            self.send_error(ch, method, props, body, 'Packet was not recognized by API SERVICE')

        except TypeError as e:
            print "Type error: " + e
            self.send_error(ch, method, props, body, 'Packet was not recognized by API SERVICE')


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

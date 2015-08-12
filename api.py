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
X_MESSAGE_TTL = 60000
MAIN_QUEUE_NAME = 'request'


def auth_handler(props, pkt):
    pass


def sync_handler(props, pkt):
    pass


VALID_ENDPOINTS = {'auth': auth_handler,
                   'sync': sync_handler}


class API_SERVICE():
    def __init__(self):
        self.mqConnection = ''
        pass

    def start_service(self):
        self.mqConnection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST,
                                                                              heartbeat_interval=HEARTBEAT))
        channel = self.mqConnection.channel()
        channel.basic_qos(prefetch_count=PREFETCH_COUNT)

        listening_on = channel.queue_declare(queue=MAIN_QUEUE_NAME,
                                             durable=True,
                                             exclusive=False,
                                             passive=False,
                                             auto_delete=False,
                                             arguments={'x-message-ttl': X_MESSAGE_TTL})

        channel.basic_consume(self.on_request, queue=listening_on.method.queue)

        print " [!] API SERVICE started"
        channel.start_consuming()

    @staticmethod
    def on_request(self, ch, method, props, body):
        try:
            pkt = NetworkPacket.fromJson(body)
            print '-- rcvd msg: ' + pkt.pretty()

            if pkt['api'] in VALID_ENDPOINTS.keys():
                thread.start_new_thread(pkt['api'], (props, pkt))
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print '-- Starting handler for: ', pkt['api'], str(props.correlation_id)


        except ValueError:
            # reject all the misformed packets
            print '-- rcvd misformed packet: ' + str(body)

            n = NetworkPacket()
            n.data['status'] = 'ERROR'
            n.data['message'] = 'Packet was not recognized by API SERVICE'
            response = n.toJson()

            ch.basic_nack(delivery_tag=method.delivery_tag,
                          multiple=False,
                          requeue=False)

            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id=props.correlation_id),
                             body=response)

            return


def main():
    api = API_SERVICE()
    api.start_service()


if __name__ == '__main__':
    main()

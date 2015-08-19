__author__ = 'vladimir'

from DatabaseModels import *
from NetworkPacket import NetworkPacket
from datetime import date, timedelta


"""
    ['api'] = 'notification'
    ['func'] = 'push', 'pull'
    ['message']
        ['sender']
        ['receiver']
            ['email'] = null
            ['phone'] = +380936737189
        ['text'] = "User has dismissed a notification"
        ['type'] = 1

"""



VALID_REQUEST_TYPES = ['push', 'pull']

class NotificationApi():
    def __init__(self):
        pass

    def on_request(self, ch, method, props, body):
        pkt = NetworkPacket.fromJson(body)

        uuid = pkt.data['uuid']
        type = pkt.data['func']

        # check if uuid valid
        try:
            user = User.select().where(User.uuid == uuid).get()
        except DoesNotExist, e:
            ApiWorker.send_error(ch, method, props, "User does not Exist")
            return

        # check for valid request
        if type in VALID_REQUEST_TYPES:
            if type in ['push']:
                rcv = pkt.data['message']['receiver']
                snd = pkt.data['uuid']

                payload = pkt.data['message']['body']
                type = pkt.data['message']['type']


                rcv_user = None
                snd_user = None
                if rcv['email'] is not None:
                    rcv_user = SocialData.select().where( SocialData.medium == 'email' and SocialData.value == rcv['email'] )
                if rcv['phone'] is not None and rcv_user is None:
                    rcv_user = SocialData.select().where( SocialData.medium == 'phone' and SocialData.value == rcv['phone'] )

                if snd['email'] is not None:
                    snd_user = SocialData.select().where( SocialData.medium == 'email' and SocialData.value == snd['email'] )
                if snd['phone'] is not None and snd_user is None:
                    snd_user = SocialData.select().where( SocialData.medium == 'phone' and SocialData.value == snd['phone'] )



                if rcv_user is None or snd_user is None:
                    ApiWorker.send_error(ch, method, props, 'Receiver or Sender user could not be found')
                else:
                    # save notification in db
                    notification = Notification()
                    notification.receiver = rcv_user
                    notification.sender = snd_user
                    notification.message = payload
                    notification.type = type
                    notification.status = False

                    # send push all connected devices based on uuid of receiver
                    ch.basic_publish(exchange='push'+VERSION_PREFIX,
                                     routing_key=rcv_user.user.uuid+".#",
                                     body=payload)

                    # send reply to client
                    n = NetworkPacket()
                    n.data['status'] = "OK"
                    n.data['message'] = None
                    ApiWorker.send_reply(ch, method, props, n.toJson())

            if type in ['pull']:
                # get notification for the last 3 days
                user_notifications = Notification.select()\
                    .where(Notification.receiver == uuid | Notification.created_date >= date.today() - timedelta(days=3))

                n = NetworkPacket()
                n.data['status'] = "OK"
                n.data['message'] = {}
                for each in user_notifications:
                    n.data['message']['notifications'].append(each)

                ApiWorker.send_reply(ch, method, props, n.toJson())


from apiWorker import byteify, ApiWorker, VERSION_PREFIX


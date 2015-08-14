__author__ = 'vladimir'
from ApiBase import ApiBase
from api import send_error
from DatabaseModels import *
from NetworkPacket import NetworkPacket

VALID_REQUEST_TYPES = []

"""
    uuid: <uuid>
    api: sync
    message:
        timestamp: <utc_time>
        db: {}

    reply: "OK"
    message: "Thank you"

    reply: "UPDATE"
    message: {db}

    reply: "ERROR"
    message: "User does not Exist"
"""

class SyncApi (ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        self.db = db
        self.db.connect()
        try:
            # self.db.drop_tables([User, SocialData, Device])
            self.db.create_tables([User, SocialData, Device])
        except OperationalError:
            pass

    def on_request(self, ch, method, props, body):
        # try:
            pkt = NetworkPacket.fromJson(body)

            uuid = pkt.data['uuid']
            cli_utc = pkt.data['message']['timestamp']

            try:
                user = User.select().where(User.uuid == uuid).get()
            except DoesNotExist, e:
                n = NetworkPacket()
                n.data['status'] = "ERROR"
                n.data['message'] = "User does not Exist"
                self.send(str(self.map[self.client_queue]), n.toJson())

            if user.db != None:
                srv_utc = user.timestamp
            else:
                srv_utc = 0

            if cli_utc > srv_utc:
                user.db = pkt.data['message']['db']
                user.save()
                n = NetworkPacket()
                n.data['status'] = "OK"
                n.data['message'] = "Thank you"
                self.send(str(self.map[self.client_queue]), n.toJson())
            else:
                n = NetworkPacket()
                n.data['status'] = "UPDATE"
                n.data['message'] = user.db
                self.send(str(self.map[self.client_queue]), n.toJson())

        # except Exception, e:
        #     print "ERROR", str(e)
        #     e.print_tb()
        # finally:
        #     self.db.close()


def main():
    import time
    n = NetworkPacket()
    n.data['api'] = 'sync'
    n.data['uuid'] = 'a3301c74-5962-58b9-a7f6-b9bdf02fef62'

    n.data['message'] = {}
    n.data['message']['timestamp'] = time.time()
    n.data['message']['db'] = {}

    print "\n", n.toJson(),"\n"


if __name__ == '__main__':
    main()


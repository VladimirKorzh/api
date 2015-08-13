__author__ = 'vladimir'
from ApiBase import ApiBase
from api import send_error
from DatabaseModels import *
from NetworkPacket import NetworkPacket

VALID_REQUEST_TYPES = []

class SyncApi (ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        self.db = db
        self.db.connect()
        try:
            #self.db.drop_tables([User, SocialData, Device])
            self.db.create_tables([User, SocialData, Device])
        except OperationalError:
            pass

    def on_request(self, ch, method, props, body):
        try:
            pkt = NetworkPacket.fromJson(body)

            uuid = pkt.data['uuid']

            cli_utc = pkt.data['message']['db']['timestamp']
            loc_utc = User.select()

            send_error(ch, method, props, body, 'Invalid request field type')
        except Exception, e:
            print "ERROR", str(e)
        finally:
            self.db.close()


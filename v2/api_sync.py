__author__ = 'vladimir'
from DatabaseModels import *
from NetworkPacket import NetworkPacket
import json

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


class SyncApi():
    def __init__(self):
        pass

    def on_request(self, ch, method, props, body):
        pkt = NetworkPacket.fromJson(body)

        uuid = pkt.data['uuid']
        cli_utc = pkt.data['message']['timestamp']

        try:
            user = User.select().where(User.uuid == uuid).get()
        except DoesNotExist, e:
            ApiWorker.send_error(ch, method, props, "User does not Exist")
            return

        if user.db != None:
            srv_utc = user.timestamp
        else:
            srv_utc = 0

        # print srv_utc, cli_utc
        if cli_utc > srv_utc:

            # print byteify(json.dumps(pkt.data['message']['db']))

            user.db = byteify(json.dumps(pkt.data['message']['db']))
            user.timestamp = cli_utc
            user.save()
            n = NetworkPacket()
            n.data['status'] = "OK"
            n.data['message'] = "Thank you"
            ApiWorker.send_reply(ch, method, props, n.toJson())
        else:
            # print byteify(json.loads(user.db))

            n = NetworkPacket()
            n.data['status'] = "UPDATE"
            n.data['message'] = byteify(json.loads(user.db))
            # print n.data['message']
            ApiWorker.send_reply(ch, method, props, n.toJson())



from apiWorker import byteify, ApiWorker

def main():
    pass
    # import time
    # n = NetworkPacket()
    # n.data['api'] = 'sync'
    # n.data['uuid'] = 'a3301c74-5962-58b9-a7f6-b9bdf02fef62'
    #
    # n.data['message'] = {}
    # n.data['message']['timestamp'] = time.time()-10000000
    # n.data['message']['db'] = {"key":"value"}
    #
    # print "\n", n.toJson(),"\n"
    #
    # n = NetworkPacket()
    # n.data['api'] = 'sync'
    # n.data['uuid'] = 'a3301c74-5962-58b9-a7f6-b9bdf02fef62'
    #
    # n.data['message'] = {}
    # n.data['message']['timestamp'] = time.time()+10000000
    # n.data['message']['db'] = {"key":"value"}
    #
    # print "\n", n.toJson(),"\n"
    #
    #
    # msg = '{"message": {"timestamp": 144944444551.208414, "db": {"key": "value"}}, "api": "sync", "uuid": "a3301c74-5962-58b9-a7f6-b9bdf02fef62"}'
    # pkt = NetworkPacket.fromJson(msg)
    #
    # print pkt.data['message']['db']
    # print json.dumps(pkt.data['message']['db'])
    # print byteify(json.dumps(pkt.data['message']['db']))


if __name__ == '__main__':
    main()


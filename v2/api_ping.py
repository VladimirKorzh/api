__author__ = 'vladimir'
from apiWorker import ApiWorker

"""
    request: ping

    reply: "pong"
"""

class PingApi():
    def __init__(self):
        pass

    def on_request(self, ch, method, props, body):
        ApiWorker.send_reply(ch, method, props, "pong")

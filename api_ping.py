__author__ = 'vladimir'
from ApiBase import ApiBase
from api import send_error

"""
    request: ping

    reply: "pong"
"""


class PingApi (ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        pass

    def on_request(self, ch, method, props, body):
        send_error(ch, method, props, body, 'error')
        self.send(str(self.map[self.server_queue]), "pong")
        self.send(str(self.map[self.client_queue]), "pong")
        self.stop()

__author__ = 'vladimir'
from ApiBase import ApiBase


class PingApi (ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        pass

    def on_request(self, ch, method, props, body):
        ApiBase.on_request(ch, method, props, body)
        self.send("pong")
        self.stop()


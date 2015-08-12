__author__ = 'vladimir'
from ApiBase import ApiBase


class PingApi (ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        pass

    def on_request(self, ch, method, props, body):
        #self.on_request(self, ch, method, props, body)
        self.send(str(self.map[self.server_queue]), "pong")
        self.send(str(self.map[self.client_queue]), "pong")


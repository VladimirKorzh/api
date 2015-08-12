#!/usr/bin/env python
import json

"""
request:
    self['uuid'] = ''
    self['api'] = ''
    self['msg'] = ''

response:
    self['status'] = ''
    self['message'] = ''
"""


class NetworkPacket():
    def __init__(self):
        self.data = {}

    def toJson(self):
        return json.dumps(self.data)

    def fromJson(self, obj):
        self.data = json.loads(obj)
        return self

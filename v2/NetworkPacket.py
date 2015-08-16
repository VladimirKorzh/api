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

    @staticmethod
    def fromJson(obj):
        data = json.loads(obj)
        np = NetworkPacket()
        np.data = data
        return np



def main():
  a = NetworkPacket()
  a.data['api'] = 'ping'
  a.data['list'] = {}
  a.data['list']['test'] = 'test'
  b = a.toJson()
  print a.toJson()
  c = NetworkPacket.fromJson(b)
  print c.toJson()
  print c.data


if __name__ == '__main__':
    main()
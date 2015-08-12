#!/usr/bin/env python
import json 


class NetworkPacket():
  def __init__(self):
    self.data = {}
    self['uuid'] = ''
    self['api'] = ''    
    self['msg'] = ''
    
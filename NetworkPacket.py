#!/usr/bin/env python
import json 

"""
  api:
    AUTH:
      sign_up - register new user in system
      login - check user authenticity
      connect - join account info    
      
    catalog - get catalog 
    
    sync - sync user db
    
    
    
    reply: 
	  {
	    STATUS:{OK, ERROR}
	    MSG: {}
	  }
"""


class NetworkPacket():
  def __init__(self):
    self.data = {}
    self['uuid'] = ''
    self['api'] = ''    
    self['msg'] = ''
    
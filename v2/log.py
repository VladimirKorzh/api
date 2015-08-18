#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Alex Petrenko'

import logging
import sys
import os

class Log():
    def __init__(self):
        self.format = u'%(levelname)-8s [%(asctime)s] %(message)s'
        self.level = logging.INFO
        self.filename = os.path.abspath(os.path.dirname(__file__)) + '/../server_api_log.log'

    def send(self, type, msg):
        logging.basicConfig(format = self.format, level = self.level, filename = self.filename)
        print msg

        if type == 'debug':
            logging.debug( msg )
        if type == 'info':
            logging.info( msg )
        if type == 'warning':
            logging.warning( msg )
        if type == 'error':
            logging.error( msg )
        if type == 'critical':
            logging.critical( msg )

if __name__ == '__main__':
    if len(sys.argv) > 1:
        Log().send(type = sys.argv[1], msg = sys.argv[2])
    else:
        Log().send(type = "info", msg = "No data!")

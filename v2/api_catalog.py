__author__ = 'Alex'


from apiWorker import send_error
from apiWorker import send_reply
import json
import time
from NetworkPacket import NetworkPacket

from playhouse.csv_loader import load_csv
from playhouse.shortcuts import *

from geopy.geocoders import Yandex

db = SqliteDatabase('test_db')
Pharmacy = load_csv(db, 'catalog_pharmacy.csv')

class CatalogApi():
    def __init__(self):

        # self.Clinics = load_csv(self.db, 'catalog_clinics.csv')
        # self.Drugs = load_csv(self.db, 'catalog_clinics.csv')
        # self.Disease = load_csv(self.db, 'catalog_disease.csv')
        self.CATALOGS = {'pharmacy': Pharmacy}
                         # 'clinics': self.Clinics,
                         # 'drugs': self.Drugs,
                         # 'diseases': self.Disease}
        self.FUNCS = {'get_catalog', 'check_hash', 'get_distances'}

    def on_request(self, ch, method, props, body):
     pkt = NetworkPacket.fromJson(body)
     type = pkt.data['catalog_name']
     n = NetworkPacket()

     if type in self.CATALOGS.keys():
        func = pkt.data['func']
        message = pkt.data['message']
        if func in self.FUNCS:
            if func == 'get_catalog':
                offset = message['offset']
                limit = message['limit']

                n.data['status'] = 'OK'
                n.data['message'] = toJson(self.CATALOGS[type], offset, limit)
        else:
            send_error(ch, method, props, body, 'Invalid func field')
            self.db.close()
     else:
        send_error(ch, method, props, body, 'Invalid catalog name')
        self.db.close()
        return
     send_reply(ch, method, props, n.toJson())
     self.db.close()
     return

def toJson(object):
    r = []
    for subObject in object:
        r.append(model_to_dict(subObject))
    return json.dumps(r)

def toJson(object, offset, limit):
 r = []
 selectQuery = (object.select().offset(offset).limit(limit))
 for subObject in selectQuery:
     print model_to_dict(subObject)
     r.append(model_to_dict(subObject))
 return json.dumps(r)

def hash(key):
        h = 0
        for c in key:
                h = ((h*37) + ord(c)) & 0xFFFFFFFF
        return h;
# def test():
#     print(hash(toJson(Pharmacy)))
# test()

def parseAndSaveAdresses(object):
    geolocator = Yandex()
    for subObject in object:
        location = geolocator.geocode(subObject.addr)
        subObject.lat = location.latitude
        subObject.lon = location.longitude
        subObject.save()
        print(subObject.lat, subObject.lon)
        time.sleep(3)

def printAdresses(object):
    for subObject in object:
        print(subObject.lat, subObject.lon)

__author__ = 'Alex'

from ApiBase import ApiBase
from api import send_error
import json
import time
from NetworkPacket import NetworkPacket

from playhouse.csv_loader import load_csv
from playhouse.shortcuts import *

from geopy.geocoders import Yandex

db = SqliteDatabase(':memory:')
Pharmacy = load_csv(db, 'catalog_pharmacy.csv')

class CatalogApi(ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        self.db = SqliteDatabase(':memory:')
        self.Pharmacy = load_csv(self.db, 'catalog_pharmacy.csv')
        self.Clinics = load_csv(self.db, 'catalog_clinics.csv')
        self.Drugs = load_csv(self.db, 'catalog_clinics.csv')
        self.Disease = load_csv(self.db, 'catalog_disease.csv')
        self.CATALOGS = {'pharmacy': self.Pharmacy}
                         # 'clinics': self.Clinics,
                         # 'drugs': self.Drugs,
                         # 'diseases': self.Disease}

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

    response =n.toJson()

    self.send(str(self.map[self.client_queue]), response)
    self.send(str(self.map[self.server_queue]), "pong")

    self.db.close()


def toJson(object):
    r = []
    for subObject in object:
        r.append(model_to_dict(subObject))
    return json.dumps(r)


def toJson(object, offset, limit):
 r = []
 selectQuery = (object.select().offset(offset).limit(limit))
 for subObject in selectQuery:
     r.append(model_to_dict(subObject))
 return json.dumps(r)

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

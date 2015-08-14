__author__ = 'Alex'

from ApiBase import ApiBase
from api import send_error
import json
import geopy
import time
import zlib
from NetworkPacket import NetworkPacket

from playhouse.csv_loader import load_csv, dump_csv
from playhouse.shortcuts import *

from geopy.geocoders import Yandex

db = SqliteDatabase('catalog.db')
Pharmacy = load_csv(db, 'catalog_pharmacy.csv')
Clinics = load_csv(db, 'catalog_clinics.csv')
Drugs = load_csv(db, 'catalog_drugs.csv')
Diseases = load_csv(db, 'catalog_disease.csv')

CATALOGS = {'clinics': Clinics, 'pharmacy': Pharmacy, 'diseases': Diseases, 'drugs': Drugs}

class CatalogApi(ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        pass

    def on_request(self, ch, method, props, body):
        pkt = NetworkPacket.fromJson(body)
        type = pkt.data['func']

        if type in CATALOGS.keys():
            n = NetworkPacket()
            n.data['status'] = 'OK'
            n.data['message'] = toJson(CATALOGS[type])
            response = n.toJson()
        else:
            send_error(ch, method, props, body, 'Invalid request field type')

        self.send(str(self.map[self.server_queue]), "pong")
        self.send(str(self.map[self.client_queue]), response)

def toJson(object):
    r = []
    for subObject in object:
        r.append(model_to_dict(subObject))
    return json.dumps(r)

def main():
    print(toJson(Pharmacy))
    # parseAndSaveAdresses(Pharmacy)
    # printAdresses(Pharmacy)

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

if __name__ == '__main__':
 main()

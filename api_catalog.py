__author__ = 'Alex'

from ApiBase import ApiBase
from api import send_error
import json
import time
from NetworkPacket import NetworkPacket

from playhouse.csv_loader import load_csv
from playhouse.shortcuts import *

from geopy.geocoders import Yandex


class CatalogApi(ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        self.db = SqliteDatabase(':memory:')

        self.Pharmacy = load_csv(self.db, 'catalog_pharmacy.csv')
        self.Clinics = load_csv(self.db,  'catalog_clinics.csv')
        self.Drugs = load_csv(self.db,    'catalog_clinics.csv')
        self.Disease = load_csv(self.db,  'catalog_disease.csv')

        self.CATALOGS = {'pharmacy': self.Pharmacy,
                        'clinics':   self.Clinics,
                        'drugs':     self.Drugs,
                        'diseases':  self.Disease}


    def on_request(self, ch, method, props, body):
        pkt = NetworkPacket.fromJson(body)
        type = pkt.data['func']

        if type in self.CATALOGS.keys():
            n = NetworkPacket()
            n.data['status'] = 'OK'
            n.data['message'] = toJson(self.CATALOGS[type])
            response = n.toJson()
        else:
            send_error(ch, method, props, body, 'Invalid request field type')
            self.db.close()
            return

        self.send(str(self.map[self.client_queue]), response)
        self.send(str(self.map[self.server_queue]), "pong")

        self.db.close()





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

__author__ = 'Alex'

from ApiBase import ApiBase
from api import send_error
import json
import geopy
import gzip
import zlib
from NetworkPacket import NetworkPacket

from playhouse.csv_loader import load_csv, dump_csv
from playhouse.shortcuts import *

from geopy.geocoders import Yandex

db = SqliteDatabase('catalog.db')
Pharmacy = load_csv(db, 'catalog_pharmacy.csv')
Clinics = load_csv(db, 'catalog_clinics.csv')
Drugs = load_csv(db, 'catalog_clinics.csv')
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
            n.data['msg'] = toJson(CATALOGS[type])

            a = zlib.compress(n.toJson())
            b = zlib.decompress(a)
            print b


            response = zlib.compress(n.toJson())
        else:
            send_error(ch, method, props, body, 'Invalid request field type')

        self.send(str(self.map[self.server_queue]), "pong")
        self.send(str(self.map[self.client_queue]), response)

def toJson(object):
    r = []
    for subObject in object:
        r.append(model_to_dict(subObject))
    return json.dumps(r)

# def main():
#     geolocator = Yandex()
#     for subObject in Pharmacy:
#
#     print (subObject.lat, subObject.lon)
#
#
#
# if __name__ == '__main__':
#     main()

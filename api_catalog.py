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


class CatalogApi(ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        db = SqliteDatabase(':memory:')

        self.Pharmacy = load_csv(db, 'catalog_pharmacy.csv', db_table="pharmacy")
        self.Clinics = load_csv(db, 'catalog_clinics.csv',   db_table="clinics")
        self.Drugs = load_csv(db, 'catalog_clinics.csv',     db_table="drugs")
        self.Disease = load_csv(db, 'catalog_disease.csv',   db_table="diseases")

        self.CATALOGS = {'pharmacy': self.Pharmacy,
                        'clinics':   self.Clinics,
                        'drugs':     self.Drugs,
                        'deseases':  self.Disease}


    def on_request(self, ch, method, props, body):
        pkt = NetworkPacket.fromJson(body)
        type = pkt.data['func']

        if type in self.CATALOGS.keys():
            n = NetworkPacket()
            n.data['status'] = 'OK'
            n.data['msg'] = toJson(self.CATALOGS[type])
            response = n.toJson()
        else:
            send_error(ch, method, props, body, 'Invalid request field type')

        self.send(str(self.map[self.client_queue]), response)
        self.send(str(self.map[self.server_queue]), "pong")

def toJson(object):
    r = []
    for subObject in object:
        r.append(model_to_dict(subObject))
    return json.dumps(r)

def main():
    db = SqliteDatabase('catalog.db')

    Pharmacy = load_csv(db, 'catalog_pharmacy.csv', db_table="pharmacy")
    Clinics = load_csv(db, 'catalog_clinics.csv',   db_table="clinics")
    Drugs = load_csv(db, 'catalog_clinics.csv',     db_table="drugs")
    Disease = load_csv(db, 'catalog_disease.csv',   db_table="diseases")

    db.close()

if __name__ == '__main__':
    main()

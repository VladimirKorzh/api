__author__ = 'Alex'

from ApiBase import ApiBase
from api import send_error
import json
import geopy;
from NetworkPacket import NetworkPacket

from playhouse.csv_loader import load_csv, dump_csv
from playhouse.shortcuts import *
from geopy.geocoders import Yandex

db = SqliteDatabase('temp.db')
Pharmacy = load_csv(db, 'pharmacy.csv')


class CatalogApi(ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        pass

    def on_request(self, ch, method, props, body):
        n = NetworkPacket()
        n.data['status'] = 'OK'
        n.data['msg'] = toJson(Pharmacy)
        response = n.toJson()

        self.send(str(self.map[self.server_queue]), "pong")
        self.send(str(self.map[self.client_queue]), response)
        self.stop()


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

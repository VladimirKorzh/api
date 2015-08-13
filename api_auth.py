__author__ = 'vladimir'
from peewee import *
from ApiBase import ApiBase
from api import send_error
from NetworkPacket import NetworkPacket
from playhouse.shortcuts import model_to_dict


"""
    "API": "auth"
    "msg": {
                "type": "login", "add_account"
            }
"""
db = SqliteDatabase('temp.db')

VALID_REQUEST_TYPES = ['login', 'add_account']
VALID_MEDIUM_TYPES = ['vk', 'fb', 'gp', 'phone']

class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    uuid = CharField(unique=True)
    db = TextField(null=True)

class Device(BaseModel):
    user = ForeignKeyField(User, related_name='devices', null=True)
    device_id = CharField(index=True)
    device_name = TextField()


class SocialData(BaseModel):
    user = ForeignKeyField(User, related_name='accounts', null=True)
    medium = CharField(null=True)
    value = CharField(null=True)
    data = TextField(null=True)


class ApiAuth(ApiBase):
    def __init__(self):
        ApiBase.__init__(self)
        self.db = db
        self.db.connect()
        try:
            #self.db.drop_tables([User, SocialData, Device])
            self.db.create_tables([User, SocialData, Device])
        except OperationalError:
            pass

    def on_request(self, ch, method, props, body):
        try:
            pkt = NetworkPacket.fromJson(body)
            type = pkt.data['func']

            #check for valid request
            if type in VALID_REQUEST_TYPES:
                if type == 'login':
                    self.handle_login(pkt)
                if type == 'add_account':
                    self.handle_addaccount(pkt)
            else:
                send_error(ch, method, props, body, 'Invalid request field type')
        except Exception, e:
            print "ERROR", str(e)
        db.close()

    def handle_login(self, pkt):
        # lets check his account information first
        # medium: phone, vk, fb, gp, loginpass
        medium = pkt.data['message']['medium_type']
        value = pkt.data['message']['medium_data']

        if medium == 'guest':
            userDevice, createdDevice = Device.get_or_create( device_id=pkt.data['message']['device_data']['device_id'],
                                                              device_name=pkt.data['message']['device_data']['device_name'])
            userDevice.save()

            n = NetworkPacket()
            n.data['status'] = "OK"
            n.data['message'] = ''

            self.send(str(self.map[self.client_queue]), n.toJson())



        if medium in VALID_MEDIUM_TYPES:

            if medium in ['vk','fb','gp']:
                url = value['url']
                userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=url)
                uuid = self.generate_uuid(url)
            if medium in ['phone']:
                userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=value)
                uuid = self.generate_uuid(value)

            if createdSocial == False:
                # user exists
                user = userSocialData.user
                print "-- returning user"
            else:
                # new user
                user = User(db=None, uuid=uuid)
                user.save()

                userDevice, createdDevice = Device.get_or_create( device_id=pkt.data['message']['device_data']['device_id'],
                                                                  device_name=pkt.data['message']['device_data']['device_name'])
                userDevice.user = user
                userDevice.save()

                userSocialData.user = user
                userSocialData.data = pkt.data['message']['medium_data']
                userSocialData.save()

                user.save()

                print "-- new device: ", createdDevice
                print "-- new social: ", createdSocial

            n = NetworkPacket()
            n.data['status'] = "OK"
            n.data['message'] = {}
            n.data['message']['db'] = user.db
            n.data['message']['uuid'] = user.uuid

            self.send(str(self.map[self.client_queue]), n.toJson())

        else:
            n = NetworkPacket()
            n.data['status'] = "ERROR"
            n.data['message'] = 'Invalid login medium'
            self.send(str(self.map[self.client_queue]), n.toJson())


    def handle_addaccount(self, pkt):
        try:
            uuid = pkt.data['uuid']
            medium = pkt.data['message']['medium_type']
            value = pkt.data['message']['medium_data']


            # find user
            user = User.get(User.uuid == uuid)

            if medium in VALID_MEDIUM_TYPES:
                if medium in ['vk','fb','gp']:
                    url = value['url']
                    userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=url)
                    uuid = self.generate_uuid(url)
                if medium in ['phone']:
                    userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=value)
                    uuid = self.generate_uuid(value)

                if createdSocial == True:
                    userSocialData = user
                    userSocialData.data = pkt.data['message']['medium_data']
                    userSocialData.save()
                    user.save()

                    n = NetworkPacket()
                    n.data['status'] = "OK"
                    n.data['message'] = {}

                    self.send(str(self.map[self.client_queue]), n.toJson())
                else:
                    n = NetworkPacket()
                    n.data['status'] = "ERROR"
                    n.data['message'] = 'Social account is linked to another User'

                    self.send(str(self.map[self.client_queue]), n.toJson())
            else:
                n = NetworkPacket()
                n.data['status'] = "ERROR"
                n.data['message'] = 'Invalid login medium'
                self.send(str(self.map[self.client_queue]), n.toJson())

        except KeyError as e:
            print "KeyError: ",
            self.send(str(self.map[self.client_queue]), 'Have you forgotten some field?')
        except DoesNotExist as e:
            print "KeyError: ",
            self.send(str(self.map[self.client_queue]), 'User with this UUID does not exist')


    def generate_uuid(self, value):
        import uuid
        uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, value.encode('utf-8')))
        return uuid


def main():
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    n = NetworkPacket()
    n.data['api'] = 'auth'
    n.data['func'] = 'login'

    n.data['message'] = {}
    n.data['message']['medium_type'] = 'phone'
    n.data['message']['medium_data'] = '2334124312'

    n.data['message']['device_data'] = {}
    n.data['message']['device_data']['device_id'] = 'test_id'
    n.data['message']['device_data']['device_name'] = 'test_name'
    pp.pprint(n.data)

    print "\n", n.toJson(),"\n"

# {   'accounts': [{   'data': u'korshakv', 'id': 1, 'medium': u'vk'}],
#     'db': None,
#     'devices': [   {   'device_id': u'test_id',
#                        'device_name': u'test_name',
#                        'id': 1}],
#     'fb': None,
#     'gp': None,
#     'id': 1,
#     'phone': None,
#     'uuid': '13ab9ad4-4904-5fa7-91d6-b5808245b46b',
#     'vk': u'korshakv'}

    n.data['api'] = 'auth'
    n.data['func'] = 'add_account'
    n.data['uuid'] = '488416f4-fcaf-5027-8c63-0105cfa213ea'



    n.data['message'] = {}
    n.data['message']['medium_type'] = 'fb'
    n.data['message']['medium_data'] = {'url':'www.google.com'}


    n.data['message']['device_data'] = {}
    n.data['message']['device_data']['device_id'] = 'test_id'
    n.data['message']['device_data']['device_name'] = 'test_name'
    pp.pprint(n.data)

    print "\n", n.toJson(),"\n"

if __name__ == '__main__':
    main()


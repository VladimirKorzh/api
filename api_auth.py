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
# TODO db.close()
db = SqliteDatabase('temp.db')

VALID_REQUEST_TYPES = ['login', 'add_account']
VALID_MEDIUM_TYPES = ['vk', 'fb', 'gp', 'phone']

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    uuid = CharField(unique=True)
    db = TextField(null=True)

    phone = CharField(null=True)
    vk = CharField(null=True)
    fb = CharField(null=True)
    gp = CharField(null=True)

class Device(BaseModel):
    user = ForeignKeyField(User, related_name='devices', null=True)
    device_id = CharField(index=True)
    device_name = TextField()

class SocialData(BaseModel):
    user = ForeignKeyField(User, related_name='accounts')
    medium = CharField(null=True)
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
        pkt = NetworkPacket.fromJson(body)
        type = pkt.data['message']['type']

        #check for valid request
        if type in VALID_REQUEST_TYPES:
            if type == 'login':
                self.handle_login(pkt)
            if type == 'add_account':
                self.handle_addaccount(pkt)
        else:
            send_error(ch, method, props, body, 'Invalid request field type')
        db.close()

    def handle_login(self, pkt):
        # lets check his account information first
        # medium: phone, vk, fb, gp, loginpass
        medium = pkt.data['message']['medium_type']
        value = pkt.data['message']['medium_data']

        if medium in VALID_MEDIUM_TYPES:
            if medium == 'vk':
                user, createdUser = User.get_or_create(vk=value, defaults={'uuid':self.generate_uuid(pkt)})
            if medium == 'fb':
                user, createdUser = User.get_or_create(fb=value, defaults={'uuid':self.generate_uuid(pkt)})
            if medium == 'gp':
                user, createdUser = User.get_or_create(gp=value, defaults={'uuid':self.generate_uuid(pkt)})
            if medium == 'phone':
                user, createdUser = User.get_or_create(phone=value, defaults={'uuid':self.generate_uuid(pkt)})

            userDevice, createdDevice = Device.get_or_create(user=user,
                                                  device_id=pkt.data['message']['device_data']['device_id'],
                                                  device_name=pkt.data['message']['device_data']['device_name'])
            userDevice.save()

            userSocialData, createdSocial = SocialData.get_or_create(user=user, medium=medium, data=value)
            userSocialData.save()

            user.save()

            n = NetworkPacket()
            n.data['status'] = "OK"
            n.data['message'] = { 'user' : str(model_to_dict(user, backrefs=True)) }

            print createdUser, createdDevice, createdSocial

            import pprint
            bbb = model_to_dict(user, backrefs=True)
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(bbb)

            self.send(str(self.map[self.client_queue]), n.toJson())

        else:
            n = NetworkPacket()
            n.data['status'] = "ERROR"
            n.data['message'] = 'Invalid login medium'
            self.send(str(self.map[self.client_queue]), n.toJson())


    def handle_addaccount(self, pkt):
        try:
            medium = pkt.data['message']['medium_type']
            value = pkt.data['message']['medium_data']
            uuid = pkt.data['message']['uuid']

            user = User.get(User.uuid == uuid)

            if medium in VALID_MEDIUM_TYPES:
                if medium == 'vk':
                    user.vk = value
                if medium == 'fb':
                    user.fb = value
                if medium == 'gp':
                    user.gp = value
                if medium == 'phone':
                    user.phone = value

                user.save()
                userSocialData, createdSocial = SocialData.get_or_create(user=user, medium=medium, data=value)
                userSocialData.save()



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

        except KeyError as e:
            print "KeyError: ",
            self.send(str(self.map[self.client_queue]), 'Have you forgotten some field?')
        # except DoesNotExist as e:
        #     print "KeyError: ",
        #     self.send(str(self.map[self.client_queue]), 'User with this UUID does not exist')


    def generate_uuid(self, pkt):
        import uuid
        uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, pkt.data['message']['medium_data'].encode('utf-8')))
        return uuid


def main():
    n = NetworkPacket()
    n.data['api'] = 'auth'
    n.data['message'] = {}
    n.data['message']['medium_type'] = 'vk'
    n.data['message']['medium_data'] = 'korshakv'
    n.data['message']['type'] = 'login'

    n.data['message']['device_data'] = {}
    n.data['message']['device_data']['device_id'] = 'test_id'
    n.data['message']['device_data']['device_name'] = 'test_name'
    print n.toJson()

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
    n.data['message'] = {}
    n.data['message']['medium_type'] = 'fb'
    n.data['message']['medium_data'] = '+asdasd'
    n.data['message']['type'] = 'add_account'
    n.data['message']['uuid'] = '13ab9ad4-4904-5fa7-91d6-b5808245b46b'

    n.data['message']['device_data'] = {}
    n.data['message']['device_data']['device_id'] = 'test_id'
    n.data['message']['device_data']['device_name'] = 'test_name'
    print n.toJson()


if __name__ == '__main__':
    main()


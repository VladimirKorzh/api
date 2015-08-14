__author__ = 'vladimir'
from ApiBase import ApiBase
from api import send_error
from NetworkPacket import NetworkPacket
from DatabaseModels import *
import json

"""
    ['api'] = 'auth'
    ['func'] = 'login'
    ['message']
        ['medium_type']
        ['medium_data']

        ['device_data']
            ['device_id']
            ['device_name']


    vk, fb, gp: <medium_data> put profile url
    phone: <medium_data> put phone number
    email: <medium_data> put {'login':<login>, 'password':<passoword>}

"""


VALID_REQUEST_TYPES = ['login', 'add_account', 'register']
VALID_MEDIUM_TYPES = ['vk', 'fb', 'gp', 'phone', 'email']


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
        # try:
        pkt = NetworkPacket.fromJson(body)
        type = pkt.data['func']

        #check for valid request
        if type in VALID_REQUEST_TYPES:
            if type in ['login', 'register']:
                self.handle_login(pkt)
            if type == 'add_account':
                self.handle_addaccount(pkt)
        else:
            send_error(ch, method, props, body, 'Invalid request field type')
        # except Exception, e:
        #     print "ERROR", str(e), e.message, e.__class__
        self.db.close()


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
            return

        if medium not in VALID_MEDIUM_TYPES:
            n = NetworkPacket()
            n.data['status'] = "ERROR"
            n.data['message'] = 'Invalid login medium'
            self.send(str(self.map[self.client_queue]), n.toJson())
            return
        else:

            if medium in ['vk', 'fb', 'gp']:
                url = value['url']
                userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=url)
                uuid = self.generate_uuid(url)

            if medium in ['phone']:
                userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=value)
                uuid = self.generate_uuid(value)

            if medium in ['email']:
                userSocialData, createdSocial = self.handle_email(pkt)
                uuid = uuid = self.generate_uuid(value['login'])

            if userSocialData is not None:
                if createdSocial == False:
                    # user exists if have not created a social account for him
                    user = userSocialData.user
                    print " -- user account exists ", user
                else:
                    print " -- new account is going to be created"
                    # we have a new incoming user trying to login
                    user = self.create_new_user(userSocialData, db, uuid, pkt)


                # prepare the reply packet
                n = NetworkPacket()
                n.data['status'] = "OK"
                n.data['message'] = {}
                n.data['message']['db'] = user.db
                n.data['message']['uuid'] = user.uuid
                self.send(str(self.map[self.client_queue]), n.toJson())
                return



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
                    n.data['message']['uuid'] = uuid
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
            n = NetworkPacket()
            n.data['status'] = "ERROR"
            n.data['message'] = 'Have you forgotten some field?'
            self.send(str(self.map[self.client_queue]), n.toJson())

        except DoesNotExist as e:
            print "KeyError: ",
            n = NetworkPacket()
            n.data['status'] = "ERROR"
            n.data['message'] = 'User with this UUID does not exist'
            self.send(str(self.map[self.client_queue]), n.toJson())

    def handle_email(self, pkt):
        medium = pkt.data['message']['medium_type']
        value = pkt.data['message']['medium_data']
        userSocialData = None

        try:
            userSocialData = SocialData.select().where(SocialData.value == value['login']).get()
        except Exception:
            print ' -- failed to select userSocialData'


        if pkt.data['func'] == 'register':
            # check if user already exists in database
            if userSocialData is not None:
                n = NetworkPacket()
                n.data['status'] = "ERROR"
                n.data['message'] = "User with these credentials exists"
                self.send(str(self.map[self.client_queue]), n.toJson())
                return None, None
            else:
                # create new social data object
                userSocialData = SocialData(medium=medium, data=str(value), value=value['login'])

                # try to save object
                userSocialData.save()
                createdSocial = True
                return userSocialData, createdSocial

        if pkt.data['func'] == 'login':

            if userSocialData is None:
                n = NetworkPacket()
                n.data['status'] = "ERROR"
                n.data['message'] = "User with these credentials does not exist"
                self.send(str(self.map[self.client_queue]), n.toJson())
                return None, None
            else:

                d = json.loads(userSocialData.data.replace("'","\"").replace("u\"", "\""))

                if d['password'] == value['password']:
                    uuid = self.generate_uuid(value['login'])
                    createdSocial = False

                    print ' -- password is valid'
                    return userSocialData, createdSocial

                else:
                    print ' -- user with such login/pass not found '
                    n = NetworkPacket()
                    n.data['status'] = "ERROR"
                    n.data['message'] = "Password is invalid"
                    self.send(str(self.map[self.client_queue]), n.toJson())
                    return None, None


    def generate_uuid(self, value):
        import uuid
        uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, value.encode('utf-8')))
        return uuid

    def create_new_user(self, userSocialData, db, uuid, pkt):
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

        print " -- new device: ", createdDevice
        print " -- User has been created"
        return user


def main():
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    n = NetworkPacket()
    n.data['api'] = 'auth'
    n.data['func'] = 'login'

    n.data['message'] = {}
    n.data['message']['medium_type'] = 'email'
    n.data['message']['medium_data'] = {}
    n.data['message']['medium_data']['login'] = 'vladimirkorshak@gmail.com'
    n.data['message']['medium_data']['password'] = '228121389'
    n.data['message']['medium_data']['action'] = 'register'

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



 # {"message": {"medium_type": "email", "device_data": {"device_name": "test_name", "device_id": "test_id"}, "medium_data": "vladimirkorshak@gmail.com"}, "api": "auth", "func": "login"}


    # {"message": {"medium_type": "fb", "device_data": {"timestamp": 1439448064478, "device_name": "LGE Nexus 4", "device_id": "9a9622ef5c84229"}, "medium_data": {"name": "Alex Yermolenko", "DOB": "", "gender": "male", "url": "https://www.facebook.com/app_scoped_user_id/10202972046261630/", "email": "alexvw@ukr.net", "fotourl": "https://graph.facebook.com/10202972046261630/picture?type=large"}}, "api": "auth", "func": "login"}


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


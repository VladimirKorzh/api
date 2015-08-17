__author__ = 'vladimir'


from NetworkPacket import NetworkPacket
from DatabaseModels import *
import json
"""
    ['api'] = 'auth'
    ['func'] = 'login'
    ['message']
        ['medium_type']   -> email
        ['medium_data']['login']   -> vladimirkorshak@gmail.com
        ['medium_data']['password'] -> 228121389

        ['device_data']
            ['device_id']
            ['device_name']


    vk, fb, gp: <medium_data> put profile url
    phone: <medium_data> put phone number
    email: <medium_data> put {'login':<login>, 'password':<password>}

"""


VALID_REQUEST_TYPES = ['login', 'add_account', 'register']
VALID_MEDIUM_TYPES = ['vk', 'fb', 'gp', 'phone', 'email', 'guest']


class ApiAuth():
    def __init__(self):
        pass

    def on_request(self, ch, method, props, body):
        pkt = NetworkPacket.fromJson(body)
        type = pkt.data['func']

        #check for valid request
        if type in VALID_REQUEST_TYPES:
            if type in ['login', 'register']:
                self.handle_login(ch, method, props, pkt)
            if type == 'add_account':
                self.handle_addaccount(ch, method, props, pkt)
        else:
            ApiWorker.send_error(ch, method, props, 'Invalid request field type')

    def handle_login(self, ch, method, props, pkt):
        # lets check his account information first
        # medium: phone, vk, fb, gp, loginpass
        medium = pkt.data['message']['medium_type']

        if medium == 'guest':
            userDevice, createdDevice = Device.get_or_create( device_id=pkt.data['message']['device_data']['device_id'],
                                                              device_name=pkt.data['message']['device_data']['device_name'])
            userDevice.save()

            n = NetworkPacket()
            n.data['status'] = "OK"
            n.data['message'] = None
            ApiWorker.send_reply(ch, method, props, n.toJson())
            return

        value = pkt.data['message']['medium_data']

        if medium not in VALID_MEDIUM_TYPES:
            ApiWorker.send_error(ch, method, props, 'Invalid login medium')
            return
        else:
            userSocialData = None
            createdSocial = None
            uuid = None
            if medium in ['vk', 'fb', 'gp']:
                url = value['url']
                userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=url)
                uuid = self.generate_uuid(url)

            if medium in ['phone']:
                userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=value)
                uuid = self.generate_uuid(value)

            if medium in ['email']:
                userSocialData, createdSocial = self.handle_email(ch, method, props, pkt)
                uuid = uuid = self.generate_uuid(value['login'])

            if userSocialData is not None:
                if createdSocial is False:
                    # user exists if have not created a social account for him
                    user = userSocialData.user
                    print " -- user account exists "
                else:
                    print " -- new account is going to be created"
                    # we have a new incoming user trying to login
                    user = self.create_new_user(userSocialData, uuid, pkt)


                # prepare the reply packet
                n = NetworkPacket()
                n.data['status'] = "OK"
                n.data['message'] = {}

                if user.db is not None:
                    n.data['message']['db'] = byteify(json.loads(user.db))
                else:
                    n.data['message']['db'] = None

                n.data['message']['uuid'] = user.uuid
                ApiWorker.send_reply(ch, method, props, n.toJson())
                return

    def handle_addaccount(self, ch, method, props, pkt):
        try:
            uuid = pkt.data['uuid']
            medium = pkt.data['message']['medium_type']
            value = pkt.data['message']['medium_data']

            # find user
            user = User.get(User.uuid == uuid)

            if medium in VALID_MEDIUM_TYPES:
                createdSocial = None
                userSocialData = None

                if medium in ['vk','fb','gp']:
                    url = value['url']
                    userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=url)
                    uuid = self.generate_uuid(url)
                if medium in ['phone']:
                    userSocialData, createdSocial = SocialData.get_or_create(medium=medium, value=value)
                    uuid = self.generate_uuid(value)

                if createdSocial == True:
                    userSocialData.user = user
                    userSocialData.data = pkt.data['message']['medium_data']
                    userSocialData.save()
                    user.save()

                    n = NetworkPacket()
                    n.data['status'] = "OK"
                    n.data['message'] = {}
                    n.data['message']['uuid'] = uuid
                    ApiWorker.send_reply(ch, method, props, n.toJson())
                else:
                    ApiWorker.send_error(ch, method, props, 'Social account is linked to another User')
            else:
                ApiWorker.send_error(ch, method, props, 'Invalid login medium')

        except KeyError as e:
            ApiWorker.send_error(ch, method, props, 'Have you forgotten some field? ' + str(e.message))

        except DoesNotExist as e:
            ApiWorker.send_error(ch, method, props, 'User with this UUID does not exist.' + str(e.message))

    def handle_email(self, ch, method, props, pkt):
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
                ApiWorker.send_error(ch, method, props, "User with these credentials exists")
                return None, None
            else:
                # create new social data object
                print value
                userSocialData = SocialData(medium=medium, data=value, value=value['login'])

                # try to save object
                userSocialData.save()
                createdSocial = True
                return userSocialData, createdSocial

        if pkt.data['func'] == 'login':

            if userSocialData is None:
                ApiWorker.send_error(ch, method, props, "User with these credentials does not exist")
                return None, None
            else:
                print userSocialData.data
                d = json.loads(userSocialData.data)

                if d['password'] == value['password']:
                    uuid = self.generate_uuid(value['login'])
                    createdSocial = False

                    print ' -- password is valid'
                    return userSocialData, createdSocial

                else:
                    print ' -- user with such login/pass not found '
                    ApiWorker.send_error(ch, method, props, "Password is invalid")
                    return None, None


    def generate_uuid(self, value):
        import uuid
        uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, value.encode('utf-8')))
        return uuid

    def create_new_user(self, userSocialData, uuid, pkt):
        user = User(db=None, uuid=uuid)
        user.save()

        userDevice, createdDevice = Device.get_or_create( device_id=pkt.data['message']['device_data']['device_id'],
                                                          device_name=pkt.data['message']['device_data']['device_name'])
        userDevice.user = user
        userDevice.save()

        userSocialData.user = user
        userSocialData.data = byteify(json.dumps(pkt.data['message']['medium_data']))
        userSocialData.save()

        user.save()

        print " -- new device: ", createdDevice
        print " -- User has been created"
        return user


from apiWorker import byteify, ApiWorker


def main():
    # import pprint
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(n.data)
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


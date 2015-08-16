__author__ = 'vladimir'

from peewee import *

# db = SqliteDatabase('nurse_mobile.db')
db = MySQLDatabase("nurse-mobile-py", host="sc.nurse-mobile.com", user="nurse_mobile_py", passwd="X7w7U1o6")

class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    uuid = CharField(unique=True)
    db = TextField(null=True)
    timestamp = IntegerField(null=True)


class Device(BaseModel):
    user = ForeignKeyField(User, related_name='devices', null=True)
    device_id = CharField(index=True)
    device_name = TextField()


class SocialData(BaseModel):
    user = ForeignKeyField(User, related_name='accounts', null=True)
    medium = CharField(null=True)
    value = CharField(null=True)
    data = TextField(null=True)

__author__ = 'vladimir'

from peewee import *

db = SqliteDatabase('nurse_mobile.db')

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


class Notification(BaseModel):
    receiver = ForeignKeyField(User, related_name='inbox', null=False)
    sender = ForeignKeyField(User, related_name='sent', null=False)

    type = IntegerField()

    message = TextField()
    status = BooleanField()
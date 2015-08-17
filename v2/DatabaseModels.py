__author__ = 'vladimir'

from peewee import *
import datetime

db = None

db = MySQLDatabase("nurse-mobile-py", host="localhost", user="nurse_mobile_py", passwd="X7w7U1o6")

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
    created_date = DateTimeField(default=datetime.datetime.now)

    type = IntegerField()

    message = TextField()
    status = BooleanField()

class Pharmacy(BaseModel):
    id = CharField(primary_key=True)
    name = TextField(null=True)
    desc = TextField()
    phone = TextField()
    website = TextField()
    email = TextField()
    city = TextField()
    addr = TextField()
    metro = TextField()
    area = TextField()
    country = TextField()
    lon = CharField(null=True)
    lat = CharField(null=True)

if db is None:
    db = SqliteDatabase(':memory:')
    DB_TABLES = [User, SocialData, Device]
    db.create_tables(DB_TABLES)
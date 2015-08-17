__author__ = 'vladimir'
from DatabaseModels import *


DB_TABLES = [User, SocialData, Device]
def main():
    db.connect()
    try:
        print 'Resetting database...'
        db.drop_tables(DB_TABLES)
    except OperationalError as e:
        print 'Error occurred while resetting DB: ' + str(e.message)

    print 'Creating tables...'
    db.create_tables(DB_TABLES)
    db.close()
    print 'Done.'

if __name__ == '__main__':
    main()
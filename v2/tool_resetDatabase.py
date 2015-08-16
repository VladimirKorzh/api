__author__ = 'vladimir'
from DatabaseModels import *

def main():
    db.connect()
    try:
        print 'Resetting database...'
        db.drop_tables([User, SocialData, Device])
    except OperationalError as e:
        print 'Error occurred while resetting DB: ' + str(e.message)

    print 'Creating tables...'
    db.create_tables([User, SocialData, Device])
    db.close()
    print 'Done.'

if __name__ == '__main__':
    main()
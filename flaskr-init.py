import sys
import os
import getopt
import getpass
import json
from pprint import pprint
import cloudant

'''
usage:
python flaskr-init.py -u <username>

The user will be prompted for their password.

If the user and messages database do not exist create them and create
and create the apropriate views.
Otherwise exit with an error message.
'''

config = dict(
    user = '',
    password = '',
    )

def parse_args(argv):
    '''
    parse through the argument list and update the config dict as appropriate
    '''
    usage = 'python ' + os.path.basename(__file__) + ' -u <username>'
    try:
        opts, args = getopt.getopt(argv, "hu:", 
                                   ["user="
                                    ])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-u", "--user"):
            config['user'] = arg
    if config['user'] == '':
        print usage
        sys.exit()

def get_password():
    config['password'] = getpass.getpass('Password for {0}:'.format(config["user"]))

class FlaskrInit():
    def __init__(self, config):
        self.config = config
        self.userdbname = 'flaskr_user'
        self.messagedbname = 'flaskr_message'
        #this is a bit messy I need to be able to change a var name at runtime
        #there may be a better way to do it.
        self.db = dict()

    def create_db(self, account, dbname):
        '''
        create the a database <dbname> under account <account>
        '''
        self.db[dbname] = account.database(dbname)
        response = self.db[dbname].put()
        #response = a.put()
        #pprint(response)
        if 'error' in response.json():
            if response.json()['error'] == 'file_exists':
                print 'The user database "{0}" already exists! Aborting.'.format(dbname)
                sys.exit()
                
    def init_dbs(self):
        account = cloudant.Account(self.config['user'])
        response = account.login(self.config['user'], self.config['password'])
        
        self.create_db(account, self.userdbname)
        self.create_db(account, self.messagedbname)

    def create_design_docs(self):
        searchfunction = '''function(doc){
        index("text", doc.text);
        index("title", doc.title);
        index("author", doc.author);
        index("date", doc.date, {"facet": true})}'''
        
        message_search = dict(analyzer = 'standard',
                              index = searchfunction)

        app = self.db[self.messagedbname].design('app')
        #pprint(app)
        #app.put(data=message_search)
        app.put(data='{"keyname":"valuename"}')

def main(argv):
    parse_args(argv)
    get_password()
    initializer = FlaskrInit(config)
    initializer.init_dbs()
    initializer.create_design_docs()

if __name__ == "__main__":
    main(sys.argv[1:])

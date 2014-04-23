import sys
import os
import getopt
import getpass
import json
from pprint import pprint
import requests

'''
usage:
python flaskr-init.py -u <username>

The user will be prompted for their password.

If the user and messages database do not exist create them and create
and create the apropriate views.
Otherwise exit with an error message.
'''

config = dict(
    username = '',
    password = '',
    userdbname = 'flaskr_user',
    messagedbname = 'flaskr_message'
    )

def parse_args(argv):
    '''
    parse through the argument list and update the config dict as appropriate
    '''
    usage = 'python ' + os.path.basename(__file__) + ' -u <username>'
    try:
        opts, args = getopt.getopt(argv, "hu:", 
                                   ["username="
                                    ])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-u", "--username"):
            config['username'] = arg
    if config['username'] == '':
        print usage
        sys.exit()

def get_password():
    config['password'] = getpass.getpass('Password for {0}:'.format(config["username"]))

def init_params():
    config['baseurl'] = 'https://{0}.cloudant.com/'.format(config['username'])

def authenticate():
    header = {'Content-type': 'application/x-www-form-urlencoded'}
    url = config['baseurl'] + '_session'
    data = dict(name=config['username'],
                password=config['password'])
    r = requests.post(url, data = data, headers = header)
    #s = requests.Session()
    #s.auth = (config['username'], config['password'])
    #r = s.get(url)
    return(r.headers['set-cookie'])

def create_db(dbname, authcookie):
    '''
    create the a database <dbname> under account <account>
    '''
    header = {'Cookie': authcookie}
    url = config['baseurl'] + dbname
    response = requests.put(url, headers = header)
    if 'error' in response.json():
        if response.json()['error'] == 'file_exists':
            print 'The user database "{0}" already exists! Aborting.'.format(dbname)
            sys.exit()
                
def create_design_docs(messagedbname, authcookie):
    searchfunction = '''function(doc){
    index("text", doc.text);
    index("title", doc.title);
    index("author", doc.author);
    index("date", doc.date, {"facet": true})}'''
    
    message_search = dict(analyzer = 'standard',
                          index = searchfunction)
    header = {'Cookie': authcookie}
    url = config['baseurl'] + messagedbname + '/'
    #put the design doc in here
#    response = requests.put

def init_dbs():
    init_params()
    authcookie = authenticate()
    create_db(config['userdbname'], authcookie)
    create_db(config['messagedbname'], authcookie)
    create_design_docs(config['messagedbname'], authcookie)
    
def main(argv):
    parse_args(argv)
    get_password()
    init_dbs()

if __name__ == "__main__":
    main(sys.argv[1:])

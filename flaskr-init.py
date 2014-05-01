import sys
import os
import getopt
import getpass
import json
import urllib
from pprint import pprint
import requests

'''
usage:
python flaskr-init.py -u <username>

The user will be prompted for their password.

If the user and messages database do not exist create them, create the 
apropriate views and show the api key/password.

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
    response = requests.post(url, data = data, headers = header)
    if 'error' in response.json():
        if response.json()['error'] == 'forbidden':
            print response.json()['reason']
            sys.exit()
    return(response.headers['set-cookie'])

def generate_api_key(authcookie):
    '''
    generate an api key and return a dict with the username/password
    '''
    url = 'https://cloudant.com/api/generate_api_key'
    header = {'Cookie': authcookie}
    r = requests.post(url, headers = header)
    key = json.loads(r.text)['key']
    password= json.loads(r.text)['password']
    api_key = dict(user = key,
                   password = password)
    print 'API Key generated'
    print 'key: {0}'.format(key)
    print 'password: {0}'.format(password)
    return(api_key)

def create_db(dbname, authcookie):
    '''
    create the a database <dbname> under account <account>
    '''
    url = config['baseurl'] + dbname
    header = {'Cookie': authcookie}
    response = requests.put(url, headers = header)
    if 'error' in response.json():
        if response.json()['error'] == 'file_exists':
            print response.json()['reason']
            sys.exit()

def set_perms(dbname, username, authcookie):
    '''
    Let's hope this version works
    curl -X POST https://cloudant.com/api/set_permissions -H 'Cookie: <authcooke>' -d 'database=<username>/<dbname>&username=<username>&roles=_writer&roles=_reader'
    '''
    url = 'https://cloudant.com/api/set_permissions'
    #data = 'database={0}/{1}&username={2}&roles=_reader&roles=_writer'.format(config['username'], dbname, username)
    data = dict( database = config['username'] + '/' + dbname,
                 username = username,
                 roles = ['_reader', '_writer']
                 )
                                 
    header = {'Cookie': authcookie}
    #the doseq=True option let's you put a list as a value in the dict and
    #have it properly encode
    response = requests.post(url,
                             data = urllib.urlencode(data, doseq=True),
                             headers = header)
                
def create_design_docs(messagedbname, authcookie):
    url = config['baseurl'] + messagedbname + '/_design/app'
    searchfunction = '''function(doc){
    index("text", doc.text, {"store":true});
    index("title", doc.title, {"store":true});
    index("author", doc.author, {"store":true});
    index("date", doc.date, {"store":true, "facet": true})}'''

    messages = dict(index = searchfunction)
    indexes = dict(messages = messages)

    message_search = dict(analyzer = 'standard',
                          indexes = indexes)
    header = {'Cookie': authcookie, 'Content-Type': 'application/json'}
    response = requests.put(url,
                            data = json.dumps(message_search),
                            headers = header)

def init_dbs():
    init_params()
    authcookie = authenticate()
    api_key = generate_api_key(authcookie)
    create_db(config['userdbname'], authcookie)
    create_db(config['messagedbname'], authcookie)
    set_perms(config['userdbname'], api_key['user'], authcookie)
    set_perms(config['messagedbname'], api_key['user'], authcookie)
    create_design_docs(config['messagedbname'], authcookie)
    
def main(argv):
    parse_args(argv)
    get_password()
    init_dbs()

if __name__ == "__main__":
    main(sys.argv[1:])

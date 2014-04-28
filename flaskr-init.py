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
    #This doesn't work at all. It returns a status code 400 and
    #{u'error': u'username_required', u'reason': u'Username not specified.'}
    url = 'https://cloudant.com/api/set_permissions'
    data = dict(database = '{0}/{1}'.format(username,dbname),
                username = username,
                roles = ['_reader', '_writer'])
    header = {'Cookie': authcookie}
    response = requests.post(url,
                             data = json.dumps(data),
                             headers = header)
    '''
    #This returns a status code of 200 and
    #{u'ok': True}
    #But I don't end up with any additional users for the database.
    url = 'https://cloudant.com/api/set_permissions?database={1}/{0}&username={1}&roles=_reader&roles=_writer'.format(dbname, username)
    header = {'Cookie': authcookie, 'Content-type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers = header)
    print url
#    print json.dumps(data)
    print header
    pprint(response.json())
    print(response.status_code)
                
def create_design_docs(messagedbname, authcookie):
    url = config['baseurl'] + messagedbname + '/_design/app'
    searchfunction = '''function(doc){
    index("text", doc.text);
    index("title", doc.title);
    index("author", doc.author);
    index("date", doc.date, {"facet": true})}'''
    
    message_search = dict(analyzer = 'standard',
                          index = searchfunction)
    header = {'Cookie': authcookie, 'Content-Type': 'application/json'}
    #print url
    response = requests.put(url,
                            data = json.dumps(message_search),
                            headers = header)
    #print response.json()

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

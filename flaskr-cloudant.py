# all the imports
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import time
import sys
import os
import getopt
import logging
import cloudant
from pprint import pprint

# configuration
# check flaskr.settings
# To run export FLASKR_SETTINGS='flaskr.settings'

# create our little application :)
# it seems that using __name__ is not canonical
# but I don't really understand why
# http://flask.pocoo.org/docs/api/
app = Flask(__name__)

# get configuration details (either from this or external file)
app.config.from_object(__name__)

# Set this environment variable using export FLASKR_SETTINGS=....
#FLASKR_SETTINGS = '/Users/Claudius/src/flaskr/flaskr.settings'
app.config.from_envvar('FLASKR_SETTINGS', silent=False)

config = dict(username='',
              password='')

def parse_args(argv):
        '''
        parse through the argument list and update the config dict as appropriate
        '''
        usage = 'python ' + os.path.basename(__file__) + ' -u <username> -p <password>'
        try:
                opts, args = getopt.getopt(argv, "hu:p:", 
                                           ["username=",
                                            "password="
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
                elif opt in ("-p", "--password"):
                        config['password'] = arg
        if config['username'] == '' or config['password'] == '':
                print usage
                pprint(config)
                sys.exit()

# Make sure you are installed
def connect_db(account_name, database_name):
	"""Returns a new connection to the Cloudant database."""
	app.logger.debug('Connecting to Cloudant database...')
	#account = cloudant.Account(app.config['ACCOUNT'])
        account = cloudant.Account(account_name)
        account.login(config['username'],config['password'])
	return account.database(database_name)
	#app.logger.debug('Connected to Cloudant database...')

@app.before_request
def before_request():
    """Make sure we are connected to the database each request."""
    g.db = connect_db(app.config['ACCOUNT'], app.config['MESSAGEDB'])
    #Entry.set_db(g.db)

@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    # nothing here

@app.route('/')
def show_entries():
    # Using _all_docs API endpoint and setting include_docs=true
	options = dict(include_docs=True)
	entries = []
	for row in g.db.all_docs(params=options):
		print row
		doc = row['doc']
		if doc.get('text') and doc.get('title'):
			entries.append(doc)
	return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	app.logger.debug('before entry added')
	entry = dict(author='test', title=request.form['title'], text=request.form['text'], date=time.time())
	# Cloudant.py post() will convert to json and pass in body of http request to load document
	g.db.post(params=entry)	
	app.logger.debug('after entry added')
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

@app.route('/search', methods=['GET', 'POST'])
def search():
	error = None
	if request.method == 'POST':
#		if request.form['searchterm'] != app.config['USERNAME']:
                return redirect(url_for('show_entries'))

@app.route('/createaccount', methods=['GET', 'POST'])
def createaccount():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('createaccount.html', error=error)

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))

app.debug = True
app.logger.setLevel(logging.DEBUG)
 
#logging.basicConfig(filename='example.log',level=logging.INFO)

def main(argv):
        parse_args(argv)
	app.run()

if __name__ == '__main__':
        main(sys.argv[1:])

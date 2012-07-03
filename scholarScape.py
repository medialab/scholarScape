###################
##   TODO LIST   ##
###################
# _ Change users managment to database
# _ Repair the tor proxy
# _ Add feedback to the 'add user' process
# Lors du clic sur Nothing to do together, verifier que tout est selectionne ou que rien n'est selectionne
# appel de la fonction : duplicates.merge_duplicates(col, dup_col, publications_ids...)

import os
import json
import pprint
import urllib
import urllib2
import hashlib
import pystache
import subprocess
from server.rpc import scholarScape
from server.utils import users, config, scholarize, data_dir, root_dir, web_client_dir
from datetime import date
from contextlib import nested
from txjsonrpc.web import jsonrpc
from urllib import quote_plus as qp
from pymongo import Connection, errors
from bson import json_util, objectid
from zope.interface import implements, Interface
from twisted.protocols import basic
from twisted.web import resource, server, static
from twisted.web.server import NOT_DONE_YET
from twisted.application import service, internet
from twisted.cred import checkers, credentials, portal
from itertools import permutations
import scholar.scholar.duplicates as duplicates

class IUser(Interface):
    '''A user account.
    '''

    def getUserName(self):
        '''Returns the name of the user account.
        '''

class User(object):
    implements(IUser)

    def __init__(self, name):
        self.__name = name

    def getUserName(self):
        return self.__name

# Read config file and fill in mongo and scrapyd config files with custom values
# Try to connect to DB, send egg to scrapyd server

# Check if the DB is available
try :
    Connection("mongodb://" + config['mongo']['user'] + ":" +
            config['mongo']['passwd'] + "@" + config['mongo']['host'] + ":" + str(config['mongo']['port']) + "/" + config['mongo']['database'] )
except errors.AutoReconnect:
    print "Could not connect to mongodb server", config['mongo']
    exit()

# Render the pipeline template
print "Rendering pipelines.py with values from config.json..."
try :
    with nested(open("scholar/scholar/pipelines-template.py", "r"), open("scholar/scholar/pipelines.py", "w")) as (template, generated):
        generated.write(pystache.render(template.read(), config['mongo']))
except IOError as e:
    print "Could not open either pipeline-template file or pipeline file"
    print "scholar/scholar/pipelines-template.py", "scholar/scholar/pipelines.py"
    print e
    exit()

# Render the scrapy cfg
print "Rendering scrapy.cfg with values from config.json..."
try :
    with nested(open("scholar/scrapy-template.cfg", "r"), open("scholar/scrapy.cfg", "w")) as (template, generated):
        generated.write(pystache.render(template.read(), config['scrapyd']))
except IOError as e:
    print "Could not open either scrapy.cfg template file or scrapy.cfg"
    print "scholar/scrapy-template.cfg", "scholar/scrapy.cfg"
    print e
    exit()

# Deploy the egg
print "Sending scholarScrape's scrapy egg to scrapyd server..."
os.chdir("scholar")
p = subprocess.Popen(['scrapy', 'deploy'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, errors = p.communicate()
print output, errors
try :
    output = json.loads(output)
    if output['status'] != "ok" :
        print "There was a problem sending the scrapy egg."
        print output, errors
        exit()
except ValueError:
    print "There was a problem sending the scrapy egg."
    print output, errors
    exit()
print "The egg was successfully sent to scrapyd server", config['scrapyd']['host'], "on port", config['scrapyd']['port']
os.chdir("..")

print "Starting the server"

class Home(resource.Resource):
    isLeaf = False

    def __init__(self):
        resource.Resource.__init__(self)

    def getChild(self, name, request) :
        if name == '' :
            return self
        return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
        request.setHeader('Content-Type', 'text/html; charset=utf-8')
        # Get session user
        session = request.getSession()
        user = session.getComponent(IUser)
        # If the user is not connected, redirection to the login page
        if not user :
            login = ''
            launch = False
            explore = False
            admin = False
            logout = False
            path = os.path.join(root_dir, web_client_dir, 'login.html')
        else:
            # Send the salt and hashed login as an hidden tag
            login = hashlib.md5(config['salt'] + user.getUserName()).hexdigest()
            role = users[user.getUserName()]['role']
            if role == 'explorer' :
                launch = False
                explore = True
                admin = False
                logout = True
            elif role == 'launcher' :
                launch = True
                explore = True
                admin = False
                logout = True
            elif role == 'admin' :
                launch = True
                explore = True
                admin = True
                logout = True
            if 'page' in request.args and request.args['page'][0] != 'layout':
                # If the page is login then reset user session
                if request.args['page'][0] == 'login' :
                    session.unsetComponent(IUser)
                    launch = False
                    explore = False
                    admin = False
                    logout = False
                path = os.path.join(root_dir, web_client_dir, "%s.html" % request.args['page'][0])
                path = path if os.path.exists(path) else os.path.join(root_dir, web_client_dir, '404.html')
            else:
                path = os.path.join(root_dir, web_client_dir, 'index.html')
        layout_path = os.path.join(root_dir, web_client_dir, 'layout.html')
        with nested(open(path, 'r'), open(layout_path, "r")) as (fpage, flayout):
            layout = flayout.read().decode('utf-8')
            page = fpage.read().decode('utf-8')
            content = pystache.render(layout, {'contenu' : page, 'login' : login, 'launch' : launch, 'explore' : explore, 'admin' : admin, 'logout' : logout})
        return content.encode('utf-8')

    def render_POST(self, request) :
        # Collect common args
        page = request.args['page'][0]
        login = request.args['form_login'][0]
        password = request.args['form_password'][0]
        # If the request comes from the login page
        if page == 'login' :
            # If the user exists and the password matches
            if login in users and users[login]['password'] == password :
                user = User(login)
                session = request.getSession()
                session.setComponent(IUser, user)
                request.args['page'][0] = 'index'
                return self.render_GET(request)
            else :
                request.args['page'][0] = 'login'
                return self.render_GET(request)
        # If the request comes from the admin page
        elif page == 'admin' :
            user_role = request.args['form_user_role'][0]
            collections = [request.args[collection][0] for collection in request.args if collection.startswith('project_')]
            # Check if user doesn't exist
            if login not in users :
                # Add user to the json file
                users[login] = {'password' : password, 'role' : user_role, 'collections' : collections}
                file = open('users.json', 'w')
                json.dump(users, file, sort_keys = True, indent = 4)
                file.close()
            return self.render_GET(request)

def _connect_to_db():
    """ attempt to connect to mongo database based on value in config_file
        return db object
    """
    host   = config['mongo']['host']
    port   = config['mongo']['port']
    db     = config['mongo']['database']
    user   = config['mongo']['user']
    passwd = config['mongo']['passwd']

    try :
        c = Connection("mongodb://" + user +  ":" + passwd  + "@" + host + ":" + str(port) + "/" + db)
        return c[db]
    except :
        print 'Could not connect to the database'
        exit()

class Downloader(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        try :
            file_path = request.args['file'][0]
            request.setHeader('Content-Disposition', 'attachment;filename=' + request.args['file'][0].split('/')[-1])
            return open(file_path).read()
        except Exception as e:
            return 'There was an error : ' + str(e)

db = _connect_to_db()

root = Home()
root.putChild('downloader', Downloader())
root.putChild('js', static.File(os.path.join(root_dir, web_client_dir, 'js')))
root.putChild('css', static.File(os.path.join(root_dir, web_client_dir, 'css')))
root.putChild('fonts', static.File(os.path.join(root_dir, web_client_dir, 'fonts')))
root.putChild('images', static.File(os.path.join(root_dir, web_client_dir, 'images')))
manageJson = scholarScape(db)
root.putChild('json', manageJson)
data = static.File('data')
root.putChild('data', data)

application = service.Application('ScholarScape server. Receives JSON-RPC Requests and also serves the client.')
site = server.Site(root)
srv = internet.TCPServer(config['twisted']['port'], site)
srv.setServiceParent(application)

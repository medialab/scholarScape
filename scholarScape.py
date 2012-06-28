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
from datetime import date
from contextlib import nested
from txjsonrpc.web import jsonrpc
from urllib import quote_plus as qp
from pymongo import Connection, errors, json_util, objectid
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
# try to connect to DB, send egg to scrapyd server
# then start twisted server
print 'Loading config file...'
try :
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except IOError as e:
    print 'Could not open config file'
    print e
    exit()    
except ValueError as e:
    print 'Config file is not valid JSON', e
    exit()

# Read config file and fill in mongo and scrapyd config files with custom values
# Try to connect to DB, send egg to scrapyd server
print 'Loading users file...'
try :
    with open('users.json', 'r') as users_file:
        users = json.load(users_file)
except IOError as e:
    print 'Could not open users file', e
    exit()    
except ValueError as e:
    print 'Users file is not valid JSON', e
    exit()

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
root_dir = os.path.dirname(__file__)    
pp = pprint.PrettyPrinter(indent=4)
web_client_dir = 'web_client'
data_dir = os.path.join(root_dir, config['data_dir'])

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
            path = os.path.join(web_client_dir, 'login.html')
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
                path = os.path.join(web_client_dir, "%s.html" % request.args['page'][0])
                path = path if os.path.exists(path) else os.path.join(web_client_dir, '404.html')
            else:
                path = os.path.join(web_client_dir, 'index.html')
        layout_path = os.path.join(web_client_dir, 'layout.html')
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

def scholarize(query="", nr_results_per_page="100", exact="", at_least_one="",
               without="", where_words_occurs="", author="", publication="",
               start_date="", end_date="", areas = [] ) :
    """
    Advanced research in Google Scholar to URL
    areas may contain "bio"  Biology, Life Sciences, and Environmental Science	            
                      "med", Medicine, Pharmacology, and Veterinary Science       
                      "bus", Business, Administration, Finance, and Economics
                      "phy", Physics, Astronomy, and Planetary Science
                      "chm", Chemistry and Materials Science      
                      "soc", Social Sciences, Arts, and Humanities
                      "eng", Engineering, Computer Science, and Mathematics
    """
    return ("http://scholar.google.com/scholar?\
             as_q="+ qp(query) +"&num="+ nr_results_per_page +"& \
             as_epq="+ qp(exact) +"&as_oq="+ qp(at_least_one) +"& \
             as_eq="+ qp(without) +"&as_occt="+ qp(where_words_occurs) +"& \
             as_sauthors="+ qp(author) +"&as_publication="+ qp(publication) +"& \
             as_ylo="+ start_date +"&as_yhi="+ end_date +"& \
             btnG=Search+Scholar&hl=en& \
             as_subj=" + str.join('&as_subj',areas) ).replace(" ","")

class scholarScape(jsonrpc.JSONRPC):
    """
    JSON-RPC interface
    """

    addSlash = True
    projects = []

    def __init__(self, db):
        jsonrpc.JSONRPC.__init__(self)
        self.db = db

    def jsonrpc_start_project(self, project_name):
        """
        JSON-RPC method to start a project
        """
        
        # checking if projects already exists
        if project_name not in self.db.collection_names() :
            self.db.create_collection(project_name)
            return dict(code = "ok", message = project_name + " successfully created.") 
        else :
            return dict(code = "fail", message = "Sorry, error" )
    
    def jsonrpc_list_project(self, login):
        """
        JSON-RPC method to get the lists of all the projects
        """
        
        # Check for the connected login
        u = None
        r = None
        for user in users :
            if login == hashlib.md5(config['salt'] + user).hexdigest() :
                u = user
                r = users[user]['role']
        if u is None :
            collection_names = []
        elif r == 'admin' :
            collection_names = self.db.collection_names()
            collection_names.remove('system.indexes')
            collection_names.remove('system.users')
            collection_names = [collection_name for collection_name in collection_names if not collection_name.startswith("__")]
        else :
            collection_names = users[u]['collections']
        return collection_names
    
    def jsonrpc_give_me_duplicates(self, project, campaign, limit, cluster_id) :
        """
        Return lists of duplicates
        """
        TITLE_THRESOLD = 0.8
        dup_col = self.db["__dup__" + project + "-" + campaign]
        col = self.db[project]
        total_number_of_possible_duplicates = dup_col.find({'title_score' : {'$gt' : TITLE_THRESOLD, '$lt' : 1}, 'cluster' : {'$exists' : True}}).count()
        number_duplicates_already_checked = dup_col.find({'title_score' : {'$gt' : TITLE_THRESOLD, '$lt' : 1}, 'human_say' : {'$exists' : True}}).count()
        # Get the first cluster
        possible_duplicates = dup_col.find({'title_score' : {'$gte' : TITLE_THRESOLD, '$lt' : 1}, 'cluster' : cluster_id, 'human_say' : {'$exists' : False}})
        # Select the ids of the duplicated publications
        duplicate_ids = []
        for possible_duplicate in possible_duplicates :
            duplicate_ids.append(possible_duplicate['_id1'])
            duplicate_ids.append(possible_duplicate['_id2'])
        duplicate_ids = list(set(duplicate_ids))
        # Get the duplicated publications
        duplicates = []
        for duplicate_id in duplicate_ids :
            publication = col.find_one({'_id' : duplicate_id})
            # TODO
            # If the publication has a parent, replace the publication by its parent
            duplicates.append(json.dumps(publication, default = json_util.default))
        return {
            'total_number_of_possible_duplicates' : total_number_of_possible_duplicates,
            'number_duplicates_already_checked' : number_duplicates_already_checked,
            'duplicates' : duplicates
            }
    
    def jsonrpc_duplicate_human_check(self, project, campaign, dup_ids, is_duplicate):
        col = self.db[project]
        dup_col = self.db["__dup__"+project+"-"+campaign]
        if is_duplicate:
            duplicates.merge_duplicates(campaign, col, dup_col, dup_ids)
            return "Has been marked as duplicate"
        else:
            # TODO
            return "Has been marked as not duplicate"

    def jsonrpc_list_campaigns(self, project_name) :
        """
        JSON-RPC method to get the lists of all the campaigns in a particular
        project.
        """
        collection = self.db[project_name]
        campaigns = [campaign for campaign in collection.find({'download_delay' : {'$exists' : True}}, {'_id' : 0}) ]
        return [project_name, campaigns]
    
    def jsonrpc_list_all_campaigns(self, login) :
        """
        JSON-RPC method Return a sorted array of arrays containing all the 
        projects with all the campaigns
        """
        collection_names = self.jsonrpc_list_project(login)
        projects = []
        for collection_name in collection_names:
            collection = self.db[collection_name]
            campaigns = [campaign for campaign in collection.find({'download_delay' : {'$exists' : True}}, {'_id' : 0}) ]
            projects.append([collection_name, sorted(campaigns, key = lambda x : x['name'])])
        return sorted(projects, key = lambda x : x[0])
        
    def jsonrpc_start_campaign(self, project, campaign, search_type, starts, download_delay = 30, depth = 1, max_start_pages = 100, max_cites_pages = 100, exact = False):
        """
        JSON-RPC method to start a campaign.
        """
        collection = self.db[project]
        if collection.find({ "name" : campaign }).count() > 0 :
            return dict(code = "fail", message = "Already existing campaign : campaign could not be created")     
        
        def scholarize_custom(x) :
            """
            Method to return GS urls based on the choice of the user.
            """
            kwargs = dict()
            
            if exact and search_type == "titles" :
                return scholarize(exact=x, where_words_occurs='title')
            if exact and search_type == "words" :
                return scholarize(exact=x)
                
            if search_type == "words"  :    return scholarize(query=x)
            if search_type == "titles"  :   return scholarize(query=x, where_words_occurs='title')
            if search_type == "authors" :   return scholarize(author=x)
            if search_type == "urls"    :   return x + "&num=100"

        # preparation of the request to scrapyd
        url = 'http://%s:%s/schedule.json' % (config['scrapyd']['host'], config['scrapyd']['port']) 
        values = [('project' , 'scholar'),
                  ('spider' , 'scholar_spider'),
                  ('project_name' , project),
                  ('setting' , 'DOWNLOAD_DELAY=' + str(download_delay)) ,
                  ('setting' , 'DEPTH_LIMIT=' + str(depth)) ,
                  ('campaign_name' , campaign),  
                  ('max_start_pages' , max_start_pages),  
                  ('max_cites_pages' , max_cites_pages),  
                  ('start_urls_' , str.join(';', [scholarize_custom(start) for start in filter(lambda x : x, starts)])),]
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        
        # sending request
        try :
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            result = dict(code = 'fail', message = 'Could not contact scrapyd server, maybe it\'s not started...')
            return result
        
        # reading the response
        results = json.loads(response.read())
        print results
        if results['status'] == 'ok' :
            result = dict(code = 'ok', message = 'The crawling campaign was successfully launched. You can see it in the Explore section.\n')
            result['job_id'] = str(results['jobid'])
            # creation of the campaign object in the DB
            campaign =  {'name' : campaign,
                         'date' : str(date.today()),
                         'depth' : depth,
                         'download_delay' : download_delay,
                         'start_urls' : [scholarize_custom(start) for start in filter(lambda x : x, starts)],
                         'job_id' : str(results['jobid']),
                         'max_start_pages' : max_start_pages,  
                         'max_cites_pages' : max_cites_pages,  
                         'status' : 'alive',}
            collection.insert(campaign)   
            return result
        else :
            result = dict(code = 'fail', message = 'There was an error telling scrapyd to launch campaign crawl.')
            return result
    
    
    #added by Paul
    def jsonrpc_remove_duplicates(self, project_name, campaign):
        col=self.db["__process__remove_duplicates"]
        existing_process_running=col.find_one({"project_name": project_name,"campaign":campaign},{"status":1,"pid":1,"start_date":1})
        if existing_process_running and existing_process_running["status"] == "running":
            return "a process to remove duplicate is already running with PID: %s started %s"%(existing_process_running["pid"],existing_process_running["start_date"])
        else :
            
            # create a process            
            p = subprocess.Popen(["python","scholar/scholar/duplicates.py",project_name, campaign])
            
            # trace it in the database
            if existing_process_running and existing_process_running["status"] == "finished":
                # remove the existing trace from database
                col.remove({"project_name": project_name,"campaign":campaign})
            
            col.insert({"project_name": project_name,"campaign":campaign,"status":"running","pid":p.pid,"start_date":datetime.now()})
            
            # wait for the subprocess to stop 
            
            def wait_for_process(project_name, campaign,p) :
            # waiting for end of process method
                print "waiting for the process %s to stop"%p.pid
                p.wait()
                col=self.db["__process__remove_duplicates"]
                col.update({"project_name": project_name,"campaign":campaign},{"$set":{"status":"finished","end_date":datetime.now()}})
                print "process %s stopped"%p.pid

            # put the blocking p.wait in a thread
            d = threads.deferToThread(wait_for_process,project_name, campaign,p)
            #log
            print "subprocess duplicates started" 
            return "process started with PID :%s"%(p.pid)
    
    
    def jsonrpc_cancel_campaign(self, project_name, campaign):
        collection = self.db[project_name]
        job_id = collection.find_one({ "name" : campaign })["job_id"]
        url = 'http://%s:%s/cancel.json' % (config['scrapyd']['host'], config['scrapyd']['port']) 
        values = [("project" , "scholar"),
                  ('job' , job_id),]
        
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        
        # sending request
        try :
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            result = dict(code = "fail", message = "Could not contact scrapyd server, maybe it's not started...")
            return result
        
        collection.update( {"download_delay" : {"$exists" : True}, "name" : campaign}, {"$set" : {"status" : "finished"}})
        # reading the response
        results = json.loads(response.read())
        return results
    
    def jsonrpc_export_gexf(self, project_name, campaign,max_depth=None):
        """JSON-RPC method to export a graph from a particular project/campaign."""
        g = nx.Graph()
        collection = self.db[project_name]
        
        # The hash table will act as a translation table child -> parent to
        # enable that a publication which links to a child will be connected
        # to the parent instead of the child
        hash_table = dict()
        children = {"parent_id" : {"$exists" : True}, "id" : {"$exists" : True}}
        if campaign != "*":
            children['campaign'] = campaign
        for publication in collection.find(children) :
            hash_table[publication['id']] = str(publication['parent_id'])

        def add_pub_in_graph(pub) :               
            cites = False
            publication_id = pub.get('id') or str(pub['_id'])
            pub['depth'] = min(pub['depths'])

            for k in pub.keys() :
                if k == "abstract" : # we don't want abstract in the graph
                    del pub[k]
                elif k == "cites" : # nor cites because there are the links already
                    cites = pub[k]
                    del pub[k]
                else :
                    #anything that is not an int or a float becomes unicode
                    if type(pub[k]) != int and type(pub[k]) != float :
                        pub[k] = unicode(pub[k])
            
            label = pub.get("title") or ""
            if pub.get("title") : del pub["title"]
            g.add_node(publication_id, label=label, **pub)

            if cites:
                source = pub.get('id') or str(pub['_id'])
                if type(cites) == unicode :
                    cites = [cites]
                # we pass the cited publications through the hash table to get
                # the parents if there is one
                targets = [hash_table.get(cite) or cite for cite in cites]
                for target in targets :
                    g.add_edge(source,target)
        
        #getting all the publications that are not children
        not_children = {"download_delay" : {"$exists" : False}, "parent_id" : {"$exists" : False}}
        if campaign != "*" :
            not_children["campaign"] = campaign
        for not_child in collection.find(not_children): 
            add_pub_in_graph(not_child) #adding them to the graph
         
        # forge a name 
        filename = os.path.join(os.path.dirname(__file__), data_dir, "gexf", project_name + "-" + campaign + "-" + str(getrandbits(128)) + ".gexf" )
        
        # filter nodes whose depth is > max_depth
        to_del = [k for k,n in g.node.iteritems() if n.get('depth') > int(max_depth)]
        g.remove_nodes_from(to_del)
        
        #write graph to gexf file
        nx.write_gexf(g,filename)
        return filename
        
    def jsonrpc_export_duplicates(self, project, campaign) :
        g = nx.Graph()
        collection = self.db[project]
        for parent in collection.find({"nr_children" : {"$exists" : True}, "campaign": campaign} ) :
            g.add_node(str(parent['_id']), title=parent['title'])

        for child in collection.find({"parent_id" : {"$exists" : True} }) :
            g.add_node(str(child["_id"]), title=child.get('title') or "")
            g.add_edge(child["parent_id"], child["_id"])

        filename = os.path.join(os.path.dirname(__file__), data_dir, "gexf", "duplicates - "+project+ "-" + campaign + "-" + str(getrandbits(128)) + ".gexf" )
        nx.write_gexf(g,filename)
        return filename
    
    def jsonrpc_export_json(self, project, campaign) :
        print "Dumping database..."
        if campaign == "*" : campaign = ""
        filename = os.path.join(os.path.dirname(__file__), data_dir, "json", project + "-" + campaign + str(getrandbits(128)) + ".json" )
        export_command = ("mongoexport -h '%(host)s' -d '%(database)s' -c '%(project)s' -o %(filename)s" 
                            % {"host" : config["mongo"]["host"], 
                               "database" : config["mongo"]["database"], 
                               "project" : project, 
                               "filename" : filename})
        if campaign :
            query = {"$or" : [ 
                        {"campaign" : campaign, "download_delay" : {"$exists" : False}}, 
                        {"name" : campaign, "download_delay" : {"$exists" : True} }]} 
            export_command += "-q '%s'" % query
        print export_command
        args = shlex.split(export_command)
        p = subprocess.call(args)
        print "Done."
        return filename
        
    def jsonrpc_export_zip(self,project_name) :
        json_file = self.jsonrpc_export_json(project_name)
        gexf_file = self.jsonrpc_export_gexf(project_name)
        filename = os.path.join(os.path.dirname(__file__), data_dir, "zip", project_name + str(getrandbits(128)) + ".zip" )
        zip_file = zipfile.ZipFile(filename,'w',compression=zipfile.ZIP_DEFLATED)
        zip_file.write(json_file)
        zip_file.write(gexf_file)
        zip_file.close()
        return filename

    def jsonrpc_monitor(self, project_name, campaign_name) :
        #nombre d'items
        collection = self.db[project_name]
        nb_super   = collection.find({"campaign" : campaign_name, "nr_children" : {"$exists" : True}}).count()
        nb_items   = collection.find({"campaign" : campaign_name}).count()  - nb_super
        last_items = list(collection.find({"campaign" : campaign_name }, {"_id" : False, "parent_id" : False}).limit(10).sort([("$natural", -1)])) # most recent items
        campaign     = collection.find({"download_delay" : {"$exists" : True}, "name" : campaign_name})[0]
        del campaign['_id']
        
        retour = {"code" : "ok",
                  "message" : {"nb_super"  : nb_super,
                               "nb_items"  : nb_items,
                               "last_items": last_items,
                               "campaign"    : campaign}}
        return retour

    def jsonrpc_monitor_project(self, project_name) :
        #nombre d'items
        collection = self.db[project_name]
        nb_campaigns = collection.find({"download_delay" : {"$exists" : True}}).count()
        nb_items = collection.find({"title" : {"$exists" : True}}).count()
        return {"nb_campaigns" : nb_campaigns,
                "nb_items"     : nb_items}

    def jsonrpc_remove_project(self,project_name) :
        try : 
            self.db.drop_collection(project_name)
            for name in self.db.collection_names(): 
                if name.startswith("__dup__" + project_name + "-") :
                    self.db.drop_collection(name) 
            return {"code":"ok", "message" : "Project " + project_name + " was deleted successfully"}
        except Exception as e:
            return {"code" : "fail", "message" : str(e)}            

    def jsonrpc_remove_campaign(self, project_name, campaign_name) :
        try :
            collection = self.db[project_name]
            collection.remove({'campaign' : campaign_name})
            collection.remove({'download_delay' : {'$exists' : True}, 'name' : campaign_name})
            return {'code' : 'ok', 'message' : 'Campaign ' + campaign_name + ' was deleted successfully'}
        except Exception as e:
            return {'code' : 'fail', 'message' : str(e)}

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

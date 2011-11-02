from twisted.web import server
from twisted.application import service, internet
from txjsonrpc.web import jsonrpc
from twisted.python import log
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from twisted.web import resource
from twisted.web.static import File

import getpass
import json
from pymongo import Connection
import argparse
import pprint 
import json
from pymongo import Connection
from scholar.scholar.graph import create_graph_from_db
import shlex, subprocess
import zipfile
import urllib
import urllib2
from datetime import date
from twisted.web import static
import networkx as nx
from random import getrandbits
import inspect
from urllib import quote_plus as qp
import os
import pystache
from contextlib import nested
import subprocess as sub

print "Loading config file..."
try :
    with open("config.json","r") as config_file:
        config = json.load(config_file)
except IOError as e:
    print "Could not open config file"
    print e
    exit()    
except ValueError as e:
    print "Config file is not valid JSON", e
    exit()

Connection("mongodb://" + config['mongo']['user'] + ":" \
            + config['mongo']['passwd'] + "@" + config['mongo']['host'] + ":" + config['mongo']['port'] + "/" config['mongo']['database'])
print "Rendering pipelines.py with values from config.json..."
try :
    with nested(open("scholar/scholar/pipelines-template.py", "r"), open("scholar/scholar/pipelines.py", "w")) as (a, b):
        b.write(pystache.render(a.read(), config['mongo']))
except IOError as e:
    print "Could not open either pipeline-template file or pipeline file"
    print e
    exit() 
except Exception as e:
    print "Unexpected error"
    print e
    exit()
  
print "Rendering scrapy.cfg with values from config.json..."
try :
    with nested(open("scholar/scrapy-template.cfg", "r"), open("scholar/scrapy.cfg", "w")) as (a, b):
        b.write(pystache.render(a.read(), config['scrapyd']))
except IOError as e:
    print "Could not open either scrapy.cfg template file or scrapy.cfg"
    print e
    exit() 
except Exception as e:
    print "Unexpected error"
    print e
    exit()  
print "Sending scholarScrape's scrapy part to scrapyd server..."
os.chdir("scholar")
p = sub.Popen(['scrapy','deploy'], stdout=sub.PIPE, stderr=sub.PIPE)
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
web_client_dir = "web_client"
data_dir = os.path.join(root_dir,config["data_dir"])

class Home(resource.Resource):
    isLeaf = False
 
    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)
 
    def render_GET(self, request):
        with open(os.path.join(web_client_dir, "client.html"),"r") as f:
            content = f.read()
        return content

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
        print "Could not connect to the database"
        exit()


def scholarize(     query="",
                    nr_results_per_page="100",
                    exact="",
                    at_least_one="",
                    without="",
                    where_words_occurs="",
                    author="",
                    publication="",
                    start_date="",
                    end_date="",
                    areas = [                               
                             #"bio",  #  Biology, Life Sciences, and Environmental Science	            
                             #"med", #  Medicine, Pharmacology, and Veterinary Science       
                             #"bus", #  Business, Administration, Finance, and Economics
                             #"phy", #  Physics, Astronomy, and Planetary Science
                             #"chm", #  Chemistry and Materials Science      
                             #"soc", #  Social Sciences, Arts, and Humanities
                             #"eng", #  Engineering, Computer Science, and Mathematics
                    ] ) :
    return ("http://scholar.google.com/scholar?\
                                 as_q="+ qp(query) +"& \
                                 num="+ nr_results_per_page +"& \
                                 as_epq="+ qp(exact) +"& \
                                 as_oq="+ qp(at_least_one) +"& \
                                 as_eq="+ qp(without) +"& \
                                 as_occt="+ qp(where_words_occurs) +"& \
                                 as_sauthors="+ qp(author) +"& \
                                 as_publication="+ qp(publication) +"& \
                                 as_ylo="+ start_date +"& \
                                 as_yhi="+ end_date +"& \
                                 btnG=Search+Scholar& \
                                 hl=en& \
                                 as_subj=" + str.join('&as_subj',areas) ).replace(" ","")

class scholarScape(jsonrpc.JSONRPC):
    """
    An example object to be published.
    """

    addSlash = True
    projects = []
    
    def jsonrpc_start_project(self,project_name):
        # checking if projects already exists      
        if project_name not in db.collection_names() :
            db.create_collection(project_name)
            return dict(code = "ok", message = project_name + " successfully created.") 
        else :
            return dict(code = "fail", message = "Sorry, error" + str(ValueError))
    
    def jsonrpc_list_project(self):
        collection_names=db.collection_names()
        collection_names.remove('system.indexes')
        collection_names.remove('system.users')
        return collection_names
        
    def jsonrpc_list_campaigns(self, project_name):
        """ returns the campaigns for a particular project"""
        collection=db[project_name]

        campaigns=[campaign for campaign in collection.find({'download_delay' : {'$exists':True}},{"_id":0}) ]
        pp.pprint(campaigns)
        return [project_name,campaigns]
    
    def jsonrpc_list_all_campaigns(self) :
        collection_names=db.collection_names()
        collection_names.remove('system.indexes')
        collection_names.remove('system.users')
        
        projects = []
        for collection_name in collection_names:
            collection=db[collection_name]
            campaigns=[campaign for campaign in collection.find({'download_delay' : {'$exists':True}},{"_id":0}) ]
            projects.append([collection_name,sorted(campaigns,key=lambda x:x['name'])])
        return sorted(projects,key=lambda x:x[0])
        
    def jsonrpc_start_campaign(self, project, campaign, start_titles, download_delay=30, depth=1):
        collection = db[project]
        if collection.find({ "name" : campaign }).count() > 0 :
            return dict(code = "fail", message = "Already existing campaign : campaign could not be created")     
        
        url = 'http://lrrr.medialab.sciences-po.fr:6800/schedule.json'
        values = [
              ("project" , "scholar"),
              ('spider' , 'scholar_spider'),
              ('project_name' , project),
              ('setting' , 'DOWNLOAD_DELAY=' + str(download_delay)) ,
              ('setting' , 'DEPTH_LIMIT=' + str(depth)) ,
              ('campaign_name' , campaign),  
              ('start_urls_' , str.join(";", [scholarize(title) for title in filter(lambda x : x, start_titles)])),  
        ]
        
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()

        results = json.loads(the_page)
        print results
        if results['status'] == "ok":
            result = dict(code = "ok", message = "The crawling campaign was successfully launched.\n")
            result['message'] += "It's job id is " + str(results["jobid"])
            campaign =  {
                        "name" : campaign,
                        "date" : str(date.today()),
                        "depth" : depth,
                        "download_delay" : download_delay,
                        "start_urls" : [scholarize(title) for title in filter(lambda x : x, start_titles)],
                        "job_id" : str(results["jobid"]),
                    }
            collection.insert(campaign)   
            return result
        else :
            result = dict(code = "fail", message = "There was an error telling scrapyd to launch campaign crawl")
            return result
    
    
    
    def jsonrpc_export_gexf(self, project_name,max_depth=None):
        print max_depth
        g = nx.Graph()
        hash_table = dict()
        collection = db[project_name]
        for publication in collection.find({"parent_id" : {"$exists" : True}, "id" : {"$exists" : True}}) :
            hash_table[publication['id']] = str(publication['parent_id'])

        def add_pub_in_graph(pub) :
            depth = pub['depth_cb'] if "depth_cb" in pub else pub['depths'][0]
            id = pub.get('id') or str(pub.get('_id')) 
            title       = pub["title"] if "title" in pub else ""
            times_cited = pub["times_cited"] if "times_cited" in pub else 1
            
            g.add_node( id,
                        weight=int(times_cited),
                        title=title,
                        depth=depth)
            if "cites" in pub:
                source = pub.get("parent_id") or pub.get('id') or str(pub['_id'])
                cites = pub['cites']
                if type(pub['cites']) == unicode :
                    cites = [cites]

                targets = [hash_table.get(cite) or cite for cite in cites]
                for target in targets :
                    g.add_edge(source,target)

        what_to_search = {"download_delay" : {"$exists" : False}, "parent_id" : {"$exists" : False}} # we don't take the campaign objects nor the leaves
        for pub in collection.find(what_to_search): # get only nodes that are not campaign
            add_pub_in_graph(pub)
            
        filename = os.path.join(os.path.dirname(__file__), data_dir, "gexf", project_name + str(getrandbits(128)) + ".gexf" )

        to_del = [k for k,n in g.node.iteritems() if n.get('depth') > int(max_depth)]
        g.remove_nodes_from(to_del)
        nx.write_gexf(g,filename)
        return filename
        
    def jsonrpc_export_json(self,project_name) :
        print "Dumping database..."
        filename = os.path.join(os.path.dirname(__file__), data_dir, "json", project_name + str(getrandbits(128)) + ".json" )
        export_command = str('mongoexport -h "' + config["mongo"]["host"] + '" -d "' + config["mongo"]["database"] + '" -c "' + project_name + '" -o ' + filename)
        print export_command
        args = shlex.split(export_command)
        p = subprocess.call(args)
        print "Done."
        return filename
        
    def jsonrpc_export_zip(self,project_name) :
        print inspect.getmembers(self)
        json_file = self.jsonrpc_export_json(project_name)
        gexf_file = self.jsonrpc_export_gexf(project_name)

        filename = os.path.join(os.path.dirname(__file__), data_dir, "zip", project_name + str(getrandbits(128)) + ".zip" )
        zip_file = zipfile.ZipFile(filename,'w',compression=zipfile.ZIP_DEFLATED)
        zip_file.write(json_file)
        zip_file.write(gexf_file)
        zip_file.close()
        return filename

    def jsonrpc_remove_project(self,project_name) :
        try : 
            db.drop_collection(project_name)
            return {"code":"ok","message" : "Project " + project_name + " was deleted successfully"}
        except Exception as e:
            return {"code" : "fail", "message" : str(e)}            
        
    def jsonrpc_remove_campaign(self,project_name,campaign_name):
        try :
            collection = db[project_name]
            collection.remove({"campaign":campaign_name})
            collection.remove({"download_delay":{"$exists":True}, "name":campaign_name})
            return {"code":"ok","message" : "Campaign " + campaign_name + " was deleted successfully"}
        except Exception as e:
            return {"code" :"fail", "message" : str(e)}
        

db =  _connect_to_db()
application = service.Application("ScholarScape server. Receives JSON-RPC Requests and also serves the client.")
root = Home()

manageJson = scholarScape()
root.putChild('json', manageJson)
root.putChild('js', static.File(os.path.join(root_dir, web_client_dir,"js")))
root.putChild('styles', static.File(os.path.join(root_dir, web_client_dir,"styles")))
data = File("data")
root.putChild("data", data)
site = server.Site(root)
server = internet.TCPServer(config["twisted"]["port"], site)
server.setServiceParent(application)













import zipfile
import shlex
import threads
import networkx as nx
import os
import json
import pprint
import urllib
import urllib2
import hashlib
import pystache
import subprocess
from datetime import datetime
from datetime import date
from contextlib import nested
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
from txjsonrpc.web import jsonrpc
from scholarScape.scholarScape import users, config, scholarize, data_dir
from random import getrandbits
import scholar.scholar.duplicates as duplicates

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
        for user in users:
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
        else:

            # create a process
            p = subprocess.Popen(["python","scholar/scholar/duplicates.py",project_name, campaign])

            # trace it in the database
            if existing_process_running and existing_process_running["status"] == "finished":
                # remove the existing trace from database
                col.remove({"project_name": project_name,"campaign":campaign})

            col.insert({"project_name": project_name,"campaign":campaign,"status":"running","pid":p.pid,"start_date":datetime.now()})

            # wait for the subprocess to stop

            def wait_for_process(project_name, campaign,p):
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
            return "process started with PID :%s" % (p.pid)


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

        def add_pub_in_graph(pub):
            cites = False
            publication_id = pub.get('id') or str(pub['_id'])
            pub['depth'] = min(pub['depths'])

            for k in pub.keys():
                if k == "abstract": # we don't want abstract in the graph
                    del pub[k]
                elif k == "cites": # nor cites because there are the links already
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

    def jsonrpc_export_zip(self, project_name, campaign_name) :
        json_file = self.jsonrpc_export_json(project_name, campaign_name)
        gexf_file = self.jsonrpc_export_gexf(project_name, campaign_name)
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
        try:
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

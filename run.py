#! /usr/bin/env python
# -*- coding: utf-8 -*-

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


def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
    while True:
        ok = raw_input(prompt)
        if ok in ('y', 'ye', 'yes'):
            return True
        if ok in ('n', 'no', 'nop', 'nope'):
            return False
        retries = retries - 1
        if retries < 0:
            raise IOError('refusenik user')
        print complaint

def _start_campaign(args):
    if not (args.start_urls or args.start_urls):
        print "You must indicate start_urls either with -s or -f"
        return False
    with open("config.json", "r") as config_file:
        try :
            print "Loading configuration file"
            config = json.load(config_file)
        except :
            print "error loading config file"
            return False
    print "Connecting to database", config[args.project]['database'], "on", config[args.project]['host']+":"+str(config[args.project]['port'])
    try :
        c = Connection(config[args.project]['host'], config[args.project]['port'])
        db = c[config[args.project]['database']]
        collection = db[args.project]
    except :
        print "Could not connect to the database with "
        return False
    if collection.find({ "name" : args.campaign }).count() > 10000 :
           print "Campaign already exists, please choose another name"
           return False
    if args.download_delay < 30 :
        if not ask_ok("Are you sure you want to crawl with such a small time between requests ?\nYou might get blacklisted... (y/n)") :
            return False
    
    if args.start_urls_file:
        start_urls = []
        with open(start_urls_file) as f :
            for line in f.readlines() :
                start_urls.append(line.strip())
    else :
        start_urls = args.start_urls
    campaign =  {

                    "name" : args.campaign,
                    "date" : str(date.today()),
                    "depth" : args.depth,
                    "download_delay" : args.download_delay,
                    "start_urls" : start_urls,
                }
    print campaign
    collection.insert(campaign)        
    print "Campaign successfully created in the DB"
    url = 'http://lrrr.medialab.sciences-po.fr:6800/schedule.json'
    values = [
          ("project" , "scholar"),
          ('spider' , 'scholar_spider'),
          ('project_name' , args.project),
          ('setting' , 'DOWNLOAD_DELAY=' + str(args.download_delay)) ,
          ('setting' , 'DEPTH_LIMIT=' + str(args.depth)) ,
          ('campaign_name' , args.campaign),  
          ('start_urls_' , str.join(";", start_urls)),  
    ]
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(values)
    data = urllib.urlencode(values)

    req = urllib2.Request(url, data)
    print str(req)
    response = urllib2.urlopen(req)
    the_page = response.read()


    results = json.loads(the_page)
    if results['status'] == "ok":
        print "The crawling campaign was successfully launched."
        print "It's job id is", results["jobid"]
        return True
    else :
        print "There was an error launching the campaign."
        print results['status']

def _start_project(args):
    # checking if projects already exists
    
    # writing or overriding previous config_file
    with open("config.json", "r") as config_file:
        try :
            config = json.load(config_file)
        except :
            print "error loading config file"
            config = {}
    
    if args.project in config :
        print "Already existing configuration for this project. Please use the command config"
        return False
    
    config[args.project] = {} 
        
    if args.host and args.port and args.database :
        config[args.project]['host'] = args.host 
        config[args.project]['port'] = args.port 
        config[args.project]['database'] = args.database
   
    with open("config.json","w") as config_file:
        json.dump(config,config_file,indent=4)
    print "Success : Configuration for ", args.project, " inserted in config file."     
    # now creates collection
    
    project = args.project
    try :
        c = Connection(config[project]['host'], config[project]['port'])
        db = c[config[project]['database']]
        db.create_collection(args.project)
        print "Success : ", args.project, " collection created." 
    except ValueError :
        print "Sorry, error"
        print ValueError
        
    return True

def _export(args):
    with open("config.json", "r") as config_file:
        try :
            config = json.load(config_file)
        except :
            print "error loading config file"
            return False
    
    project = args.project
    
    host = config[project]['host']
    port = config[project]['port']
    database = config[project]['database']
    
    gexf_output = args.gexf_file if args.gexf_file else None
    json_output = args.json_file if args.gexf_file else None
    zip_output = args.zip_file if args.gexf_file   else None

    if gexf_output :
        print "Creating graph...."
        create_graph_from_db(host, port, database, project, gexf_output)
    if json_output :
        print "Dumping database..."
        export_command = str('mongoexport -h "' + host + '" -d "' + database + '" -c "' + project + '" -o ' + json_output)
        print export_command
        args = shlex.split(export_command)
        p = subprocess.call(args)
        print "Done."
    if zip_output and (json_output or gexf_output):
        print "Zipping..."
        zip_file = zipfile.ZipFile('archive.zip','w',compression=zipfile.ZIP_DEFLATED)
        if json_output :
            zip_file.write(json_output)
        if gexf_output :
            zip_file.write(gexf_output)
        zip_file.close() 
    print "Done."
    
def _config(args):
    config = _get_config()
    
    if args.project not in config:
        config[project] = {"host" : "localhost", "port":27017, "database":"scholarScrape"}
    if args.host :
        config[project]['host'] = args.host 
    if args.port :
        config[project]['port'] = args.port 
    if args.database :
        config[project]['database'] = args.database
   
    with open("config.json","w") as config_file:
        json.dump(config,config_file,indent=4)
    
def _get_config():
    with open("config.json", "r") as config_file:
        try :
            return json.load(config_file) 
        except :
            print "Error loading config file"
            return False         

def _list(args):
    config = _get_config()
    
#    c = Connection(config[args.project]['host'], config[args.project]['port'])
#    db = c[config[args.project]['database']]
    
    c = Connection('localhost', 27017)
    db = c['scholarScape']
    
    collection_names=db.collection_names()
    collection_names.remove('system.indexes')
    for collection_name in collection_names :
        campaigns = db[collection_name].find({ 'name' : { '$exists' : 'true' } })
        if campaigns.count() > 0 :
            print collection_name
            for campaign in campaigns :
                print "   -", campaign['name']
    
parser = argparse.ArgumentParser(add_help=True)

subparsers = parser.add_subparsers(dest="subparser_name",help='commands')

# A startproject command
start_project_parser = subparsers.add_parser('startproject', help='Start a new project')
start_project_parser.add_argument('project', action='store', help='Project to create')
start_project_config = start_project_parser.add_argument_group()
start_project_config.add_argument('-s', action='store', dest='host', default="localhost", help='Specify host where database is stored')
start_project_config.add_argument('-p', action='store', dest='port', default=27017, help='Specify the port which scholarScrape shall use to communicate with the DB')
start_project_config.add_argument('-d', action='store', dest='database', default="scholarScape", help='Specify the name of the database scholarScrape shall use')
start_project_parser.set_defaults(func=_start_project)

# A startcampaign command
start_campaign = subparsers.add_parser('startcampaign', help='Start a new campaign')
start_campaign.add_argument('campaign', help='Name fo the campaign')
start_campaign.add_argument('project', help='Project to which to belong the campaign')
start_url_group = start_campaign.add_mutually_exclusive_group(required=True)
start_url_group.add_argument('-f', action='store', dest="start_urls_file", type=argparse.FileType('rt'),  help='Start urls file')
start_url_group.add_argument('-s', nargs="+", dest='start_urls', help='Start url, repeat argument to add more')
start_campaign.add_argument('-d', action='store', dest='depth', help='Depth to which to crawl', required=True)
start_campaign.add_argument('-g', action='store', dest='gexf_file', type=argparse.FileType('wt'), help='Output GEXF file (if no name is specified default is graph.gexf)')
start_campaign.add_argument('-j', action='store', dest='json_file', type=argparse.FileType('wt'), help='Output JSON file (if no name is specified default is database.gexf)')
start_campaign.add_argument('-z', action='store', dest='zip_file', type=argparse.FileType('wt'),  help='Output ZIP file (if no name is specified default is all.zip)')
start_campaign.add_argument('-t', action='store', dest='download_delay', type=int, default=30, help='Time to wait between each request')
start_campaign.set_defaults(func=_start_campaign)

# An export command
export_parser = subparsers.add_parser('export', help='Export project/campaign to zip/gexf/json')
export_parser.add_argument('project', action='store', help='The project from which to export')
export_parser.add_argument('-g', action='store', dest='gexf_file', help='Output GEXF file (if no name is specified default is graph.gexf)')
export_parser.add_argument('-j', action='store', dest='json_file', help='Output JSON file (if no name is specified default is database.gexf)')
export_parser.add_argument('-z', action='store', dest='zip_file', help='Output ZIP file (if no name is specified default is all.zip)')
export_parser.set_defaults(func=_export)

# A config command
config_parser = subparsers.add_parser('configdb', help='Configure database parameters for projects')
config_parser.add_argument('project', action='store', help='Configure which project')
config_parser.add_argument('-s', action='store', dest='host', help='Specify host where database is stored')
config_parser.add_argument('-p', action='store', dest='port', help='Specify the port which scholarScrape shall use to communicate with the DB')
config_parser.add_argument('-d', action='store', dest='database', help='Specify the name of the database scholarScrape shall use')
config_parser.set_defaults(func=_config)

# A list command
list_parser = subparsers.add_parser('list', help='List projects and campaigns')
list_parser.add_argument('-p', action='store', dest='project', help='Specify particular project to be listed')
list_parser.set_defaults(func=_list)

args = parser.parse_args()
args.func(args)




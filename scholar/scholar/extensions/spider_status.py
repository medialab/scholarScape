from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scholar.graph import create_graph_from_db
import shlex, subprocess
import zipfile
import time
from scholar.pipelines import MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE
from scrapy import log
from pymongo import Connection

class Spider_status(object):

    def __init__(self):
        dispatcher.connect(self.engine_started, signal=signals.engine_started)
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)

    def engine_started(self):
        log.msg("SALUUUUUUT NOUNOU!!", level=log.INFO)
        log.msg( "%s:%s@%s:%s/%s" % (MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE), level=log.INFO)

    def spider_closed(self, spider, reason):
        connection = Connection("mongodb://%s:%s@%s:%s/%s" % (MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE) )
        db = connection[MONGO_DATABASE]
        db[spider.project].update( {"download_delay" : {"$exists" : True}, "name" : spider.campaign}, {"$set" : {"status" : "finished"}})
        log.msg("%s/%s" % (spider.project, spider.campaign), level=log.INFO)
        log.msg(reason, level=log.INFO)
        
        

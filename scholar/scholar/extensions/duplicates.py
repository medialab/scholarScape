from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import time
from scrapy import log
from pymongo import Connection
from itertools import combinations, product
import Levenshtein
import math
import networkx as nx
import os
from scholar.pipelines import MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE
from scholar.duplicates import remove_duplicates 

class Duplicates(object):

    def __init__(self):
        dispatcher.connect(self.engine_started, signal=signals.engine_started)
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)

    def engine_started(self):
        log.msg(os.getcwd())
        log.msg( "Duplicates will be merged at the end of the crawl", level=log.INFO)

    def spider_closed(self, spider, reason):
        connection = Connection("mongodb://%s:%s@%s:%s/%s" % (MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE) )
        db = connection[MONGO_DATABASE]
        remove_duplicates(db, spider.project, spider.campaign)

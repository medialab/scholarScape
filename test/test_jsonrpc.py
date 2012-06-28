import os
import json
import pprint
import urllib
import urllib2
import hashlib
import pystache
import subprocess
from scholarScape.server.rpc import scholarScape
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
import scholar.scholar.duplicates as duplicates

class TestJsonRPC:
    def setup_method(self, method):
        self.connection = pymongo.Connection()
        self.database_name = str(uuid.uuid4())
        self.database = self.connection[self.database_name]
        self.jsonrpc = scholarScape(self.database)

    def teardown_method(self, method):
        self.connection.drop_database(self.database)

    def test_duplicates(self):
        project = "test_project"
        campaign = "test_campaign"
        project_col = self.database[project]
        campaign_col = self.database["__dup__"+project+"-"+campaign]
        _id1 = ObjectId()
        _id2 = ObjectId()
        _id3 = ObjectId()
        project_col.insert({"_id" : _id1})
        project_col.insert({"_id" : _id2})
        project_col.insert({"_id" : _id3})
        campaign_col.insert({"_id1" : _id1, "_id2" : _id2})
        campaign_col.insert({"_id1" : _id2, "_id2" : _id3})
        self.jsonrpc.jsonrpc_duplicate_human_check(project, campaign, [str(_id1), str(_id2), str(_id3)], True)
        assert campaign_col.find({"human_say" : True}).count() == 2

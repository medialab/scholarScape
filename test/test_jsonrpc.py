from bson.objectid import ObjectId
from scholarScape.server.rpc import scholarScape
import pymongo
import uuid
import json

class TestJsonRPC:
    def setup_class(self):
        self.connection = pymongo.Connection()
        self.database_name = str(uuid.uuid4())
        self.database = self.connection[self.database_name]
        self.jsonrpc = scholarScape(self.database)
        self.project = "test_project"
        self.campaign = "test_campaign"
        self.project_col = self.database[self.project]
        self.campaign_col = self.database["__dup__"+self.project+"-"+self.campaign]

    def teardown_method(self, method):
        self.project_col.remove()
        self.campaign_col.remove()

    def teardown_class(self):
        self.connection.drop_database(self.database)

    def test_duplicates(self):
        _id1 = ObjectId()
        _id2 = ObjectId()
        _id3 = ObjectId()
        self.project_col.insert({"_id" : _id1})
        self.project_col.insert({"_id" : _id2})
        self.project_col.insert({"_id" : _id3})
        self.campaign_col.insert({"_id1" : _id1, "_id2" : _id2})
        self.campaign_col.insert({"_id1" : _id2, "_id2" : _id3})
        self.jsonrpc.jsonrpc_duplicate_human_check(self.project, self.campaign, [str(_id1), str(_id2), str(_id3)], True)
        assert self.campaign_col.find({"human_say" : True}).count() == 2
        assert self.project_col.find_one({"type" : "super_publication"})

    def test_give_me_duplicates(self):
        _id1 = ObjectId()
        _id2 = ObjectId()
        _id3 = ObjectId()
        _id4 = ObjectId()
        _id5 = ObjectId()
        self.project_col.insert({"_id" : _id1, "title" : "test1"})
        self.project_col.insert({"_id" : _id2, "title" : "test2"})
        self.project_col.insert({"_id" : _id3, "title" : "test3"})
        self.project_col.insert({"_id" : _id4, "title" : "test4"})
        self.project_col.insert({"_id" : _id5, "title" : "test5"})
        self.campaign_col.insert({"_id1" : _id1, "_id2" : _id2, "cluster" : 1, "title_score" : 0.9})
        self.campaign_col.insert({"_id1" : _id2, "_id2" : _id3, "cluster" : 1, "title_score" : 0.9})
        self.campaign_col.insert({"_id1" : _id3, "_id2" : _id4, "cluster" : 2, "title_score" : 0.3})
        self.campaign_col.insert({"_id1" : _id4, "_id2" : _id5, "cluster" : 2, "title_score" : 0.9})

        duplicates = self.jsonrpc.jsonrpc_give_me_duplicates(self.project, self.campaign, 3, 1)
        assert len(duplicates["duplicates"]) == 3
        for dup in duplicates["duplicates"]:
            dup = json.loads(dup)
            assert dup["title"] in ["test1", "test2", "test3"]

        duplicates = self.jsonrpc.jsonrpc_give_me_duplicates(self.project, self.campaign, 2, 1)
        assert len(duplicates["duplicates"]) == 2
        for dup in duplicates["duplicates"]:
            dup = json.loads(dup)
            assert dup["title"] in ["test1", "test2", "test3"]

        duplicates = self.jsonrpc.jsonrpc_give_me_duplicates(self.project, self.campaign, 3, 2)
        assert len(duplicates["duplicates"]) == 2
        for dup in duplicates["duplicates"]:
            dup = json.loads(dup)
            assert dup["title"] in ["test4", "test5"]

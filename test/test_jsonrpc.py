from scholarScape import scholarScape
from bson.objectid import ObjectId
import pymongo
import uuid

class TestJsonRPC:
    def setup_method(self, method):
        self.connection = pymongo.Connection()
        self.database_name = str(uuid.uuid4())
        self.database = self.connection[self.database_name]
        self.jsonrpc = scholarScape.scholarScape(self.database)

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

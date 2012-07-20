import json
from scholarScape.server.rpc import scholarScape
from scholarScape.server import rpc
from flexmock import flexmock

class TestJsonRPCIsolation:
    def test_give_me_duplicates_no_cluster_id(self):
        expected = [{"test1" : 1},{"test2" : 2},{"test3" : 3}]

        Duplicates = flexmock(rpc.Duplicates)

        Duplicates.should_receive("get_cluster_with_possible_duplicates_left").with_args(None, "project", "campaign").and_return(2).once()
        Duplicates.should_receive("count_already_checked").with_args(None, "project", "campaign").and_return(352).once()
        Duplicates.should_receive("count_duplicates_left_for_cluster").with_args(None, "project", "campaign", 2).and_return(700).once()
        Duplicates.should_receive("get_list_of_potential_duplicates").with_args(None, "project", "campaign", 2).and_return(expected).once()

        jsonrpc = scholarScape(None)
        result = jsonrpc.jsonrpc_give_me_duplicates("project", "campaign", 3)

        assert result == {
            'number_of_duplicates_left_for_cluster' : 700,
            'number_duplicates_already_checked' : 352,
            'duplicates' : map(json.dumps, expected),
            'cluster' : 2,
            }

    def test_give_me_duplicates_with_cluster_id(self):
        expected = [{"test1" : 1},{"test2" : 2},{"test3" : 3}]

        Duplicates = flexmock(rpc.Duplicates)

        Duplicates.should_receive("get_cluster_with_possible_duplicates_left").never()
        Duplicates.should_receive("count_already_checked").with_args(None, "project", "campaign").and_return(352)
        Duplicates.should_receive("count_duplicates_left_for_cluster").with_args(None, "project", "campaign", 2).and_return(700)
        Duplicates.should_receive("get_list_of_potential_duplicates").with_args(None, "project", "campaign", 2).and_return(expected)

        jsonrpc = scholarScape(None)
        result = jsonrpc.jsonrpc_give_me_duplicates("project", "campaign", 3, 2)

        assert result == {
            'number_of_duplicates_left_for_cluster' : 700,
            'number_duplicates_already_checked' : 352,
            'duplicates' : map(json.dumps, expected),
            'cluster' : 2,
            }

    def test_cannot_find_cluster(self):
        Duplicates = flexmock(rpc.Duplicates)

        Duplicates.should_receive("count_duplicates_left_for_cluster").never()
        Duplicates.should_receive("get_list_of_potential_duplicates").never()
        Duplicates.should_receive("get_cluster_with_possible_duplicates_left").with_args(None, "project", "campaign").and_return(None)
        Duplicates.should_receive("count_already_checked").with_args(None, "project", "campaign").and_return(352)

        jsonrpc = scholarScape(None)
        result = jsonrpc.jsonrpc_give_me_duplicates("project", "campaign", 3)

        assert result == {
            'number_of_duplicates_left_for_cluster' : 0,
            'number_duplicates_already_checked' : 352,
            'duplicates' : [],
            'cluster' : -1,
            }

    def test_human_check_mark_as_duplicate(self):
        Duplicates = flexmock(rpc.Duplicates)

        db = flexmock()
        expected = ["123", "456", "789"]

        Duplicates.should_receive("merge_duplicates").with_args(db, "p", "c", expected).once()
        Duplicates.should_receive("dont_merge_duplicates").never()

        jsonrpc = scholarScape(db)
        result = jsonrpc.jsonrpc_duplicate_human_check("p", "c", expected, True)

    def test_human_check_mark_as_not_duplicate(self):
        Duplicates = flexmock(rpc.Duplicates)

        db = flexmock()
        expected = ["123", "456", "789"]

        Duplicates.should_receive("merge_duplicates").never()
        Duplicates.should_receive("dont_merge_duplicates").with_args(db, "p", "c", expected).once()

        jsonrpc = scholarScape(db)
        result = jsonrpc.jsonrpc_duplicate_human_check("p", "c", expected, False)

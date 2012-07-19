import json
from scholarScape.server.rpc import scholarScape
from mock import patch

@patch("scholarScape.server.rpc.Duplicates")
class TestJsonRPCIsolation:
    def test_give_me_duplicates_no_cluster_id(self, Duplicates):
        expected = [{"test1" : 1},{"test2" : 2},{"test3" : 3}]

        Duplicates.get_cluster_with_possible_duplicates_left.return_value = 2
        Duplicates.count_already_checked.return_value = 352
        Duplicates.count_duplicates_left_for_cluster.return_value = 700
        Duplicates.get_list_of_potential_duplicates.return_value = expected

        jsonrpc = scholarScape(None)
        result = jsonrpc.jsonrpc_give_me_duplicates("project", "campaign", 3)

        assert result == {
            'number_of_duplicates_left_for_cluster' : 700,
            'number_duplicates_already_checked' : 352,
            'duplicates' : map(json.dumps, expected),
            'cluster' : 2,
            }

        Duplicates.get_cluster_with_possible_duplicates_left.assert_called_once_with(None, "project", "campaign")
        Duplicates.count_already_checked.assert_called_once_with(None, "project", "campaign")
        Duplicates.count_duplicates_left_for_cluster.assert_called_once_with(None, "project", "campaign", 2)
        Duplicates.get_list_of_potential_duplicates.assert_called_once_with(None, "project", "campaign", 2)

    def test_give_me_duplicates_with_cluster_id(self, Duplicates):
        expected = [{"test1" : 1},{"test2" : 2},{"test3" : 3}]

        Duplicates.get_cluster_with_possible_duplicates_left.return_value = 2
        Duplicates.count_already_checked.return_value = 352
        Duplicates.count_duplicates_left_for_cluster.return_value = 700
        Duplicates.get_list_of_potential_duplicates.return_value = expected

        jsonrpc = scholarScape(None)
        result = jsonrpc.jsonrpc_give_me_duplicates("project", "campaign", 3, 2)

        assert result == {
            'number_of_duplicates_left_for_cluster' : 700,
            'number_duplicates_already_checked' : 352,
            'duplicates' : map(json.dumps, expected),
            'cluster' : 2,
            }

        assert not Duplicates.get_cluster_with_possible_duplicates_left.called
        Duplicates.count_already_checked.assert_called_once_with(None, "project", "campaign")
        Duplicates.count_duplicates_left_for_cluster.assert_called_once_with(None, "project", "campaign", 2)
        Duplicates.get_list_of_potential_duplicates.assert_called_once_with(None, "project", "campaign", 2)

    def test_cannot_find_cluster(self, Duplicates):
        Duplicates.get_cluster_with_possible_duplicates_left.return_value = 0
        Duplicates.count_already_checked.return_value = 352

        jsonrpc = scholarScape(None)
        result = jsonrpc.jsonrpc_give_me_duplicates("project", "campaign", 3)

        assert result == {
            'number_of_duplicates_left_for_cluster' : 0,
            'number_duplicates_already_checked' : 352,
            'duplicates' : [],
            'cluster' : -1,
            }

        Duplicates.get_cluster_with_possible_duplicates_left.assert_called_once_with(None, "project", "campaign")
        Duplicates.count_already_checked.assert_called_once_with(None, "project", "campaign")
        assert not Duplicates.count_duplicates_left_for_cluster.called
        assert not Duplicates.get_list_of_potential_duplicates.called


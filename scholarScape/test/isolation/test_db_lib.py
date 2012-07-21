from scholarScape.server import db_lib
from flexmock import flexmock

class TestDBLib(object):
    def test_get_list_of_potential_duplicates(self):
        get_list_of_potential_duplicates = db_lib.Duplicates.get_list_of_potential_duplicates
        Duplicates = flexmock(db_lib.Duplicates)
        db = flexmock()
        Duplicates.should_receive("get_duplicates_pair_for_cluster").with_args(db, "p1", "c1", 2).and_return([
            {"_id1" : 1, "_id2" : 2},
            {"_id1" : 3, "_id2" : 4},
            {"_id1" : 2, "_id2" : 4},
            {"_id1" : 5, "_id2" : 2},
            ]).once()
        mocks = set([flexmock(), flexmock(), flexmock(), flexmock(), flexmock()])
        Publications = flexmock(db_lib.Publications)

        for i, mock in enumerate(mocks):
            Publications.should_receive("get_publication_by_id").with_args(db, "p1", "c1", i + 1).and_return(mock).once()

        result = get_list_of_potential_duplicates(db, "p1", "c1", 2)
        for pub in result:
            assert pub in mocks
            mocks.remove(pub)

        assert len(mocks) == 0

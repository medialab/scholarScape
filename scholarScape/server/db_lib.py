TITLE_THRESOLD = 0.8

from scholarScape.scholar.scholar import duplicates

class Publications(object):
    @staticmethod
    def get_publication_by_id(db, project, campaign, id):
        col = db[project]
        return col.find_one({'_id' : id})

class Duplicates(object):
    @staticmethod
    def get_cluster_with_possible_duplicates_left(db, project, campaign):
        dup_col = db["__dup__" + project + "-" + campaign]
        clusters = dup_col.distinct("cluster")

        cluster_id = None
        if len(clusters) != 0:
            for potential_cluster_id in clusters:
                possible_duplicates_left = Duplicates.count_duplicates_left_for_cluster(db, project, campaign, potential_cluster_id)
                if possible_duplicates_left:
                    cluster_id = potential_cluster_id

        return cluster_id

    @staticmethod
    def count_duplicates_left_for_cluster(db, project, campaign, cluster_id):
        dup_col = db["__dup__" + project + "-" + campaign]
        s = set()
        for dup in dup_col.find({'title_score' : {'$gt' : TITLE_THRESOLD, '$lt' : 1}, 'cluster' : cluster_id, 'human_say' : {"$exists" : False}}):
            s.add(dup["_id1"])
            s.add(dup["_id2"])
        return len(s)

    @staticmethod
    def count_already_checked(db, project, campaign):
        dup_col = db["__dup__" + project + "-" + campaign]
        s = set()
        for dup in dup_col.find({'title_score' : {'$gt' : TITLE_THRESOLD, '$lt' : 1}, 'human_say' : {'$exists' : True}}):
            s.add(dup["_id1"])
            s.add(dup["_id2"])
        return len(s)

    @staticmethod
    def get_list_of_potential_duplicates(db, project, campaign, cluster_id):
        dup_col = db["__dup__" + project + "-" + campaign]

        # Get the cluster
        possible_duplicates = dup_col.find({'title_score' : {'$gt' : TITLE_THRESOLD, '$lt' : 1}, 'cluster' : cluster_id, 'human_say' : {'$exists' : False}})

        # Select the ids of the duplicated publications
        duplicate_ids = set()
        for possible_duplicate in possible_duplicates :
            duplicate_ids.add(possible_duplicate['_id1'])
            duplicate_ids.add(possible_duplicate['_id2'])

        # Get the duplicated publications
        duplicates = []
        for duplicate_id in duplicate_ids :
            publication = Publications.get_publication_by_id(db, project, campaign, duplicate_id)
            # TODO
            # If the publication has a parent, replace the publication by its parent
            duplicates.append(publication)

        return duplicates

    @staticmethod
    def merge_duplicates(db, project, campaign, ids):
        col = db[project]
        dup_col = db["__dup__" + project + "-" + campaign]
        duplicates.merge_duplicates(campaign, col, dup_col, ids)

    @staticmethod
    def dont_merge_duplicates(db, project, campaign, ids):
        col = db[project]
        dup_col = db["__dup__" + project + "-" + campaign]
        duplicates.merge_duplicates(campaign, col, dup_col, ids, mark_with=False)

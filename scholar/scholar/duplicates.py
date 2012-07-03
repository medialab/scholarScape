import time
import logging
from pymongo import Connection
from bson.objectid import ObjectId
from itertools import combinations, product, chain
import Levenshtein
import math
import networkx as nx
import sys
from scrapy import log

from pipelines import MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE

def myprint(x):
    pass

def factorial(n):
    """factorial(n): return the factorial of the integer n.
    factorial(0) = 1
    factorial(n) with n<0 is -factorial(abs(n))
    """
    result = 1
    for i in xrange(1, abs(n)+1):
        result *= i
    if n >= 0:
        return result
    else:
        return -result

def binomial(n, k):
    """binomial(n, k): return the binomial coefficient (n k)."""
    assert isinstance(n, (int, long)) and isinstance(k, (int, long))
    if k < 0 or k > n or n == 0:
        return 0
    if k == 0 or k == n:
        return 1
    return factorial(n) // (factorial(k) * factorial(n-k))


def rate_duplicates(pub1,pub2) :
    def _clean(_str) :
        _str=_str.encode("utf-8") if isinstance(_str,unicode) else _str
        _str=_str.lower()
        return _str

    string1=_clean(pub1["title"])
    string2=_clean(pub2["title"])
    if not string1 or not string2 :
        return 0 , None
    min_len, max_len = min(len(string1),len(string2)), max(len(string1),len(string2))

    # inclusion test
    if (string1 in string2 or string2 in string1) and min_len/max_len > 0.4:
        inclusion_rate=abs(len(string1)-len(string2))/float(len(string1)+len(string2))
    else :
        inclusion_rate=0
    # levenshtein test
    levenshtein_rate=Levenshtein.ratio(string1,string2)

    if inclusion_rate>0.4 :
        # add 0.2 to level up to levenshtein rate
        title_score = inclusion_rate+0.2
    elif levenshtein_rate>0.6 :
        title_score = levenshtein_rate
    else :
        return (None, None)

    # authors test : score = 1 if one author is common (i.e. inclusion test), none otherwise
    # actually not used in the duplicates calculation because not sure about the test
    if pub1.get("authors") and pub2.get("authors") :
        authors1 = map(_clean, pub1["authors"])
        authors2 = map(_clean, pub2["authors"])

        for pair in product(authors1, authors2) :
            if pair[0] in pair[1] or pair[1] in pair[0]:
                author_score = 1
                return title_score, author_score

    return title_score, None


def calculate_dup_scores(col,dup_col,human_check_treshold) :
    """
       calculate duplicates scores on all combinations of publications found in collection col
       TODO: groups duplicates in clusters
       store data in the collection dup_col given
    """
    t1 = time.clock()
    logging.info("Calculating duplicates ratio")
    dup_col.remove({})
    dup_col.drop_indexes() # for fast insertion
    publications = col.find({"download_delay" : {"$exists" : False}, "campaign" : campaign})
    total_nr_pairs = binomial(col.find({"download_delay" : {"$exists" : False}, "campaign" : campaign }).count(),2)

    #prepare graph
    g = nx.Graph()

    advance = 0
    dup_scores = []
    myprint(publications.count())
    for i, pairs in enumerate(combinations(publications,2)):
        percentage = math.floor( float(i)/float(total_nr_pairs)*100 )
        title_score, author_score = rate_duplicates(pairs[0], pairs[1])
        if title_score :
            dup_scores.append({   # preparation of bulk insert
                "_id1" : pairs[0]["_id"],
                "_id2" : pairs[1]["_id"],
                "title_score" :  title_score,
                "author_score" : author_score
            })
            if title_score >= human_check_treshold :
                g.add_node(pairs[0]["_id"] )
                g.add_node(pairs[1]["_id"] )
                g.add_edge(pairs[0]["_id"], pairs[1]["_id"], weight=title_score)
        if percentage > advance and dup_scores:
            dup_col.insert(dup_scores) #bulk insert to gain perf
            dup_scores = []
            advance = percentage
            logging.info("%i : %i" % (advance, time.clock()-t1))

    cluster_id=0
    logging.info("construct network of duplicates clusters ")
    for duplication_cluster in nx.connected_component_subgraphs(g) :
        dups=[{"_id1":edge[1],"_id2":edge[0]} for edge in duplication_cluster.edges_iter()]
        logging.info("found one cluster %s with %s duplicates " % (cluster_id,len(dups)))
        #logging.info(str(dups))
        dup_col.update({"$or" : dups}, {"$set" : {"cluster" : cluster_id} }, multi=True )
        cluster_id+=1

    dup_col.ensure_index([("title_score",1), ("human_say",1)]) # for fast querying
    logging.info("Created the graph at %i, writing it on the disk" % (time.clock() - t1) )
    nx.write_gexf(g,"duplicates_" + project + " - " + campaign + ".gexf")
    logging.info("Done : %i", time.clock() - t1)


def merge_duplicates(campaign, col, dup_col, publication_ids, duplicate_flag="human_say") :
    """
        merge a list of publications ids in one parent publication
        already merged publication can be present in publication_ids
        duplicate_flag indicates the name of the key to set to True in the duplicate collection (default 'human_say')
    """
    t1 = time.clock()

    # replace parent publications by their children
    children = dict()
    for publication_id in publication_ids :
        children_pattern = {"parent_id" : publication_id}
        if campaign != "*":
            children_pattern['campaign'] = campaign
        # Be carefule : if children[pub_id] = [] then pub_id is a child
        children[publication_id] = list(col.find(children_pattern,{"_id" : 1}))

    logging.info("nb parents found : %s"%(len([k for (k,v) in children.iteritems() if v])))

    # UPDATE the combinations of duplicates
    for pub1,pub2 in combinations(publication_ids,2):
        # retrieve children
        _pub1 = children[pub1] if children[pub1] else [pub1]
        _pub2 = children[pub2] if children[pub2] else [pub2]
        # generate duplicates pairs from children, pairs are generated in both ways (a,b) and (b,a)
        # change the flag sepcified in duplicate_flag to true i.e. human_say or automatic_treshold_1 to track merging in dup_col
        dup_col.update({"$or" : [{"_id1":ObjectId(pair[0]),"_id2":ObjectId(pair[1])} for pair in chain(product(_pub1,_pub2),product(_pub2,_pub1)) ] }, {"$set" : {duplicate_flag : True} }, multi=True )


    #information to get to create the father
    what_to_get = {
        "title"      : 1,
        "authors"    : 1,
        "times_cited": 1,
        "book_title" : 1,
        "depths"     : 1,
        "cites"      : 1,
        "campaign"   : 1,
        "source"     : 1,
        "_id"        : 0
    }

    # get all children : children of publications + publications without children
    publications_and_children=[v for v in children.values() if v] + [k for (k,v) in children.iteritems() if not v]
    logging.info("%s"%(publications_and_children))
    # old parents = pulications with children
    old_parents=[k for (k,v) in children.iteritems() if v]

    # remove old parents
    if old_parents :
        col.remove({"$and" : [ {"$or":[{"_id":id} for id in old_parents]} , {"type" : "super_publication"}]})

    children_ids = []
    title = ""
    authors = set()
    book_title = ""
    depths = set()
    cites = set()
    times_cited = 0
    nr_children = 0



    # merge all children in one parent
    for pub_id in publications_and_children :
        children_ids.append({"_id" : pub_id })
        nr_children += 1
        pub = col.find_one( {"_id" : pub_id }, what_to_get)
        if not pub:
            # should not happen !
            logging.info("unknown Publication found in _dup_ collection : "+str(pub_id))
        else :
            if pub.get("title") and len(pub["title"]) > len(title):
                title =  pub["title"]
            if pub.get("authors"):
                authors = authors|set(pub["authors"])
            if pub.get("book_title") and len(pub["book_title"]) > len(book_title):
                book_title = pub["book_title"]
            depths = depths | set(pub["depths"])
            if pub.get("cites") :
                try :
                    cites = cites | set( [ pub["cites"] ] )
                except :
                    print pub["cites"]
                    exit(0)
            if pub.get("times_cited") :
                times_cited += pub["times_cited"]
    # create a new common parent
    newparent_id = col.insert( {
                    "title" : title,
                    "authors" : list(authors),
                    "book_title" : book_title,
                    "depths" : list(depths),
                    "cites" : list(cites),
                    "times_cited" : times_cited,
                    "type" : "super_publication",
                    "nr_children" : nr_children,
                    "campaign" : campaign
                } )
    logging.info("created the parent with id : %s for %i children" % (newparent_id,nr_children) )
    # add reference to the new parent in children
    col.update({"$or" : children_ids}, {"$set" : {"parent_id" : newparent_id} }, multi=True )
    logging.info("Finished merging duplicates in %i" % (t1 - time.clock()) )


def remove_duplicates(db, project, campaign) :
    title_thresold = 0.8
    col = db[project]
    dup_col = db["__dup__" + project + "-" + campaign]
    dup_col.drop()
    col.remove({"type" : "super_publication"})
    dup_col = db["__dup__" + project + "-" + campaign]
    myprint("REMOVE_DUPLICATES : I've been summoned to eradicate all duplicates")
    t1 = time.clock()

    logging.info("Going to calculate_dup_scores for %s - %s" % (project, campaign) )
    calculate_dup_scores(col,dup_col,title_thresold)
    logging.info("I finished calculating dup scores, it took %i seconds" % ( t1 - time.clock()) )
    logging.info("Now I'm going to merge duplicates of score 1")
    t1 = time.clock()

    # get clusters of duplicates by filtering on title score
    list_dup_ids_by_cluster=dup_col.group(
    ["cluster"],
    {"title_score" : {"$gte" : 1} },
    {'list': []},
    'function(dup, cluster) {cluster.list.push(dup["_id1"]);cluster.list.push(dup["_id2"]);}'
    )
    logging.info("number of clusters with title_score=1 : %i"%(len(list_dup_ids_by_cluster)))

    # merge dups by clusters
    for cluster in list_dup_ids_by_cluster :
        duplicates_to_merge = list(set(cluster["list"]))
        logging.info("%s"%(duplicates_to_merge))
        logging.info(" merging a cluster with %s duplicates" % len(duplicates_to_merge))
        merge_duplicates(col, dup_col, duplicates_to_merge,"automatic_treshold_1")

    nr_parents = col.find({"nr_children" : {"$exists" : True}}).count()
    nr_children = col.find({"parent_id" : {"$exists" : True}}).count()
    logging.info("Found %i mergeable duplications in %i 'families' for an average of %f children per family"
            % ( nr_children, nr_parents, float(nr_children)/(float(nr_parents) or 1) ) )


if __name__ == "__main__":
    if len(sys.argv) == 3 :
        connection = Connection("mongodb://%s:%s@%s:%s/%s" % (MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE) )
        db = connection[MONGO_DATABASE]
        project = sys.argv[1]
        campaign = sys.argv[2]
        if project not in db.collection_names():
            print "bad project"
            exit(0)
        if not db[project].find( { "download_delay" : {"$exists" : True}, "name" : campaign } ).count() > 0 :
            print "bad_campaign"
            exit(0)

        logging.basicConfig(filename='duplicates-'+project+'-'+campaign+'.log',filemode="w+",level=logging.DEBUG)
        myprint = logging.info
        remove_duplicates(db, project,campaign)
    else :
        print "bad number of arguments"
        exit(0)

# if called inside scrapy
else :
    myprint = log.msg

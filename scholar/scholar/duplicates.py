import time
import logging
from pymongo import Connection
from itertools import combinations, product
import Levenshtein
import math
import networkx as nx
import sys
from scrapy import log

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

    if pub1.get("authors") and pub2.get("authors") :
        authors1 = map(_clean, pub1["authors"])
        authors2 = map(_clean, pub2["authors"])
        
        author_score = 0
        
        for pair in product(authors1, authors2) :
            if pair[0] in pair[1] or pair[1] in pair[0]:
                author_score=1
                return title_score, author_score
                
    return title_score, None

def remove_duplicates(db, project, campaign) :
    title_thresold = 0.8
    col = db[project]
    dup_col = db["__dup__" + project + "-" + campaign]
    myprint("REMOVE_DUPLICATES : I've been summoned to eradicate all duplicates")
    def calculate_dup_scores() :
        logging.info("Calculating duplicates ratio")
        dup_col.remove({})
        dup_col.drop_indexes() # for fast insertion
        publications = col.find({"download_delay" : {"$exists" : False}, "campaign" : campaign})
        total_nr_pairs = binomial(col.find({"download_delay" : {"$exists" : False}, "campaign" : campaign }).count(),2)
        
        advance = 0
        dup_scores = []
        
        for i, pairs in enumerate(combinations(publications,2)):
            percentage = math.floor( float(i)/float(total_nr_pairs)*100 )
            if percentage > advance:
                dup_col.insert(dup_scores) #bulk insert to gain perf
                dup_scores = []
                advance = percentage
                logging.info("%i : %i" % (advance, time.clock()-t1))
            title_score, author_score = rate_duplicates(pairs[0], pairs[1])
            if title_score :
                dup_scores.append({   # preparation of bulk insert
                    "_id1" : pairs[0]["_id"], 
                    "_id2" : pairs[1]["_id"],
                    "title_score" :  title_score,
                    "author_score" : author_score
                })
        
        dup_col.ensure_index([("title_score",1), ("human_say",1)]) # for fast querying

    def find_and_merge_duplicates() :
        t1 = time.clock()
        g = nx.Graph()
        col.remove({"type" : "super_publication"})
        pairs = dup_col.find({"$or" : [
                                {"title_score" : {"$gt" : title_thresold}, "human_say" : {"$ne" : False} }, 
                                {"human_say" : True} 
                               ] 
                              })
        total = pairs.count()
        advance = 0
        for i,pair in enumerate(pairs) :
            percentage = float(i)/float(total)*100
            
            g.add_node(pair['_id1'] )
            g.add_node(pair['_id2'] )
            g.add_edge(pair['_id1'], pair['_id2'], weight=pair['title_score'])
        
        logging.info("Created the graph at %i, writing it on the disk" % (time.clock() - t1) )
        #nx.write_gexf(g,"duplicates" + project + " - " + campaign + ".gexf")
        logging.info("Done : %i", time.clock() - t1)

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

        for mergeable_publications in nx.connected_components(g) :
            # find longuest title
            
            children_ids = []
            title = ""
            authors = set()
            book_title = ""
            depths = set()
            cites = set()
            times_cited = 0
            nr_children = 0
            
            for pub_id in mergeable_publications :
                children_ids.append({"_id" : pub_id })
                nr_children += 1
                pub = col.find_one( {"_id" : pub_id }, what_to_get)
                if not pub:
                    print pub_id
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
            sP_id = col.insert( {  
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
            col.update({"$or" : children_ids}, {"$set" : {"parent_id" : sP_id} }, multi=True )
    
    t1 = time.clock()
    logging.info("Going to calculate_dup_scores for %s - %s" % (project, campaign) )
    calculate_dup_scores()
    logging.info("I finished calculating dup scores, it took %i seconds" % ( t1 - time.clock()) )
    logging.info("Now I'm going to find and merge duplicates")
    t1 = time.clock()
    find_and_merge_duplicates()
    logging.info("Finished merging duplicates in %i" % (t1 - time.clock()) )
    nr_parents = col.find({"nr_children" : {"$exists" : True}}).count()
    nr_children = col.find({"parent_id" : {"$exists" : True}}).count()
    logging.info("Found %i mergeable duplications in %i 'families' for an average of %f children per family" 
            % ( nr_children, nr_parents, float(nr_children)/(float(nr_parents) or 1) ) )
            
            
if __name__ == "__main__":
    if len(sys.argv) == 3 :   
        db = Connection("lrrr.medialab.sciences-po.fr")['scholarScape']
        project = sys.argv[1]
        campaign = sys.argv[2]
        if project not in db.collection_names():
            print "bad project"
            exit(0)
        if not db[project].find( { "download_delay" : {"$exists" : True}, "name" : campaign } ).count() > 0 :
            print "bad_campaign"
            exit(0)
        #filename='duplicates-'+project+'-'+campaign+'.log',
        logging.basicConfig(level=logging.DEBUG)
        myprint = logging.info
        remove_duplicates(db, project,campaign)
    else :
        print "bad number of arguments"
        exit(0)

# if called inside scrapy     
else :
    myprint = log.msg

from pymongo import Connection
import networkx as nx

def create_graph_from_db(host, port, db, collection, gexf_output) :
    g = nx.Graph()

    connection = Connection(host,port)
    db = connection[db]
    collection = db[collection]

    def add_pub_in_graph(pub) :
        title       = pub["title"] if "title" in pub else ""
        times_cited = pub["times_cited"] if "times_cited" in pub else 1
        
        if "id" in pub :
            g.add_node(pub["id"],weight=int(times_cited),title=title)
            if "cites" in pub:
                g.add_edge(pub["id"],pub["cites"])

    for pub in collection.find({"parent_id": {"$ne" : "null"}}): # get only nodes that are not leaves/children
        add_pub_in_graph(pub)
      
    nx.write_gexf(g,gexf_output)



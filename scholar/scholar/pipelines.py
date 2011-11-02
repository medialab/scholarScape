#-*- coding:utf-8 -*-


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from pymongo import Connection
import Levenshtein
from colorize import colorize
import pprint

pp = pprint.PrettyPrinter(indent=4)

class MongoDBPipeline(object):
    def __init__(self):
        #TODO a templater
        self.connection = Connection("mongodb://scholarScape:diabal@localhost:27017/scholarScape")
        self.db=self.connection['scholarScape']
    def process_item(self, item, spider):
        collection = self.db[item['project']]
        print collection
            
        blue = colorize.blue
        green = colorize.green
        red = colorize.red
               
        del item['project']
        # 1st lets check if the id is in the database
        print green("processing item")
        if item.get('id') : 
            same_item = collection.find_one({"id" : item.get('id')})
            if same_item :
                print same_item
                collection.update({"id" : item.get('id')}, {
                                            "$push" : {
                                                "depths" : item['depth_cb']} }) 
                print red("Already in the database, added item's depth to the publication's depth list")
                return item
        # then we have to check against all the 1st records
        for each in collection.find({"parent_id" : {"$exists" : False}}) : # we don't get the children
            if each.get("title") and \
               item.get("title") and \
               rate_duplicates(each.get("title"), item.get("title"))  :
                # if item has children, its already a superPublication
                print red("""This item's title fuzzy matches another one, add it with property parent_id
                            and add his depth to the parent""")
                            
                 # if it's a superPublication it already has nr_children attribute            
                if 'nr_children' in each:
                    each['ids'].append(item['id'])
                    each['times_cited']+=   item.get('times_cited')
                    each['cites']      += [ item.get('cites') ]
                    if len(item.get('title') or "") > len(each.get("title") or "") :
                        each['title']= item['title']
                    if len(item.get('authors') or "") > len(each.get("authors") or "") :
                        each['authors'] = item['authors']
                    each['depths'].append(item['depth_cb'])
                    each['nr_children'] += 1       
                    item['parent_id'] = each['_id']
                    
                # we have to create the superpublication    
                else :
                    superPublication = {
                        "title"      : max( [ each.get('title') or "", item.get("title") or "" ], key=len   ),
                        "authors"    : max( [ each.get('authors') or "", item.get("authors") or ""], key=len   ),
                        "times_cited": each.get('times_cited') or 0 + item.get('times_cited') or 0,
                        "cites"      : [ each.get('cites'), item.get('cites') ],
                        "depths"     : [ each['depth_cb'], item['depth_cb'] ],
                        "type" :"SuperPublicacion",
                        "ids" : [ each.get('id'), item.get('id') ]
                    }
                    superPublication["cites"] = filter(lambda v : v,superPublication["cites"]) # remove Nones
                    superPublication["nr_children"] = 2
                    sP_id = collection.insert(dict(superPublication))
                    each['parent_id'] = sP_id
                    item['parent_id'] = sP_id                        
                print red("duplicate item: was detected!")
                collection.update({"_id": each['_id']}, dict(each))
                collection.insert(dict(item))
                return item
            # if we could not determine it was a duplicate we insert it         
        collection.insert(dict(item))
        print blue("item inserted")
        return item



def rate_duplicates(string1,string2) :
	
	def _clean(_str) :
		_str=_str.encode("utf-8") if isinstance(_str,unicode) else _str
		_str=_str.lower()
		return _str
	
	string1=_clean(string1)
	string2=_clean(string2)
	
	# inclusion test
	if (string1 in string2 or string2 in string1) :
		inclusion_rate=abs(len(string1)-len(string2))/float(len(string1)+len(string2))
	else :
		inclusion_rate=0
	# levenshtein test
	levenshtein_rate=Levenshtein.ratio(string1,string2)
	
	if inclusion_rate>0.4 :
		# add 0.2 to level up to levenshtein rate
		return inclusion_rate+0.2
	elif levenshtein_rate>0.6 :
		return levenshtein_rate
	else :	
		return None	
   

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from pymongo import Connection
import Levenshtein
from colorize import colorize

def size(thing) :
 if thing:
    return len(thing)
 else:
    return 0

def myInt(i) :
    if i:
        return i
    else :
        return 0

class MongoDBPipeline(object):
    #sudo mongod --dbpath /var/lib/mongodb
    

    
    def __init__(self):
        self.connection = Connection()
        self.db=self.connection['scholarScape']
        self.collection=self.db['publications']    
        self.collection.remove({}); 
                
    def process_item(self, item, spider):
        blue = colorize.blue
        green = colorize.green
        red = colorize.red
        # lets see if its not a duplicate
        
        # 1st lets check if the id is in the database
        print green("processing item")
        same_item = self.collection.find_one({"id" : item.get('id')})
        if same_item :
            self.collection.update({"id" : item.get('id')}, {
                                        "$push" : {
                                            "depths" : item['depth_cb']
                                         }
                                    }) 
            print red("Already in the database, added item's depth to the publication's depth list")
            return item
        # then we have to check against all the 1st records
        if self.collection.find({}).count() :    
            for each in self.collection.find({"parent_id": {"$ne" : "null"}}) : # we don't get the children
                if each.get("title") and \
                   item.get("title") and \
                   rate_duplicates(each.get("title"), item.get("title"))  :
                    # if item has children, its already a superPublication
                    print red("This item's title fuzzy matches another one, add it with property parent_id \
                                and add his depth to the parent")
                    if 'nr_children' in each: # we got ourselves a parent
                        each['times_cited']+=   item.get('times_cited')
                        each['cites']      += [ item.get('cites') ]
                        if size(item.get('title')) > size(each.get("title")) : # i use my function "size" because dict.get can return None
                            each['title']= item['title']
                        if size(item.get('authors')) > size(each.get("authors")) :
                            each['authors'] = item['authors']
                        each['depths'].append(item['depth_cb'])
                        each['nr_children'] += 1
                        self.collection.update(dict(each))
                        item['parent_id'] = each['_id']
                        self.collection.insert(dict(item)) 
                    else :
                        superPublication = {
                            "title"      : max( [ each.get('title')  , item.get("title")  ], key=size   ),
                            "authors"    : max( [ each.get('authors'), item.get("authors")], key=size   ),
                            "times_cited": myInt(each.get('times_cited')) + myInt(item.get('times_cited')),
                            "cites"      : [ each.get('cites'), item.get('cites') ],
                            "depths"   : [ each['depth_cb'], item['depth_cb'] ],
                        }
                        superPublication["cites"] = filter(lambda v : v,superPublication["cites"]) # remove Nones
                        superPublication["nr_children"] = 2
                        sP_id = self.collection.insert(dict(superPublication))
                        each['parent_id'] = sP_id
                        item['parent_id'] = sP_id                        
                        self.collection.update(dict(each))
                        self.collection.update(dict(item))
                        print red("duplicate item:" + str(item) + "was detected!")
                        return item    
                    
                else :
                    self.collection.insert(dict(item))
                    print blue("item inserted")
                    return item
        else :
            self.collection.insert(dict(item))
            print green("first item inserted")
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
		return 0	
   

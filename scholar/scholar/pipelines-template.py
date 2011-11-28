#-*- coding:utf-8 -*-


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from pymongo import Connection
import Levenshtein
import pprint
from scrapy import log

MONGO_USER     = "{{user}}"
MONGO_PASSWD   = "{{passwd}}"
MONGO_HOST     = "{{host}}"
MONGO_PORT     = "{{port}}"
MONGO_DATABASE = "{{database}}"

class MongoDBPipeline(object):
    def __init__(self):
        self.connection = Connection("mongodb://%s:%s@%s:%s/%s" % (MONGO_USER, MONGO_PASSWD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE) )
        self.db=self.connection[MONGO_DATABASE]
    def process_item(self, item, spider):
        collection = self.db[item['project']]
        print collection
    
        del item['project']
        # 1st lets check if the id is in the database
        log.msg("processing item")
        if item.get('id') : 
            same_item = collection.find_one({"id" : item.get('id'), "campaign" : item['campaign']})
            if same_item :
                collection.update({"id" : item['id']}, {
                                            "$addToSet" : {
                                                "depths" : item['depth_cb']} }) 
                log.msg("item " + str(item['id']) + " already in DB, added only depth")
                return item
                
        # then we have to check against all the 1st records
#        for each in collection.find({"parent_id" : {"$exists" : False}}) : # we don't get the children
#            if each.get("title") and \
#               item.get("title") and \
#               rate_duplicates(each.get("title"), item.get("title"))  :
#                    log.msg(rate_duplicates(each.get("title"), item.get("title")))
#                    log.msg("found duplicate")
#                                
#                     # if it's a superPublication it already has nr_children attribute            
#                    if 'nr_children' in each:
#                        log.msg("already superPublication")                    
#                        new_values={
#                            "$push"     : { "children_ids"  : item['id']},
#                            "$inc"      : { "times_cited"   : item.get('times_cited'),
#                                            "nr_children"   : 1},
#                            "$addToSet" : { "cites"         : item.get('cites'),
#                                            "depths"        : item["depth_cb"]},
#                            "$set"      : {}
#                        }
#                        if len(item.get('title') or "") > len(each.get("title") or "") :
#                            new_values["$set"]["title"] = item['title']
#                        if len(item.get('authors') or "") > len(each.get("authors") or "") :
#                            new_values["$set"]["authors"] = item['authors']
#                        
#                        collection.update({"_id" : each["_id"]} , new_values)
#                        item['parent_id'] = each['_id']
#                        
#                    # we have to create the superpublication    
#                    else :
#                        log.msg("create superpublication")
#                        try :
#                            superPublication={
#                                "title"       : max([each.get('title') or "",item.get("title") or ""],key=len),
#                                "authors"     : max([each.get('authors') or "",item.get("authors") or ""],key=len),
#                                "times_cited" : (each.get('times_cited') or 0)+(item.get('times_cited') or 0),
#                                "cites"       : [each.get('cites'),item.get('cites')],
#                                "depths"      : list(set( each['depths'] + [ item['depth_cb'] ] )),
#                                "campaign"    : each['campaign'],
#                                "children_ids": [each.get('id'),item.get('id')]
#                            }
#                        except Exception as e:
#                            log.msg(str(item))
#                            log.msg(str(each))
#                        log.msg(str(superPublication))
#                        superPublication["cites"] = filter(lambda v : v,superPublication["cites"]) # remove Nones
#                        log.msg("after filtring Nones")
#                        log.msg(str(superPublication))
#                        superPublication["nr_children"] = 2
#                        sP_id = collection.insert(dict(superPublication))
#                        collection.update({"_id": each['_id']}, { "$set" : {"parent_id" : sP_id} })
#                        item['parent_id'] = sP_id                          
        item_to_insert = dict(item)
        item_to_insert['depths'] = [ item_to_insert['depth_cb'] ]
        del item_to_insert['depth_cb']
        collection.insert(item_to_insert)
        log.msg("item inserted")
        return item

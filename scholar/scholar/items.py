# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class ScholarItem(Item):
    # define the fields for your item here like:
    id = Field()
    title = Field()
    type_pub = Field()
    authors = Field()
    href = Field()
    times_cited = Field()
    cites = Field()
    scrapped_from = Field()
    abstract = Field()
    authors = Field()
    source = Field()
    book_title = Field()
    date = Field()
    depth_cb = Field()
    parent_id = Field()
    
    
    

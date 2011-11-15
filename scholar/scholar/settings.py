# Scrapy settings for scholar project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'scholar'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['scholar.spiders']
NEWSPIDER_MODULE = 'scholar.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

DEPTH_LIMIT=3
CONCURRENT_REQUESTS_PER_DOMAIN = 1

#CLOSESPIDER_ITEMCOUNT=5
#CLOSESPIDER_TIMEOUT=5

SPIDER_MIDDLEWARES = {
    'scholar.middlewares.dontincreasedepth.DontIncreaseMiddleware' : 901,
    #depth middleware number is 900 so dontIncreaseMiddleware will be called before depthmiddleware on the output path
}

DOWNLOADER_MIDDLEWARES = {
    'scholar.middlewares.randomuseragent.RandomUserAgentMiddleware': None,
    'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': 400,
}

USER_AGENT_LIST = [
"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.6) Gecko/20070725 Firefox/2.0.0.6",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)",
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)",
"Mozilla/4.0 (compatible; MSIE 5.0; Windows NT 5.1; .NET CLR 1.1.4322)",
"Opera/9.20 (Windows NT 6.0; U; en)",
"Opera/9.00 (Windows NT 5.1; U; en)",
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 8.50",
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 8.0",
"Mozilla/4.0 (compatible; MSIE 6.0; MSIE 5.5; Windows NT 5.1) Opera 7.02 [en]",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20060127 Netscape/8.1"
]

EXTENSIONS = [
'scholar.extensions.spider_status.Spider_status',
'scrapy.contrib.closespider.CloseSpider'
]

ITEM_PIPELINES = [
'scholar.pipelines.MongoDBPipeline'
]

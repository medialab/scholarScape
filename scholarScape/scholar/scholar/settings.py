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
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6'

DEPTH_LIMIT=3
CONCURRENT_REQUESTS_PER_DOMAIN = 1

#CLOSESPIDER_ITEMCOUNT=5
#CLOSESPIDER_TIMEOUT=5

SPIDER_MIDDLEWARES = {
    'scholar.middlewares.dontincreasedepth.DepthDontIncreaseMiddleware' : 900,
    'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
    #depth middleware number is 900 so dontIncreaseMiddleware will be called before depthmiddleware on the output path
}

DOWNLOADER_MIDDLEWARES = {
    # 'scholar.middlewares.randomuseragent.RandomUserAgentMiddleware': None,
    # 'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': 400,
	'scholar.middlewares.proxymiddleware.ProxyMiddleware': 750,
    'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
}

PROXY_URL="http://localhost:8118/"

EXTENSIONS = [
'scholar.extensions.spider_status.Spider_status',
'scholar.extensions.duplicates.Duplicates',
'scrapy.contrib.closespider.CloseSpider'
]

ITEM_PIPELINES = [
'scholar.pipelines.MongoDBPipeline'
]

#Breadth first 
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'

from scholar.settings import PROXY_URL
from scrapy import log

class ProxyMiddleware(object):
    
    def process_request(self, request, spider):
        request.meta["proxy"]=PROXY_URL
        log.msg('using proxy %s'%request.meta["proxy"])

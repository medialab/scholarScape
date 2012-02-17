from scholar.settings import USER_AGENT_LIST
import random
from scrapy import log

class RandomUserAgentMiddleware(object):
    
    def process_request(self, request, spider):
        ua  = random.choice(USER_AGENT_LIST)
        if ua:
            request.headers.setdefault('User-Agent', ua)
        log.msg(' UserAgent %s'%request.headers)
        request.meta["proxy"]="http://localhost:8118/"
        log.msg('proxy %s'%request.meta["proxy"])

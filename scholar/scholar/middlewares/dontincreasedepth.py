""" 
DontIncreaseDepth Middleware
works in conjunction with DepthMiddleware
It enables you to specify which link must because
counted as going deeper
"""


from scrapy import log
from scrapy.http import Request

class DontIncreaseMiddleware(object):
    def process_spider_output(self,response,result,spider):
        def process_dontIncrease(request) :
            if isinstance(request, Request):
                if request.meta.get('dontIncrease'):
                    if 'depth' in request.meta :
                        request.meta['depth'] -= 1
                    else :
                        request.meta['depth'] = -1             
                    log.msg("\n\nrequest to " + request.url + ": depth was not increased\n\n")
            return request
        
        return (process_dontIncrease(r) for r in result)

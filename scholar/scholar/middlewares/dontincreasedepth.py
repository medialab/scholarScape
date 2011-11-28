#""" 
#DontIncreaseDepth Middleware
#works in conjunction with DepthMiddleware
#It enables you to specify which link must because
#counted as going deeper
#"""


#from scrapy import log
#from scrapy.http import Request

#class DontIncreaseMiddleware(object):
#    def process_spider_output(self,response,result,spider):
#        def process_dontIncrease(request) :
#            if isinstance(request, Request):
#                if request.meta.get('dontIncrease'):
#                    if 'depth' in request.meta :
#                        log.msg('depth before %i' % request.meta['depth'])
#                        request.meta['depth'] -= 1
#                        log.msg('depth after %i' % request.meta['depth'])
#                    else :
#                        request.meta['depth'] = -1
#                        log.msg('request had not depth so I set it to %i' % request.meta['depth'])        
#                    log.msg("\n\nrequest to " + request.url + ": depth was not increased\n\n")
#            return request
#        
#        return (process_dontIncrease(r) for r in result)
#        
#        
#        
"""
Depth Spider Middleware + DontIncreaseDepth Middleware

See documentation in docs/topics/spider-middleware.rst
"""

import warnings

from scrapy import log
from scrapy.http import Request
from scrapy.exceptions import ScrapyDeprecationWarning

class DepthDontIncreaseMiddleware(object):

    def __init__(self, maxdepth, stats=None, verbose_stats=False, prio=1):
        self.maxdepth = maxdepth
        self.stats = stats
        self.verbose_stats = verbose_stats
        self.prio = prio

    @classmethod
    def from_settings(cls, settings):
        maxdepth = settings.getint('DEPTH_LIMIT')
        usestats = settings.getbool('DEPTH_STATS')
        verbose = settings.getbool('DEPTH_STATS_VERBOSE')
        prio = settings.getint('DEPTH_PRIORITY')
        if usestats:
            from scrapy.stats import stats
        else:
            stats = None
        return cls(maxdepth, stats, verbose, prio)

    def process_spider_output(self, response, result, spider):
        def _filter(request):
            if isinstance(request, Request):
                log.msg(request.url)
                if "start=" in request.url:
                    inc = 0
                    log.msg(response.url)
                    log.msg("pagination link, no increase") 
                else :
                    inc = 1
                depth = response.request.meta['depth'] + inc
                request.meta['depth'] = depth
                if self.prio:
                    request.priority -= depth * self.prio
                if self.maxdepth and depth > self.maxdepth:
                    log.msg("Ignoring link (depth > %d): %s " % (self.maxdepth, request.url), \
                        level=log.DEBUG, spider=spider)
                    return False
                elif self.stats:
                    if self.verbose_stats:
                        self.stats.inc_value('request_depth_count/%s' % depth, spider=spider)
                    self.stats.max_value('request_depth_max', depth, spider=spider)
            return True

        # base case (depth=0)
        if self.stats and 'depth' not in response.request.meta: 
            response.request.meta['depth'] = 0
            if self.verbose_stats:
                self.stats.inc_value('request_depth_count/0', spider=spider)
        
        log.msg("max depth :" + str(self.maxdepth))
        return (r for r in result or () if _filter(r))

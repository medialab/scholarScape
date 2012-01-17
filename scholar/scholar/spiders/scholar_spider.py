# -*- coding: utf-8 -*-

from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scholar.items import ScholarItem
from scrapy.http import Request, FormRequest

import copy

from scrapy.utils.spider import iterate_spider_output
from scrapy.contrib.spiders.init import InitSpider
from scrapy.conf import settings

from scrapy import log
import re


from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc

from urllib import quote_plus as qp
import json
from urlparse import urlparse

class ParsingRules :
	
	# result item 
	item_xpath="//div[@class ='gs_r']"
 
 	#inside item
 	title_xpath="div[@class ='gs_rt']/h3" 	    # title  (anchor element)
 	href_xpath="div[@class ='gs_rt']/h3/a/@href" 	# document href
	info_xpath="font/*[@class ='gs_a']" 	        # author, year and publisher 
 	cited_by_xpath=".//span[@class ='gs_fl']/a[1]"  
 	abstract_xpath = "font"
 	type_pub_xpath = ".//span[@class='gs_ctc']"     # [PDF], [BOOK], [HTML] etc..
 	bibtex_path = "font//span[@class ='gs_fl']/a[last()]/@href"

class ScholarRule(Rule):
    ''' Rule is specialized to have the 
        attribute dontIncreaseDepth '''
    def __init__(self, *a, **kw):
        if 'dontIncreaseDepth' in kw:
            self.dontIncreaseDepth = kw['dontIncreaseDepth']
            del kw['dontIncreaseDepth'] 
        super(ScholarRule, self).__init__(*a, **kw)


class ScholarSpider(CrawlSpider): #depth first left to right
   
   # ------soon the crawlspider will inherit from initspider
   #       and this will no longer be necessary  -----------

    def __init__(self, *a, **kw):
        self.bibtex = False
        if 'start_urls_' in kw :
            self.start_urls = kw['start_urls_'].split(";")
            print self.start_urls
        super(ScholarSpider, self).__init__(*a, **kw)

        self.log("\nArguments passed to the spider are\n")
        self.log(str(json.dumps(kw, indent=4)))
        
        self._postinit_reqs = []
        self._init_complete = False
        self._init_started = False
        if 'project_name' in kw:
            self.project = kw['project_name']
        if 'campaign_name' in kw:
            self.campaign = kw['campaign_name']
        
        # max page starts is the number of starting points maximum for a given
        # query
        # max page cites is the number maximum of cited by publications which
        # will be retrieved for a single publication
        self.max_pages_starts = kw["max_pages_starts"] if 'max_pages' in kw else 100
        self.max_pages_cites = kw["max_pages_cites"] if 'max_pages' in kw else 100
    
    def make_requests_from_url(self, url):
        req = super(ScholarSpider, self).make_requests_from_url(url)
        if self._init_complete:
            return req
        self._postinit_reqs.append(req)
        if not self._init_started:
            self._init_started = True
            return self.init_request()
            
    def initialized(self, response=None):
        """This method must be set as the callback of your last initialization
        request. See self.init_request() docstring for more info.
        """
        self._init_complete = True
        reqs = self._postinit_reqs[:]
        del self._postinit_reqs
        return reqs
    #------------------------------------------

    # ---------------  LOGIN  -----------------------------------
    
    user_email =  'dialabal@gmail.com'
    user_passwd = 'jaunisse'
    
    def init_request(self): 
        """This function is called before crawling starts."""
        return self.login()

    def login(self):
        return self.initialized()
        return Request("https://www.google.com/accounts/ServiceLogin?hl=en", callback=self.fillForm)

    def fillForm(self, response) :
        headers={'User-agent' : self.USER_AGENT} 
        return FormRequest.from_response(response, formname="gaia_loginform", formdata={'Email' : self.user_email, "Passwd" : self.user_passwd}, headers=headers,callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """
        with open('sauvegarde.html','r+') as f:
            f.write(response.body)
        if "Dialab Ali" in response.body:
            self.log("\n\n\nSuccessfully logged in. Let's start crawling!\n\n\n")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.log("\n\n\nBad times :(\n\n\n")
            # Something went wrong, we couldn't log in, so nothing happens.
    # --------------------------------------------------    
    
    name = 'scholar_spider'
    allowed_domains = ['accounts.google.com','scholar.google.com']
   
    nr_results_per_page = "10"
    query              = qp("")     # with all of the words
    exact              = qp("")                             # with the exact phrase
    at_least_one       = qp("")                             # with at least one of the words
    without            = qp("")                             # without the words
    where_words_occurs = qp("any")                          # where my words occur	(any or title)
    author             = qp("")                             # Return articles written by
    publication        = qp("")                             # Return articles published in
    start_date         = qp("")                             # Return articles published between	this date ..
    end_date           = qp("")                             # ..and this date
    areas              = [                                 #Search only articles in the following subject areas
             #"bio",  #  Biology, Life Sciences, and Environmental Science	            
             #"med", #  Medicine, Pharmacology, and Veterinary Science       
             #"bus", #  Business, Administration, Finance, and Economics
             #"phy", #  Physics, Astronomy, and Planetary Science
             #"chm", #  Chemistry and Materials Science      
             #"soc", #  Social Sciences, Arts, and Humanities
             #"eng", #  Engineering, Computer Science, and Mathematics
             ]

    scholarUrl = ("http://scholar.google.com/scholar?\
                                 as_q="+ query +"& \
                                 num="+ nr_results_per_page +"& \
                                 as_epq="+ exact +"& \
                                 as_oq="+ at_least_one +"& \
                                 as_eq="+ without +"& \
                                 as_occt="+ where_words_occurs +"& \
                                 as_sauthors="+ author +"& \
                                 as_publication="+ publication +"& \
                                 as_ylo="+ start_date +"& \
                                 as_yhi="+ end_date +"& \
                                 btnG=Search+Scholar& \
                                 hl=en& \
                                 as_subj=" + str.join('&as_subj',areas) ).replace(" ","")
    start_urls = [scholarUrl]

    USER_AGENT = "Mozilla/5.0 (X11; Linux i686; rv:6.0.2) Gecko/20100101 Firefox/6.0.2"


    rules = (
        Rule(
            SgmlLinkExtractor(
                allow=r'.*cites=.*',
                restrict_xpaths="//div[@class ='gs_r']/font//a",
            ),  
            callback='parse_items', 
            follow=True),
        ScholarRule(
            SgmlLinkExtractor(
                allow=[],
                restrict_xpaths="//div[@class='n']/table//td[last()]",
            ),  
            callback='parse_items', 
            follow=True,
            dontIncreaseDepth=True),
    )
    
#     override default method to take account of the dontIncreaseDepth
#     TODO put that as a middleware
    def _requests_to_follow(self, response):
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [l for l in rule.link_extractor.extract_links(response) if l not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            seen = seen.union(links)
            for link in links:
                r = Request(url=link.url, callback=self._response_downloaded)
                r.meta.update(rule=n, link_text=link.text)
                if isinstance(rule, ScholarRule ) and rule.dontIncreaseDepth:
                        r.meta['dontIncrease'] = True
                yield rule.process_request(r)
   
    def parse_start_url(self, response):
        return self.parse_items(response)

    def parse_items(self, response):  
        url = urlparse(response.url)
        params = dict([part.split('=') for part in url[4].split('&')])

        self.log("heyehye")
        if self.max_pages_starts and params.get("start") > self.max_pages_starts and "cites" not in params:
            self.log("number of maximal start pages exceeded")
            self.log("%s %s %s %s" % (self.max_pages_starts, self.max_pages_cites, ", ".join(params), params.get("start")))
            return []
         
        if self.max_pages_cites and params.get("start") > self.max_pages_cites and "cites" in params:
            self.log("number of maximal cites documents exceeded")
            self.log("%s %s %s %s" % (self.max_pages_starts, self.max_pages_cites, ", ".join(params), params.get("start")))
            return []
        
        self.log("heyehye")
        hxs = HtmlXPathSelector(response)
        pr = ParsingRules()
        publications = hxs.select(pr.item_xpath)
        items_or_requests = []
        self.log("%s " % len(publications))
        for p in publications:
            item = ScholarItem()
        
            #TITLE
            if p.select(pr.title_xpath  + "//text()").extract():
                item['title'] = str.join("", p.select(pr.title_xpath  + "//text()").extract())
                item['depth_cb'] = response.meta['depth']
                
                #PUBLICATION TYPE (PDF,BOOK,HTML)
                if p.select(pr.type_pub_xpath+ "/text()").extract():
                    item['type_pub'] = ( p.select(pr.type_pub_xpath+ "/text()").extract()[0]
                                          .replace("[","")
                                          .replace("]","")
                                          .lower() )
                    item['title'] = item['title'].replace(item['type_pub'],"")
                
                if "[CITATION]" in item['title'] :
                    item["title"] = item['title'].replace("[CITATION]","")
                    item['type_pub'] = "citation"
                
                # LINK
                if p.select(pr.href_xpath).extract() :    
                    item['href'] = p.select(pr.href_xpath).extract()[0]
                
                first_link = p.select(pr.cited_by_xpath) # not necessarily Cited by link
                if  first_link :
                    if 'Cited by' in first_link.select("./text()").extract()[0] :
                        item['times_cited'] = int(re.search('Cited by ([0-9]*)',first_link.select("./text()").extract()[0]).group(1))
                        item['id'] = re.search('.*cites=([0-9]*)&.*',first_link.select("./@href").extract()[0]).group(1)
                if 'cites=' in response.url:
                        cites = re.search('.*cites=([0-9]*)&.*', response.url).group(1)
                        item['cites'] = cites
                item['scrapped_from'] = response.url
                
                infos = p.select(pr.info_xpath + "//text()").extract()[0]
                
                item['abstract'] = str.join("", p.select(pr.abstract_xpath +"//text()").extract() )
                item['abstract'] = item['abstract'].replace(infos,"")
                
                infos = infos.split(" - ")
                
                if len(infos)>1 :
                    item["authors"]=infos[0].split(", ")
                    infos=" ".join(infos[1:])
                    d=re.match("(.*?),? *(\d\d\d\d) *(.*)",infos)
                    if d : 
                        item['book_title'] = d.group(1)
                        item['date']       = d.group(2)
                        item['source']     = d.group(3) #source
                    else :                    
                        item['source']     = infos			
                else :
                    item['authors']=infos[0].split(", ")
                
                item['project']  = self.project
                item['campaign'] = self.campaign    
                
                
                follow_links = p.select("font//span[@class ='gs_fl']/a")
                related_url = ""
                for fl in follow_links:
                    if fl.select("text()").extract()[0] == u"Related articles" :
                        related_url = fl.select("@href").extract()[0]
                if related_url:    
                    item['bibtex_id'] = related_url.split(":")[1]
                
                if not self.bibtex:
                    items_or_requests.append(item)
                else:
                    base_url = get_base_url(response)
                    text_bibtex = p.select("font//span[@class ='gs_fl']/a[last()]/text()").extract()
                    follow_links = p.select("font//span[@class ='gs_fl']/a")
                    related_url = ""
                    for fl in follow_links:
                        if fl.select("text()").extract()[0] == u"Related articles" :
                            related_url = fl.select("@href").extract()[0]
                    
                    bibtex_id = related_url.split(":")[1]
                    url_bibtex = "http://scholar.google.com/scholar.bib?q=info:" + bibtex_id + ":scholar.google.com/&output=citation&hl=en&as_sdt=0,5&ct=citation&cd=0"
                    request = Request(url_bibtex,callback=self.parse_bibtex)
                    request.meta['item'] = item
                    items_or_requests.append(request)            
        return items_or_requests
        
    def parse_bibtex(self, response): 
         item = response.meta['item']
         item['bibtex'] = response.body
         return item 
        
        

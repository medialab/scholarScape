import json
import os.path
import pprint

class LazyJsonObject(object):
    def __init__(self, filename):
        self.filename = filename
        self.json = None

    def _compute_json(self):
        with open(self.filename, 'r') as config_file:
            self.json = json.load(config_file)

    def __getattr__(self, attrname):
        if not self.json:
            self._compute_json()
        return getattr(self.json, attrname)

    def __getitem__(self, itemname):
        if not self.json:
            self._compute_json()
        return self.json[itemname]

class Config(object):
    def __init__(self):
        self.config = LazyJsonObject("config.json")
        self.users = LazyJsonObject("users.json")

        self.root_dir = os.path.abspath(os.path.dirname(__file__))
        self.pp = pprint.PrettyPrinter(indent=4)
        self.web_client_dir = 'web_client'

    @property
    def data_dir(self):
        return os.path.join(self.root_dir, self.config['data_dir'])

def scholarize(query="", nr_results_per_page="100", exact="", at_least_one="",
               without="", where_words_occurs="", author="", publication="",
               start_date="", end_date="", areas = [] ) :
    """
    Advanced research in Google Scholar to URL
    areas may contain "bio"  Biology, Life Sciences, and Environmental Science	            
                      "med", Medicine, Pharmacology, and Veterinary Science       
                      "bus", Business, Administration, Finance, and Economics
                      "phy", Physics, Astronomy, and Planetary Science
                      "chm", Chemistry and Materials Science      
                      "soc", Social Sciences, Arts, and Humanities
                      "eng", Engineering, Computer Science, and Mathematics
    """
    return ("http://scholar.google.com/scholar?\
             as_q="+ qp(query) +"&num="+ nr_results_per_page +"& \
             as_epq="+ qp(exact) +"&as_oq="+ qp(at_least_one) +"& \
             as_eq="+ qp(without) +"&as_occt="+ qp(where_words_occurs) +"& \
             as_sauthors="+ qp(author) +"&as_publication="+ qp(publication) +"& \
             as_ylo="+ start_date +"&as_yhi="+ end_date +"& \
             btnG=Search+Scholar&hl=en& \
             as_subj=" + str.join('&as_subj',areas) ).replace(" ","")

config = Config()

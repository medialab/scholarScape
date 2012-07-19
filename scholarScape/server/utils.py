import json
import os.path
import pprint

print 'Loading users file...'
try :
    with open('users.json', 'r') as users_file:
        users = json.load(users_file)
except IOError as e:
    print 'Could not open users file', e
    exit()
except ValueError as e:
    print 'Users file is not valid JSON', e
    exit()

# Read config file and fill in mongo and scrapyd config files with custom values
# try to connect to DB, send egg to scrapyd server
# then start twisted server
print 'Loading config file...'
try :
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except IOError as e:
    print 'Could not open config file'
    print e
    exit()    
except ValueError as e:
    print 'Config file is not valid JSON', e
    exit()

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

root_dir = os.path.abspath(os.path.dirname(__file__))
pp = pprint.PrettyPrinter(indent=4)
web_client_dir = 'web_client'
data_dir = os.path.join(root_dir, config['data_dir'])

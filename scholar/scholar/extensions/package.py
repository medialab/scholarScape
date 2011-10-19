from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scholar.graph import create_graph_from_db
import shlex, subprocess
import zipfile

class Create_package(object):

    def __init__(self):
        dispatcher.connect(self.engine_started, signal=signals.engine_started)
        dispatcher.connect(self.engine_stopped, signal=signals.engine_stopped)

    def engine_started(self):
        print "Starting crawling..."

    def engine_stopped(self):
        print "Creating graph...."
        create_graph_from_db('localhost', 27017, 'scholarScape', 'publications', 'graph.gexf')
        print "Dumping database..."
        export_command = 'mongoexport -h "localhost" -d "scholarScape" -c "publications" -o dump.json'
        args = shlex.split(export_command)
        p = subprocess.call(args)
        print "Done."
        print "Zipping it all..."
        zip_file = zipfile.ZipFile('archive.zip','w',compression=zipfile.ZIP_DEFLATED)
        zip_file.write('dump.json')
        zip_file.write('graph.gexf')
        zip_file.close() 
        print "Done."
        

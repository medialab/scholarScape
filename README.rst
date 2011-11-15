============
scholarScape
============

Description
-----------

This program allows one to automatically scrape publications from Google Scholar,
starting from words to search ("Bruno Latour", "We have never been modern") and
following the "Cited by" links. You can then export the graph of the publications.
 
User Functions
--------------

The main interface is for now a WebService

Data Structure
--------------

Our data structure enable the user to separate its different projects, to 
add new scraped data to one projects, to pause or unpause a crawl campaign::

    Project "Bruno Latour"
       |-Campaign 1 : start_urls=['authors:Bruno Latour',deep=3]
           |- publication 1
           |- publication 2
           |- publication 3 #superPublication made from 5 and 6
           |- publication 4
           |- publication 5 : parent=3
           |- publication 6 : parent=3
           ...
       |-Campaign 2 : start_urls['authors:Bruno Latour',deep=4]
           |- publication 151
           |- publication 152
           |- publication 153
           |- publication 154
    AnotherProject
       |-Campaign 4
           ...
       |- Campaign 5
       ...
        
    
Command Line
------------

scholarScrape should allow users to use this commands. It will be added soon.

*scholarScrape startproject project_name*
    This command should add a new collection named project_name in the database.

*scholarScrape startcampaign  [(-f file | -s start_url)[-d depth][-c nr_camp]]*
    This command should add a new campaign object in the database and start
    the crawler with the parameter campaign_id and also start_urls
    
    -f start_file   File with a list of start urls separated by break
    -s start_url    URL of a google scholar result page
    -d depth        Cited by depth
    -c nr_camp      From campaign, nr_camp is the campaign id as seen with scholarScrape -l
                    scholarScrape should take the deepmost publications as starting points
                    therefore it should set the DEPTH_LIMIT setting to depth-previous_max_depth
                    
                    if depth <= previous_depth
                        it doesn't mean nothing, user should start a new project
                        error message
    -g gexf_file    Output GEXF file (if no name is specified default is graph.gexf)                      
    -j json_file    Output JSON file (if no name is specified default is database.json)
    -z zip_file     Output ZIP file (if no name is specified default is all.zip)
    
*scholarScrape export -p project\* -c campaign [-z zipfile | -j jsonfile | -g gexf_file]*
    The user can export the database to a json file, export a graph from the crawl,
    from an entire project or from a particular campaign.
    
    
*scholarScrape config*  
    Specify host, port, database
    
*scholarScrape list*  
    Lists all the project and their campaigns
    (list all the database and find all campaigns object)   

                      


    
    
    
        

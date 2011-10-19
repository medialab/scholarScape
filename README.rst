============
scholarScape
============

Description
-----------

This command line programm allow users to crawl and scrape Google Scholar. One
would start a new crawl campain from starting points or from another campain in
order to deepen the crawl.

User Functions
--------------

1.  Start project
2.  In a particular project, start campaign from url(s) 
3.  In a particular project, start campaign from another campain to deepen the crawl
4.  Export data from a particular campain 
        * JSON
        * GEXF
5. List projects and number of campaigns
6. See states of campaigns [alive,paused,finished]

Specifications
--------------

1.  Best data quality (we don't want to lose data)
        detect duplicates, mark them as duplicates of another publication but
        don't remove them

Data Structure
--------------

>>> Project "Bruno Latour"
>>>    |-Campaign 1 : start_urls=['authors:Bruno Latour',deep=3]
>>>        |- publication 1
>>>        |- publication 2
>>>        |- publication 3 #superPublication made from 5 and 6
>>>        |- publication 4
>>>        |- publication 5 : parent=3
>>>        |- publication 6 : parent=3
>>>        ...
>>>    |-Campaign 2 : start_urls['authors:Bruno Latour',deep=4]
>>>        |- publication 151
>>>        |- publication 152
>>>        |- publication 153
>>>        |- publication 154
>>> AnotherProject
>>>    |-Campaign 4
>>>        ...
>>>    |- Campaign 5
>>>    ...
    
    
Command Line
------------

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

*scholarScrape config*
    
    Specify host, port, database
    
*scholarScrape list*
    
    Lists all the project and their campaigns
    (list all the database and find all campaigns object)   

                      


    
    
    
        

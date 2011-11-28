============
scholarScape
============

Description
-----------

This program allows one to automatically scrape publications from Google Scholar,
starting from words to search ("Bruno Latour", "We have never been modern") and
following the "Cited by" links. You can then export the graph of the publications.
 
Dependencies
------------
- Scrapy
- Pymustache
- Networkx
- MongoDB
- Pymongo

Installation
------------

For the moment, a package has not been crafted, you'll have to manually install
the dependencies and having a scrapyd and mongodb server up and running (you can do it
on the same machine).
Next you will have to download the sources and modify the config.json according
to the addresses of your servers.
The final step is to launch the scholarScape server with :
twistd -noy scholarScape.tac
If there is a problem with your configuration, it will try to tell you what it is.

Usage
-----
After the installation you'll want to type in localhost:portyouhavedefine in your
browser and you will find the WebUI of scholarScape. You can then follow the tutorial from
there.

************
scholarScape
************

Description
===========

This program allows one to automatically scrape publications from Google Scholar,
starting from words to search ("osteoporosis", "we have never been modern") and
following the "Cited by" links. You can then export the graph of the publications.
 
Dependencies
============
- MongoDB
- ``scrapy``
- ``networkx``
- ``pystache``
- ``pymongo``
- ``levensthein``

How to install scholarScape
===========================

The first two steps (starred one) are designed for a Debian based distribution as they involve installing packages (MongoDB and Scrapy) with apt-get. However MongoDB has a package in other distributions and you can install Scrapy from the sources. See in the "Read More" section the links to the install pages of these softwares.
 
The last steps should not be specific to any version of Linux.

Tell me if you have or have resolved any problem and I will add your solution here.

\*Add some repositories first
-----------------------------

Add these lines to sources.list, it will add the repositories for *MongoDB Ubuntu* package and for *Scrapyd* package::

    deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen
    deb http://archive.scrapy.org/ubuntu DISTRO main1. 

and after ::

    sudo apt-get update

\*Install them all
------------------

You can now install all the dependencies scholarScape relies upon. It is recommended to install ``virtualenv`` to set up a virtual environment in order not to disturb other programs. ::

    sudo apt-get install python-dev bzr mongodb-10gen scrapyd-0.15 git
    easy_install virtualenv
    easy_install scrapy 
    easy_install pymongo 
    easy_install pystache

    bzr branch lp:txjsonrpc
    cd txjsonrpc
    sudo python setup.py install

    curl http://pypi.python.org/packages/source/n/networkx/networkx-1.6.tar.gz#md5=a5e62b841b30118574b57d0eaf1917ca | tar zx
    cd network-1.6
    sudo python setup.py install
    
Fork some code
--------------

The latest version of scholarScape is always available at http://github.com/medialab/scholarScape/. To clone the repository ::

    git clone https://github.com/medialab/scholarScape.git

Setup Mongodb
-------------
Connect to MongoDB and add the user configured in ``config.json``, in the MongoDB part (user : "scholarScape", password : "diabal" by default) . ::
 
    ./mongo
    > use scholarScape
    > db.addUser("scholarScape", "diabal")

Setup a few directories
-----------------------
You'll want to create the directories where scholarScape will export the graphs. The adress can be relative
(to the directory where scholarScape.tac is) or absolute. By default, the export directory
is data and graph files are exported under gexf/ so you'll do : ::

    mkdir data data/gexf data/zip data/json

Launch the server
-----------------
Now you can launch the scholarScape server. Go to the source directory and execute this command ::

    cd scholarScape
    twistd -ny scholarScape.tac

You can omit the parameter "n" if you want to start the server as a daemon.

Usage
=====
After the installation you'll want to type in ``localhost:TWISTED_PORT``\* in your
favorite browser and you will find the scholarScape's WebUI. You can then follow the tutorial from
there.
* TWISTED_PORT is configured in config.json


Read also
=========
Mongodb
-------

http://www.mongodb.org/display/DOCS/Ubuntu+and+Debian+packages

Scrapyd
-------

http://readthedocs.org/docs/scrapy/en/latest/topics/scrapyd.html


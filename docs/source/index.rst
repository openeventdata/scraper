.. OEDA Scraper documentation master file, created by
   sphinx-quickstart on Mon Apr 14 15:59:00 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to OEDA Scraper's documentation!
========================================

This site hosts the documentation for the web scraper used by the `Open Event
Data Alliance <http://openeventdata.org/>`_. The scraper functions by
specifying a `whitelist <https://github.com/openeventdata/scraper/blob/master/whitelist_urls.csv>`_ of
trusted RSS feed URLs and scraping the articles from these RSS feeds. The
scraper makes use of `goose <https://github.com/grangier/python-goose>`_ in
order to scrape arbitrary pages, and stores the output content in a `MongoDB
<http://www.mongodb.org/>`_ instance.

Installation
------------

You should probably create a `virtual environment
<http://www.virtualenv.org/en/latest/>`_, but in any event doing ``pip install
-r requirements.txt`` should do the trick. You might (probably will) have to
specify something along the lines of ``--allow-all-external pattern
--allow-unverified pattern`` for the pattern library since it gets downloaded
from its homepage. 

The scraper requires  a running MongoDB instance to dump the scraped stories
into.  Make sure you have MongoDB `installed
<http://docs.mongodb.org/manual/installation/>`_ and type ``mongod`` at the
terminal to begin the instance if your install method didn't set up the MongoDB
process to run automatically. MongoDB doesn't require you to prepare the
collection or database ahead of time, so when you run the program it should
automatically create a database called ``event_scrape`` with a collection
called ``stories``. Once you've run ``python scraper.py``, you can verify that
the stories are in the Mongo database by opening a new terminal window and
typing `mongo`. 
 
To interface with Mongo, enter ``mongo`` at the command line. From inside
Mongo, type ``show dbs`` to verify that there's a database called
``event_scrape``.  Enter the database with ``use event_scrape`` and type ``show
collections`` to make sure there's a ``stories`` collection.
``db.stories.find()`` will show you the first 20 entries.

Running
-------

After everything is installed, it's as simple as ``python scraper.py``. That is
assuming, of course, that you wish to use the configuration seen in the
``default_config.ini`` file. If not, just modify that. For the source type
section of the config, the three types of sources are ``wire``, ``international``,
and ``local``. It is possible to specify any combination of those source types,
with the source types separated by commas in the config file. For more
information on the source types, see the `Contributing <contributing.html>`_
page.



Contents:

.. toctree::
   :maxdepth: 2

   contributing
   scraper



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


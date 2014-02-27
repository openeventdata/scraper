scraper
=======

Scrapes sites. Gets news. Eventually events.


###Installation

You should probably create a [virtual environment](http://www.virtualenv.org/en/latest/), but
in any event doing `pip install -r requirements.txt` should do the trick. You
might (probably will) have to specify something along the lines of 
`--allow-all-external pattern --allow-unverified pattern` for the pattern
library since it gets downloaded from its homepage. 

The scraper requires  a running MongoDB instance to dump the scraped stories into. 
Make sure you have MongoDB [installed](http://docs.mongodb.org/manual/installation/) 
and type `mongod` at the terminal to begin the instance. MongoDB doesn't require you to prepare
the collection or database ahead of time, so when you run the program it should automatically
create a database called `event_scrape` with a collection called `stories`. Once you've run  `python scraper.py`, 
you can verify that the stories are in the Mongo database by opening a new terminal window and typing `mongo`. NOTE: 
the scraper runs once every hour, meaning that stories may not immediately appear in your database. To force immediate scraping,
 comment out the scheduling part at the end of `scraper.py` and uncomment `call_scrape_func`. 
 
To interface with Mongo, enter `mongo` at the command line. From inside Mongo, type `show dbs` to verify that there's a database called `event_scrape`. 
Enter the database with `use event_scrape` and type `show collections` to make sure there's a `stories` collection. 
 `db.stories.find()` will show you the first 20 entries.

###Running

After everything is installed, it's as simple as `python scraper.py`. That is
assuming, of course, that you wish to use the configuration seen in the
`default_config.ini` file. If not, just modify that. It's only set up to
specify the path to the file of URLs and the MongoDB collection that you want
to used.

The program will run once an hour and will pull from the RSS feeds specified in
the URL file. 

###Contributing

More RSS feeds are always useful. If there's something specific you want to
see, just add it in and open a pull request. The only requirement is that each
line contains one entry with the first column as a unique ID and the second the
URL to the raw XML feed.

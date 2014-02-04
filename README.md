scraper
=======

Scrapes sites. Gets news. Eventually events.


###Installation

You should probably create a [virtual environment](http://www.virtualenv.org/en/latest/), but
in any event doing `pip install -r requirements.txt` should do the trick. You
might (probably will) have to specify something along the lines of 
`--allow-all-external pattern --allow-unverified pattern` for the pattern
library since it gets downloaded from its homepage. 

Oh yea. It also requires a running MongoDB instance. See
[here](http://docs.mongodb.org/manual/installation/) for more on how to get
that running.

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

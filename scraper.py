import os
import glob
import time
import logging
import pattern.web
import pages_scrape
import mongo_connection
from goose import Goose
from pymongo import MongoClient
from ConfigParser import ConfigParser
from apscheduler.scheduler import Scheduler


def scrape_func(address, website, COLL):
    """
    Function to scrape various RSS feeds. Uses the 'keep' and 'ignore'
    iterables to define which words should be used in the text search.

    Parameters
    ------
    address : String
                Address for the RSS feed to scrape.

    name : String
            Nickname for the RSS feed being scraped.

    COLL : String
            Collection within MongoDB that holds the scraped data.
    """
    #Setup the database
    connection = MongoClient()
    db = connection.event_scrape
    collection = db[COLL]

    #Scrape the RSS feed
    try:
        results = pattern.web.Newsfeed().search(address, count=100,
                                                cached=False)
        logger.info('There are {} results from {}'.format(len(results),
                                                          website))
    except Exception, e:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Problem fetching RSS feed for {}. {}'.format(address,
                                                                     e))
        results = None
    #Pursue each link in the feed
    if results:
        goose_extractor = Goose({'use_meta_language': False,
                                 'target_language': 'en'})
        for result in results:
            if website == 'xinhua':
                page_url = result.url.replace('"', '')
                page_url = page_url.encode('ascii')
            elif website == 'upi':
                page_url = result.url.encode('ascii')
            else:
                page_url = result.url

            try:
                text, meta = pages_scrape.scrape(page_url, goose_extractor)
                text = text.encode('utf-8')
            except TypeError:
                logger.warning('Problem obtaining text from URL: {}'.format(page_url))
                text = ''

            if text:
                if website == 'bbc':
                    text = text.replace("This page is best viewed in an up-to-date web browser with style sheets (CSS) enabled. While you will be able to view the content of this page in your current browser, you will not be able to get the full visual experience. Please consider upgrading your browser software or enabling style sheets (CSS) if you are able to do so.", '')
                elif website == 'upi':
                    text = text.replace("Since 1907, United Press International (UPI) has been a leading provider of critical information to media outlets, businesses, governments and researchers worldwide. UPI is a global operation with offices in Beirut, Hong Kong, London, Santiago, Seoul and Tokyo. Our headquarters is located in downtown Washington, DC, surrounded by major international policy-making governmental and non-governmental organizations. UPI licenses content directly to print outlets, online media and institutions of all types. In addition, UPI's distribution partners provide our content to thousands of businesses, policy groups and academic institutions worldwide. Our audience consists of millions of decision-makers who depend on UPI's insightful and analytical stories to make better business or policy decisions. In the year of our 107th anniversary, our company strives to continue being a leading and trusted source for news, analysis and insight for readers around the world.", '')

                entry_id = mongo_connection.add_entry(collection, text,
                                                      result.title, result.url,
                                                      result.date, website)
                if entry_id:
                    logger.info('Added entry from {} with id {}'.format(result.url,
                                                                        entry_id))
                else:
                    logger.info('Result from {} already in database'.format(result.url,
                                                                            entry_id))
    logger.info('Scrape of {} finished'.format(website))


def call_scrape_func(siteList, db_collection):
    """
    Helper function to iterate over a list of RSS feeds and scrape each.

    Parameters
    ----------

    siteList : dictionary
                Dictionary of sites, with a nickname as the key and RSS URL
                as the value.
    """
    for website in siteList:
        scrape_func(siteList[website], website, db_collection)
    logger.info('Completed full scrape.')


def parse_config():
    """Function to parse the config file."""
    config_file = glob.glob('config.ini')
    parser = ConfigParser()
    if config_file:
        logger.info('Found a config file in working directory')
        parser.read(config_file)
        try:
            collection = parser.get('Database', 'collection_list')
            whitelist = parser.get('URLS', 'file')
            return collection, whitelist
        except Exception, e:
            print 'There was an error. Check the log file for more information.'
            logger.warning('Problem parsing config file. {}'.format(e))
    else:
        cwd = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(cwd, 'default_config.ini')
        parser.read(config_file)
        logger.info('No config found. Using default.')
        try:
            collection = parser.get('Database', 'collection_list')
            whitelist = parser.get('URLS', 'file')
            return collection, whitelist
        except Exception, e:
            print 'There was an error. Check the log file for more information.'
            logger.warning('Problem parsing config file. {}'.format(e))


if __name__ == '__main__':
    #Setup the logging
    logger = logging.getLogger('scraper_log')
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler('scraping_log.log', 'w')
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.info('Running in scheduled hourly mode')

    print 'Running. See log file for further information.'
    #Get the info from the config
    db_collection, whitelist_file = parse_config()

    #Convert from CSV of URLs to a dictionary
    try:
        url_whitelist = open(whitelist_file, 'r').readlines()
        url_whitelist = [line.split(',') for line in url_whitelist if line]
        to_scrape = {listing[0]: listing[1] for listing in url_whitelist}
    except IOError:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Could not open URL whitelist file.')

    #Line to aid in debugging
    #call_scrape_func(to_scrape, db_collection)

    #Run the `scrape_func` once each hour
    sched = Scheduler()
    sched.add_interval_job(call_scrape_func, args=[to_scrape, db_collection],
                           hours=1)
    sched.start()
    while True:
        time.sleep(10)
    sched.shutdown()

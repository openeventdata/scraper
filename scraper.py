import os
import re
import glob
import logging
import pattern.web
import pages_scrape
import mongo_connection
from goose import Goose
from pymongo import MongoClient
from ConfigParser import ConfigParser
from multiprocessing import Pool


def scrape_func(website, address, COLL):
    """
    Function to scrape various RSS feeds.

    Parameters
    ------
    website: String
            Nickname for the RSS feed being scraped.

    address : String
                Address for the RSS feed to scrape.

    COLL : String
            Collection within MongoDB that holds the scraped data.
    """
    #Setup the database
    connection = MongoClient()
    db = connection.event_scrape
    collection = db[COLL]

    #Scrape the RSS feed
    results = _get_rss(address, website)

    #Pursue each link in the feed
    if results:
        _parse_results(results, website, collection)

    logger.info('Scrape of {} finished'.format(website))


def _get_rss(address, website):
    """
    Private function to parse an RSS feed and extract the relevant links.

    Parameters
    ------
    address: String.
                Address for the RSS feed to scrape.

    website: String.
                Nickname for the RSS feed being scraped.

    Returns
    -------

    results : pattern.web.Results.
                Object containing data on the parsed RSS feed. Each item
                represents a unique entry in the RSS feed and contains relevant
                information such as the URL and title of the story.

    """
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

    return results


def _parse_results(rss_results, website, db_collection):
    """
    Private function to parse the links drawn from an RSS feed.

    Parameters
    ------
    rss_results: pattern.web.Results.
                    Object containing data on the parsed RSS feed. Each item
                    represents a unique entry in the RSS feed and contains
                    relevant information such as the URL and title of the
                    story.

    website: String.
                Nickname for the RSS feed being scraped.

    db_collection: pymongo Collection.
                        Collection within MongoDB that in which results are
                        stored.
    """
    goose_extractor = Goose({'use_meta_language': False,
                             'target_language': 'en'})

    for result in rss_results:
        if website == 'xinhua':
            page_url = result.url.replace('"', '')
            page_url = page_url.encode('ascii')
        elif website == 'upi':
            page_url = result.url.encode('ascii')
        else:
            page_url = result.url.encode('utf-8')

        try:
            text, meta = pages_scrape.scrape(page_url, goose_extractor)
            text = text.encode('utf-8')
        except TypeError:
            logger.warning('Problem obtaining text from URL: {}'.format(page_url))
            text = ''

        if text:
            cleaned_text = _clean_text(text, website)

            entry_id = mongo_connection.add_entry(db_collection, cleaned_text,
                                                  result.title, result.url,
                                                  result.date, website)
            if entry_id:
                try:
                    logger.info('Added entry from {} with id {}'.format(page_url,
                                                                        entry_id))
                except UnicodeDecodeError:
                    logger.info('Added entry from {}. Unicode error for id'.format(result.url))
            else:
                logger.info('Result from {} already in database'.format(page_url))


def _clean_text(text, website):
    """
    Private function to clean some of the cruft from the content pulled from
    various sources.

    Parameters
    --------

    text: String.
            Dirty text.

    website: String.
                Nickname for the RSS feed being scraped.

    Returns
    ------

    text: String.
            Less dirty text.
    """
    site_list = ['menafn_algeria', 'menafn_bahrain', 'menafn_egypt',
                 'menafn_iraq', 'menafn_jordan', 'menafn_kuwait',
                 'menafn_lebanon', 'menafn_morocco', 'menafn_oman',
                 'menafn_palestine', 'menafn_qatar', 'menafn_saudi',
                 'menafn_syria', 'menafn_tunisia', 'menafn_turkey',
                 'menafn_uae', 'menafn_yemen']

    if website == 'bbc':
        text = text.replace("This page is best viewed in an up-to-date web browser with style sheets (CSS) enabled. While you will be able to view the content of this page in your current browser, you will not be able to get the full visual experience. Please consider upgrading your browser software or enabling style sheets (CSS) if you are able to do so.", '')
    if website == 'almonitor':
        text = re.sub("^.*?\(photo by REUTERS.*?\)", "", text)
    if website in site_list:
        text = re.sub("^\(.*?MENAFN.*?\)", "", text)
    elif website == 'upi':
        text = text.replace("Since 1907, United Press International (UPI) has been a leading provider of critical information to media outlets, businesses, governments and researchers worldwide. UPI is a global operation with offices in Beirut, Hong Kong, London, Santiago, Seoul and Tokyo. Our headquarters is located in downtown Washington, DC, surrounded by major international policy-making governmental and non-governmental organizations. UPI licenses content directly to print outlets, online media and institutions of all types. In addition, UPI's distribution partners provide our content to thousands of businesses, policy groups and academic institutions worldwide. Our audience consists of millions of decision-makers who depend on UPI's insightful and analytical stories to make better business or policy decisions. In the year of our 107th anniversary, our company strives to continue being a leading and trusted source for news, analysis and insight for readers around the world.", '')

    text = text.replace('\n', '')

    return text


def call_scrape_func(siteList, db_collection, pool_size):
    """
    Helper function to iterate over a list of RSS feeds and scrape each.

    Parameters
    ----------

    siteList: dictionary
                Dictionary of sites, with a nickname as the key and RSS URL
                as the value.

    db_collection : collection
                    Mongo collection to put stories

    pool_size : int
                Number of processes to distribute work
    """
    pool = Pool(pool_size)
    results = [pool.apply_async(scrape_func, (address, website, db_collection))
               for address, website in siteList.iteritems()]
    timeout = [r.get(9999999) for r in results]
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
            pool_size = int(parser.get('Processes', 'pool_size'))
            return collection, whitelist, pool_size
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
            pool_size = int(parser.get('Processes', 'pool_size'))
            return collection, whitelist, pool_size
        except Exception, e:
            print 'There was an error. Check the log file for more information.'
            logger.warning('Problem parsing config file. {}'.format(e))


if __name__ == '__main__':
    #Setup the logging
    logger = logging.getLogger('scraper_log')
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler('scraping_log.log', 'a')
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.info('Running in scheduled hourly mode')

    print 'Running. See log file for further information.'
    #Get the info from the config
    db_collection, whitelist_file, pool_size = parse_config()

    #Convert from CSV of URLs to a dictionary
    try:
        url_whitelist = open(whitelist_file, 'r').readlines()
        url_whitelist = [line.split(',') for line in url_whitelist if line]
        to_scrape = {listing[0]: listing[1] for listing in url_whitelist}
    except IOError:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Could not open URL whitelist file.')

    call_scrape_func(to_scrape, db_collection, pool_size)

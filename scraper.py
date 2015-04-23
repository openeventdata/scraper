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


def scrape_func(website, lang, address, COLL, db_auth, db_user, db_pass, db_host=None):
    """
    Function to scrape various RSS feeds.

    Parameters
    ----------

    website: String
            Nickname for the RSS feed being scraped.

    address: String
                Address for the RSS feed to scrape.

    COLL: String
            Collection within MongoDB that holds the scraped data.

    db_auth: String.
                MongoDB database that should be used for user authentication.

    db_user: String.
                Username for MongoDB authentication.

    db_user: String.
                Password for MongoDB authentication.
    """
    # Setup the database
    connection = MongoClient(host=db_host)
    if db_auth:
        connection[db_auth].authenticate(db_user, db_pass)
    db = connection.event_scrape
    collection = db[COLL]

    # Scrape the RSS feed
    results = get_rss(address, website)

    # Pursue each link in the feed
    if results:
        parse_results(results, website, lang, collection)

    logger.info('Scrape of {} finished'.format(website))


def get_rss(address, website):
    """
    Function to parse an RSS feed and extract the relevant links.

    Parameters
    ----------

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
                                                cached=False, timeout=30)
        logger.debug('There are {} results from {}'.format(len(results),
                                                           website))
    except Exception, e:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Problem fetching RSS feed for {}. {}'.format(address,
                                                                     e))
        results = None

    return results


def parse_results(rss_results, website, lang, db_collection):
    """
    Function to parse the links drawn from an RSS feed.

    Parameters
    ----------

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
    if lang == 'english':
        goose_extractor = Goose({'use_meta_language': False,
                                 'target_language': 'en',
                                 'enable_image_fetching': False})
    elif lang == 'arabic':
        from goose.text import StopWordsArabic

        goose_extractor = Goose({'stopwords_class': StopWordsArabic,
                                 'enable_image_fetching': False})
    else:
        print(lang)

    for result in rss_results:

        page_url = _convert_url(result.url, website)

        in_database = _check_mongo(page_url, db_collection)

        if not in_database:
            try:
                text, meta = pages_scrape.scrape(page_url, goose_extractor)
                text = text.encode('utf-8')
            except TypeError:
                logger.warning('Problem obtaining text from URL: {}'.format(page_url))
                text = ''
        else:
            logger.debug('Result from {} already in database'.format(page_url))
            text = ''

        if text:
            cleaned_text = _clean_text(text, website)

            entry_id = mongo_connection.add_entry(db_collection, cleaned_text,
                                                  result.title, result.url,
                                                  result.date, website, lang)
            if entry_id:
                try:
                    logger.info('Added entry from {} with id {}'.format(page_url,
                                                                        entry_id))
                except UnicodeDecodeError:
                    logger.info('Added entry from {}. Unicode error for id'.format(result.url))


def _check_mongo(url, db_collection):
    """
    Private function to check if a URL appears in the database.

    Parameters
    ----------

    url: String.
            URL for the news stories to be scraped.

    db_collection: pymongo Collection.
                        Collection within MongoDB that in which results are
                        stored.

    Returns
    -------

    found: Boolean.
            Indicates whether or not a URL was found in the database.
    """

    if db_collection.find_one({"url": url}):
        found = True
    else:
        found = False

    return found


def _convert_url(url, website):
    """
    Private function to clean a given page URL.

    Parameters
    ----------

    url: String.
            URL for the news stories to be scraped.

    website: String.
                Nickname for the RSS feed being scraped.

    Returns
    -------

    page_url: String.
                Cleaned and unicode converted page URL.
    """

    if website == 'xinhua':
        page_url = url.replace('"', '')
        page_url = page_url.encode('ascii')
    elif website == 'upi':
        page_url = url.encode('ascii')
    elif website == 'zaman':
        # Find the weird thing. They tend to be ap or reuters, but generalized
        # just in case
        com = url.find('.com')
        slash = url[com + 4:].find('/')
        replaced_url = url.replace(url[com + 4:com + slash + 4], '')
        split = replaced_url.split('/')
        # This is nasty and hackish but it gets the jobs done.
        page_url = '/'.join(['/'.join(split[0:3]), 'world_' + split[-1]])
    else:
        page_url = url.encode('utf-8')

    return page_url


def _clean_text(text, website):
    """
    Private function to clean some of the cruft from the content pulled from
    various sources.

    Parameters
    ----------

    text: String.
            Dirty text.

    website: String.
                Nickname for the RSS feed being scraped.

    Returns
    -------

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
        text = text.replace(
            "This page is best viewed in an up-to-date web browser with style sheets (CSS) "
            "enabled. While you will be able to view the content of this page in your current "
            "browser, you will not be able to get the full visual experience. Please consider "
            "upgrading your browser software or enabling style sheets (CSS) if you are able to do "
            "so.",
            '')
    if website == 'almonitor':
        text = re.sub("^.*?\(photo by REUTERS.*?\)", "", text)
    if website in site_list:
        text = re.sub("^\(.*?MENAFN.*?\)", "", text)
    elif website == 'upi':
        text = text.replace(
            "Since 1907, United Press International (UPI) has been a leading provider of critical "
            "information to media outlets, businesses, governments and researchers worldwide. UPI "
            "is a global operation with offices in Beirut, Hong Kong, London, Santiago, Seoul and "
            "Tokyo. Our headquarters is located in downtown Washington, DC, surrounded by major "
            "international policy-making governmental and non-governmental organizations. UPI "
            "licenses content directly to print outlets, online media and institutions of all "
            "types. In addition, UPI's distribution partners provide our content to thousands of "
            "businesses, policy groups and academic institutions worldwide. Our audience consists "
            "of millions of decision-makers who depend on UPI's insightful and analytical stories "
            "to make better business or policy decisions. In the year of our 107th anniversary, "
            "our company strives to continue being a leading and trusted source for news, "
            "analysis and insight for readers around the world.",
            '')

    text = text.replace('\n', ' ')

    return text


def call_scrape_func(siteList, db_collection, pool_size, db_auth, db_user,
                     db_pass, db_host=None):
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
    results = [pool.apply_async(scrape_func, (address, lang, website,
                                              db_collection, db_auth, db_user,
                                              db_pass, db_host))
               for address, (website, lang) in siteList.iteritems()]
    [r.get(9999999) for r in results]
    pool.terminate()
    logger.info('Completed full scrape.')


def _parse_config(parser):
    try:
        if 'Auth' in parser.sections():
            auth_db = parser.get('Auth', 'auth_db')
            auth_user = parser.get('Auth', 'auth_user')
            auth_pass = parser.get('Auth', 'auth_pass')
            db_host = parser.get('Auth', 'db_host')
        else:
            # Try env vars too
            auth_db = os.getenv('MONGO_AUTH_DB') or ''
            auth_user = os.getenv('MONGO_AUTH_USER') or ''
            auth_pass = os.getenv('MONGO_AUTH_PASS') or ''
            db_host = os.getenv('MONGO_HOST') or ''

        log_dir = parser.get('Logging', 'log_file')
        log_level = parser.get('Logging', 'level')
        collection = parser.get('Database', 'collection_list')
        whitelist = parser.get('URLS', 'file')
        sources = parser.get('URLS', 'sources').split(',')
        pool_size = int(parser.get('Processes', 'pool_size'))
        return collection, whitelist, sources, pool_size, log_dir, log_level, auth_db, auth_user, \
               auth_pass, db_host
    except Exception, e:
        print 'Problem parsing config file. {}'.format(e)


def parse_config():
    """Function to parse the config file."""
    config_file = glob.glob('config.ini')
    parser = ConfigParser()
    if config_file:
        parser.read(config_file)
    else:
        cwd = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(cwd, 'default_config.ini')
        parser.read(config_file)
    return _parse_config(parser)


if __name__ == '__main__':
    # Get the info from the config
    db_collection, whitelist_file, sources, pool_size, log_dir, log_level, auth_db, auth_user, \
    auth_pass, db_host = parse_config()
    # Setup the logging
    logger = logging.getLogger('scraper_log')
    if log_level == 'info':
        logger.setLevel(logging.INFO)
    elif log_level == 'warning':
        logger.setLevel(logging.WARNING)
    elif log_level == 'debug':
        logger.setLevel(logging.DEBUG)

    if log_dir:
        fh = logging.FileHandler(log_dir, 'a')
    else:
        fh = logging.FileHandler('scraping.log', 'a')
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.info('Running in scheduled hourly mode')

    print 'Running. See log file for further information.'

    # Convert from CSV of URLs to a dictionary
    try:
        url_whitelist = open(whitelist_file, 'r').readlines()
        url_whitelist = [line.replace('\n', '').split(',') for line in
                         url_whitelist if line]
        # Filtering based on list of sources from the config file
        to_scrape = {listing[0]: [listing[1], listing[3]] for listing in
                     url_whitelist if listing[2] in sources}
    except IOError:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Could not open URL whitelist file.')
        raise

    call_scrape_func(to_scrape, db_collection, pool_size, auth_db, auth_user,
                     auth_pass, db_host=db_host)
    logger.info('All done.')

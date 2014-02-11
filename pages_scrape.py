import logging
import requests
from goose import Goose


def scrape(url):
    """
    Function to request and parse a given URL. Returns only the "relevant"
    text.

    Parameters
    ----------

    url : String.
            URL to request and parse.

    Returns
    -------

    text : String.
            Parsed text from the specified website.

    meta : String.
            Parsed meta description of an article. Usually equivalent to the
            lede.
    """
    logger = logging.getLogger('scraper_log')
    try:
        page = requests.get(url)
        g = Goose({'use_meta_language': False, 'target_language': 'en'})
        try:
            article = g.extract(raw_html=page.content)
            text = article.cleaned_text
            meta = article.meta_description
            return text, meta
        #Generic error catching is bad
        except Exception, e:
            print 'There was an error. Check the log file for more information.'
            logger.warning('Problem scraping URL: {}. {}.'.format(url, e))
    except Exception, e:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Problem requesting url: {}. {}'.format(url, e))


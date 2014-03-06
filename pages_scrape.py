import logging
import requests


def scrape(url, extractor):
    """
    Function to request and parse a given URL. Returns only the "relevant"
    text.

    Parameters
    ----------

    url : String.
            URL to request and parse.

    extractor : Goose class instance.
                An instance of Goose that allows for parsing of content.

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
        headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36"}

        page = requests.get(url, headers=headers)
        try:
            article = extractor.extract(raw_html=page.content)
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

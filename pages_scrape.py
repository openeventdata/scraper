import justext
import logging
import requests


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
    """
    logger = logging.getLogger('scraper_log')
    text = ''
    try:
        headers = {'User-Agent':
                   "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36"}
        page = requests.get(url, headers=headers)
        #Use justext to pull out the relevant info
        paragraphs = justext.justext(page.content,
                                     justext.get_stoplist('English'))
        #And keep only the good paragraphs
        for par in paragraphs:
            if par['class'] == 'good':
                text += par['text'] + ' '
        return text
    #Generic error catching is bad
    except Exception, e:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Problem scraping URL: {}. {}.'.format(url, e))

import justext
import logging
import requests


def scrape(url, title):
    logger = logging.getLogger('scraper_log')
    text = ''
    try:
        page = requests.get(url)
        #Use justext to pull out the relevant info
        paragraphs = justext.justext(page.content,
                                     justext.get_stoplist('English'))
        #And keep only the good paragraphs
        for par in paragraphs:
            if par['class'] == 'good':
                text += par['text']
        return text
    #Generic error catching is bad
    except Exception, e:
        print 'There was an error. Check the log file for more information.'
        logger.warning('Problem scraping URL: {}. {}.'.format(url, e))

import datetime


def add_entry(collection, text, title, url, date, website):
    """
    Function that creates the dictionary of content to add to a MongoDB
    instance, checks whether a given URL is already in the database, and
    inserts the new content into the database.

    Parameters
    ----------

    collection : pymongo Collection.
                    Collection within MongoDB that in which results are stored.

    text : String.
            Text from a given webpage.

    title : String.
            Title of the news story.

    url : String.
            URL of the webpage from which the content was pulled.

    date : String.
            Date pulled from the RSS feed.

    website : String.
                Nickname of the site from which the content was pulled.

    Returns
    -------

    object_id : String
    """
    toInsert = {"url": url,
                "title": title,
                "source": website,
                "date": date,
                "date_added": datetime.datetime.utcnow(),
                "content": text,
                "stanford": 0}
    object_id = collection.insert(toInsert)
    return object_id

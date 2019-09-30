Integration
===========

:mod:`mwparserfromhell` is used by and originally developed for EarwigBot_;
:class:`~earwigbot.wiki.page.Page` objects have a
:meth:`~earwigbot.wiki.page.Page.parse` method that essentially calls
:func:`mwparserfromhell.parse() <mwparserfromhell.__init__.parse>` on
:meth:`~earwigbot.wiki.page.Page.get`.

If you're using Pywikibot_, your code might look like this:

    import mwparserfromhell
    import pywikibot

    def parse(title):
        site = pywikibot.Site()
        page = pywikibot.Page(site, title)
        text = page.get()
        return mwparserfromhell.parse(text)

If you're not using a library, you can parse any page with the following
Python 3 code (using the API_ and the requests_ library):

    import mwparserfromhell
    import requests

    API_URL = "https://en.wikipedia.org/w/api.php"

    def parse(title):
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "rvlimit": 1,
            "titles": title,
            "format": "json",
            "formatversion": "2",
        }
        headers = {"User-Agent": "My-Bot-Name/1.0"}
        req = requests.get(API_URL, headers=headers, params=params)
        res = req.json()
        revision = res["query"]["pages"][0]["revisions"][0]
        text = revision["slots"]["main"]["content"]
        return mwparserfromhell.parse(text)

.. _EarwigBot:            https://github.com/earwig/earwigbot
.. _Pywikibot:            https://www.mediawiki.org/wiki/Manual:Pywikibot
.. _API:                  https://www.mediawiki.org/wiki/API:Main_page
.. _requests:             https://2.python-requests.org

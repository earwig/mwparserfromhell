Integration
===========

:mod:`mwparserfromhell` is used by and originally developed for EarwigBot_;
:class:`~earwigbot.wiki.page.Page` objects have a
:meth:`~earwigbot.wiki.page.Page.parse` method that essentially calls
:func:`mwparserfromhell.parse() <mwparserfromhell.__init__.parse>` on
:meth:`~earwigbot.wiki.page.Page.get`.

If you're using Pywikibot_, your code might look like this::

    import mwparserfromhell
    import pywikibot

    def parse(title):
        site = pywikibot.Site()
        page = pywikibot.Page(site, title)
        text = page.get()
        return mwparserfromhell.parse(text)

If you're not using a library, you can parse any page using the following code
(via the API_)::

    import json
    from urllib.parse import urlencode
    from urllib.request import urlopen
    import mwparserfromhell
    API_URL = "https://en.wikipedia.org/w/api.php"

    def parse(title):
        data = {"action": "query", "prop": "revisions", "rvlimit": 1,
                "rvprop": "content", "format": "json", "titles": title}
        raw = urlopen(API_URL, urlencode(data).encode()).read()
        res = json.loads(raw)
        text = res["query"]["pages"].values()[0]["revisions"][0]["*"]
        return mwparserfromhell.parse(text)

.. _EarwigBot:            https://github.com/earwig/earwigbot
.. _Pywikibot:            https://www.mediawiki.org/wiki/Manual:Pywikibot
.. _API:                  http://mediawiki.org/wiki/API

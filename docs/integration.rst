Integration
===========

:py:mod:`mwparserfromhell` is used by and originally developed for EarwigBot_;
:py:class:`~earwigbot.wiki.page.Page` objects have a
:py:meth:`~earwigbot.wiki.page.Page.parse` method that essentially calls
:py:func:`mwparserfromhell.parse() <mwparserfromhell.__init__.parse>` on
:py:meth:`~earwigbot.wiki.page.Page.get`.

If you're using PyWikipedia_, your code might look like this::

    import mwparserfromhell
    import wikipedia as pywikibot
    def parse(title):
        site = pywikibot.get_site()
        page = pywikibot.Page(site, title)
        text = page.get()
        return mwparserfromhell.parse(text)

If you're not using a library, you can parse templates in any page using the
following code (via the API_)::

    import json
    import urllib
    import mwparserfromhell
    API_URL = "http://en.wikipedia.org/w/api.php"
    def parse(title):
        raw = urllib.urlopen(API_URL, data).read()
        res = json.loads(raw)
        text = res["query"]["pages"].values()[0]["revisions"][0]["*"]
        return mwparserfromhell.parse(text)

.. _EarwigBot:            https://github.com/earwig/earwigbot
.. _PyWikipedia:          http://pywikipediabot.sourceforge.net/
.. _API:                  http://mediawiki.org/wiki/API

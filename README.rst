mwparserfromhell
========================

**mwparserfromhell** (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode.

Developed by Earwig_ and named by `Σ`_.

Installation
------------

The easiest way to install the parser is through the `Python Package Index`_,
so you can install the latest release with ``pip install mwparserfromhell``
(`get pip`_). Alternatively, get the latest development version::

    git clone git://github.com/earwig/mwparserfromhell.git mwparserfromhell
    cd mwparserfromhell
    python setup.py install

You can run the comprehensive unit testing suite with ``python setup.py test``.

Usage
-----

Normal usage is rather straightforward (where ``text`` is page text)::

    >>> import mwparserfromhell
    >>> parser = mwparserfromhell.Parser()
    >>> templates = parser.parse(text)

``templates`` is a list of ``mwparserfromhell.Template`` objects, which contain
a ``name`` attribute, a ``params`` attribute, and a ``render()`` method. Slices
are supported to get parameters. For example::

    >>> templates = parser.parse("{{foo|bar|baz|eggs=spam}}")
    >>> print templates
    [Template(name="foo", params={"1": "bar", "2": "baz", "eggs": "spam"})]
    >>> template = templates[0]
    >>> print template.name
    foo
    >>> print template.params
    ['bar', 'baz']
    >>> print template[0]
    bar
    >>> print template["eggs"]
    spam
    >>> print template.render()
    {{foo|bar|baz|eggs=spam}}

If ``get``\ 's argument is a number *n*, it'll return the *n*\ th parameter,
otherwise it will return the parameter with the given name. Unnamed parameters
are given numerical names starting with 1, so ``{{foo|bar}}`` is the same as
``{{foo|1=bar}}``, and ``templates[0].get(0) is templates[0].get("1")``.

By default, nested templates are supported like so::

    >>> templates = parser.parse("{{foo|this {{includes a|template}}}}")
    >>> print templates
    [Template(name="foo", params={"1": "this {{includes a|template}}"})]
    >>> print templates[0].get(0)
    this {{includes a|template}}
    >>> print templates[0].get(0).templates
    [Template(name="includes a", params={"1": "template"})]
    >>> print templates[0].get(0).templates[0].params[0]
    template

Integration
-----------

``mwparserfromhell`` is used by and originally developed for EarwigBot_;
``Page`` objects have a ``parse_templates`` method that essentially calls
``Parser().parse()`` on ``page.get()``.

If you're using PyWikipedia_, your code might look like this::

    import mwparserfromhell
    import wikipedia as pywikibot
    def parse_templates(title):
        site = pywikibot.get_site()
        page = pywikibot.Page(site, title)
        text = page.get()
        parser = mwparserfromhell.Parser()
        return parser.parse(text)

If you're not using a library, you can parse templates in any page using the
following code (via the API_)::

    import json
    import urllib
    import mwparserfromhell
    API_URL = "http://en.wikipedia.org/w/api.php"
    def parse_templates(title):
        raw = urllib.urlopen(API_URL, data).read()
        res = json.loads(raw)
        text = res["query"]["pages"].values()[0]["revisions"][0]["*"]
        parser = mwparserfromhell.Parser()
        return parser.parse(text)

.. _MediaWiki:            http://mediawiki.org
.. _Earwig:               http://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                    http://en.wikipedia.org/wiki/User:Σ
.. _Python Package Index: http://pypi.python.org
.. _get pip:              http://pypi.python.org/pypi/pip
.. _EarwigBot:            https://github.com/earwig/earwigbot
.. _PyWikipedia:          http://pywikipediabot.sourceforge.net/
.. _API:                  http://mediawiki.org/wiki/API

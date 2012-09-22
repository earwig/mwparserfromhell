mwparserfromhell
================

**mwparserfromhell** (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 2 and Python 3.

Developed by Earwig_ with help from `Σ`_.

Installation
------------

The easiest way to install the parser is through the `Python Package Index`_,
so you can install the latest release with ``pip install mwparserfromhell``
(`get pip`_). Alternatively, get the latest development version::

    git clone git://github.com/earwig/mwparserfromhell.git
    cd mwparserfromhell
    python setup.py install

You can run the comprehensive unit testing suite with ``python setup.py test``.

Usage
-----

Normal usage is rather straightforward (where ``text`` is page text)::

    >>> import mwparserfromhell
    >>> wikicode = mwparserfromhell.parse(text)

``wikicode`` is a ``mwparserfromhell.Wikicode`` object, which acts like an
ordinary ``unicode`` object (or ``str`` in Python 3) with some extra methods.
For example::

    >>> text = "I has a template! {{foo|bar|baz|eggs=spam}} See it?"
    >>> wikicode = mwparserfromhell.parse(text)
    >>> print wikicode
    I has a template! {{foo|bar|baz|eggs=spam}} See it?
    >>> templates = wikicode.filter_templates()
    >>> print templates
    ['{{foo|bar|baz|eggs=spam}}']
    >>> template = templates[0]
    >>> print template.name
    foo
    >>> print template.params
    ['bar', 'baz', 'eggs=spam']
    >>> print template.get(1).value
    bar
    >>> print template.get("eggs").value
    spam

Since every node you reach is also a ``Wikicode`` object, it's trivial to get
nested templates::

    >>> code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
    >>> print code.filter_templates()
    ['{{foo|this {{includes a|template}}}}']
    >>> foo = code.filter_templates()[0]
    >>> print foo.get(1).value
    this {{includes a|template}}
    >>> print foo.get(1).value.filter_templates()[0]
    {{includes a|template}}
    >>> print foo.get(1).value.filter_templates()[0].get(1).value
    template

Additionally, you can include nested templates in ``filter_templates()`` by
passing ``recursive=True``::

    >>> text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
    >>> mwparserfromhell.parse(text).filter_templates(recursive=True)
    ['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']

Templates can be easily modified to add, remove, or alter params. ``Wikicode``
can also be treated like a list with ``append()``, ``insert()``, ``remove()``,
``replace()``, and more::

    >>> text = "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}"
    >>> code = mwparserfromhell.parse(text)
    >>> for template in code.filter_templates():
    ...     if template.name == "cleanup" and not template.has_param("date"):
    ...         template.add("date", "July 2012")
    ...
    >>> print code
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{uncategorized}}
    >>> code.replace("{{uncategorized}}", "{{bar-stub}}")
    >>> print code
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> print code.filter_templates()
    ['{{cleanup|date=July 2012}}', '{{bar-stub}}']

You can then convert ``code`` back into a regular ``unicode`` object (for
saving the page!) by calling ``unicode()`` on it::

    >>> text = unicode(code)
    >>> print text
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> text == code
    True

Likewise, use ``str(code)`` in Python 3.

Integration
-----------

``mwparserfromhell`` is used by and originally developed for EarwigBot_;
``Page`` objects have a ``parse`` method that essentially calls
``mwparserfromhell.parse()`` on ``page.get()``.

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

.. _MediaWiki:            http://mediawiki.org
.. _Earwig:               http://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                    http://en.wikipedia.org/wiki/User:%CE%A3
.. _Python Package Index: http://pypi.python.org
.. _get pip:              http://pypi.python.org/pypi/pip
.. _EarwigBot:            https://github.com/earwig/earwigbot
.. _PyWikipedia:          http://pywikipediabot.sourceforge.net/
.. _API:                  http://mediawiki.org/wiki/API

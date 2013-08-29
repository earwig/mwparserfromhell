mwparserfromhell
================

.. image:: https://travis-ci.org/earwig/mwparserfromhell.png?branch=develop
  :alt: Build Status
  :target: http://travis-ci.org/earwig/mwparserfromhell

**mwparserfromhell** (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 2 and Python 3.

Developed by Earwig_ with contributions from `Σ`_, Legoktm_, and others.
Full documentation is available on ReadTheDocs_. Development occurs on GitHub_.

Installation
------------

The easiest way to install the parser is through the `Python Package Index`_,
so you can install the latest release with ``pip install mwparserfromhell``
(`get pip`_). Alternatively, get the latest development version::

    git clone https://github.com/earwig/mwparserfromhell.git
    cd mwparserfromhell
    python setup.py install

If you get ``error: Unable to find vcvarsall.bat`` while installing, this is
because Windows can't find the compiler for C extensions. Consult this
`StackOverflow question`_ for help. You can also set ``ext_modules`` in
``setup.py`` to an empty list to prevent the extension from building.

You can run the comprehensive unit testing suite with
``python setup.py test -q``.

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

Since nodes can contain other nodes, getting nested templates is trivial::

    >>> text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
    >>> mwparserfromhell.parse(text).filter_templates()
    ['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']

You can also pass ``recursive=False`` to ``filter_templates()`` and explore
templates manually. This is possible because nodes can contain additional
``Wikicode`` objects::

    >>> code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
    >>> print code.filter_templates(recursive=False)
    ['{{foo|this {{includes a|template}}}}']
    >>> foo = code.filter_templates(recursive=False)[0]
    >>> print foo.get(1).value
    this {{includes a|template}}
    >>> print foo.get(1).value.filter_templates()[0]
    {{includes a|template}}
    >>> print foo.get(1).value.filter_templates()[0].get(1).value
    template

Templates can be easily modified to add, remove, or alter params. ``Wikicode``
objects can be treated like lists, with ``append()``, ``insert()``,
``remove()``, ``replace()``, and more. They also have a ``matches()`` method
for comparing page or template names, which takes care of capitalization and
whitespace::

    >>> text = "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}"
    >>> code = mwparserfromhell.parse(text)
    >>> for template in code.filter_templates():
    ...     if template.name.matches("Cleanup") and not template.has("date"):
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

If you're using Pywikipedia_, your code might look like this::

    import mwparserfromhell
    import wikipedia as pywikibot
    def parse(title):
        site = pywikibot.getSite()
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
        data = {"action": "query", "prop": "revisions", "rvlimit": 1,
                "rvprop": "content", "format": "json", "titles": title}
        raw = urllib.urlopen(API_URL, urllib.urlencode(data)).read()
        res = json.loads(raw)
        text = res["query"]["pages"].values()[0]["revisions"][0]["*"]
        return mwparserfromhell.parse(text)

.. _MediaWiki:              http://mediawiki.org
.. _ReadTheDocs:            http://mwparserfromhell.readthedocs.org
.. _Earwig:                 http://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                      http://en.wikipedia.org/wiki/User:%CE%A3
.. _Legoktm:                http://en.wikipedia.org/wiki/User:Legoktm
.. _GitHub:                 https://github.com/earwig/mwparserfromhell
.. _Python Package Index:   http://pypi.python.org
.. _StackOverflow question: http://stackoverflow.com/questions/2817869/error-unable-to-find-vcvarsall-bat
.. _get pip:                http://pypi.python.org/pypi/pip
.. _EarwigBot:              https://github.com/earwig/earwigbot
.. _Pywikipedia:            https://www.mediawiki.org/wiki/Manual:Pywikipediabot
.. _API:                    http://mediawiki.org/wiki/API

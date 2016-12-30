mwparserfromhell
================

.. image:: https://img.shields.io/travis/earwig/mwparserfromhell/develop.svg
  :alt: Build Status
  :target: http://travis-ci.org/earwig/mwparserfromhell

.. image:: https://img.shields.io/coveralls/earwig/mwparserfromhell/develop.svg
  :alt: Coverage Status
  :target: https://coveralls.io/r/earwig/mwparserfromhell

**mwparserfromhell** (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 2 and Python 3.

Developed by Earwig_ with contributions from `Σ`_, Legoktm_, and others.
Full documentation is available on ReadTheDocs_. Development occurs on GitHub_.

Installation
------------

The easiest way to install the parser is through the `Python Package Index`_;
you can install the latest release with ``pip install mwparserfromhell``
(`get pip`_). Make sure your pip is up-to-date first, especially on Windows.

Alternatively, get the latest development version::

    git clone https://github.com/earwig/mwparserfromhell.git
    cd mwparserfromhell
    python setup.py install

You can run the comprehensive unit testing suite with
``python setup.py test -q``.

Usage
-----

Normal usage is rather straightforward (where ``text`` is page text)::

    >>> import mwparserfromhell
    >>> wikicode = mwparserfromhell.parse(text)

``wikicode`` is a ``mwparserfromhell.Wikicode`` object, which acts like an
ordinary ``str`` object (or ``unicode`` in Python 2) with some extra methods.
For example::

    >>> text = "I has a template! {{foo|bar|baz|eggs=spam}} See it?"
    >>> wikicode = mwparserfromhell.parse(text)
    >>> print(wikicode)
    I has a template! {{foo|bar|baz|eggs=spam}} See it?
    >>> templates = wikicode.filter_templates()
    >>> print(templates)
    ['{{foo|bar|baz|eggs=spam}}']
    >>> template = templates[0]
    >>> print(template.name)
    foo
    >>> print(template.params)
    ['bar', 'baz', 'eggs=spam']
    >>> print(template.get(1).value)
    bar
    >>> print(template.get("eggs").value)
    spam

Since nodes can contain other nodes, getting nested templates is trivial::

    >>> text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
    >>> mwparserfromhell.parse(text).filter_templates()
    ['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']

You can also pass ``recursive=False`` to ``filter_templates()`` and explore
templates manually. This is possible because nodes can contain additional
``Wikicode`` objects::

    >>> code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
    >>> print(code.filter_templates(recursive=False))
    ['{{foo|this {{includes a|template}}}}']
    >>> foo = code.filter_templates(recursive=False)[0]
    >>> print(foo.get(1).value)
    this {{includes a|template}}
    >>> print(foo.get(1).value.filter_templates()[0])
    {{includes a|template}}
    >>> print(foo.get(1).value.filter_templates()[0].get(1).value)
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
    >>> print(code)
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{uncategorized}}
    >>> code.replace("{{uncategorized}}", "{{bar-stub}}")
    >>> print(code)
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> print(code.filter_templates())
    ['{{cleanup|date=July 2012}}', '{{bar-stub}}']

You can then convert ``code`` back into a regular ``str`` object (for
saving the page!) by calling ``str()`` on it::

    >>> text = str(code)
    >>> print(text)
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> text == code
    True

Likewise, use ``unicode(code)`` in Python 2.

Caveats
-------

An inherent limitation in wikicode prevents us from generating complete parse
trees in certain cases. For example, the string ``{{echo|''Hello}}, world!''``
produces the valid output ``<i>Hello, world!</i>`` in MediaWiki, assuming
``{{echo}}`` is a template that returns its first parameter. But since
representing this in mwparserfromhell's node tree would be impossible, we
compromise by treating the first node (i.e., the template) as plain text,
parsing only the italics.

The current workaround for cases where you are not interested in text
formatting is to pass ``skip_style_tags=True`` to ``mwparserfromhell.parse()``.
This treats ``''`` and ``'''`` like plain text.

A future version of mwparserfromhell will include multiple parsing modes to get
around this restriction.

Integration
-----------

``mwparserfromhell`` is used by and originally developed for EarwigBot_;
``Page`` objects have a ``parse`` method that essentially calls
``mwparserfromhell.parse()`` on ``page.get()``.

If you're using Pywikibot_, your code might look like this::

    import mwparserfromhell
    import pywikibot

    def parse(title):
        site = pywikibot.Site()
        page = pywikibot.Page(site, title)
        text = page.get()
        return mwparserfromhell.parse(text)

If you're not using a library, you can parse any page using the following
Python 3 code (via the API_)::

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

.. _MediaWiki:              http://mediawiki.org
.. _ReadTheDocs:            http://mwparserfromhell.readthedocs.org
.. _Earwig:                 http://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                      http://en.wikipedia.org/wiki/User:%CE%A3
.. _Legoktm:                http://en.wikipedia.org/wiki/User:Legoktm
.. _GitHub:                 https://github.com/earwig/mwparserfromhell
.. _Python Package Index:   http://pypi.python.org
.. _get pip:                http://pypi.python.org/pypi/pip
.. _EarwigBot:              https://github.com/earwig/earwigbot
.. _Pywikibot:              https://www.mediawiki.org/wiki/Manual:Pywikibot
.. _API:                    http://mediawiki.org/wiki/API

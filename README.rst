mwparserfromhell
================

.. image:: https://api.travis-ci.com/earwig/mwparserfromhell.svg
  :alt: Build Status
  :target: https://travis-ci.org/earwig/mwparserfromhell

.. image:: https://img.shields.io/coveralls/earwig/mwparserfromhell/main.svg
  :alt: Coverage Status
  :target: https://coveralls.io/r/earwig/mwparserfromhell

**mwparserfromhell** (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 3.8+.

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

The comprehensive unit testing suite requires `pytest`_ (``pip install pytest``)
and can be run with ``python -m pytest``.

Usage
-----

Normal usage is rather straightforward (where ``text`` is page text):

>>> import mwparserfromhell
>>> wikicode = mwparserfromhell.parse(text)

``wikicode`` is a ``mwparserfromhell.Wikicode`` object, which acts like an
ordinary ``str`` object with some extra methods. For example:

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

Since nodes can contain other nodes, getting nested templates is trivial:

>>> text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
>>> mwparserfromhell.parse(text).filter_templates()
['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']

You can also pass ``recursive=False`` to ``filter_templates()`` and explore
templates manually. This is possible because nodes can contain additional
``Wikicode`` objects:

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
whitespace:

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
saving the page!) by calling ``str()`` on it:

>>> text = str(code)
>>> print(text)
{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
>>> text == code
True

Limitations
-----------

While the MediaWiki parser generates HTML and has access to the contents of
templates, among other things, mwparserfromhell acts as a direct interface to
the source code only. This has several implications:

* Syntax elements produced by a template transclusion cannot be detected. For
  example, imagine a hypothetical page ``"Template:End-bold"`` that contained
  the text ``</b>``. While MediaWiki would correctly understand that
  ``<b>foobar{{end-bold}}`` translates to ``<b>foobar</b>``, mwparserfromhell
  has no way of examining the contents of ``{{end-bold}}``. Instead, it would
  treat the bold tag as unfinished, possibly extending further down the page.

* Templates adjacent to external links, as in ``http://example.com{{foo}}``,
  are considered part of the link. In reality, this would depend on the
  contents of the template.

* When different syntax elements cross over each other, as in
  ``{{echo|''Hello}}, world!''``, the parser gets confused because this cannot
  be represented by an ordinary syntax tree. Instead, the parser will treat the
  first syntax construct as plain text. In this case, only the italic tag would
  be properly parsed.

  **Workaround:** Since this commonly occurs with text formatting and text
  formatting is often not of interest to users, you may pass
  *skip_style_tags=True* to ``mwparserfromhell.parse()``. This treats ``''``
  and ``'''`` as plain text.

  A future version of mwparserfromhell may include multiple parsing modes to
  get around this restriction more sensibly.

Additionally, the parser lacks awareness of certain wiki-specific settings:

* `Word-ending links`_ are not supported, since the linktrail rules are
  language-specific.

* Localized namespace names aren't recognized, so file links (such as
  ``[[File:...]]``) are treated as regular wikilinks.

* Anything that looks like an XML tag is treated as a tag, even if it is not a
  recognized tag name, since the list of valid tags depends on loaded MediaWiki
  extensions.

Integration
-----------

``mwparserfromhell`` is used by and originally developed for EarwigBot_;
``Page`` objects have a ``parse`` method that essentially calls
``mwparserfromhell.parse()`` on ``page.get()``.

If you're using Pywikibot_, your code might look like this:

.. code-block:: python

    import mwparserfromhell
    import pywikibot

    def parse(title):
        site = pywikibot.Site()
        page = pywikibot.Page(site, title)
        text = page.get()
        return mwparserfromhell.parse(text)

If you're not using a library, you can parse any page with the following
Python 3 code (using the API_ and the requests_ library):

.. code-block:: python

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

.. _MediaWiki:              https://www.mediawiki.org
.. _ReadTheDocs:            https://mwparserfromhell.readthedocs.io
.. _Earwig:                 https://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                      https://en.wikipedia.org/wiki/User:%CE%A3
.. _Legoktm:                https://en.wikipedia.org/wiki/User:Legoktm
.. _GitHub:                 https://github.com/earwig/mwparserfromhell
.. _Python Package Index:   https://pypi.org/
.. _get pip:                https://pypi.org/project/pip/
.. _pytest:                 https://docs.pytest.org/
.. _Word-ending links:      https://www.mediawiki.org/wiki/Help:Links#linktrail
.. _EarwigBot:              https://github.com/earwig/earwigbot
.. _Pywikibot:              https://www.mediawiki.org/wiki/Manual:Pywikibot
.. _API:                    https://www.mediawiki.org/wiki/API:Main_page
.. _requests:               https://2.python-requests.org

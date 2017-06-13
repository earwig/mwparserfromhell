MWParserFromHell v\ |version| Documentation
===========================================

:mod:`mwparserfromhell` (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 2 and Python 3.

Developed by Earwig_ with contributions from `Σ`_, Legoktm_, and others.
Development occurs on GitHub_.

.. _MediaWiki:            http://mediawiki.org
.. _Earwig:               http://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                    http://en.wikipedia.org/wiki/User:%CE%A3
.. _Legoktm:              http://en.wikipedia.org/wiki/User:Legoktm
.. _GitHub:               https://github.com/earwig/mwparserfromhell

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

.. _Python Package Index:   http://pypi.python.org
.. _get pip:                http://pypi.python.org/pypi/pip

Contents
--------

.. toctree::
   :maxdepth: 2

   usage
   limitations
   integration
   changelog
   API Reference <api/modules>


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

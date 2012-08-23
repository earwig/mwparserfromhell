MWParserFromHell v0.2 Documentation
===================================

:py:mod:`mwparserfromhell` (the *MediaWiki Parser from Hell*) is a Python
package that provides an easy-to-use and outrageously powerful parser for
MediaWiki_ wikicode. It supports Python 2 and Python 3.

Developed by Earwig_ with help from `Σ`_.

.. _MediaWiki:            http://mediawiki.org
.. _Earwig:               http://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                    http://en.wikipedia.org/wiki/User:%CE%A3

Installation
------------

The easiest way to install the parser is through the `Python Package Index`_,
so you can install the latest release with ``pip install mwparserfromhell``
(`get pip`_). Alternatively, get the latest development version::

    git clone git://github.com/earwig/mwparserfromhell.git
    cd mwparserfromhell
    python setup.py install

You can run the comprehensive unit testing suite with ``python setup.py test``.

.. _Python Package Index: http://pypi.python.org
.. _get pip:              http://pypi.python.org/pypi/pip

Contents
--------

.. toctree::
   :maxdepth: 2

   usage
   integration
   API Reference <api/modules>


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

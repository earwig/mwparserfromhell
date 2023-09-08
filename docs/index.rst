MWParserFromHell v\ |version| Documentation
===========================================

:mod:`mwparserfromhell` (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 3.8+.

Developed by Earwig_ with contributions from `Σ`_, Legoktm_, and others.
Development occurs on GitHub_.

.. _MediaWiki:            https://www.mediawiki.org
.. _Earwig:               https://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                    https://en.wikipedia.org/wiki/User:%CE%A3
.. _Legoktm:              https://en.wikipedia.org/wiki/User:Legoktm
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

The comprehensive unit testing suite requires `pytest`_ (``pip install pytest``)
and can be run with ``python -m pytest``.

.. _Python Package Index:   https://pypi.org/
.. _get pip:                https://pypi.org/project/pip/
.. _pytest:                 https://docs.pytest.org/

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

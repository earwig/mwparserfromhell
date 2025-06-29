MWParserFromHell v\ |version| Documentation
===========================================

:mod:`mwparserfromhell` (the *MediaWiki Parser from Hell*) is a Python package
that provides an easy-to-use and outrageously powerful parser for MediaWiki_
wikicode. It supports Python 3.9+.

Developed by Earwig_ with contributions from `Σ`_, Legoktm_, and others.
Development occurs on GitHub_.

.. _MediaWiki:            https://www.mediawiki.org
.. _Earwig:               https://en.wikipedia.org/wiki/User:The_Earwig
.. _Σ:                    https://en.wikipedia.org/wiki/User:%CE%A3
.. _Legoktm:              https://en.wikipedia.org/wiki/User:Legoktm
.. _GitHub:               https://github.com/earwig/mwparserfromhell

Installation
------------

The easiest way to install the parser is from `PyPI`_; you can install the
latest release with ``pip install mwparserfromhell``.

Alternatively, get the latest development version::

    git clone https://github.com/earwig/mwparserfromhell.git
    cd mwparserfromhell
    uv sync
    uv run python -c 'import mwparserfromhell; print(mwparserfromhell.__version__)'

The comprehensive test suite can be run with ``pytest``. If using ``uv``, pass
``--reinstall-package`` so updates to the extension module are properly tested::

    uv run --reinstall-package mwparserfromhell pytest

.. _PyPI:                   https://pypi.org/project/mwparserfromhell/
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

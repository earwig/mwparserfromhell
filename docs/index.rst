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

Prebuilt wheels are available on PyPI with a fast, compiled C tokenizer
extension for most environments (Linux x86_64 and arm64, macOS x86_64 and
arm64, Windows x86 and x86_64). If building from source and the C tokenizer
cannot be built, you can fall back to the slower pure-Python implementation by
setting the environment variable ``WITH_EXTENSION=0`` when installing.

To get the latest development version (with `uv`_)::

    git clone https://github.com/earwig/mwparserfromhell.git
    cd mwparserfromhell
    uv sync
    uv run python -c 'import mwparserfromhell; print(mwparserfromhell.__version__)'

The comprehensive test suite can be run with ``pytest``. If using ``uv``, pass
``--reinstall-package`` so updates to the extension module are properly tested::

    uv run --reinstall-package mwparserfromhell pytest

.. note::

    To see if the fast C tokenizer is being used, check the value of
    ``mwparserfromhell.parser.use_c``. If ``True``, it's being used; if
    ``False``, the Python fallback is being used.

.. _PyPI:                   https://pypi.org/project/mwparserfromhell/
.. _uv:                     https://docs.astral.sh/uv/
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

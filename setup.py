#! /usr/bin/env python
# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2015 Ben Kurtovic <ben.kurtovic@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys

if (sys.version_info[0] == 2 and sys.version_info[1] < 6) or \
   (sys.version_info[1] == 3 and sys.version_info[1] < 2):
    raise Exception("mwparserfromhell needs Python 2.6+ or 3.2+")

if sys.version_info >= (3, 0):
    basestring = (str, )

from setuptools import setup, find_packages, Extension

from mwparserfromhell import __version__
from mwparserfromhell.compat import py26, py3k

with open("README.rst", **{'encoding':'utf-8'} if py3k else {}) as fp:
    long_docs = fp.read()

tokenizer = Extension("mwparserfromhell.parser._tokenizer",
                      sources=["mwparserfromhell/parser/tokenizer.c"],
                      depends=["mwparserfromhell/parser/tokenizer.h"])

use_extension=True

# Allow env var WITHOUT_EXTENSION and args --with[out]-extension
if '--without-extension' in sys.argv:
    use_extension = False
elif '--with-extension' in sys.argv:
    pass
elif os.environ.get('WITHOUT_EXTENSION', '0') == '1':
    use_extension = False

# Remove the command line argument as it isnt understood by
# setuptools/distutils
sys.argv = [arg for arg in sys.argv
            if not arg.startswith('--with')
            and not arg.endswith('-extension')]


def optional_compile_setup(func=setup, use_ext=use_extension,
                           *args, **kwargs):
    """
    Wrap setup to allow optional compilation of extensions.

    Falls back to pure python mode (no extensions)
    if compilation of extensions fails.
    """
    extensions = kwargs.get('ext_modules', None)

    if use_ext and extensions:
        try:
            func(*args, **kwargs)
            return
        except SystemExit as e:
            assert(e.args)
            if e.args[0] is False:
                raise
            elif isinstance(e.args[0], basestring):
                if e.args[0].startswith('usage: '):
                    raise
                else:
                    # Fallback to pure python mode
                    print('setup with extension failed: %s' % repr(e))
                    pass
        except Exception as e:
            print('setup with extension failed: %s' % repr(e))

    if extensions:
        if use_ext:
            print('Falling back to pure python mode.')
        else:
            print('Using pure python mode.')

        del kwargs['ext_modules']

    func(*args, **kwargs)


optional_compile_setup(
    name = "mwparserfromhell",
    packages = find_packages(exclude=("tests",)),
    ext_modules = [tokenizer],
    tests_require = ["unittest2"] if py26 else [],
    test_suite = "tests.discover",
    version = __version__,
    author = "Ben Kurtovic",
    author_email = "ben.kurtovic@gmail.com",
    url = "https://github.com/earwig/mwparserfromhell",
    description = "MWParserFromHell is a parser for MediaWiki wikicode.",
    long_description = long_docs,
    download_url = "https://github.com/earwig/mwparserfromhell/tarball/v{0}".format(__version__),
    keywords = "earwig mwparserfromhell wikipedia wiki mediawiki wikicode template parsing",
    license = "MIT License",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Text Processing :: Markup"
    ],
)

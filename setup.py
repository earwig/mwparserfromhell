#! /usr/bin/env python
# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2014 Ben Kurtovic <ben.kurtovic@gmail.com>
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

import sys

if (sys.version_info[0] == 2 and sys.version_info[1] < 6) or \
   (sys.version_info[1] == 3 and sys.version_info[1] < 2):
    raise Exception('mwparserfromhell needs Python 2.6+ or 3.2+')

from setuptools import setup, find_packages, Extension

from mwparserfromhell import __version__
from mwparserfromhell.compat import py26, py3k

with open("README.rst") as fp:
    long_docs = fp.read()

tokenizer = Extension("mwparserfromhell.parser._tokenizer",
                      sources = ["mwparserfromhell/parser/tokenizer.c"])

setup(
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

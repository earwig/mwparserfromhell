#! /usr/bin/env python
# -*- coding: utf-8  -*-
#
# Copyright (C) 2012 Ben Kurtovic <ben.kurtovic@verizon.net>
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

from setuptools import setup, find_packages

from mwparserfromhell import __version__

with open("README.rst") as fp:
    long_docs = fp.read()

setup(
    name = "mwparserfromhell",
    packages = find_packages(exclude=("tests",)),
    test_suite = "tests",
    version = __version__,
    author = "Ben Kurtovic",
    author_email = "ben.kurtovic@verizon.net",
    url = "https://github.com/earwig/mwparserfromhell",
    description = "MWParserFromHell is a parser for MediaWiki wikicode.",
    long_description = long_docs,
    download_url = "https://github.com/earwig/mwparserfromhell/tarball/v{0}".format(__version__),
    keywords = "earwig mwparserfromhell wikipedia wiki mediawiki wikicode template parsing",
    license = "MIT License",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Text Processing :: Markup"
    ],
)

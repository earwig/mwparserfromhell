#! /usr/bin/env python
#
# Copyright (C) 2012-2023 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from glob import glob
import os
import sys

from setuptools import find_packages, setup, Extension
from setuptools.command.build_ext import build_ext

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mwparserfromhell import __version__

with open("README.rst") as fp:
    long_docs = fp.read()

use_extension = True
fallback = True

# Allow env var WITHOUT_EXTENSION and args --with[out]-extension:

env_var = os.environ.get("WITHOUT_EXTENSION")
if "--without-extension" in sys.argv:
    use_extension = False
elif "--with-extension" in sys.argv:
    fallback = False
elif env_var is not None:
    if env_var == "1":
        use_extension = False
    elif env_var == "0":
        fallback = False

# Remove the command line argument as it isn't understood by setuptools:

sys.argv = [
    arg for arg in sys.argv if arg not in ("--without-extension", "--with-extension")
]


def build_ext_patched(self):
    try:
        build_ext_original(self)
    except Exception as exc:
        print("error: " + str(exc))
        print("Falling back to pure Python mode.")
        del self.extensions[:]


if fallback:
    build_ext.run, build_ext_original = build_ext_patched, build_ext.run

# Project-specific part begins here:

tokenizer = Extension(
    "mwparserfromhell.parser._tokenizer",
    sources=sorted(glob("src/mwparserfromhell/parser/ctokenizer/*.c")),
    depends=sorted(glob("src/mwparserfromhell/parser/ctokenizer/*.h")),
)

setup(
    name="mwparserfromhell",
    packages=find_packages("src"),
    package_dir={"": "src"},
    ext_modules=[tokenizer] if use_extension else [],
    setup_requires=["pytest-runner"]
    if "test" in sys.argv or "pytest" in sys.argv
    else [],
    tests_require=["pytest"],
    version=__version__,
    python_requires=">= 3.8",
    author="Ben Kurtovic",
    author_email="ben.kurtovic@gmail.com",
    url="https://github.com/earwig/mwparserfromhell",
    description="MWParserFromHell is a parser for MediaWiki wikicode.",
    long_description=long_docs,
    download_url="https://github.com/earwig/mwparserfromhell/tarball/v{}".format(
        __version__
    ),
    keywords="earwig mwparserfromhell wikipedia wiki mediawiki wikicode template parsing",
    license="MIT License",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Markup",
    ],
)

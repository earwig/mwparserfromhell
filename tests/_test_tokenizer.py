# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from __future__ import print_function, unicode_literals
import codecs
from os import listdir, path
import sys

from mwparserfromhell.compat import py3k, str
from mwparserfromhell.parser import tokens
from mwparserfromhell.parser.builder import Builder

class _TestParseError(Exception):
    """Raised internally when a test could not be parsed."""
    pass


class TokenizerTestCase(object):
    """A base test case for tokenizers, whose tests are loaded dynamically.

    Subclassed along with unittest.TestCase to form TestPyTokenizer and
    TestCTokenizer. Tests are loaded dynamically from files in the 'tokenizer'
    directory.
    """

    @staticmethod
    def _build_test_method(funcname, data):
        """Create and return a method to be treated as a test case method.

        *data* is a dict containing multiple keys: the *input* text to be
        tokenized, the expected list of tokens as *output*, and an optional
        *label* for the method's docstring.
        """
        def inner(self):
            if hasattr(self, "roundtrip"):
                expected = data["input"]
                actual = str(Builder().build(data["output"][:]))
            else:
                expected = data["output"]
                actual = self.tokenizer().tokenize(data["input"])
            self.assertEqual(expected, actual)

        if not py3k:
            inner.__name__ = funcname.encode("utf8")
        inner.__doc__ = data["label"]
        return inner

    @staticmethod
    def _parse_test(test, data):
        """Parse an individual *test*, storing its info in *data*."""
        for line in test.strip().splitlines():
            if line.startswith("name:"):
                data["name"] = line[len("name:"):].strip()
            elif line.startswith("label:"):
                data["label"] = line[len("label:"):].strip()
            elif line.startswith("input:"):
                raw = line[len("input:"):].strip()
                if raw[0] == '"' and raw[-1] == '"':
                    raw = raw[1:-1]
                raw = raw.encode("raw_unicode_escape")
                data["input"] = raw.decode("unicode_escape")
            elif line.startswith("output:"):
                raw = line[len("output:"):].strip()
                try:
                    data["output"] = eval(raw, vars(tokens))
                except Exception as err:
                    raise _TestParseError(err)

    @classmethod
    def _load_tests(cls, filename, name, text, restrict=None):
        """Load all tests in *text* from the file *filename*."""
        tests = text.split("\n---\n")
        counter = 1
        digits = len(str(len(tests)))
        for test in tests:
            data = {"name": None, "label": None, "input": None, "output": None}
            try:
                cls._parse_test(test, data)
            except _TestParseError as err:
                if data["name"]:
                    error = "Could not parse test '{0}' in '{1}':\n\t{2}"
                    print(error.format(data["name"], filename, err))
                else:
                    error = "Could not parse a test in '{0}':\n\t{1}"
                    print(error.format(filename, err))
                continue

            if not data["name"]:
                error = "A test in '{0}' was ignored because it lacked a name"
                print(error.format(filename))
                continue
            if data["input"] is None or data["output"] is None:
                error = "Test '{0}' in '{1}' was ignored because it lacked an input or an output"
                print(error.format(data["name"], filename))
                continue

            number = str(counter).zfill(digits)
            counter += 1
            if restrict and data["name"] != restrict:
                continue

            fname = "test_{0}{1}_{2}".format(name, number, data["name"])
            meth = cls._build_test_method(fname, data)
            setattr(cls, fname, meth)

    @classmethod
    def build(cls):
        """Load and install all tests from the 'tokenizer' directory."""
        def load_file(filename, restrict=None):
            with codecs.open(filename, "rU", encoding="utf8") as fp:
                text = fp.read()
                name = path.split(filename)[1][:-len(extension)]
                cls._load_tests(filename, name, text, restrict)

        directory = path.join(path.dirname(__file__), "tokenizer")
        extension = ".mwtest"
        if len(sys.argv) > 2 and sys.argv[1] == "--use":
            for name in sys.argv[2:]:
                if "." in name:
                    name, test = name.split(".", 1)
                else:
                    test = None
                load_file(path.join(directory, name + extension), test)
            sys.argv = [sys.argv[0]]  # So unittest doesn't try to parse this
            cls.skip_others = True
        else:
            for filename in listdir(directory):
                if not filename.endswith(extension):
                    continue
                load_file(path.join(directory, filename))
            cls.skip_others = False

TokenizerTestCase.build()

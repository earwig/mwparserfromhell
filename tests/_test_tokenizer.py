# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>
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
from os import listdir, path

from mwparserfromhell.parser import tokens

class _TestParseError(Exception):
    """Raised internally when a test could not be parsed."""
    pass


class TokenizerTestCase(object):
    @classmethod
    def _build_test_method(cls, funcname, data):
        def inner(self):
            actual = self.tokenizer().tokenize(data["input"])
            self.assertEqual(actual, data["output"])
        inner.__name__ = funcname.encode("utf8")
        inner.__doc__ = data["label"]
        return inner

    @classmethod
    def _load_tests(cls, filename, text):
        tests = text.split("\n---\n")
        for test in tests:
            data = {"name": "", "label": "", "input": "", "output": []}
            try:
                for line in test.strip().splitlines():
                    if line.startswith("name:"):
                        data["name"] = line[len("name:"):].strip()
                    elif line.startswith("label:"):
                        data["label"] = line[len("label:"):].strip()
                    elif line.startswith("input:"):
                        raw = line[len("input:"):].strip()
                        if raw[0] == '"' and raw[-1] == '"':
                            raw = raw[1:-1]
                        data["input"] = raw.decode("unicode_escape")
                    elif line.startswith("output:"):
                        raw = line[len("output:"):].strip()
                        data["output"] = eval(raw, vars(tokens))
            except _TestParseError:
                if data["name"]:
                    error = "Could not parse test {0} in {1}"
                    print(error.format(data["name"], filename))
                else:
                    print("Could not parse a test in {0}".format(filename))
                continue
            if not data["name"]:
                error = "A test in {0} was ignored because it lacked a name"
                print(error.format(filename))
                continue
            if not data["input"] or not data["output"]:
                error = "Test {0} in {1} was ignored because it lacked an input or an output"
                print(error.format(data["name"], filename))
                continue
            funcname = "test_" + filename + "_" + data["name"]
            meth = cls._build_test_method(funcname, data)
            setattr(cls, funcname, meth)

    @classmethod
    def build(cls):
        directory = path.join(path.dirname(__file__), "tokenizer")
        extension = ".test"
        for filename in listdir(directory):
            if not filename.endswith(extension):
                continue
            with open(path.join(directory, filename), "r") as fp:
                text = fp.read().decode("utf8")
                cls._load_tests(filename[:0-len(extension)], text)

TokenizerTestCase.build()

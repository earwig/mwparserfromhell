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

import unittest

from mwparserfromhell.parameter import Parameter
from mwparserfromhell.parser import Parser
from mwparserfromhell.template import Template

TESTS = [
    ("", []),
    ("abcdef ghijhk", []),
    ("abc{this is not a template}def", []),
    ("neither is {{this one}nor} {this one {despite}} containing braces", []),
    ("this is an acceptable {{template}}", [Template("template")]),
    ("{{multiple}}{{templates}}", [Template("multiple"),
                                   Template("templates")]),
    ("multiple {{-}} templates {{+}}!", [Template("-"), Template("+")]),
    ("{{{no templates here}}}", []),
    ("{ {{templates here}}}", [Template("templates here")]),
    ("{{{{I do not exist}}}}", []),
    ("{{foo|bar|baz|eggs=spam}}",
     [Template("foo", [Parameter("1", "bar"), Parameter("2", "baz"),
                       Parameter("eggs", "spam")])]),
    ("{{abc def|ghi|jk=lmno|pqr|st=uv|wx|yz}}",
     [Template("abc def", [Parameter("1", "ghi"), Parameter("jk", "lmno"),
                           Parameter("2", "pqr"), Parameter("st", "uv"),
                           Parameter("3", "wx"), Parameter("4", "yz")])]),
    ("{{this has a|{{template}}|inside of it}}",
     [Template("this has a", [Parameter("1", "{{template}}",
                                        [Template("template")]),
                              Parameter("2", "inside of it")])]),
    ("{{{{I exist}} }}", [Template("I exist", [] )]),
    ("{{}}")
]

class TestParser(unittest.TestCase):
    def test_parse(self):
        parser = Parser()
        for unparsed, parsed in TESTS:
            self.assertEqual(parser.parse(unparsed), parsed)

if __name__ == "__main__":
    unittest.main(verbosity=2)

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

from __future__ import unicode_literals
import unittest

from mwparserfromhell import parser
from mwparserfromhell.nodes import Template, Text, Wikilink
from mwparserfromhell.nodes.extras import Parameter

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext
from .compat import range

class TestParser(TreeEqualityTestCase):
    """Tests for the Parser class itself, which tokenizes and builds nodes."""

    def test_use_c(self):
        """make sure the correct tokenizer is used"""
        if parser.use_c:
            self.assertTrue(parser.Parser()._tokenizer.USES_C)
            parser.use_c = False
        self.assertFalse(parser.Parser()._tokenizer.USES_C)

    def test_parsing(self):
        """integration test for parsing overall"""
        text = "this is text; {{this|is=a|template={{with|[[links]]|in}}it}}"
        expected = wrap([
            Text("this is text; "),
            Template(wraptext("this"), [
                Parameter(wraptext("is"), wraptext("a")),
                Parameter(wraptext("template"), wrap([
                    Template(wraptext("with"), [
                        Parameter(wraptext("1"),
                                  wrap([Wikilink(wraptext("links"))]),
                                  showkey=False),
                        Parameter(wraptext("2"),
                                  wraptext("in"), showkey=False)
                    ]),
                    Text("it")
                ]))
            ])
        ])
        actual = parser.Parser().parse(text)
        self.assertWikicodeEqual(expected, actual)

if __name__ == "__main__":
    unittest.main(verbosity=2)

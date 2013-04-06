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

from mwparserfromhell.nodes import Template, Text
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.utils import parse_anything
from mwparserfromhell.wikicode import Wikicode

from ._test_tree_equality import TreeEqualityTestCase

class TestUtils(TreeEqualityTestCase):
    """Tests for the utils module, which provides parse_anything()."""

    def test_parse_anything_valid(self):
        """tests for valid input to utils.parse_anything()"""
        wrap = lambda L: Wikicode(SmartList(L))
        textify = lambda L: wrap([Text(item) for item in L])
        tests = [
            (wrap([Text("foobar")]), textify(["foobar"])),
            (Template(wrap([Text("spam")])),
                wrap([Template(textify(["spam"]))])),
            ("fóóbar", textify(["fóóbar"])),
            (b"foob\xc3\xa1r", textify(["foobár"])),
            (123, textify(["123"])),
            (True, textify(["True"])),
            (None, wrap([])),
            ([Text("foo"), Text("bar"), Text("baz")],
                textify(["foo", "bar", "baz"])),
            ([wrap([Text("foo")]), Text("bar"), "baz", 123, 456],
                textify(["foo", "bar", "baz", "123", "456"])),
            ([[[([[((("foo",),),)], "bar"],)]]], textify(["foo", "bar"]))
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, parse_anything(test))

    def test_parse_anything_invalid(self):
        """tests for invalid input to utils.parse_anything()"""
        self.assertRaises(ValueError, parse_anything, Ellipsis)
        self.assertRaises(ValueError, parse_anything, object)
        self.assertRaises(ValueError, parse_anything, object())
        self.assertRaises(ValueError, parse_anything, type)
        self.assertRaises(ValueError, parse_anything, ["foo", [object]])

if __name__ == "__main__":
    unittest.main(verbosity=2)

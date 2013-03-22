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

from mwparserfromhell.smart_list import SmartList, _ListProxy

class TestSmartList(unittest.TestCase):
    """Test cases for the SmartList class and its child, _ListProxy."""
    def test_docs(self):
        """make sure the methods of SmartList/_ListProxy have docstrings"""
        methods = ["append", "count", "extend", "index", "insert", "pop",
                   "remove", "reverse", "sort"]
        for meth in methods:
            expected = getattr(list, meth).__doc__
            smartlist_doc = getattr(SmartList, meth).__doc__
            listproxy_doc = getattr(_ListProxy, meth).__doc__
            self.assertEquals(expected, smartlist_doc)
            self.assertEquals(expected, listproxy_doc)

    def test_doctest(self):
        """make sure a test embedded in SmartList's docstring passes"""
        parent = SmartList([0, 1, 2, 3])
        self.assertEquals([0, 1, 2, 3], parent)
        child = parent[2:]
        self.assertEquals([2, 3], child)
        child.append(4)
        self.assertEquals([2, 3, 4], child)
        self.assertEquals([0, 1, 2, 3, 4], parent)

if __name__ == "__main__":
    unittest.main(verbosity=2)

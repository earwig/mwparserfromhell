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

from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mwparserfromhell.compat import str
from mwparserfromhell.nodes import Text
from mwparserfromhell.nodes.extras import Parameter

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestParameter(TreeEqualityTestCase):
    """Test cases for the Parameter node extra."""

    def test_unicode(self):
        """test Parameter.__unicode__()"""
        node = Parameter(wraptext("1"), wraptext("foo"), showkey=False)
        self.assertEqual("foo", str(node))
        node2 = Parameter(wraptext("foo"), wraptext("bar"))
        self.assertEqual("foo=bar", str(node2))

    def test_name(self):
        """test getter/setter for the name attribute"""
        name1 = wraptext("1")
        name2 = wraptext("foobar")
        node1 = Parameter(name1, wraptext("foobar"), showkey=False)
        node2 = Parameter(name2, wraptext("baz"))
        self.assertIs(name1, node1.name)
        self.assertIs(name2, node2.name)
        node1.name = "héhehé"
        node2.name = "héhehé"
        self.assertWikicodeEqual(wraptext("héhehé"), node1.name)
        self.assertWikicodeEqual(wraptext("héhehé"), node2.name)

    def test_value(self):
        """test getter/setter for the value attribute"""
        value = wraptext("bar")
        node = Parameter(wraptext("foo"), value)
        self.assertIs(value, node.value)
        node.value = "héhehé"
        self.assertWikicodeEqual(wraptext("héhehé"), node.value)

    def test_showkey(self):
        """test getter/setter for the showkey attribute"""
        node1 = Parameter(wraptext("1"), wraptext("foo"), showkey=False)
        node2 = Parameter(wraptext("foo"), wraptext("bar"))
        self.assertFalse(node1.showkey)
        self.assertTrue(node2.showkey)
        node1.showkey = True
        self.assertTrue(node1.showkey)
        node1.showkey = ""
        self.assertFalse(node1.showkey)
        self.assertRaises(ValueError, setattr, node2, "showkey", False)

if __name__ == "__main__":
    unittest.main(verbosity=2)

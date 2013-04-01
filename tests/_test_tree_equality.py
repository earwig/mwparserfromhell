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
from unittest import TestCase

from mwparserfromhell.nodes import Template, Text, Wikilink
from mwparserfromhell.nodes.extras import Parameter
from mwparserfromhell.wikicode import Wikicode

class TreeEqualityTestCase(TestCase):
    """A base test case with support for comparing the equality of node trees.

    This adds a number of type equality functions, for Wikicode, Text,
    Templates, and Wikilinks.
    """

    def assertNodeEqual(self, expected, actual):
        """Assert that two Nodes have the same type and have the same data."""
        registry = {
            Text: self.assertTextNodeEqual,
            Template: self.assertTemplateNodeEqual,
            Wikilink: self.assertWikilinkNodeEqual
        }
        for nodetype in registry:
            if isinstance(expected, nodetype):
                self.assertIsInstance(actual, nodetype)
                registry[nodetype](expected, actual)

    def assertTextNodeEqual(self, expected, actual):
        """Assert that two Text nodes have the same data."""
        self.assertEqual(expected.value, actual.value)

    def assertTemplateNodeEqual(self, expected, actual):
        """Assert that two Template nodes have the same data."""
        self.assertWikicodeEqual(expected.name, actual.name)
        length = len(expected.params)
        self.assertEqual(length, len(actual.params))
        for i in range(length):
            exp_param = expected.params[i]
            act_param = actual.params[i]
            self.assertWikicodeEqual(exp_param.name, act_param.name)
            self.assertWikicodeEqual(exp_param.value, act_param.value)
            self.assertIs(exp_param.showkey, act_param.showkey)

    def assertWikilinkNodeEqual(self, expected, actual):
        """Assert that two Wikilink nodes have the same data."""
        self.assertWikicodeEqual(expected.title, actual.title)
        if expected.text is not None:
            self.assertWikicodeEqual(expected.text, actual.text)
        else:
            self.assertIs(None, actual.text)

    def assertWikicodeEqual(self, expected, actual):
        """Assert that two Wikicode objects have the same data."""
        self.assertIsInstance(actual, Wikicode)
        length = len(expected.nodes)
        self.assertEqual(length, len(actual.nodes))
        for i in range(length):
            self.assertNodeEqual(expected.get(i), actual.get(i))

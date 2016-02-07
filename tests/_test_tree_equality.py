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
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

from mwparserfromhell.compat import range
from mwparserfromhell.nodes import (Argument, Comment, Heading, HTMLEntity,
                                    Tag, Template, Text, Wikilink)
from mwparserfromhell.nodes.extras import Attribute, Parameter
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode

wrap = lambda L: Wikicode(SmartList(L))
wraptext = lambda *args: wrap([Text(t) for t in args])

class TreeEqualityTestCase(TestCase):
    """A base test case with support for comparing the equality of node trees.

    This adds a number of type equality functions, for Wikicode, Text,
    Templates, and Wikilinks.
    """

    def assertNodeEqual(self, expected, actual):
        """Assert that two Nodes have the same type and have the same data."""
        registry = {
            Argument: self.assertArgumentNodeEqual,
            Comment: self.assertCommentNodeEqual,
            Heading: self.assertHeadingNodeEqual,
            HTMLEntity: self.assertHTMLEntityNodeEqual,
            Tag: self.assertTagNodeEqual,
            Template: self.assertTemplateNodeEqual,
            Text: self.assertTextNodeEqual,
            Wikilink: self.assertWikilinkNodeEqual
        }
        for nodetype in registry:
            if isinstance(expected, nodetype):
                self.assertIsInstance(actual, nodetype)
                registry[nodetype](expected, actual)

    def assertArgumentNodeEqual(self, expected, actual):
        """Assert that two Argument nodes have the same data."""
        self.assertWikicodeEqual(expected.name, actual.name)
        if expected.default is not None:
            self.assertWikicodeEqual(expected.default, actual.default)
        else:
            self.assertIs(None, actual.default)

    def assertCommentNodeEqual(self, expected, actual):
        """Assert that two Comment nodes have the same data."""
        self.assertWikicodeEqual(expected.contents, actual.contents)

    def assertHeadingNodeEqual(self, expected, actual):
        """Assert that two Heading nodes have the same data."""
        self.assertWikicodeEqual(expected.title, actual.title)
        self.assertEqual(expected.level, actual.level)

    def assertHTMLEntityNodeEqual(self, expected, actual):
        """Assert that two HTMLEntity nodes have the same data."""
        self.assertEqual(expected.value, actual.value)
        self.assertIs(expected.named, actual.named)
        self.assertIs(expected.hexadecimal, actual.hexadecimal)
        self.assertEqual(expected.hex_char, actual.hex_char)

    def assertTagNodeEqual(self, expected, actual):
        """Assert that two Tag nodes have the same data."""
        self.assertWikicodeEqual(expected.tag, actual.tag)
        if expected.contents is not None:
            self.assertWikicodeEqual(expected.contents, actual.contents)
        length = len(expected.attributes)
        self.assertEqual(length, len(actual.attributes))
        for i in range(length):
            exp_attr = expected.attributes[i]
            act_attr = actual.attributes[i]
            self.assertWikicodeEqual(exp_attr.name, act_attr.name)
            if exp_attr.value is not None:
                self.assertWikicodeEqual(exp_attr.value, act_attr.value)
                self.assertEqual(exp_attr.quotes, act_attr.quotes)
            self.assertEqual(exp_attr.pad_first, act_attr.pad_first)
            self.assertEqual(exp_attr.pad_before_eq, act_attr.pad_before_eq)
            self.assertEqual(exp_attr.pad_after_eq, act_attr.pad_after_eq)
        self.assertEqual(expected.wiki_markup, actual.wiki_markup)
        self.assertIs(expected.self_closing, actual.self_closing)
        self.assertIs(expected.invalid, actual.invalid)
        self.assertIs(expected.implicit, actual.implicit)
        self.assertEqual(expected.padding, actual.padding)
        self.assertWikicodeEqual(expected.closing_tag, actual.closing_tag)

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

    def assertTextNodeEqual(self, expected, actual):
        """Assert that two Text nodes have the same data."""
        self.assertEqual(expected.value, actual.value)

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

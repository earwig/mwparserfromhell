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

from mwparserfromhell.nodes import (Argument, Comment, Heading, HTMLEntity,
                                    Tag, Template, Text, Wikilink)
from mwparserfromhell.nodes.extras import Attribute, Parameter
from mwparserfromhell.parser import tokens
from mwparserfromhell.parser.builder import Builder
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode

from ._test_tree_equality import TreeEqualityTestCase

wrap = lambda L: Wikicode(SmartList(L))

class TestBuilder(TreeEqualityTestCase):
    """Tests for the builder, which turns tokens into Wikicode objects."""

    def setUp(self):
        self.builder = Builder()

    def test_text(self):
        """tests for building Text nodes"""
        tests = [
            ([tokens.Text(text="foobar")], wrap([Text("foobar")])),
            ([tokens.Text(text="fóóbar")], wrap([Text("fóóbar")])),
            ([tokens.Text(text="spam"), tokens.Text(text="eggs")],
             wrap([Text("spam"), Text("eggs")])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_template(self):
        """tests for building Template nodes"""
        tests = [
            ([tokens.TemplateOpen(), tokens.Text(text="foobar"),
              tokens.TemplateClose()],
             wrap([Template(wrap([Text("foobar")]))])),

            ([tokens.TemplateOpen(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.TemplateClose()],
             wrap([Template(wrap([Text("spam"), Text("eggs")]))])),

            ([tokens.TemplateOpen(), tokens.Text(text="foo"),
              tokens.TemplateParamSeparator(), tokens.Text(text="bar"),
              tokens.TemplateClose()],
             wrap([Template(wrap([Text("foo")]), params=[
                 Parameter(wrap([Text("1")]), wrap([Text("bar")]),
                           showkey=False)])])),

            ([tokens.TemplateOpen(), tokens.Text(text="foo"),
              tokens.TemplateParamSeparator(), tokens.Text(text="bar"),
              tokens.TemplateParamEquals(), tokens.Text(text="baz"),
              tokens.TemplateClose()],
             wrap([Template(wrap([Text("foo")]), params=[
                 Parameter(wrap([Text("bar")]), wrap([Text("baz")]))])])),

            ([tokens.TemplateOpen(), tokens.Text(text="foo"),
              tokens.TemplateParamSeparator(), tokens.Text(text="bar"),
              tokens.TemplateParamEquals(), tokens.Text(text="baz"),
              tokens.TemplateParamSeparator(), tokens.Text(text="biz"),
              tokens.TemplateParamSeparator(), tokens.Text(text="buzz"),
              tokens.TemplateParamSeparator(), tokens.Text(text="3"),
              tokens.TemplateParamEquals(), tokens.Text(text="buff"),
              tokens.TemplateParamSeparator(), tokens.Text(text="baff"),
              tokens.TemplateClose()],
             wrap([Template(wrap([Text("foo")]), params=[
                 Parameter(wrap([Text("bar")]), wrap([Text("baz")])),
                 Parameter(wrap([Text("1")]), wrap([Text("biz")]),
                           showkey=False),
                 Parameter(wrap([Text("2")]), wrap([Text("buzz")]),
                           showkey=False),
                 Parameter(wrap([Text("3")]), wrap([Text("buff")])),
                 Parameter(wrap([Text("3")]), wrap([Text("baff")]),
                           showkey=False)])])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_argument(self):
        """tests for building Argument nodes"""
        tests = [
            ([tokens.ArgumentOpen(), tokens.Text(text="foobar"),
              tokens.ArgumentClose()],
             wrap([Argument(wrap([Text("foobar")]))])),

            ([tokens.ArgumentOpen(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.ArgumentClose()],
             wrap([Argument(wrap([Text("spam"), Text("eggs")]))])),

            ([tokens.ArgumentOpen(), tokens.Text(text="foo"),
              tokens.ArgumentSeparator(), tokens.Text(text="bar"),
              tokens.ArgumentClose()],
             wrap([Argument(wrap([Text("foo")]), wrap([Text("bar")]))])),

            ([tokens.ArgumentOpen(), tokens.Text(text="foo"),
              tokens.Text(text="bar"), tokens.ArgumentSeparator(),
              tokens.Text(text="baz"), tokens.Text(text="biz"),
              tokens.ArgumentClose()],
             wrap([Argument(wrap([Text("foo"), Text("bar")]),
                            wrap([Text("baz"), Text("biz")]))])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_wikilink(self):
        """tests for building Wikilink nodes"""
        tests = [
            ([tokens.WikilinkOpen(), tokens.Text(text="foobar"),
              tokens.WikilinkClose()],
             wrap([Wikilink(wrap([Text("foobar")]))])),

            ([tokens.WikilinkOpen(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.WikilinkClose()],
             wrap([Wikilink(wrap([Text("spam"), Text("eggs")]))])),

            ([tokens.WikilinkOpen(), tokens.Text(text="foo"),
              tokens.WikilinkSeparator(), tokens.Text(text="bar"),
              tokens.WikilinkClose()],
             wrap([Wikilink(wrap([Text("foo")]), wrap([Text("bar")]))])),

            ([tokens.WikilinkOpen(), tokens.Text(text="foo"),
              tokens.Text(text="bar"), tokens.WikilinkSeparator(),
              tokens.Text(text="baz"), tokens.Text(text="biz"),
              tokens.WikilinkClose()],
             wrap([Wikilink(wrap([Text("foo"), Text("bar")]),
                            wrap([Text("baz"), Text("biz")]))])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_html_entity(self):
        """tests for building HTMLEntity nodes"""
        tests = [
            ([tokens.HTMLEntityStart(), tokens.Text(text="nbsp"),
              tokens.HTMLEntityEnd()],
             wrap([HTMLEntity("nbsp", named=True, hexadecimal=False)])),

            ([tokens.HTMLEntityStart(), tokens.HTMLEntityNumeric(),
              tokens.Text(text="107"), tokens.HTMLEntityEnd()],
             wrap([HTMLEntity("107", named=False, hexadecimal=False)])),

            ([tokens.HTMLEntityStart(), tokens.HTMLEntityNumeric(),
              tokens.HTMLEntityHex(char="X"), tokens.Text(text="6B"),
              tokens.HTMLEntityEnd()],
             wrap([HTMLEntity("6B", named=False, hexadecimal=True,
                              hex_char="X")])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_heading(self):
        """tests for building Heading nodes"""
        tests = [
            ([tokens.HeadingStart(level=2), tokens.Text(text="foobar"),
              tokens.HeadingEnd()],
             wrap([Heading(wrap([Text("foobar")]), 2)])),

            ([tokens.HeadingStart(level=4), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.HeadingEnd()],
             wrap([Heading(wrap([Text("spam"), Text("eggs")]), 4)])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_comment(self):
        """tests for building Comment nodes"""
        tests = [
            ([tokens.CommentStart(), tokens.Text(text="foobar"),
              tokens.CommentEnd()],
             wrap([Comment(wrap([Text("foobar")]))])),

            ([tokens.CommentStart(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.CommentEnd()],
             wrap([Comment(wrap([Text("spam"), Text("eggs")]))])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    @unittest.skip("holding this until feature/html_tags is ready")
    def test_tag(self):
        """tests for building Tag nodes"""
        pass

    def test_integration(self):
        """a test for building a combination of templates together"""
        # {{{{{{{{foo}}bar|baz=biz}}buzz}}usr|{{bin}}}}
        test = [tokens.TemplateOpen(), tokens.TemplateOpen(),
                tokens.TemplateOpen(), tokens.TemplateOpen(),
                tokens.Text(text="foo"), tokens.TemplateClose(),
                tokens.Text(text="bar"), tokens.TemplateParamSeparator(),
                tokens.Text(text="baz"), tokens.TemplateParamEquals(),
                tokens.Text(text="biz"), tokens.TemplateClose(),
                tokens.Text(text="buzz"), tokens.TemplateClose(),
                tokens.Text(text="usr"), tokens.TemplateParamSeparator(),
                tokens.TemplateOpen(), tokens.Text(text="bin"),
                tokens.TemplateClose(), tokens.TemplateClose()]
        valid = wrap(
            [Template(wrap([Template(wrap([Template(wrap([Template(wrap([Text(
            "foo")])), Text("bar")]), params=[Parameter(wrap([Text("baz")]),
            wrap([Text("biz")]))]), Text("buzz")])), Text("usr")]), params=[
            Parameter(wrap([Text("1")]), wrap([Template(wrap([Text("bin")]))]),
            showkey=False)])])
        self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_integration2(self):
        """an even more audacious test for building a horrible wikicode mess"""
        # {{a|b|{{c|[[d]]{{{e}}}}}}}[[f|{{{g}}}<!--h-->]]{{i|j=&nbsp;}}
        test = [tokens.TemplateOpen(), tokens.Text(text="a"),
                tokens.TemplateParamSeparator(), tokens.Text(text="b"),
                tokens.TemplateParamSeparator(), tokens.TemplateOpen(),
                tokens.Text(text="c"), tokens.TemplateParamSeparator(),
                tokens.WikilinkOpen(), tokens.Text(text="d"),
                tokens.WikilinkClose(), tokens.ArgumentOpen(),
                tokens.Text(text="e"), tokens.ArgumentClose(),
                tokens.TemplateClose(), tokens.TemplateClose(),
                tokens.WikilinkOpen(), tokens.Text(text="f"),
                tokens.WikilinkSeparator(), tokens.ArgumentOpen(),
                tokens.Text(text="g"), tokens.ArgumentClose(),
                tokens.CommentStart(), tokens.Text(text="h"),
                tokens.CommentEnd(), tokens.WikilinkClose(),
                tokens.TemplateOpen(), tokens.Text(text="i"),
                tokens.TemplateParamSeparator(), tokens.Text(text="j"),
                tokens.TemplateParamEquals(), tokens.HTMLEntityStart(),
                tokens.Text(text="nbsp"), tokens.HTMLEntityEnd(),
                tokens.TemplateClose()]
        valid = wrap(
            [Template(wrap([Text("a")]), params=[Parameter(wrap([Text("1")]),
            wrap([Text("b")]), showkey=False), Parameter(wrap([Text("2")]),
            wrap([Template(wrap([Text("c")]), params=[Parameter(wrap([Text("1")
            ]), wrap([Wikilink(wrap([Text("d")])), Argument(wrap([Text("e")]))]
            ), showkey=False)])]), showkey=False)]), Wikilink(wrap([Text("f")]
            ), wrap([Argument(wrap([Text("g")])), Comment(wrap([Text("h")]))])
            ), Template(wrap([Text("i")]), params=[Parameter(wrap([Text("j")]),
            wrap([HTMLEntity("nbsp", named=True)]))])])
        self.assertWikicodeEqual(valid, self.builder.build(test))

if __name__ == "__main__":
    unittest.main(verbosity=2)

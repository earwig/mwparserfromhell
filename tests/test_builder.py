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

from mwparserfromhell.compat import py3k
from mwparserfromhell.nodes import (Argument, Comment, ExternalLink, Heading,
                                    HTMLEntity, Tag, Template, Text, Wikilink)
from mwparserfromhell.nodes.extras import Attribute, Parameter
from mwparserfromhell.parser import tokens, ParserError
from mwparserfromhell.parser.builder import Builder

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestBuilder(TreeEqualityTestCase):
    """Tests for the builder, which turns tokens into Wikicode objects."""

    def setUp(self):
        self.builder = Builder()

    def test_text(self):
        """tests for building Text nodes"""
        tests = [
            ([tokens.Text(text="foobar")], wraptext("foobar")),
            ([tokens.Text(text="fóóbar")], wraptext("fóóbar")),
            ([tokens.Text(text="spam"), tokens.Text(text="eggs")],
             wraptext("spam", "eggs")),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_template(self):
        """tests for building Template nodes"""
        tests = [
            ([tokens.TemplateOpen(), tokens.Text(text="foobar"),
              tokens.TemplateClose()],
             wrap([Template(wraptext("foobar"))])),

            ([tokens.TemplateOpen(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.TemplateClose()],
             wrap([Template(wraptext("spam", "eggs"))])),

            ([tokens.TemplateOpen(), tokens.Text(text="foo"),
              tokens.TemplateParamSeparator(), tokens.Text(text="bar"),
              tokens.TemplateClose()],
             wrap([Template(wraptext("foo"), params=[
                 Parameter(wraptext("1"), wraptext("bar"), showkey=False)])])),

            ([tokens.TemplateOpen(), tokens.Text(text="foo"),
              tokens.TemplateParamSeparator(), tokens.Text(text="bar"),
              tokens.TemplateParamEquals(), tokens.Text(text="baz"),
              tokens.TemplateClose()],
             wrap([Template(wraptext("foo"), params=[
                 Parameter(wraptext("bar"), wraptext("baz"))])])),

            ([tokens.TemplateOpen(), tokens.TemplateParamSeparator(),
              tokens.TemplateParamSeparator(), tokens.TemplateParamEquals(),
              tokens.TemplateParamSeparator(), tokens.TemplateClose()],
             wrap([Template(wrap([]), params=[
                 Parameter(wraptext("1"), wrap([]), showkey=False),
                 Parameter(wrap([]), wrap([]), showkey=True),
                 Parameter(wraptext("2"), wrap([]), showkey=False)])])),

            ([tokens.TemplateOpen(), tokens.Text(text="foo"),
              tokens.TemplateParamSeparator(), tokens.Text(text="bar"),
              tokens.TemplateParamEquals(), tokens.Text(text="baz"),
              tokens.TemplateParamSeparator(), tokens.Text(text="biz"),
              tokens.TemplateParamSeparator(), tokens.Text(text="buzz"),
              tokens.TemplateParamSeparator(), tokens.Text(text="3"),
              tokens.TemplateParamEquals(), tokens.Text(text="buff"),
              tokens.TemplateParamSeparator(), tokens.Text(text="baff"),
              tokens.TemplateClose()],
             wrap([Template(wraptext("foo"), params=[
                 Parameter(wraptext("bar"), wraptext("baz")),
                 Parameter(wraptext("1"), wraptext("biz"), showkey=False),
                 Parameter(wraptext("2"), wraptext("buzz"), showkey=False),
                 Parameter(wraptext("3"), wraptext("buff")),
                 Parameter(wraptext("3"), wraptext("baff"),
                           showkey=False)])])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_argument(self):
        """tests for building Argument nodes"""
        tests = [
            ([tokens.ArgumentOpen(), tokens.Text(text="foobar"),
              tokens.ArgumentClose()],
             wrap([Argument(wraptext("foobar"))])),

            ([tokens.ArgumentOpen(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.ArgumentClose()],
             wrap([Argument(wraptext("spam", "eggs"))])),

            ([tokens.ArgumentOpen(), tokens.Text(text="foo"),
              tokens.ArgumentSeparator(), tokens.Text(text="bar"),
              tokens.ArgumentClose()],
             wrap([Argument(wraptext("foo"), wraptext("bar"))])),

            ([tokens.ArgumentOpen(), tokens.Text(text="foo"),
              tokens.Text(text="bar"), tokens.ArgumentSeparator(),
              tokens.Text(text="baz"), tokens.Text(text="biz"),
              tokens.ArgumentClose()],
             wrap([Argument(wraptext("foo", "bar"), wraptext("baz", "biz"))])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_wikilink(self):
        """tests for building Wikilink nodes"""
        tests = [
            ([tokens.WikilinkOpen(), tokens.Text(text="foobar"),
              tokens.WikilinkClose()],
             wrap([Wikilink(wraptext("foobar"))])),

            ([tokens.WikilinkOpen(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.WikilinkClose()],
             wrap([Wikilink(wraptext("spam", "eggs"))])),

            ([tokens.WikilinkOpen(), tokens.Text(text="foo"),
              tokens.WikilinkSeparator(), tokens.Text(text="bar"),
              tokens.WikilinkClose()],
             wrap([Wikilink(wraptext("foo"), wraptext("bar"))])),

            ([tokens.WikilinkOpen(), tokens.Text(text="foo"),
              tokens.Text(text="bar"), tokens.WikilinkSeparator(),
              tokens.Text(text="baz"), tokens.Text(text="biz"),
              tokens.WikilinkClose()],
             wrap([Wikilink(wraptext("foo", "bar"), wraptext("baz", "biz"))])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_external_link(self):
        """tests for building ExternalLink nodes"""
        tests = [
            ([tokens.ExternalLinkOpen(brackets=False),
              tokens.Text(text="http://example.com/"),
              tokens.ExternalLinkClose()],
             wrap([ExternalLink(wraptext("http://example.com/"),
                                brackets=False)])),

            ([tokens.ExternalLinkOpen(brackets=True),
              tokens.Text(text="http://example.com/"),
              tokens.ExternalLinkClose()],
             wrap([ExternalLink(wraptext("http://example.com/"))])),

            ([tokens.ExternalLinkOpen(brackets=True),
              tokens.Text(text="http://example.com/"),
              tokens.ExternalLinkSeparator(), tokens.ExternalLinkClose()],
             wrap([ExternalLink(wraptext("http://example.com/"), wrap([]))])),

            ([tokens.ExternalLinkOpen(brackets=True),
              tokens.Text(text="http://example.com/"),
              tokens.ExternalLinkSeparator(), tokens.Text(text="Example"),
              tokens.ExternalLinkClose()],
             wrap([ExternalLink(wraptext("http://example.com/"),
                                wraptext("Example"))])),

            ([tokens.ExternalLinkOpen(brackets=False),
              tokens.Text(text="http://example"), tokens.Text(text=".com/foo"),
              tokens.ExternalLinkClose()],
             wrap([ExternalLink(wraptext("http://example", ".com/foo"),
                                brackets=False)])),

            ([tokens.ExternalLinkOpen(brackets=True),
              tokens.Text(text="http://example"), tokens.Text(text=".com/foo"),
              tokens.ExternalLinkSeparator(), tokens.Text(text="Example"),
              tokens.Text(text=" Web Page"), tokens.ExternalLinkClose()],
             wrap([ExternalLink(wraptext("http://example", ".com/foo"),
                                wraptext("Example", " Web Page"))])),
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
             wrap([Heading(wraptext("foobar"), 2)])),

            ([tokens.HeadingStart(level=4), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.HeadingEnd()],
             wrap([Heading(wraptext("spam", "eggs"), 4)])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_comment(self):
        """tests for building Comment nodes"""
        tests = [
            ([tokens.CommentStart(), tokens.Text(text="foobar"),
              tokens.CommentEnd()],
             wrap([Comment(wraptext("foobar"))])),

            ([tokens.CommentStart(), tokens.Text(text="spam"),
              tokens.Text(text="eggs"), tokens.CommentEnd()],
             wrap([Comment(wraptext("spam", "eggs"))])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_tag(self):
        """tests for building Tag nodes"""
        tests = [
            # <ref></ref>
            ([tokens.TagOpenOpen(), tokens.Text(text="ref"),
              tokens.TagCloseOpen(padding=""), tokens.TagOpenClose(),
              tokens.Text(text="ref"), tokens.TagCloseClose()],
             wrap([Tag(wraptext("ref"), wrap([]),
                       closing_tag=wraptext("ref"))])),

            # <ref name></ref>
            ([tokens.TagOpenOpen(), tokens.Text(text="ref"),
              tokens.TagAttrStart(pad_first=" ", pad_before_eq="",
                                  pad_after_eq=""),
              tokens.Text(text="name"), tokens.TagCloseOpen(padding=""),
              tokens.TagOpenClose(), tokens.Text(text="ref"),
              tokens.TagCloseClose()],
             wrap([Tag(wraptext("ref"), wrap([]),
                      attrs=[Attribute(wraptext("name"))])])),

            # <ref name="abc" />
            ([tokens.TagOpenOpen(), tokens.Text(text="ref"),
              tokens.TagAttrStart(pad_first=" ", pad_before_eq="",
                                  pad_after_eq=""),
              tokens.Text(text="name"), tokens.TagAttrEquals(),
              tokens.TagAttrQuote(char='"'), tokens.Text(text="abc"),
              tokens.TagCloseSelfclose(padding=" ")],
             wrap([Tag(wraptext("ref"),
                       attrs=[Attribute(wraptext("name"), wraptext("abc"))],
                       self_closing=True, padding=" ")])),

            # <br/>
            ([tokens.TagOpenOpen(), tokens.Text(text="br"),
              tokens.TagCloseSelfclose(padding="")],
             wrap([Tag(wraptext("br"), self_closing=True)])),

            # <li>
            ([tokens.TagOpenOpen(), tokens.Text(text="li"),
              tokens.TagCloseSelfclose(padding="", implicit=True)],
             wrap([Tag(wraptext("li"), self_closing=True, implicit=True)])),

            # </br>
            ([tokens.TagOpenOpen(invalid=True), tokens.Text(text="br"),
              tokens.TagCloseSelfclose(padding="", implicit=True)],
             wrap([Tag(wraptext("br"), self_closing=True, invalid=True,
                       implicit=True)])),

            # </br/>
            ([tokens.TagOpenOpen(invalid=True), tokens.Text(text="br"),
              tokens.TagCloseSelfclose(padding="")],
             wrap([Tag(wraptext("br"), self_closing=True, invalid=True)])),

            # <ref name={{abc}}   foo="bar {{baz}}" abc={{de}}f ghi=j{{k}}{{l}}
            #      mno =  '{{p}} [[q]] {{r}}'>[[Source]]</ref>
            ([tokens.TagOpenOpen(), tokens.Text(text="ref"),
              tokens.TagAttrStart(pad_first=" ", pad_before_eq="",
                                  pad_after_eq=""),
              tokens.Text(text="name"), tokens.TagAttrEquals(),
              tokens.TemplateOpen(), tokens.Text(text="abc"),
              tokens.TemplateClose(),
              tokens.TagAttrStart(pad_first="   ", pad_before_eq="",
                                  pad_after_eq=""),
              tokens.Text(text="foo"), tokens.TagAttrEquals(),
              tokens.TagAttrQuote(char='"'), tokens.Text(text="bar "),
              tokens.TemplateOpen(), tokens.Text(text="baz"),
              tokens.TemplateClose(),
              tokens.TagAttrStart(pad_first=" ", pad_before_eq="",
                                  pad_after_eq=""),
              tokens.Text(text="abc"), tokens.TagAttrEquals(),
              tokens.TemplateOpen(), tokens.Text(text="de"),
              tokens.TemplateClose(), tokens.Text(text="f"),
              tokens.TagAttrStart(pad_first=" ", pad_before_eq="",
                                  pad_after_eq=""),
              tokens.Text(text="ghi"), tokens.TagAttrEquals(),
              tokens.Text(text="j"), tokens.TemplateOpen(),
              tokens.Text(text="k"), tokens.TemplateClose(),
              tokens.TemplateOpen(), tokens.Text(text="l"),
              tokens.TemplateClose(),
              tokens.TagAttrStart(pad_first=" \n ", pad_before_eq=" ",
                                  pad_after_eq="  "),
              tokens.Text(text="mno"), tokens.TagAttrEquals(),
              tokens.TagAttrQuote(char="'"), tokens.TemplateOpen(),
              tokens.Text(text="p"), tokens.TemplateClose(),
              tokens.Text(text=" "), tokens.WikilinkOpen(),
              tokens.Text(text="q"), tokens.WikilinkClose(),
              tokens.Text(text=" "), tokens.TemplateOpen(),
              tokens.Text(text="r"), tokens.TemplateClose(),
              tokens.TagCloseOpen(padding=""), tokens.WikilinkOpen(),
              tokens.Text(text="Source"), tokens.WikilinkClose(),
              tokens.TagOpenClose(), tokens.Text(text="ref"),
              tokens.TagCloseClose()],
             wrap([Tag(wraptext("ref"), wrap([Wikilink(wraptext("Source"))]), [
                    Attribute(wraptext("name"),
                              wrap([Template(wraptext("abc"))]), None),
                    Attribute(wraptext("foo"), wrap([Text("bar "),
                              Template(wraptext("baz"))]), pad_first="   "),
                    Attribute(wraptext("abc"), wrap([Template(wraptext("de")),
                              Text("f")]), None),
                    Attribute(wraptext("ghi"), wrap([Text("j"),
                              Template(wraptext("k")),
                              Template(wraptext("l"))]), None),
                    Attribute(wraptext("mno"), wrap([Template(wraptext("p")),
                              Text(" "), Wikilink(wraptext("q")), Text(" "),
                              Template(wraptext("r"))]), "'", " \n ", " ",
                              "  ")])])),

            # "''italic text''"
            ([tokens.TagOpenOpen(wiki_markup="''"), tokens.Text(text="i"),
              tokens.TagCloseOpen(), tokens.Text(text="italic text"),
              tokens.TagOpenClose(), tokens.Text(text="i"),
              tokens.TagCloseClose()],
             wrap([Tag(wraptext("i"), wraptext("italic text"),
                       wiki_markup="''")])),

            # * bullet
            ([tokens.TagOpenOpen(wiki_markup="*"), tokens.Text(text="li"),
              tokens.TagCloseSelfclose(), tokens.Text(text=" bullet")],
             wrap([Tag(wraptext("li"), wiki_markup="*", self_closing=True),
                   Text(" bullet")])),
        ]
        for test, valid in tests:
            self.assertWikicodeEqual(valid, self.builder.build(test))

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
            [Template(wrap([Template(wrap([Template(wrap([Template(wraptext(
            "foo")), Text("bar")]), params=[Parameter(wraptext("baz"),
            wraptext("biz"))]), Text("buzz")])), Text("usr")]), params=[
            Parameter(wraptext("1"), wrap([Template(wraptext("bin"))]),
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
            [Template(wraptext("a"), params=[Parameter(wraptext("1"), wraptext(
            "b"), showkey=False), Parameter(wraptext("2"), wrap([Template(
            wraptext("c"), params=[Parameter(wraptext("1"), wrap([Wikilink(
            wraptext("d")), Argument(wraptext("e"))]), showkey=False)])]),
            showkey=False)]), Wikilink(wraptext("f"), wrap([Argument(wraptext(
            "g")), Comment(wraptext("h"))])), Template(wraptext("i"), params=[
            Parameter(wraptext("j"), wrap([HTMLEntity("nbsp",
            named=True)]))])])
        self.assertWikicodeEqual(valid, self.builder.build(test))

    def test_parser_errors(self):
        """test whether ParserError gets thrown for bad input"""
        missing_closes = [
            [tokens.TemplateOpen(), tokens.TemplateParamSeparator()],
            [tokens.TemplateOpen()], [tokens.ArgumentOpen()],
            [tokens.WikilinkOpen()], [tokens.ExternalLinkOpen()],
            [tokens.HeadingStart()], [tokens.CommentStart()],
            [tokens.TagOpenOpen(), tokens.TagAttrStart()],
            [tokens.TagOpenOpen()]
        ]

        func = self.assertRaisesRegex if py3k else self.assertRaisesRegexp
        msg = r"_handle_token\(\) got unexpected TemplateClose"
        func(ParserError, msg, self.builder.build, [tokens.TemplateClose()])
        for test in missing_closes:
            self.assertRaises(ParserError, self.builder.build, test)

if __name__ == "__main__":
    unittest.main(verbosity=2)

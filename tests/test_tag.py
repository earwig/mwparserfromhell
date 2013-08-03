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

from mwparserfromhell.compat import str
from mwparserfromhell.nodes import Tag, Template, Text
from mwparserfromhell.nodes.extras import Attribute
from ._test_tree_equality import TreeEqualityTestCase, getnodes, wrap, wraptext

agen = lambda name, value: Attribute(wraptext(name), wraptext(value))
agennq = lambda name, value: Attribute(wraptext(name), wraptext(value), False)
agenpnv = lambda name, a, b, c: Attribute(wraptext(name), None, True, a, b, c)

class TestTag(TreeEqualityTestCase):
    """Test cases for the Tag node."""

    def test_unicode(self):
        """test Tag.__unicode__()"""
        node1 = Tag(wraptext("ref"))
        node2 = Tag(wraptext("span"), wraptext("foo"),
                    [agen("style", "color: red;")])
        node3 = Tag(wraptext("ref"),
                    attrs=[agennq("name", "foo"),
                           agenpnv("some_attr", "   ", "", "")],
                    self_closing=True)
        node4 = Tag(wraptext("br"), self_closing=True, padding=" ")
        node5 = Tag(wraptext("br"), self_closing=True, implicit=True)
        node6 = Tag(wraptext("br"), self_closing=True, invalid=True,
                    implicit=True)
        node7 = Tag(wraptext("br"), self_closing=True, invalid=True,
                    padding=" ")
        node8 = Tag(wraptext("hr"), showtag=False, self_closing=True)
        node9 = Tag(wraptext("i"), wraptext("italics!"), showtag=False)

        self.assertEqual("<ref></ref>", str(node1))
        self.assertEqual('<span style="color: red;">foo</span>', str(node2))
        self.assertEqual("<ref name=foo   some_attr/>", str(node3))
        self.assertEqual("<br />", str(node4))
        self.assertEqual("<br>", str(node5))
        self.assertEqual("</br>", str(node6))
        self.assertEqual("</br />", str(node7))
        self.assertEqual("----", str(node8))
        self.assertEqual("''italics!''", str(node9))

    def test_iternodes(self):
        """test Tag.__iternodes__()"""
        node1n1, node1n2 = Text("ref"), Text("foobar")
        node2n1, node3n1, node3n2 = Text("bold text"), Text("img"), Text("id")
        node3n3, node3n4, node3n5 = Text("foo"), Text("class"), Text("bar")

        # <ref>foobar</ref>
        node1 = Tag(wrap([node1n1]), wrap([node1n2]))
        # '''bold text'''
        node2 = Tag(wraptext("i"), wrap([node2n1]), showtag=False)
        # <img id="foo" class="bar" />
        node3 = Tag(wrap([node3n1]),
                    attrs=[Attribute(wrap([node3n2]), wrap([node3n3])),
                           Attribute(wrap([node3n4]), wrap([node3n5]))],
                    self_closing=True, padding=" ")

        gen1 = node1.__iternodes__(getnodes)
        gen2 = node2.__iternodes__(getnodes)
        gen3 = node3.__iternodes__(getnodes)
        self.assertEqual((None, node1), next(gen1))
        self.assertEqual((None, node2), next(gen2))
        self.assertEqual((None, node3), next(gen3))
        self.assertEqual((node1.tag, node1n1), next(gen1))
        self.assertEqual((node3.tag, node3n1), next(gen3))
        self.assertEqual((node3.attributes[0].name, node3n2), next(gen3))
        self.assertEqual((node3.attributes[0].value, node3n3), next(gen3))
        self.assertEqual((node3.attributes[1].name, node3n4), next(gen3))
        self.assertEqual((node3.attributes[1].value, node3n5), next(gen3))
        self.assertEqual((node1.contents, node1n2), next(gen1))
        self.assertEqual((node2.contents, node2n1), next(gen2))
        self.assertEqual((node1.closing_tag, node1n1), next(gen1))
        self.assertRaises(StopIteration, next, gen1)
        self.assertRaises(StopIteration, next, gen2)
        self.assertRaises(StopIteration, next, gen3)

    def test_strip(self):
        """test Tag.__strip__()"""
        node1 = Tag(wraptext("i"), wraptext("foobar"))
        node2 = Tag(wraptext("math"), wraptext("foobar"))
        node3 = Tag(wraptext("br"), self_closing=True)
        for a in (True, False):
            for b in (True, False):
                self.assertEqual("foobar", node1.__strip__(a, b))
                self.assertEqual(None, node2.__strip__(a, b))
                self.assertEqual(None, node3.__strip__(a, b))

    def test_showtree(self):
        """test Tag.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = Tag(wraptext("ref"), wraptext("text"), [agen("name", "foo")])
        node2 = Tag(wraptext("br"), self_closing=True, padding=" ")
        node3 = Tag(wraptext("br"), self_closing=True, invalid=True,
                    implicit=True, padding=" ")
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        node3.__showtree__(output.append, get, mark)
        valid = [
            "<", (getter, node1.tag), (getter, node1.attributes[0].name),
            "    = ", marker, (getter, node1.attributes[0].value), ">",
            (getter, node1.contents), "</", (getter, node1.closing_tag), ">",
            "<", (getter, node2.tag), "/>", "</", (getter, node3.tag), ">"]
        self.assertEqual(valid, output)

    def test_tag(self):
        """test getter/setter for the tag attribute"""
        tag = wraptext("ref")
        node = Tag(tag, wraptext("text"))
        self.assertIs(tag, node.tag)
        self.assertIs(tag, node.closing_tag)
        node.tag = "span"
        self.assertWikicodeEqual(wraptext("span"), node.tag)
        self.assertWikicodeEqual(wraptext("span"), node.closing_tag)
        self.assertEqual("<span>text</span>", node)

    def test_contents(self):
        """test getter/setter for the contents attribute"""
        contents = wraptext("text")
        node = Tag(wraptext("ref"), contents)
        self.assertIs(contents, node.contents)
        node.contents = "text and a {{template}}"
        parsed = wrap([Text("text and a "), Template(wraptext("template"))])
        self.assertWikicodeEqual(parsed, node.contents)
        self.assertEqual("<ref>text and a {{template}}</ref>", node)

    def test_attributes(self):
        """test getter for the attributes attribute"""
        attrs = [agen("name", "bar")]
        node1 = Tag(wraptext("ref"), wraptext("foo"))
        node2 = Tag(wraptext("ref"), wraptext("foo"), attrs)
        self.assertEqual([], node1.attributes)
        self.assertIs(attrs, node2.attributes)

    def test_showtag(self):
        """test getter/setter for the showtag attribute"""
        node = Tag(wraptext("i"), wraptext("italic text"))
        self.assertTrue(node.showtag)
        node.showtag = False
        self.assertFalse(node.showtag)
        self.assertEqual("''italic text''", node)
        node.showtag = 1
        self.assertTrue(node.showtag)
        self.assertEqual("<i>italic text</i>", node)

    def test_self_closing(self):
        """test getter/setter for the self_closing attribute"""
        node = Tag(wraptext("ref"), wraptext("foobar"))
        self.assertFalse(node.self_closing)
        node.self_closing = True
        self.assertTrue(node.self_closing)
        self.assertEqual("<ref/>", node)
        node.self_closing = 0
        self.assertFalse(node.self_closing)
        self.assertEqual("<ref>foobar</ref>", node)

    def test_invalid(self):
        """test getter/setter for the invalid attribute"""
        node = Tag(wraptext("br"), self_closing=True, implicit=True)
        self.assertFalse(node.invalid)
        node.invalid = True
        self.assertTrue(node.invalid)
        self.assertEqual("</br>", node)
        node.invalid = 0
        self.assertFalse(node.invalid)
        self.assertEqual("<br>", node)

    def test_implicit(self):
        """test getter/setter for the implicit attribute"""
        node = Tag(wraptext("br"), self_closing=True)
        self.assertFalse(node.implicit)
        node.implicit = True
        self.assertTrue(node.implicit)
        self.assertEqual("<br>", node)
        node.implicit = 0
        self.assertFalse(node.implicit)
        self.assertEqual("<br/>", node)

    def test_padding(self):
        """test getter/setter for the padding attribute"""
        node = Tag(wraptext("ref"), wraptext("foobar"))
        self.assertEqual("", node.padding)
        node.padding = "  "
        self.assertEqual("  ", node.padding)
        self.assertEqual("<ref  >foobar</ref>", node)
        node.padding = None
        self.assertEqual("", node.padding)
        self.assertEqual("<ref>foobar</ref>", node)
        self.assertRaises(ValueError, setattr, node, "padding", True)

    def test_closing_tag(self):
        """test getter/setter for the closing_tag attribute"""
        tag = wraptext("ref")
        node = Tag(tag, wraptext("foobar"))
        self.assertIs(tag, node.closing_tag)
        node.closing_tag = "ref {{ignore me}}"
        parsed = wrap([Text("ref "), Template(wraptext("ignore me"))])
        self.assertWikicodeEqual(parsed, node.closing_tag)
        self.assertEqual("<ref>foobar</ref {{ignore me}}>", node)

if __name__ == "__main__":
    unittest.main(verbosity=2)

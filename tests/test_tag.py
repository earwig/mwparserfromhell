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
from mwparserfromhell.nodes import Tag, Template, Text
from mwparserfromhell.nodes.extras import Attribute
from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

agen = lambda name, value: Attribute(wraptext(name), wraptext(value))
agennv = lambda name: Attribute(wraptext(name))
agennq = lambda name, value: Attribute(wraptext(name), wraptext(value), None)
agenp = lambda name, v, a, b, c: Attribute(wraptext(name), v, '"', a, b, c)
agenpnv = lambda name, a, b, c: Attribute(wraptext(name), None, '"', a, b, c)

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
        node8 = Tag(wraptext("hr"), wiki_markup="----", self_closing=True)
        node9 = Tag(wraptext("i"), wraptext("italics!"), wiki_markup="''")

        self.assertEqual("<ref></ref>", str(node1))
        self.assertEqual('<span style="color: red;">foo</span>', str(node2))
        self.assertEqual("<ref name=foo   some_attr/>", str(node3))
        self.assertEqual("<br />", str(node4))
        self.assertEqual("<br>", str(node5))
        self.assertEqual("</br>", str(node6))
        self.assertEqual("</br />", str(node7))
        self.assertEqual("----", str(node8))
        self.assertEqual("''italics!''", str(node9))

    def test_children(self):
        """test Tag.__children__()"""
        # <ref>foobar</ref>
        node1 = Tag(wraptext("ref"), wraptext("foobar"))
        # '''bold text'''
        node2 = Tag(wraptext("b"), wraptext("bold text"), wiki_markup="'''")
        # <img id="foo" class="bar" selected />
        node3 = Tag(wraptext("img"),
                    attrs=[agen("id", "foo"), agen("class", "bar"),
                           agennv("selected")],
                    self_closing=True, padding=" ")

        gen1 = node1.__children__()
        gen2 = node2.__children__()
        gen3 = node3.__children__()
        self.assertEqual(node1.tag, next(gen1))
        self.assertEqual(node3.tag, next(gen3))
        self.assertEqual(node3.attributes[0].name, next(gen3))
        self.assertEqual(node3.attributes[0].value, next(gen3))
        self.assertEqual(node3.attributes[1].name, next(gen3))
        self.assertEqual(node3.attributes[1].value, next(gen3))
        self.assertEqual(node3.attributes[2].name, next(gen3))
        self.assertEqual(node1.contents, next(gen1))
        self.assertEqual(node2.contents, next(gen2))
        self.assertEqual(node1.closing_tag, next(gen1))
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
        node1 = Tag(wraptext("ref"), wraptext("text"),
                    [agen("name", "foo"), agennv("selected")])
        node2 = Tag(wraptext("br"), self_closing=True, padding=" ")
        node3 = Tag(wraptext("br"), self_closing=True, invalid=True,
                    implicit=True, padding=" ")
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        node3.__showtree__(output.append, get, mark)
        valid = [
            "<", (getter, node1.tag), (getter, node1.attributes[0].name),
            "    = ", marker, (getter, node1.attributes[0].value),
            (getter, node1.attributes[1].name), ">", (getter, node1.contents),
            "</", (getter, node1.closing_tag), ">", "<", (getter, node2.tag),
            "/>", "</", (getter, node3.tag), ">"]
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

    def test_wiki_markup(self):
        """test getter/setter for the wiki_markup attribute"""
        node = Tag(wraptext("i"), wraptext("italic text"))
        self.assertIs(None, node.wiki_markup)
        node.wiki_markup = "''"
        self.assertEqual("''", node.wiki_markup)
        self.assertEqual("''italic text''", node)
        node.wiki_markup = False
        self.assertFalse(node.wiki_markup)
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

    def test_wiki_style_separator(self):
        """test getter/setter for wiki_style_separator attribute"""
        node = Tag(wraptext("table"), wraptext("\n"))
        self.assertIs(None, node.wiki_style_separator)
        node.wiki_style_separator = "|"
        self.assertEqual("|", node.wiki_style_separator)
        node.wiki_markup = "{"
        self.assertEqual("{|\n{", node)
        node2 = Tag(wraptext("table"), wraptext("\n"), wiki_style_separator="|")
        self.assertEqual("|", node.wiki_style_separator)

    def test_closing_wiki_markup(self):
        """test getter/setter for closing_wiki_markup attribute"""
        node = Tag(wraptext("table"), wraptext("\n"))
        self.assertIs(None, node.closing_wiki_markup)
        node.wiki_markup = "{|"
        self.assertEqual("{|", node.closing_wiki_markup)
        node.closing_wiki_markup = "|}"
        self.assertEqual("|}", node.closing_wiki_markup)
        self.assertEqual("{|\n|}", node)
        node.wiki_markup = "!!"
        self.assertEqual("|}", node.closing_wiki_markup)
        self.assertEqual("!!\n|}", node)
        node.wiki_markup = False
        self.assertFalse(node.closing_wiki_markup)
        self.assertEqual("<table>\n</table>", node)
        node2 = Tag(wraptext("table"), wraptext("\n"),
                    attrs=[agen("id", "foo")], wiki_markup="{|",
                    closing_wiki_markup="|}")
        self.assertEqual("|}", node2.closing_wiki_markup)
        self.assertEqual('{| id="foo"\n|}', node2)

    def test_has(self):
        """test Tag.has()"""
        node = Tag(wraptext("ref"), wraptext("cite"), [agen("name", "foo")])
        self.assertTrue(node.has("name"))
        self.assertTrue(node.has("  name  "))
        self.assertTrue(node.has(wraptext("name")))
        self.assertFalse(node.has("Name"))
        self.assertFalse(node.has("foo"))

        attrs = [agen("id", "foo"), agenp("class", "bar", "  ", "\n", "\n"),
                 agen("foo", "bar"), agenpnv("foo", " ", "  \n ", " \t")]
        node2 = Tag(wraptext("div"), attrs=attrs, self_closing=True)
        self.assertTrue(node2.has("id"))
        self.assertTrue(node2.has("class"))
        self.assertTrue(node2.has(attrs[1].pad_first + str(attrs[1].name) +
                                  attrs[1].pad_before_eq))
        self.assertTrue(node2.has(attrs[3]))
        self.assertTrue(node2.has(str(attrs[3])))
        self.assertFalse(node2.has("idclass"))
        self.assertFalse(node2.has("id class"))
        self.assertFalse(node2.has("id=foo"))

    def test_get(self):
        """test Tag.get()"""
        attrs = [agen("name", "foo")]
        node = Tag(wraptext("ref"), wraptext("cite"), attrs)
        self.assertIs(attrs[0], node.get("name"))
        self.assertIs(attrs[0], node.get("  name  "))
        self.assertIs(attrs[0], node.get(wraptext("name")))
        self.assertRaises(ValueError, node.get, "Name")
        self.assertRaises(ValueError, node.get, "foo")

        attrs = [agen("id", "foo"), agenp("class", "bar", "  ", "\n", "\n"),
                 agen("foo", "bar"), agenpnv("foo", " ", "  \n ", " \t")]
        node2 = Tag(wraptext("div"), attrs=attrs, self_closing=True)
        self.assertIs(attrs[0], node2.get("id"))
        self.assertIs(attrs[1], node2.get("class"))
        self.assertIs(attrs[1], node2.get(
            attrs[1].pad_first + str(attrs[1].name) + attrs[1].pad_before_eq))
        self.assertIs(attrs[3], node2.get(attrs[3]))
        self.assertIs(attrs[3], node2.get(str(attrs[3])))
        self.assertIs(attrs[3], node2.get(" foo"))
        self.assertRaises(ValueError, node2.get, "idclass")
        self.assertRaises(ValueError, node2.get, "id class")
        self.assertRaises(ValueError, node2.get, "id=foo")

    def test_add(self):
        """test Tag.add()"""
        node = Tag(wraptext("ref"), wraptext("cite"))
        node.add("name", "value")
        node.add("name", "value", quotes=None)
        node.add("name", "value", quotes="'")
        node.add("name")
        node.add(1, False)
        node.add("style", "{{foobar}}")
        node.add("name", "value", '"', "\n", " ", "   ")
        attr1 = ' name="value"'
        attr2 = " name=value"
        attr3 = " name='value'"
        attr4 = " name"
        attr5 = ' 1="False"'
        attr6 = ' style="{{foobar}}"'
        attr7 = '\nname =   "value"'
        self.assertEqual(attr1, node.attributes[0])
        self.assertEqual(attr2, node.attributes[1])
        self.assertEqual(attr3, node.attributes[2])
        self.assertEqual(attr4, node.attributes[3])
        self.assertEqual(attr5, node.attributes[4])
        self.assertEqual(attr6, node.attributes[5])
        self.assertEqual(attr7, node.attributes[6])
        self.assertEqual(attr7, node.get("name"))
        self.assertWikicodeEqual(wrap([Template(wraptext("foobar"))]),
                                 node.attributes[5].value)
        self.assertEqual("".join(("<ref", attr1, attr2, attr3, attr4, attr5,
                                  attr6, attr7, ">cite</ref>")), node)
        self.assertRaises(ValueError, node.add, "name", "foo", quotes="bar")
        self.assertRaises(ValueError, node.add, "name", "a bc d", quotes=None)

    def test_remove(self):
        """test Tag.remove()"""
        attrs = [agen("id", "foo"), agenp("class", "bar", "  ", "\n", "\n"),
                 agen("foo", "bar"), agenpnv("foo", " ", "  \n ", " \t")]
        node = Tag(wraptext("div"), attrs=attrs, self_closing=True)
        node.remove("class")
        self.assertEqual('<div id="foo" foo="bar" foo  \n />', node)
        node.remove("foo")
        self.assertEqual('<div id="foo"/>', node)
        self.assertRaises(ValueError, node.remove, "foo")
        node.remove("id")
        self.assertEqual('<div/>', node)

if __name__ == "__main__":
    unittest.main(verbosity=2)

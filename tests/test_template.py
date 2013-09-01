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
from mwparserfromhell.nodes import HTMLEntity, Template, Text
from mwparserfromhell.nodes.extras import Parameter
from ._test_tree_equality import TreeEqualityTestCase, getnodes, wrap, wraptext

pgens = lambda k, v: Parameter(wraptext(k), wraptext(v), showkey=True)
pgenh = lambda k, v: Parameter(wraptext(k), wraptext(v), showkey=False)

class TestTemplate(TreeEqualityTestCase):
    """Test cases for the Template node."""

    def test_unicode(self):
        """test Template.__unicode__()"""
        node = Template(wraptext("foobar"))
        self.assertEqual("{{foobar}}", str(node))
        node2 = Template(wraptext("foo"),
                         [pgenh("1", "bar"), pgens("abc", "def")])
        self.assertEqual("{{foo|bar|abc=def}}", str(node2))

    def test_iternodes(self):
        """test Template.__iternodes__()"""
        node1n1 = Text("foobar")
        node2n1, node2n2, node2n3 = Text("foo"), Text("bar"), Text("abc")
        node2n4, node2n5 = Text("def"), Text("ghi")
        node2p1 = Parameter(wraptext("1"), wrap([node2n2]), showkey=False)
        node2p2 = Parameter(wrap([node2n3]), wrap([node2n4, node2n5]),
                            showkey=True)
        node1 = Template(wrap([node1n1]))
        node2 = Template(wrap([node2n1]), [node2p1, node2p2])

        gen1 = node1.__iternodes__(getnodes)
        gen2 = node2.__iternodes__(getnodes)
        self.assertEqual((None, node1), next(gen1))
        self.assertEqual((None, node2), next(gen2))
        self.assertEqual((node1.name, node1n1), next(gen1))
        self.assertEqual((node2.name, node2n1), next(gen2))
        self.assertEqual((node2.params[0].value, node2n2), next(gen2))
        self.assertEqual((node2.params[1].name, node2n3), next(gen2))
        self.assertEqual((node2.params[1].value, node2n4), next(gen2))
        self.assertEqual((node2.params[1].value, node2n5), next(gen2))
        self.assertRaises(StopIteration, next, gen1)
        self.assertRaises(StopIteration, next, gen2)

    def test_strip(self):
        """test Template.__strip__()"""
        node1 = Template(wraptext("foobar"))
        node2 = Template(wraptext("foo"),
                         [pgenh("1", "bar"), pgens("abc", "def")])
        for a in (True, False):
            for b in (True, False):
                self.assertEqual(None, node1.__strip__(a, b))
                self.assertEqual(None, node2.__strip__(a, b))

    def test_showtree(self):
        """test Template.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = Template(wraptext("foobar"))
        node2 = Template(wraptext("foo"),
                         [pgenh("1", "bar"), pgens("abc", "def")])
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        valid = [
            "{{", (getter, node1.name), "}}", "{{", (getter, node2.name),
            "    | ", marker, (getter, node2.params[0].name), "    = ", marker,
            (getter, node2.params[0].value), "    | ", marker,
            (getter, node2.params[1].name), "    = ", marker,
            (getter, node2.params[1].value), "}}"]
        self.assertEqual(valid, output)

    def test_name(self):
        """test getter/setter for the name attribute"""
        name = wraptext("foobar")
        node1 = Template(name)
        node2 = Template(name, [pgenh("1", "bar")])
        self.assertIs(name, node1.name)
        self.assertIs(name, node2.name)
        node1.name = "asdf"
        node2.name = "téstïng"
        self.assertWikicodeEqual(wraptext("asdf"), node1.name)
        self.assertWikicodeEqual(wraptext("téstïng"), node2.name)

    def test_params(self):
        """test getter for the params attribute"""
        node1 = Template(wraptext("foobar"))
        plist = [pgenh("1", "bar"), pgens("abc", "def")]
        node2 = Template(wraptext("foo"), plist)
        self.assertEqual([], node1.params)
        self.assertIs(plist, node2.params)

    def test_has(self):
        """test Template.has()"""
        node1 = Template(wraptext("foobar"))
        node2 = Template(wraptext("foo"),
                         [pgenh("1", "bar"), pgens("\nabc ", "def")])
        node3 = Template(wraptext("foo"),
                         [pgenh("1", "a"), pgens("b", "c"), pgens("1", "d")])
        node4 = Template(wraptext("foo"), [pgenh("1", "a"), pgens("b", " ")])
        self.assertFalse(node1.has("foobar"))
        self.assertTrue(node2.has(1))
        self.assertTrue(node2.has("abc"))
        self.assertFalse(node2.has("def"))
        self.assertTrue(node3.has("1"))
        self.assertTrue(node3.has(" b "))
        self.assertFalse(node4.has("b"))
        self.assertTrue(node3.has("b", False))
        self.assertTrue(node4.has("b", False))

    def test_get(self):
        """test Template.get()"""
        node1 = Template(wraptext("foobar"))
        node2p1 = pgenh("1", "bar")
        node2p2 = pgens("abc", "def")
        node2 = Template(wraptext("foo"), [node2p1, node2p2])
        node3p1 = pgens("b", "c")
        node3p2 = pgens("1", "d")
        node3 = Template(wraptext("foo"), [pgenh("1", "a"), node3p1, node3p2])
        node4p1 = pgens(" b", " ")
        node4 = Template(wraptext("foo"), [pgenh("1", "a"), node4p1])
        self.assertRaises(ValueError, node1.get, "foobar")
        self.assertIs(node2p1, node2.get(1))
        self.assertIs(node2p2, node2.get("abc"))
        self.assertRaises(ValueError, node2.get, "def")
        self.assertIs(node3p1, node3.get("b"))
        self.assertIs(node3p2, node3.get("1"))
        self.assertIs(node4p1, node4.get("b "))

    def test_add(self):
        """test Template.add()"""
        node1 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
        node2 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
        node3 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
        node4 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
        node5 = Template(wraptext("a"), [pgens("b", "c"),
                                         pgens("    d ", "e")])
        node6 = Template(wraptext("a"), [pgens("b", "c"), pgens("b", "d"),
                                         pgens("b", "e")])
        node7 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
        node8p = pgenh("1", "d")
        node8 = Template(wraptext("a"), [pgens("b", "c"), node8p])
        node9 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
        node10 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "e")])
        node11 = Template(wraptext("a"), [pgens("b", "c")])
        node12 = Template(wraptext("a"), [pgens("b", "c")])
        node13 = Template(wraptext("a"), [
            pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")])
        node14 = Template(wraptext("a\n"), [
            pgens("b ", "c\n"), pgens("d ", " e"), pgens("f ", "g\n"),
            pgens("h ", " i\n")])
        node15 = Template(wraptext("a"), [
            pgens("b  ", " c\n"), pgens("\nd  ", " e"), pgens("\nf  ", "g ")])
        node16 = Template(wraptext("a"), [
            pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")])
        node17 = Template(wraptext("a"), [
            pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")])
        node18 = Template(wraptext("a\n"), [
            pgens("b ", "c\n"), pgens("d ", " e"), pgens("f ", "g\n"),
            pgens("h ", " i\n")])
        node19 = Template(wraptext("a"), [
            pgens("b  ", " c\n"), pgens("\nd  ", " e"), pgens("\nf  ", "g ")])
        node20 = Template(wraptext("a"), [
            pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")])
        node21 = Template(wraptext("a"), [pgenh("1", "b")])
        node22 = Template(wraptext("a"), [pgenh("1", "b")])
        node23 = Template(wraptext("a"), [pgenh("1", "b")])
        node24 = Template(wraptext("a"), [pgenh("1", "b"), pgenh("2", "c"),
                                          pgenh("3", "d"), pgenh("4", "e")])
        node25 = Template(wraptext("a"), [pgenh("1", "b"), pgenh("2", "c"),
                                          pgens("4", "d"), pgens("5", "e")])
        node26 = Template(wraptext("a"), [pgenh("1", "b"), pgenh("2", "c"),
                                          pgens("4", "d"), pgens("5", "e")])
        node27 = Template(wraptext("a"), [pgenh("1", "b")])
        node28 = Template(wraptext("a"), [pgenh("1", "b")])
        node29 = Template(wraptext("a"), [pgens("b", "c")])
        node30 = Template(wraptext("a"), [pgenh("1", "b")])
        node31 = Template(wraptext("a"), [pgenh("1", "b")])
        node32 = Template(wraptext("a"), [pgens("1", "b")])
        node33 = Template(wraptext("a"), [
            pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")])
        node34 = Template(wraptext("a\n"), [
            pgens("b ", "c\n"), pgens("d ", " e"), pgens("f ", "g\n"),
            pgens("h ", " i\n")])
        node35 = Template(wraptext("a"), [
            pgens("b  ", " c\n"), pgens("\nd  ", " e"), pgens("\nf  ", "g ")])
        node36 = Template(wraptext("a"), [
            pgens("\nb ", " c "), pgens("\nd ", " e "), pgens("\nf ", " g ")])
        node37 = Template(wraptext("a"), [pgens("b", "c"), pgens("d", "e"),
                                          pgens("b", "f"), pgens("b", "h"),
                                          pgens("i", "j")])
        node37 = Template(wraptext("a"), [pgens("b", "c"), pgens("d", "e"),
                                          pgens("b", "f"), pgens("b", "h"),
                                          pgens("i", "j")])
        node38 = Template(wraptext("a"), [pgens("1", "b"), pgens("x", "y"),
                                          pgens("1", "c"), pgens("2", "d")])
        node39 = Template(wraptext("a"), [pgens("1", "b"), pgens("x", "y"),
                                          pgenh("1", "c"), pgenh("2", "d")])
        node40 = Template(wraptext("a"), [pgens("b", "c"), pgens("d", "e"),
                                          pgens("f", "g")])

        node1.add("e", "f", showkey=True)
        node2.add(2, "g", showkey=False)
        node3.add("e", "foo|bar", showkey=True)
        node4.add("e", "f", showkey=True, before="b")
        node5.add("f", "g", showkey=True, before=" d     ")
        node6.add("f", "g", showkey=True, before="b")
        self.assertRaises(ValueError, node7.add, "e", "f", showkey=True,
                          before="q")
        node8.add("e", "f", showkey=True, before=node8p)
        node9.add("e", "f", showkey=True, before=pgenh("1", "d"))
        self.assertRaises(ValueError, node10.add, "e", "f", showkey=True,
                          before=pgenh("1", "d"))
        node11.add("d", "foo=bar", showkey=True)
        node12.add("1", "foo=bar", showkey=False)
        node13.add("h", "i", showkey=True)
        node14.add("j", "k", showkey=True)
        node15.add("h", "i", showkey=True)
        node16.add("h", "i", showkey=True, preserve_spacing=False)
        node17.add("h", "i", showkey=False)
        node18.add("j", "k", showkey=False)
        node19.add("h", "i", showkey=False)
        node20.add("h", "i", showkey=False, preserve_spacing=False)
        node21.add("2", "c")
        node22.add("3", "c")
        node23.add("c", "d")
        node24.add("5", "f")
        node25.add("3", "f")
        node26.add("6", "f")
        node27.add("c", "foo=bar")
        node28.add("2", "foo=bar")
        node29.add("b", "d")
        node30.add("1", "foo=bar")
        node31.add("1", "foo=bar", showkey=True)
        node32.add("1", "foo=bar", showkey=False)
        node33.add("d", "foo")
        node34.add("f", "foo")
        node35.add("f", "foo")
        node36.add("d", "foo", preserve_spacing=False)
        node37.add("b", "k")
        node38.add("1", "e")
        node39.add("1", "e")
        node40.add("d", "h", before="b")

        self.assertEqual("{{a|b=c|d|e=f}}", node1)
        self.assertEqual("{{a|b=c|d|g}}", node2)
        self.assertEqual("{{a|b=c|d|e=foo&#124;bar}}", node3)
        self.assertIsInstance(node3.params[2].value.get(1), HTMLEntity)
        self.assertEqual("{{a|e=f|b=c|d}}", node4)
        self.assertEqual("{{a|b=c|f=g|    d =e}}", node5)
        self.assertEqual("{{a|b=c|b=d|f=g|b=e}}", node6)
        self.assertEqual("{{a|b=c|d}}", node7)
        self.assertEqual("{{a|b=c|e=f|d}}", node8)
        self.assertEqual("{{a|b=c|e=f|d}}", node9)
        self.assertEqual("{{a|b=c|e}}", node10)
        self.assertEqual("{{a|b=c|d=foo=bar}}", node11)
        self.assertEqual("{{a|b=c|foo&#61;bar}}", node12)
        self.assertIsInstance(node12.params[1].value.get(1), HTMLEntity)
        self.assertEqual("{{a|\nb = c|\nd = e|\nf = g|\nh = i}}", node13)
        self.assertEqual("{{a\n|b =c\n|d = e|f =g\n|h = i\n|j =k\n}}", node14)
        self.assertEqual("{{a|b  = c\n|\nd  = e|\nf  =g |h  =i}}", node15)
        self.assertEqual("{{a|\nb = c|\nd = e|\nf = g|h=i}}", node16)
        self.assertEqual("{{a|\nb = c|\nd = e|\nf = g| i}}", node17)
        self.assertEqual("{{a\n|b =c\n|d = e|f =g\n|h = i\n|k\n}}", node18)
        self.assertEqual("{{a|b  = c\n|\nd  = e|\nf  =g |i}}", node19)
        self.assertEqual("{{a|\nb = c|\nd = e|\nf = g|i}}", node20)
        self.assertEqual("{{a|b|c}}", node21)
        self.assertEqual("{{a|b|3=c}}", node22)
        self.assertEqual("{{a|b|c=d}}", node23)
        self.assertEqual("{{a|b|c|d|e|f}}", node24)
        self.assertEqual("{{a|b|c|4=d|5=e|f}}", node25)
        self.assertEqual("{{a|b|c|4=d|5=e|6=f}}", node26)
        self.assertEqual("{{a|b|c=foo=bar}}", node27)
        self.assertEqual("{{a|b|foo&#61;bar}}", node28)
        self.assertIsInstance(node28.params[1].value.get(1), HTMLEntity)
        self.assertEqual("{{a|b=d}}", node29)
        self.assertEqual("{{a|foo&#61;bar}}", node30)
        self.assertIsInstance(node30.params[0].value.get(1), HTMLEntity)
        self.assertEqual("{{a|1=foo=bar}}", node31)
        self.assertEqual("{{a|foo&#61;bar}}", node32)
        self.assertIsInstance(node32.params[0].value.get(1), HTMLEntity)
        self.assertEqual("{{a|\nb = c|\nd = foo|\nf = g}}", node33)
        self.assertEqual("{{a\n|b =c\n|d = e|f =foo\n|h = i\n}}", node34)
        self.assertEqual("{{a|b  = c\n|\nd  = e|\nf  =foo }}", node35)
        self.assertEqual("{{a|\nb = c |\nd =foo|\nf = g }}", node36)
        self.assertEqual("{{a|b=k|d=e|i=j}}", node37)
        self.assertEqual("{{a|1=e|x=y|2=d}}", node38)
        self.assertEqual("{{a|x=y|e|d}}", node39)
        self.assertEqual("{{a|b=c|d=h|f=g}}", node40)

    def test_remove(self):
        """test Template.remove()"""
        node1 = Template(wraptext("foobar"))
        node2 = Template(wraptext("foo"),
            [pgenh("1", "bar"), pgens("abc", "def")])
        node3 = Template(wraptext("foo"),
            [pgenh("1", "bar"), pgens("abc", "def")])
        node4 = Template(wraptext("foo"),
            [pgenh("1", "bar"), pgenh("2", "baz")])
        node5 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node6 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node7 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgens("  1", "b"), pgens("2", "c")])
        node8 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgens("  1", "b"), pgens("2", "c")])
        node9 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node10 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node11 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node12 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node13 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node14 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node15 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node16 = Template(wraptext("foo"), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node17 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node18 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node19 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node20 = Template(wraptext("foo"), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node21 = Template(wraptext("foo"), [
            pgens("a", "b"), pgens("c", "d"), pgens("e", "f"), pgens("a", "b"),
            pgens("a", "b")])
        node22 = Template(wraptext("foo"), [
            pgens("a", "b"), pgens("c", "d"), pgens("e", "f"), pgens("a", "b"),
            pgens("a", "b")])
        node23 = Template(wraptext("foo"), [
            pgens("a", "b"), pgens("c", "d"), pgens("e", "f"), pgens("a", "b"),
            pgens("a", "b")])
        node24 = Template(wraptext("foo"), [
            pgens("a", "b"), pgens("c", "d"), pgens("e", "f"), pgens("a", "b"),
            pgens("a", "b")])
        node25 = Template(wraptext("foo"), [
            pgens("a", "b"), pgens("c", "d"), pgens("e", "f"), pgens("a", "b"),
            pgens("a", "b")])
        node26 = Template(wraptext("foo"), [
            pgens("a", "b"), pgens("c", "d"), pgens("e", "f"), pgens("a", "b"),
            pgens("a", "b")])

        node2.remove("1")
        node2.remove("abc")
        node3.remove(1, keep_field=True)
        node3.remove("abc", keep_field=True)
        node4.remove("1", keep_field=False)
        node5.remove("a", keep_field=False)
        node6.remove("a", keep_field=True)
        node7.remove(1, keep_field=True)
        node8.remove(1, keep_field=False)
        node9.remove(1, keep_field=True)
        node10.remove(1, keep_field=False)
        node11.remove(node11.params[0], keep_field=False)
        node12.remove(node12.params[0], keep_field=True)
        node13.remove(node13.params[1], keep_field=False)
        node14.remove(node14.params[1], keep_field=True)
        node15.remove(node15.params[2], keep_field=False)
        node16.remove(node16.params[2], keep_field=True)
        node17.remove(node17.params[0], keep_field=False)
        node18.remove(node18.params[0], keep_field=True)
        node19.remove(node19.params[1], keep_field=False)
        node20.remove(node20.params[1], keep_field=True)
        node21.remove("a", keep_field=False)
        node22.remove("a", keep_field=True)
        node23.remove(node23.params[0], keep_field=False)
        node24.remove(node24.params[0], keep_field=True)
        node25.remove(node25.params[3], keep_field=False)
        node26.remove(node26.params[3], keep_field=True)

        self.assertRaises(ValueError, node1.remove, 1)
        self.assertRaises(ValueError, node1.remove, "a")
        self.assertRaises(ValueError, node2.remove, "1")
        self.assertEqual("{{foo}}", node2)
        self.assertEqual("{{foo||abc=}}", node3)
        self.assertEqual("{{foo||baz}}", node4)
        self.assertEqual("{{foo|b=c}}", node5)
        self.assertEqual("{{foo| a=|b=c}}", node6)
        self.assertEqual("{{foo|1  =|2=c}}", node7)
        self.assertEqual("{{foo|2=c}}", node8)
        self.assertEqual("{{foo||c}}", node9)
        self.assertEqual("{{foo||c}}", node10)
        self.assertEqual("{{foo|b=c|a =d}}", node11)
        self.assertEqual("{{foo| a=|b=c|a =d}}", node12)
        self.assertEqual("{{foo| a=b|a =d}}", node13)
        self.assertEqual("{{foo| a=b|b=|a =d}}", node14)
        self.assertEqual("{{foo| a=b|b=c}}", node15)
        self.assertEqual("{{foo| a=b|b=c|a =}}", node16)
        self.assertEqual("{{foo|b|c}}", node17)
        self.assertEqual("{{foo|1  =|b|c}}", node18)
        self.assertEqual("{{foo|1  =a||c}}", node19)
        self.assertEqual("{{foo|1  =a||c}}", node20)
        self.assertEqual("{{foo|c=d|e=f}}", node21)
        self.assertEqual("{{foo|a=|c=d|e=f}}", node22)
        self.assertEqual("{{foo|c=d|e=f|a=b|a=b}}", node23)
        self.assertEqual("{{foo|a=|c=d|e=f|a=b|a=b}}", node24)
        self.assertEqual("{{foo|a=b|c=d|e=f|a=b}}", node25)
        self.assertEqual("{{foo|a=b|c=d|e=f|a=|a=b}}", node26)

if __name__ == "__main__":
    unittest.main(verbosity=2)

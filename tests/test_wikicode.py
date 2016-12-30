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
from functools import partial
import re
from types import GeneratorType

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mwparserfromhell.compat import py3k, str
from mwparserfromhell.nodes import (Argument, Comment, Heading, HTMLEntity,
                                    Node, Tag, Template, Text, Wikilink)
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell import parse

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestWikicode(TreeEqualityTestCase):
    """Tests for the Wikicode class, which manages a list of nodes."""

    def test_unicode(self):
        """test Wikicode.__unicode__()"""
        code1 = parse("foobar")
        code2 = parse("Have a {{template}} and a [[page|link]]")
        self.assertEqual("foobar", str(code1))
        self.assertEqual("Have a {{template}} and a [[page|link]]", str(code2))

    def test_nodes(self):
        """test getter/setter for the nodes attribute"""
        code = parse("Have a {{template}}")
        self.assertEqual(["Have a ", "{{template}}"], code.nodes)
        L1 = SmartList([Text("foobar"), Template(wraptext("abc"))])
        L2 = [Text("barfoo"), Template(wraptext("cba"))]
        L3 = "abc{{def}}"
        code.nodes = L1
        self.assertIs(L1, code.nodes)
        code.nodes = L2
        self.assertIs(L2, code.nodes)
        code.nodes = L3
        self.assertEqual(["abc", "{{def}}"], code.nodes)
        self.assertRaises(ValueError, setattr, code, "nodes", object)

    def test_get(self):
        """test Wikicode.get()"""
        code = parse("Have a {{template}} and a [[page|link]]")
        self.assertIs(code.nodes[0], code.get(0))
        self.assertIs(code.nodes[2], code.get(2))
        self.assertRaises(IndexError, code.get, 4)

    def test_set(self):
        """test Wikicode.set()"""
        code = parse("Have a {{template}} and a [[page|link]]")
        code.set(1, "{{{argument}}}")
        self.assertEqual("Have a {{{argument}}} and a [[page|link]]", code)
        self.assertIsInstance(code.get(1), Argument)
        code.set(2, None)
        self.assertEqual("Have a {{{argument}}}[[page|link]]", code)
        code.set(-3, "This is an ")
        self.assertEqual("This is an {{{argument}}}[[page|link]]", code)
        self.assertRaises(ValueError, code.set, 1, "foo {{bar}}")
        self.assertRaises(IndexError, code.set, 3, "{{baz}}")
        self.assertRaises(IndexError, code.set, -4, "{{baz}}")

    def test_index(self):
        """test Wikicode.index()"""
        code = parse("Have a {{template}} and a [[page|link]]")
        self.assertEqual(0, code.index("Have a "))
        self.assertEqual(3, code.index("[[page|link]]"))
        self.assertEqual(1, code.index(code.get(1)))
        self.assertRaises(ValueError, code.index, "foo")

        code = parse("{{foo}}{{bar|{{baz}}}}")
        self.assertEqual(1, code.index("{{bar|{{baz}}}}"))
        self.assertEqual(1, code.index("{{baz}}", recursive=True))
        self.assertEqual(1, code.index(code.get(1).get(1).value,
                                       recursive=True))
        self.assertRaises(ValueError, code.index, "{{baz}}", recursive=False)
        self.assertRaises(ValueError, code.index,
                          code.get(1).get(1).value, recursive=False)

    def test_insert(self):
        """test Wikicode.insert()"""
        code = parse("Have a {{template}} and a [[page|link]]")
        code.insert(1, "{{{argument}}}")
        self.assertEqual(
            "Have a {{{argument}}}{{template}} and a [[page|link]]", code)
        self.assertIsInstance(code.get(1), Argument)
        code.insert(2, None)
        self.assertEqual(
            "Have a {{{argument}}}{{template}} and a [[page|link]]", code)
        code.insert(-3, Text("foo"))
        self.assertEqual(
            "Have a {{{argument}}}foo{{template}} and a [[page|link]]", code)

        code2 = parse("{{foo}}{{bar}}{{baz}}")
        code2.insert(1, "abc{{def}}ghi[[jk]]")
        self.assertEqual("{{foo}}abc{{def}}ghi[[jk]]{{bar}}{{baz}}", code2)
        self.assertEqual(["{{foo}}", "abc", "{{def}}", "ghi", "[[jk]]",
                          "{{bar}}", "{{baz}}"], code2.nodes)

        code3 = parse("{{foo}}bar")
        code3.insert(1000, "[[baz]]")
        code3.insert(-1000, "derp")
        self.assertEqual("derp{{foo}}bar[[baz]]", code3)

    def _test_search(self, meth, expected):
        """Base test for insert_before(), insert_after(), and replace()."""
        code = parse("{{a}}{{b}}{{c}}{{d}}{{e}}")
        func = partial(meth, code)
        func("{{b}}", "x", recursive=True)
        func("{{d}}", "[[y]]", recursive=False)
        func(code.get(2), "z")
        self.assertEqual(expected[0], code)
        self.assertRaises(ValueError, func, "{{r}}", "n", recursive=True)
        self.assertRaises(ValueError, func, "{{r}}", "n", recursive=False)
        fake = parse("{{a}}").get(0)
        self.assertRaises(ValueError, func, fake, "n", recursive=True)
        self.assertRaises(ValueError, func, fake, "n", recursive=False)

        code2 = parse("{{a}}{{a}}{{a}}{{b}}{{b}}{{b}}")
        func = partial(meth, code2)
        func(code2.get(1), "c", recursive=False)
        func("{{a}}", "d", recursive=False)
        func(code2.get(-1), "e", recursive=True)
        func("{{b}}", "f", recursive=True)
        self.assertEqual(expected[1], code2)

        code3 = parse("{{a|{{b}}|{{c|d={{f}}}}}}")
        func = partial(meth, code3)
        obj = code3.get(0).params[0].value.get(0)
        self.assertRaises(ValueError, func, obj, "x", recursive=False)
        func(obj, "x", recursive=True)
        self.assertRaises(ValueError, func, "{{f}}", "y", recursive=False)
        func("{{f}}", "y", recursive=True)
        self.assertEqual(expected[2], code3)

        code4 = parse("{{a}}{{b}}{{c}}{{d}}{{e}}{{f}}{{g}}{{h}}{{i}}{{j}}")
        func = partial(meth, code4)
        fake = parse("{{b}}{{c}}")
        self.assertRaises(ValueError, func, fake, "q", recursive=False)
        self.assertRaises(ValueError, func, fake, "q", recursive=True)
        func("{{b}}{{c}}", "w", recursive=False)
        func("{{d}}{{e}}", "x", recursive=True)
        func(wrap(code4.nodes[-2:]), "y", recursive=False)
        func(wrap(code4.nodes[-2:]), "z", recursive=True)
        self.assertEqual(expected[3], code4)
        self.assertRaises(ValueError, func, "{{c}}{{d}}", "q", recursive=False)
        self.assertRaises(ValueError, func, "{{c}}{{d}}", "q", recursive=True)

        code5 = parse("{{a|{{b}}{{c}}|{{f|{{g}}={{h}}{{i}}}}}}")
        func = partial(meth, code5)
        self.assertRaises(ValueError, func, "{{b}}{{c}}", "x", recursive=False)
        func("{{b}}{{c}}", "x", recursive=True)
        obj = code5.get(0).params[1].value.get(0).params[0].value
        self.assertRaises(ValueError, func, obj, "y", recursive=False)
        func(obj, "y", recursive=True)
        self.assertEqual(expected[4], code5)

        code6 = parse("here is {{some text and a {{template}}}}")
        func = partial(meth, code6)
        self.assertRaises(ValueError, func, "text and", "ab", recursive=False)
        func("text and", "ab", recursive=True)
        self.assertRaises(ValueError, func, "is {{some", "cd", recursive=False)
        func("is {{some", "cd", recursive=True)
        self.assertEqual(expected[5], code6)

        code7 = parse("{{foo}}{{bar}}{{baz}}{{foo}}{{baz}}")
        func = partial(meth, code7)
        obj = wrap([code7.get(0), code7.get(2)])
        self.assertRaises(ValueError, func, obj, "{{lol}}")
        func("{{foo}}{{baz}}", "{{lol}}")
        self.assertEqual(expected[6], code7)

    def test_insert_before(self):
        """test Wikicode.insert_before()"""
        meth = lambda code, *args, **kw: code.insert_before(*args, **kw)
        expected = [
            "{{a}}xz{{b}}{{c}}[[y]]{{d}}{{e}}",
            "d{{a}}cd{{a}}d{{a}}f{{b}}f{{b}}ef{{b}}",
            "{{a|x{{b}}|{{c|d=y{{f}}}}}}",
            "{{a}}w{{b}}{{c}}x{{d}}{{e}}{{f}}{{g}}{{h}}yz{{i}}{{j}}",
            "{{a|x{{b}}{{c}}|{{f|{{g}}=y{{h}}{{i}}}}}}",
            "here cdis {{some abtext and a {{template}}}}",
            "{{foo}}{{bar}}{{baz}}{{lol}}{{foo}}{{baz}}"]
        self._test_search(meth, expected)

    def test_insert_after(self):
        """test Wikicode.insert_after()"""
        meth = lambda code, *args, **kw: code.insert_after(*args, **kw)
        expected = [
            "{{a}}{{b}}xz{{c}}{{d}}[[y]]{{e}}",
            "{{a}}d{{a}}dc{{a}}d{{b}}f{{b}}f{{b}}fe",
            "{{a|{{b}}x|{{c|d={{f}}y}}}}",
            "{{a}}{{b}}{{c}}w{{d}}{{e}}x{{f}}{{g}}{{h}}{{i}}{{j}}yz",
            "{{a|{{b}}{{c}}x|{{f|{{g}}={{h}}{{i}}y}}}}",
            "here is {{somecd text andab a {{template}}}}",
            "{{foo}}{{bar}}{{baz}}{{foo}}{{baz}}{{lol}}"]
        self._test_search(meth, expected)

    def test_replace(self):
        """test Wikicode.replace()"""
        meth = lambda code, *args, **kw: code.replace(*args, **kw)
        expected = [
            "{{a}}xz[[y]]{{e}}", "dcdffe", "{{a|x|{{c|d=y}}}}",
            "{{a}}wx{{f}}{{g}}z", "{{a|x|{{f|{{g}}=y}}}}",
            "here cd ab a {{template}}}}", "{{foo}}{{bar}}{{baz}}{{lol}}"]
        self._test_search(meth, expected)

    def test_append(self):
        """test Wikicode.append()"""
        code = parse("Have a {{template}}")
        code.append("{{{argument}}}")
        self.assertEqual("Have a {{template}}{{{argument}}}", code)
        self.assertIsInstance(code.get(2), Argument)
        code.append(None)
        self.assertEqual("Have a {{template}}{{{argument}}}", code)
        code.append(Text(" foo"))
        self.assertEqual("Have a {{template}}{{{argument}}} foo", code)
        self.assertRaises(ValueError, code.append, slice(0, 1))

    def test_remove(self):
        """test Wikicode.remove()"""
        meth = lambda code, obj, value, **kw: code.remove(obj, **kw)
        expected = [
            "{{a}}{{c}}", "", "{{a||{{c|d=}}}}", "{{a}}{{f}}",
            "{{a||{{f|{{g}}=}}}}", "here   a {{template}}}}",
            "{{foo}}{{bar}}{{baz}}"]
        self._test_search(meth, expected)

    def test_matches(self):
        """test Wikicode.matches()"""
        code1 = parse("Cleanup")
        code2 = parse("\nstub<!-- TODO: make more specific -->")
        code3 = parse("")
        self.assertTrue(code1.matches("Cleanup"))
        self.assertTrue(code1.matches("cleanup"))
        self.assertTrue(code1.matches("  cleanup\n"))
        self.assertFalse(code1.matches("CLEANup"))
        self.assertFalse(code1.matches("Blah"))
        self.assertTrue(code2.matches("stub"))
        self.assertTrue(code2.matches("Stub<!-- no, it's fine! -->"))
        self.assertFalse(code2.matches("StuB"))
        self.assertTrue(code1.matches(("cleanup", "stub")))
        self.assertTrue(code2.matches(("cleanup", "stub")))
        self.assertFalse(code2.matches(("StuB", "sTUb", "foobar")))
        self.assertFalse(code2.matches(["StuB", "sTUb", "foobar"]))
        self.assertTrue(code2.matches(("StuB", "sTUb", "foo", "bar", "Stub")))
        self.assertTrue(code2.matches(["StuB", "sTUb", "foo", "bar", "Stub"]))
        self.assertTrue(code3.matches(""))
        self.assertTrue(code3.matches("<!-- nothing -->"))
        self.assertTrue(code3.matches(("a", "b", "")))

    def test_filter_family(self):
        """test the Wikicode.i?filter() family of functions"""
        def genlist(gen):
            self.assertIsInstance(gen, GeneratorType)
            return list(gen)
        ifilter = lambda code: (lambda *a, **k: genlist(code.ifilter(*a, **k)))

        code = parse("a{{b}}c[[d]]{{{e}}}{{f}}[[g]]")
        for func in (code.filter, ifilter(code)):
            self.assertEqual(["a", "{{b}}", "b", "c", "[[d]]", "d", "{{{e}}}",
                              "e", "{{f}}", "f", "[[g]]", "g"], func())
            self.assertEqual(["{{{e}}}"], func(forcetype=Argument))
            self.assertIs(code.get(4), func(forcetype=Argument)[0])
            self.assertEqual(list("abcdefg"), func(forcetype=Text))
            self.assertEqual([], func(forcetype=Heading))
            self.assertRaises(TypeError, func, forcetype=True)

        funcs = [
            lambda name, **kw: getattr(code, "filter_" + name)(**kw),
            lambda name, **kw: genlist(getattr(code, "ifilter_" + name)(**kw))
        ]
        for get_filter in funcs:
            self.assertEqual(["{{{e}}}"], get_filter("arguments"))
            self.assertIs(code.get(4), get_filter("arguments")[0])
            self.assertEqual([], get_filter("comments"))
            self.assertEqual([], get_filter("external_links"))
            self.assertEqual([], get_filter("headings"))
            self.assertEqual([], get_filter("html_entities"))
            self.assertEqual([], get_filter("tags"))
            self.assertEqual(["{{b}}", "{{f}}"], get_filter("templates"))
            self.assertEqual(list("abcdefg"), get_filter("text"))
            self.assertEqual(["[[d]]", "[[g]]"], get_filter("wikilinks"))

        code2 = parse("{{a|{{b}}|{{c|d={{f}}{{h}}}}}}")
        for func in (code2.filter, ifilter(code2)):
            self.assertEqual(["{{a|{{b}}|{{c|d={{f}}{{h}}}}}}"],
                             func(recursive=False, forcetype=Template))
            self.assertEqual(["{{a|{{b}}|{{c|d={{f}}{{h}}}}}}", "{{b}}",
                              "{{c|d={{f}}{{h}}}}", "{{f}}", "{{h}}"],
                             func(recursive=True, forcetype=Template))

        code3 = parse("{{foobar}}{{FOO}}{{baz}}{{bz}}{{barfoo}}")
        for func in (code3.filter, ifilter(code3)):
            self.assertEqual(["{{foobar}}", "{{barfoo}}"],
                             func(False, matches=lambda node: "foo" in node))
            self.assertEqual(["{{foobar}}", "{{FOO}}", "{{barfoo}}"],
                             func(False, matches=r"foo"))
            self.assertEqual(["{{foobar}}", "{{FOO}}"],
                             func(matches=r"^{{foo.*?}}"))
            self.assertEqual(["{{foobar}}"],
                             func(matches=r"^{{foo.*?}}", flags=re.UNICODE))
            self.assertEqual(["{{baz}}", "{{bz}}"], func(matches=r"^{{b.*?z"))
            self.assertEqual(["{{baz}}"], func(matches=r"^{{b.+?z}}"))

        exp_rec = ["{{a|{{b}}|{{c|d={{f}}{{h}}}}}}", "{{b}}",
                        "{{c|d={{f}}{{h}}}}", "{{f}}", "{{h}}"]
        exp_unrec = ["{{a|{{b}}|{{c|d={{f}}{{h}}}}}}"]
        self.assertEqual(exp_rec, code2.filter_templates())
        self.assertEqual(exp_unrec, code2.filter_templates(recursive=False))
        self.assertEqual(exp_rec, code2.filter_templates(recursive=True))
        self.assertEqual(exp_rec, code2.filter_templates(True))
        self.assertEqual(exp_unrec, code2.filter_templates(False))

        self.assertEqual(["{{foobar}}"], code3.filter_templates(
            matches=lambda node: node.name.matches("Foobar")))
        self.assertEqual(["{{baz}}", "{{bz}}"],
                         code3.filter_templates(matches=r"^{{b.*?z"))
        self.assertEqual([], code3.filter_tags(matches=r"^{{b.*?z"))
        self.assertEqual([], code3.filter_tags(matches=r"^{{b.*?z", flags=0))

        self.assertRaises(TypeError, code.filter_templates, a=42)
        self.assertRaises(TypeError, code.filter_templates, forcetype=Template)
        self.assertRaises(TypeError, code.filter_templates, 1, 0, 0, Template)

        code4 = parse("{{foo}}<b>{{foo|{{bar}}}}</b>")
        actual1 = code4.filter_templates(recursive=code4.RECURSE_OTHERS)
        actual2 = code4.filter_templates(code4.RECURSE_OTHERS)
        self.assertEqual(["{{foo}}", "{{foo|{{bar}}}}"], actual1)
        self.assertEqual(["{{foo}}", "{{foo|{{bar}}}}"], actual2)

    def test_get_sections(self):
        """test Wikicode.get_sections()"""
        page1 = parse("")
        page2 = parse("==Heading==")
        page3 = parse("===Heading===\nFoo bar baz\n====Gnidaeh====\n")

        p4_lead = "This is a lead.\n"
        p4_IA = "=== Section I.A ===\nSection I.A [[body]].\n"
        p4_IB1 = "==== Section I.B.1 ====\nSection I.B.1 body.\n\n&bull;Some content.\n\n"
        p4_IB = "=== Section I.B ===\n" + p4_IB1
        p4_I = "== Section I ==\nSection I body. {{and a|template}}\n" + p4_IA + p4_IB
        p4_II = "== Section II ==\nSection II body.\n\n"
        p4_IIIA1a = "===== Section III.A.1.a =====\nMore text.\n"
        p4_IIIA2ai1 = "======= Section III.A.2.a.i.1 =======\nAn invalid section!"
        p4_IIIA2 = "==== Section III.A.2 ====\nEven more text.\n" + p4_IIIA2ai1
        p4_IIIA = "=== Section III.A ===\nText.\n" + p4_IIIA1a + p4_IIIA2
        p4_III = "== Section III ==\n" + p4_IIIA
        page4 = parse(p4_lead + p4_I + p4_II + p4_III)

        self.assertEqual([""], page1.get_sections())
        self.assertEqual(["", "==Heading=="], page2.get_sections())
        self.assertEqual(["", "===Heading===\nFoo bar baz\n====Gnidaeh====\n",
                          "====Gnidaeh====\n"], page3.get_sections())
        self.assertEqual([p4_lead, p4_I, p4_IA, p4_IB, p4_IB1, p4_II,
                          p4_III, p4_IIIA, p4_IIIA1a, p4_IIIA2, p4_IIIA2ai1],
                         page4.get_sections())

        self.assertEqual(["====Gnidaeh====\n"], page3.get_sections(levels=[4]))
        self.assertEqual(["===Heading===\nFoo bar baz\n====Gnidaeh====\n"],
                         page3.get_sections(levels=(2, 3)))
        self.assertEqual(["===Heading===\nFoo bar baz\n"],
                         page3.get_sections(levels=(2, 3), flat=True))
        self.assertEqual([], page3.get_sections(levels=[0]))
        self.assertEqual(["", "====Gnidaeh====\n"],
                         page3.get_sections(levels=[4], include_lead=True))
        self.assertEqual(["===Heading===\nFoo bar baz\n====Gnidaeh====\n",
                          "====Gnidaeh====\n"],
                         page3.get_sections(include_lead=False))
        self.assertEqual(["===Heading===\nFoo bar baz\n", "====Gnidaeh====\n"],
                         page3.get_sections(flat=True, include_lead=False))

        self.assertEqual([p4_IB1, p4_IIIA2], page4.get_sections(levels=[4]))
        self.assertEqual([p4_IA, p4_IB, p4_IIIA], page4.get_sections(levels=[3]))
        self.assertEqual([p4_IA, "=== Section I.B ===\n",
                          "=== Section III.A ===\nText.\n"],
                         page4.get_sections(levels=[3], flat=True))
        self.assertEqual(["", ""], page2.get_sections(include_headings=False))
        self.assertEqual(["\nSection I.B.1 body.\n\n&bull;Some content.\n\n",
                          "\nEven more text.\n" + p4_IIIA2ai1],
                         page4.get_sections(levels=[4],
                                            include_headings=False))

        self.assertEqual([], page4.get_sections(matches=r"body"))
        self.assertEqual([p4_I, p4_IA, p4_IB, p4_IB1],
                         page4.get_sections(matches=r"Section\sI[.\s].*?"))
        self.assertEqual([p4_IA, p4_IIIA, p4_IIIA1a, p4_IIIA2, p4_IIIA2ai1],
                         page4.get_sections(matches=r".*?a.*?"))
        self.assertEqual([p4_IIIA1a, p4_IIIA2ai1],
                         page4.get_sections(matches=r".*?a.*?", flags=re.U))
        self.assertEqual(["\nMore text.\n", "\nAn invalid section!"],
                         page4.get_sections(matches=r".*?a.*?", flags=re.U,
                                            include_headings=False))

        sections = page2.get_sections(include_headings=False)
        sections[0].append("Lead!\n")
        sections[1].append("\nFirst section!")
        self.assertEqual("Lead!\n==Heading==\nFirst section!", page2)

        page5 = parse("X\n== Foo ==\nBar\n== Baz ==\nBuzz")
        section = page5.get_sections(matches="Foo")[0]
        section.replace("\nBar\n", "\nBarf ")
        section.append("{{Haha}}\n")
        self.assertEqual("== Foo ==\nBarf {{Haha}}\n", section)
        self.assertEqual("X\n== Foo ==\nBarf {{Haha}}\n== Baz ==\nBuzz", page5)

    def test_strip_code(self):
        """test Wikicode.strip_code()"""
        # Since individual nodes have test cases for their __strip__ methods,
        # we're only going to do an integration test:
        code = parse("Foo [[bar]]\n\n{{baz}}\n\n[[a|b]] &Sigma;")
        self.assertEqual("Foo bar\n\nb Σ",
                         code.strip_code(normalize=True, collapse=True))
        self.assertEqual("Foo bar\n\n\n\nb Σ",
                         code.strip_code(normalize=True, collapse=False))
        self.assertEqual("Foo bar\n\nb &Sigma;",
                         code.strip_code(normalize=False, collapse=True))
        self.assertEqual("Foo bar\n\n\n\nb &Sigma;",
                         code.strip_code(normalize=False, collapse=False))

    def test_get_tree(self):
        """test Wikicode.get_tree()"""
        # Since individual nodes have test cases for their __showtree___
        # methods, and the docstring covers all possibilities for the output of
        # __showtree__, we'll test it only:
        code = parse("Lorem ipsum {{foo|bar|{{baz}}|spam=eggs}}")
        expected = "Lorem ipsum \n{{\n\t  foo\n\t| 1\n\t= bar\n\t| 2\n\t= " + \
                   "{{\n\t\t\tbaz\n\t  }}\n\t| spam\n\t= eggs\n}}"
        self.assertEqual(expected.expandtabs(4), code.get_tree())

if __name__ == "__main__":
    unittest.main(verbosity=2)

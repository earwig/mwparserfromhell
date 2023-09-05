# Copyright (C) 2012-2023 Ben Kurtovic <ben.kurtovic@gmail.com>
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

"""
Tests for the Wikicode class, which manages a list of nodes.
"""

from functools import partial
import re
import pickle
from types import GeneratorType

import pytest

from mwparserfromhell.nodes import Argument, Heading, Template, Text
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell import parse
from .conftest import wrap, wraptext


def test_str():
    """test Wikicode.__str__()"""
    code1 = parse("foobar")
    code2 = parse("Have a {{template}} and a [[page|link]]")
    assert "foobar" == str(code1)
    assert "Have a {{template}} and a [[page|link]]" == str(code2)


def test_nodes():
    """test getter/setter for the nodes attribute"""
    code = parse("Have a {{template}}")
    assert ["Have a ", "{{template}}"] == code.nodes
    L1 = SmartList([Text("foobar"), Template(wraptext("abc"))])
    L2 = [Text("barfoo"), Template(wraptext("cba"))]
    L3 = "abc{{def}}"
    code.nodes = L1
    assert L1 is code.nodes
    code.nodes = L2
    assert L2 is code.nodes
    code.nodes = L3
    assert ["abc", "{{def}}"] == code.nodes
    with pytest.raises(ValueError):
        code.__setattr__("nodes", object)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickling(protocol: int):
    """test Wikicode objects can be pickled"""
    code = parse("Have a {{template}} and a [[page|link]]")
    enc = pickle.dumps(code, protocol=protocol)
    assert pickle.loads(enc) == code


def test_get():
    """test Wikicode.get()"""
    code = parse("Have a {{template}} and a [[page|link]]")
    assert code.nodes[0] is code.get(0)
    assert code.nodes[2] is code.get(2)
    with pytest.raises(IndexError):
        code.get(4)


def test_set():
    """test Wikicode.set()"""
    code = parse("Have a {{template}} and a [[page|link]]")
    code.set(1, "{{{argument}}}")
    assert "Have a {{{argument}}} and a [[page|link]]" == code
    assert isinstance(code.get(1), Argument)
    code.set(2, None)
    assert "Have a {{{argument}}}[[page|link]]" == code
    code.set(-3, "This is an ")
    assert "This is an {{{argument}}}[[page|link]]" == code
    with pytest.raises(ValueError):
        code.set(1, "foo {{bar}}")
    with pytest.raises(IndexError):
        code.set(3, "{{baz}}")
    with pytest.raises(IndexError):
        code.set(-4, "{{baz}}")


def test_contains():
    """test Wikicode.contains()"""
    code = parse("Here is {{aaa|{{bbb|xyz{{ccc}}}}}} and a [[page|link]]")
    tmpl1, tmpl2, tmpl3 = code.filter_templates()
    tmpl4 = parse("{{ccc}}").filter_templates()[0]
    assert code.contains(tmpl1) is True
    assert code.contains(tmpl3) is True
    assert code.contains(tmpl4) is False
    assert code.contains(str(tmpl4)) is True
    assert code.contains(tmpl2.params[0].value) is True


def test_index():
    """test Wikicode.index()"""
    code = parse("Have a {{template}} and a [[page|link]]")
    assert 0 == code.index("Have a ")
    assert 3 == code.index("[[page|link]]")
    assert 1 == code.index(code.get(1))
    with pytest.raises(ValueError):
        code.index("foo")

    code = parse("{{foo}}{{bar|{{baz}}}}")
    assert 1 == code.index("{{bar|{{baz}}}}")
    assert 1 == code.index("{{baz}}", recursive=True)
    assert 1 == code.index(code.get(1).get(1).value, recursive=True)
    with pytest.raises(ValueError):
        code.index("{{baz}}", recursive=False)
    with pytest.raises(ValueError):
        code.index(code.get(1).get(1).value, recursive=False)


def test_get_ancestors_parent():
    """test Wikicode.get_ancestors() and Wikicode.get_parent()"""
    code = parse("{{a|{{b|{{d|{{e}}{{f}}}}{{g}}}}}}{{c}}")
    tmpl = code.filter_templates(matches=lambda n: n.name == "f")[0]
    parent1 = code.filter_templates(matches=lambda n: n.name == "d")[0]
    parent2 = code.filter_templates(matches=lambda n: n.name == "b")[0]
    parent3 = code.filter_templates(matches=lambda n: n.name == "a")[0]
    fake = parse("{{f}}").get(0)

    assert [parent3, parent2, parent1] == code.get_ancestors(tmpl)
    assert parent1 is code.get_parent(tmpl)
    assert [] == code.get_ancestors(parent3)
    assert None is code.get_parent(parent3)
    with pytest.raises(ValueError):
        code.get_ancestors(fake)
    with pytest.raises(ValueError):
        code.get_parent(fake)


def test_insert():
    """test Wikicode.insert()"""
    code = parse("Have a {{template}} and a [[page|link]]")
    code.insert(1, "{{{argument}}}")
    assert "Have a {{{argument}}}{{template}} and a [[page|link]]" == code
    assert isinstance(code.get(1), Argument)
    code.insert(2, None)
    assert "Have a {{{argument}}}{{template}} and a [[page|link]]" == code
    code.insert(-3, Text("foo"))
    assert "Have a {{{argument}}}foo{{template}} and a [[page|link]]" == code

    code2 = parse("{{foo}}{{bar}}{{baz}}")
    code2.insert(1, "abc{{def}}ghi[[jk]]")
    assert "{{foo}}abc{{def}}ghi[[jk]]{{bar}}{{baz}}" == code2
    assert [
        "{{foo}}",
        "abc",
        "{{def}}",
        "ghi",
        "[[jk]]",
        "{{bar}}",
        "{{baz}}",
    ] == code2.nodes

    code3 = parse("{{foo}}bar")
    code3.insert(1000, "[[baz]]")
    code3.insert(-1000, "derp")
    assert "derp{{foo}}bar[[baz]]" == code3


def _test_search(meth, expected):
    """Base test for insert_before(), insert_after(), and replace()."""
    code = parse("{{a}}{{b}}{{c}}{{d}}{{e}}")
    func = partial(meth, code)
    func("{{b}}", "x", recursive=True)
    func("{{d}}", "[[y]]", recursive=False)
    func(code.get(2), "z")
    assert expected[0] == code
    with pytest.raises(ValueError):
        func("{{r}}", "n", recursive=True)
    with pytest.raises(ValueError):
        func("{{r}}", "n", recursive=False)
    fake = parse("{{a}}").get(0)
    with pytest.raises(ValueError):
        func(fake, "n", recursive=True)
    with pytest.raises(ValueError):
        func(fake, "n", recursive=False)

    code2 = parse("{{a}}{{a}}{{a}}{{b}}{{b}}{{b}}")
    func = partial(meth, code2)
    func(code2.get(1), "c", recursive=False)
    func("{{a}}", "d", recursive=False)
    func(code2.get(-1), "e", recursive=True)
    func("{{b}}", "f", recursive=True)
    assert expected[1] == code2

    code3 = parse("{{a|{{b}}|{{c|d={{f}}}}}}")
    func = partial(meth, code3)
    obj = code3.get(0).params[0].value.get(0)
    with pytest.raises(ValueError):
        func(obj, "x", recursive=False)
    func(obj, "x", recursive=True)
    with pytest.raises(ValueError):
        func("{{f}}", "y", recursive=False)
    func("{{f}}", "y", recursive=True)
    assert expected[2] == code3

    code4 = parse("{{a}}{{b}}{{c}}{{d}}{{e}}{{f}}{{g}}{{h}}{{i}}{{j}}")
    func = partial(meth, code4)
    fake = parse("{{b}}{{c}}")
    with pytest.raises(ValueError):
        func(fake, "q", recursive=False)
    with pytest.raises(ValueError):
        func(fake, "q", recursive=True)
    func("{{b}}{{c}}", "w", recursive=False)
    func("{{d}}{{e}}", "x", recursive=True)
    func(Wikicode(code4.nodes[-2:]), "y", recursive=False)
    func(Wikicode(code4.nodes[-2:]), "z", recursive=True)
    assert expected[3] == code4
    with pytest.raises(ValueError):
        func("{{c}}{{d}}", "q", recursive=False)
    with pytest.raises(ValueError):
        func("{{c}}{{d}}", "q", recursive=True)

    code5 = parse("{{a|{{b}}{{c}}|{{f|{{g}}={{h}}{{i}}}}}}")
    func = partial(meth, code5)
    with pytest.raises(ValueError):
        func("{{b}}{{c}}", "x", recursive=False)
    func("{{b}}{{c}}", "x", recursive=True)
    obj = code5.get(0).params[1].value.get(0).params[0].value
    with pytest.raises(ValueError):
        func(obj, "y", recursive=False)
    func(obj, "y", recursive=True)
    assert expected[4] == code5

    code6 = parse("here is {{some text and a {{template}}}}")
    func = partial(meth, code6)
    with pytest.raises(ValueError):
        func("text and", "ab", recursive=False)
    func("text and", "ab", recursive=True)
    with pytest.raises(ValueError):
        func("is {{some", "cd", recursive=False)
    func("is {{some", "cd", recursive=True)
    assert expected[5] == code6

    code7 = parse("{{foo}}{{bar}}{{baz}}{{foo}}{{baz}}")
    func = partial(meth, code7)
    obj = wrap([code7.get(0), code7.get(2)])
    with pytest.raises(ValueError):
        func(obj, "{{lol}}")
    func("{{foo}}{{baz}}", "{{lol}}")
    assert expected[6] == code7

    code8 = parse("== header ==")
    func = partial(meth, code8)
    sec1, sec2 = code8.get_sections(include_headings=False)
    func(sec1, "lead\n")
    func(sec2, "\nbody")
    assert expected[7] == code8

    code9 = parse("{{foo}}")
    meth(code9.get_sections()[0], code9.get_sections()[0], "{{bar}}")
    meth(code9.get_sections()[0], code9, "{{baz}}")
    meth(code9, code9, "{{qux}}")
    meth(code9, code9.get_sections()[0], "{{quz}}")
    assert expected[8] == code9


def test_insert_before():
    """test Wikicode.insert_before()"""
    meth = lambda code, *args, **kw: code.insert_before(*args, **kw)
    expected = [
        "{{a}}xz{{b}}{{c}}[[y]]{{d}}{{e}}",
        "d{{a}}cd{{a}}d{{a}}f{{b}}f{{b}}ef{{b}}",
        "{{a|x{{b}}|{{c|d=y{{f}}}}}}",
        "{{a}}w{{b}}{{c}}x{{d}}{{e}}{{f}}{{g}}{{h}}yz{{i}}{{j}}",
        "{{a|x{{b}}{{c}}|{{f|{{g}}=y{{h}}{{i}}}}}}",
        "here cdis {{some abtext and a {{template}}}}",
        "{{foo}}{{bar}}{{baz}}{{lol}}{{foo}}{{baz}}",
        "lead\n== header ==\nbody",
        "{{quz}}{{qux}}{{baz}}{{bar}}{{foo}}",
    ]
    _test_search(meth, expected)


def test_insert_after():
    """test Wikicode.insert_after()"""
    meth = lambda code, *args, **kw: code.insert_after(*args, **kw)
    expected = [
        "{{a}}{{b}}xz{{c}}{{d}}[[y]]{{e}}",
        "{{a}}d{{a}}dc{{a}}d{{b}}f{{b}}f{{b}}fe",
        "{{a|{{b}}x|{{c|d={{f}}y}}}}",
        "{{a}}{{b}}{{c}}w{{d}}{{e}}x{{f}}{{g}}{{h}}{{i}}{{j}}yz",
        "{{a|{{b}}{{c}}x|{{f|{{g}}={{h}}{{i}}y}}}}",
        "here is {{somecd text andab a {{template}}}}",
        "{{foo}}{{bar}}{{baz}}{{foo}}{{baz}}{{lol}}",
        "lead\n== header ==\nbody",
        "{{foo}}{{bar}}{{baz}}{{qux}}{{quz}}",
    ]
    _test_search(meth, expected)


def test_replace():
    """test Wikicode.replace()"""
    meth = lambda code, *args, **kw: code.replace(*args, **kw)
    expected = [
        "{{a}}xz[[y]]{{e}}",
        "dcdffe",
        "{{a|x|{{c|d=y}}}}",
        "{{a}}wx{{f}}{{g}}z",
        "{{a|x|{{f|{{g}}=y}}}}",
        "here cd ab a {{template}}}}",
        "{{foo}}{{bar}}{{baz}}{{lol}}",
        "lead\n== header ==\nbody",
        "{{quz}}",
    ]
    _test_search(meth, expected)


def test_append():
    """test Wikicode.append()"""
    code = parse("Have a {{template}}")
    code.append("{{{argument}}}")
    assert "Have a {{template}}{{{argument}}}" == code
    assert isinstance(code.get(2), Argument)
    code.append(None)
    assert "Have a {{template}}{{{argument}}}" == code
    code.append(Text(" foo"))
    assert "Have a {{template}}{{{argument}}} foo" == code
    with pytest.raises(ValueError):
        code.append(slice(0, 1))


def test_remove():
    """test Wikicode.remove()"""
    meth = lambda code, obj, value, **kw: code.remove(obj, **kw)
    expected = [
        "{{a}}{{c}}",
        "",
        "{{a||{{c|d=}}}}",
        "{{a}}{{f}}",
        "{{a||{{f|{{g}}=}}}}",
        "here   a {{template}}}}",
        "{{foo}}{{bar}}{{baz}}",
        "== header ==",
        "",
    ]
    _test_search(meth, expected)


def test_matches():
    """test Wikicode.matches()"""
    code1 = parse("Cleanup")
    code2 = parse("\nstub<!-- TODO: make more specific -->")
    code3 = parse("Hello world!")
    code4 = parse("World,_hello?")
    code5 = parse("")
    assert code1.matches("Cleanup") is True
    assert code1.matches("cleanup") is True
    assert code1.matches("  cleanup\n") is True
    assert code1.matches("CLEANup") is False
    assert code1.matches("Blah") is False
    assert code2.matches("stub") is True
    assert code2.matches("Stub<!-- no, it's fine! -->") is True
    assert code2.matches("StuB") is False
    assert code1.matches(("cleanup", "stub")) is True
    assert code2.matches(("cleanup", "stub")) is True
    assert code2.matches(("StuB", "sTUb", "foobar")) is False
    assert code2.matches(["StuB", "sTUb", "foobar"]) is False
    assert code2.matches(("StuB", "sTUb", "foo", "bar", "Stub")) is True
    assert code2.matches(["StuB", "sTUb", "foo", "bar", "Stub"]) is True
    assert code3.matches("hello world!") is True
    assert code3.matches("hello_world!") is True
    assert code3.matches("hello__world!") is False
    assert code4.matches("World,_hello?") is True
    assert code4.matches("World, hello?") is True
    assert code4.matches("World,  hello?") is False
    assert code5.matches("") is True
    assert code5.matches("<!-- nothing -->") is True
    assert code5.matches(("a", "b", "")) is True


def test_filter_family():
    """test the Wikicode.i?filter() family of functions"""

    def genlist(gen):
        assert isinstance(gen, GeneratorType)
        return list(gen)

    ifilter = lambda code: (lambda *a, **k: genlist(code.ifilter(*a, **k)))

    code = parse("a{{b}}c[[d]]{{{e}}}{{f}}[[g]]")
    for func in (code.filter, ifilter(code)):
        assert [
            "a",
            "{{b}}",
            "b",
            "c",
            "[[d]]",
            "d",
            "{{{e}}}",
            "e",
            "{{f}}",
            "f",
            "[[g]]",
            "g",
        ] == func()
        assert ["{{{e}}}"] == func(forcetype=Argument)
        assert code.get(4) is func(forcetype=Argument)[0]
        assert list("abcdefg") == func(forcetype=Text)
        assert [] == func(forcetype=Heading)
        with pytest.raises(TypeError):
            func(forcetype=True)

    funcs = [
        lambda name, **kw: getattr(code, "filter_" + name)(**kw),
        lambda name, **kw: genlist(getattr(code, "ifilter_" + name)(**kw)),
    ]
    for get_filter in funcs:
        assert ["{{{e}}}"] == get_filter("arguments")
        assert code.get(4) is get_filter("arguments")[0]
        assert [] == get_filter("comments")
        assert [] == get_filter("external_links")
        assert [] == get_filter("headings")
        assert [] == get_filter("html_entities")
        assert [] == get_filter("tags")
        assert ["{{b}}", "{{f}}"] == get_filter("templates")
        assert list("abcdefg") == get_filter("text")
        assert ["[[d]]", "[[g]]"] == get_filter("wikilinks")

    code2 = parse("{{a|{{b}}|{{c|d={{f}}{{h}}}}}}")
    for func in (code2.filter, ifilter(code2)):
        assert ["{{a|{{b}}|{{c|d={{f}}{{h}}}}}}"] == func(
            recursive=False, forcetype=Template
        )
        assert [
            "{{a|{{b}}|{{c|d={{f}}{{h}}}}}}",
            "{{b}}",
            "{{c|d={{f}}{{h}}}}",
            "{{f}}",
            "{{h}}",
        ] == func(recursive=True, forcetype=Template)

    code3 = parse("{{foobar}}{{FOO}}{{baz}}{{bz}}{{barfoo}}")
    for func in (code3.filter, ifilter(code3)):
        assert ["{{foobar}}", "{{barfoo}}"] == func(
            False, matches=lambda node: "foo" in node
        )
        assert ["{{foobar}}", "{{FOO}}", "{{barfoo}}"] == func(False, matches=r"foo")
        assert ["{{foobar}}", "{{FOO}}"] == func(matches=r"^{{foo.*?}}")
        assert ["{{foobar}}"] == func(matches=r"^{{foo.*?}}", flags=re.UNICODE)
        assert ["{{baz}}", "{{bz}}"] == func(matches=r"^{{b.*?z")
        assert ["{{baz}}"] == func(matches=r"^{{b.+?z}}")

    exp_rec = [
        "{{a|{{b}}|{{c|d={{f}}{{h}}}}}}",
        "{{b}}",
        "{{c|d={{f}}{{h}}}}",
        "{{f}}",
        "{{h}}",
    ]
    exp_unrec = ["{{a|{{b}}|{{c|d={{f}}{{h}}}}}}"]
    assert exp_rec == code2.filter_templates()
    assert exp_unrec == code2.filter_templates(recursive=False)
    assert exp_rec == code2.filter_templates(recursive=True)
    assert exp_rec == code2.filter_templates(True)
    assert exp_unrec == code2.filter_templates(False)

    assert ["{{foobar}}"] == code3.filter_templates(
        matches=lambda node: node.name.matches("Foobar")
    )
    assert ["{{baz}}", "{{bz}}"] == code3.filter_templates(matches=r"^{{b.*?z")
    assert [] == code3.filter_tags(matches=r"^{{b.*?z")
    assert [] == code3.filter_tags(matches=r"^{{b.*?z", flags=0)
    with pytest.raises(TypeError):
        code.filter_templates(a=42)
    with pytest.raises(TypeError):
        code.filter_templates(forcetype=Template)
    with pytest.raises(TypeError):
        code.filter_templates(1, 0, 0, Template)

    code4 = parse("{{foo}}<b>{{foo|{{bar}}}}</b>")
    actual1 = code4.filter_templates(recursive=code4.RECURSE_OTHERS)
    actual2 = code4.filter_templates(code4.RECURSE_OTHERS)
    assert ["{{foo}}", "{{foo|{{bar}}}}"] == actual1
    assert ["{{foo}}", "{{foo|{{bar}}}}"] == actual2


def test_get_sections():
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

    assert [""] == page1.get_sections()
    assert ["", "==Heading=="] == page2.get_sections()
    assert [
        "",
        "===Heading===\nFoo bar baz\n====Gnidaeh====\n",
        "====Gnidaeh====\n",
    ] == page3.get_sections()
    assert [
        p4_lead,
        p4_I,
        p4_IA,
        p4_IB,
        p4_IB1,
        p4_II,
        p4_III,
        p4_IIIA,
        p4_IIIA1a,
        p4_IIIA2,
        p4_IIIA2ai1,
    ] == page4.get_sections()

    assert ["====Gnidaeh====\n"] == page3.get_sections(levels=[4])
    assert ["===Heading===\nFoo bar baz\n====Gnidaeh====\n"] == page3.get_sections(
        levels=(2, 3)
    )
    assert ["===Heading===\nFoo bar baz\n"] == page3.get_sections(
        levels=(2, 3), flat=True
    )
    assert [] == page3.get_sections(levels=[0])
    assert ["", "====Gnidaeh====\n"] == page3.get_sections(
        levels=[4], include_lead=True
    )
    assert [
        "===Heading===\nFoo bar baz\n====Gnidaeh====\n",
        "====Gnidaeh====\n",
    ] == page3.get_sections(include_lead=False)
    assert ["===Heading===\nFoo bar baz\n", "====Gnidaeh====\n"] == page3.get_sections(
        flat=True, include_lead=False
    )

    assert [p4_IB1, p4_IIIA2] == page4.get_sections(levels=[4])
    assert [p4_IA, p4_IB, p4_IIIA] == page4.get_sections(levels=[3])
    assert [
        p4_IA,
        "=== Section I.B ===\n",
        "=== Section III.A ===\nText.\n",
    ] == page4.get_sections(levels=[3], flat=True)
    assert ["", ""] == page2.get_sections(include_headings=False)
    assert [
        "\nSection I.B.1 body.\n\n&bull;Some content.\n\n",
        "\nEven more text.\n" + p4_IIIA2ai1,
    ] == page4.get_sections(levels=[4], include_headings=False)

    assert [] == page4.get_sections(matches=r"body")
    assert [p4_I, p4_IA, p4_IB, p4_IB1] == page4.get_sections(
        matches=r"Section\sI[.\s].*?"
    )
    assert [p4_IA, p4_IIIA, p4_IIIA1a, p4_IIIA2, p4_IIIA2ai1] == page4.get_sections(
        matches=r".*?a.*?"
    )
    assert [p4_IIIA1a, p4_IIIA2ai1] == page4.get_sections(
        matches=r".*?a.*?", flags=re.U
    )
    assert ["\nMore text.\n", "\nAn invalid section!"] == page4.get_sections(
        matches=r".*?a.*?", flags=re.U, include_headings=False
    )

    sections = page2.get_sections(include_headings=False)
    sections[0].append("Lead!\n")
    sections[1].append("\nFirst section!")
    assert "Lead!\n==Heading==\nFirst section!" == page2

    page5 = parse("X\n== Foo ==\nBar\n== Baz ==\nBuzz")
    section = page5.get_sections(matches="Foo")[0]
    section.replace("\nBar\n", "\nBarf ")
    section.append("{{Haha}}\n")
    assert "== Foo ==\nBarf {{Haha}}\n" == section
    assert "X\n== Foo ==\nBarf {{Haha}}\n== Baz ==\nBuzz" == page5


def test_strip_code():
    """test Wikicode.strip_code()"""
    # Since individual nodes have test cases for their __strip__ methods,
    # we're only going to do an integration test:
    code = parse("Foo [[bar]]\n\n{{baz|hello}}\n\n[[a|b]] &Sigma;")
    assert "Foo bar\n\nb Σ" == code.strip_code(normalize=True, collapse=True)
    assert "Foo bar\n\n\n\nb Σ" == code.strip_code(normalize=True, collapse=False)
    assert "Foo bar\n\nb &Sigma;" == code.strip_code(normalize=False, collapse=True)
    assert "Foo bar\n\n\n\nb &Sigma;" == code.strip_code(
        normalize=False, collapse=False
    )
    assert "Foo bar\n\nhello\n\nb Σ" == code.strip_code(
        normalize=True, collapse=True, keep_template_params=True
    )


def test_get_tree():
    """test Wikicode.get_tree()"""
    # Since individual nodes have test cases for their __showtree___
    # methods, and the docstring covers all possibilities for the output of
    # __showtree__, we'll test it only:
    code = parse("Lorem ipsum {{foo|bar|{{baz}}|spam=eggs}}")
    expected = (
        "Lorem ipsum \n{{\n\t  foo\n\t| 1\n\t= bar\n\t| 2\n\t= "
        + "{{\n\t\t\tbaz\n\t  }}\n\t| spam\n\t= eggs\n}}"
    )
    assert expected.expandtabs(4) == code.get_tree()

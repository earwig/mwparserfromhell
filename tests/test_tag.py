# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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
Test cases for the Tag node.
"""

import pytest

from mwparserfromhell.nodes import Tag, Template, Text
from mwparserfromhell.nodes.extras import Attribute
from .conftest import assert_wikicode_equal, wrap, wraptext

agen = lambda name, value: Attribute(wraptext(name), wraptext(value))
agennv = lambda name: Attribute(wraptext(name))
agennq = lambda name, value: Attribute(wraptext(name), wraptext(value), None)
agenp = lambda name, v, a, b, c: Attribute(wraptext(name), v, '"', a, b, c)
agenpnv = lambda name, a, b, c: Attribute(wraptext(name), None, '"', a, b, c)


def test_str():
    """test Tag.__str__()"""
    node1 = Tag(wraptext("ref"))
    node2 = Tag(wraptext("span"), wraptext("foo"), [agen("style", "color: red;")])
    node3 = Tag(
        wraptext("ref"),
        attrs=[agennq("name", "foo"), agenpnv("some_attr", "   ", "", "")],
        self_closing=True,
    )
    node4 = Tag(wraptext("br"), self_closing=True, padding=" ")
    node5 = Tag(wraptext("br"), self_closing=True, implicit=True)
    node6 = Tag(wraptext("br"), self_closing=True, invalid=True, implicit=True)
    node7 = Tag(wraptext("br"), self_closing=True, invalid=True, padding=" ")
    node8 = Tag(wraptext("hr"), wiki_markup="----", self_closing=True)
    node9 = Tag(wraptext("i"), wraptext("italics!"), wiki_markup="''")

    assert "<ref></ref>" == str(node1)
    assert '<span style="color: red;">foo</span>' == str(node2)
    assert "<ref name=foo   some_attr/>" == str(node3)
    assert "<br />" == str(node4)
    assert "<br>" == str(node5)
    assert "</br>" == str(node6)
    assert "</br />" == str(node7)
    assert "----" == str(node8)
    assert "''italics!''" == str(node9)


def test_children():
    """test Tag.__children__()"""
    # <ref>foobar</ref>
    node1 = Tag(wraptext("ref"), wraptext("foobar"))
    # '''bold text'''
    node2 = Tag(wraptext("b"), wraptext("bold text"), wiki_markup="'''")
    # <img id="foo" class="bar" selected />
    node3 = Tag(
        wraptext("img"),
        attrs=[agen("id", "foo"), agen("class", "bar"), agennv("selected")],
        self_closing=True,
        padding=" ",
    )

    gen1 = node1.__children__()
    gen2 = node2.__children__()
    gen3 = node3.__children__()
    assert node1.tag == next(gen1)
    assert node3.tag == next(gen3)
    assert node3.attributes[0].name == next(gen3)
    assert node3.attributes[0].value == next(gen3)
    assert node3.attributes[1].name == next(gen3)
    assert node3.attributes[1].value == next(gen3)
    assert node3.attributes[2].name == next(gen3)
    assert node1.contents == next(gen1)
    assert node2.contents == next(gen2)
    assert node1.closing_tag == next(gen1)
    with pytest.raises(StopIteration):
        next(gen1)
    with pytest.raises(StopIteration):
        next(gen2)
    with pytest.raises(StopIteration):
        next(gen3)


def test_strip():
    """test Tag.__strip__()"""
    node1 = Tag(wraptext("i"), wraptext("foobar"))
    node2 = Tag(wraptext("math"), wraptext("foobar"))
    node3 = Tag(wraptext("br"), self_closing=True)

    assert "foobar" == node1.__strip__()
    assert node2.__strip__() is None
    assert node3.__strip__() is None


def test_showtree():
    """test Tag.__showtree__()"""
    output = []
    getter, marker = object(), object()
    get = lambda code: output.append((getter, code))
    mark = lambda: output.append(marker)
    node1 = Tag(
        wraptext("ref"), wraptext("text"), [agen("name", "foo"), agennv("selected")]
    )
    node2 = Tag(wraptext("br"), self_closing=True, padding=" ")
    node3 = Tag(
        wraptext("br"), self_closing=True, invalid=True, implicit=True, padding=" "
    )
    node1.__showtree__(output.append, get, mark)
    node2.__showtree__(output.append, get, mark)
    node3.__showtree__(output.append, get, mark)
    valid = [
        "<",
        (getter, node1.tag),
        (getter, node1.attributes[0].name),
        "    = ",
        marker,
        (getter, node1.attributes[0].value),
        (getter, node1.attributes[1].name),
        ">",
        (getter, node1.contents),
        "</",
        (getter, node1.closing_tag),
        ">",
        "<",
        (getter, node2.tag),
        "/>",
        "</",
        (getter, node3.tag),
        ">",
    ]
    assert valid == output


def test_tag():
    """test getter/setter for the tag attribute"""
    tag = wraptext("ref")
    node = Tag(tag, wraptext("text"))
    assert tag is node.tag
    assert tag is node.closing_tag
    node.tag = "span"
    assert_wikicode_equal(wraptext("span"), node.tag)
    assert_wikicode_equal(wraptext("span"), node.closing_tag)
    assert "<span>text</span>" == node


def test_contents():
    """test getter/setter for the contents attribute"""
    contents = wraptext("text")
    node = Tag(wraptext("ref"), contents)
    assert contents is node.contents
    node.contents = "text and a {{template}}"
    parsed = wrap([Text("text and a "), Template(wraptext("template"))])
    assert_wikicode_equal(parsed, node.contents)
    assert "<ref>text and a {{template}}</ref>" == node


def test_attributes():
    """test getter for the attributes attribute"""
    attrs = [agen("name", "bar")]
    node1 = Tag(wraptext("ref"), wraptext("foo"))
    node2 = Tag(wraptext("ref"), wraptext("foo"), attrs)
    assert [] == node1.attributes
    assert attrs is node2.attributes


def test_wiki_markup():
    """test getter/setter for the wiki_markup attribute"""
    node = Tag(wraptext("i"), wraptext("italic text"))
    assert None is node.wiki_markup
    node.wiki_markup = "''"
    assert "''" == node.wiki_markup
    assert "''italic text''" == node
    node.wiki_markup = False
    assert node.wiki_markup is None
    assert "<i>italic text</i>" == node


def test_self_closing():
    """test getter/setter for the self_closing attribute"""
    node = Tag(wraptext("ref"), wraptext("foobar"))
    assert node.self_closing is False
    node.self_closing = True
    assert node.self_closing is True
    assert "<ref/>" == node
    node.self_closing = 0
    assert node.self_closing is False
    assert "<ref>foobar</ref>" == node


def test_invalid():
    """test getter/setter for the invalid attribute"""
    node = Tag(wraptext("br"), self_closing=True, implicit=True)
    assert node.invalid is False
    node.invalid = True
    assert node.invalid is True
    assert "</br>" == node
    node.invalid = 0
    assert node.invalid is False
    assert "<br>" == node


def test_implicit():
    """test getter/setter for the implicit attribute"""
    node = Tag(wraptext("br"), self_closing=True)
    assert node.implicit is False
    node.implicit = True
    assert node.implicit is True
    assert "<br>" == node
    node.implicit = 0
    assert node.implicit is False
    assert "<br/>" == node


def test_padding():
    """test getter/setter for the padding attribute"""
    node = Tag(wraptext("ref"), wraptext("foobar"))
    assert "" == node.padding
    node.padding = "  "
    assert "  " == node.padding
    assert "<ref  >foobar</ref>" == node
    node.padding = None
    assert "" == node.padding
    assert "<ref>foobar</ref>" == node
    with pytest.raises(ValueError):
        node.__setattr__("padding", True)


def test_closing_tag():
    """test getter/setter for the closing_tag attribute"""
    tag = wraptext("ref")
    node = Tag(tag, wraptext("foobar"))
    assert tag is node.closing_tag
    node.closing_tag = "ref {{ignore me}}"
    parsed = wrap([Text("ref "), Template(wraptext("ignore me"))])
    assert_wikicode_equal(parsed, node.closing_tag)
    assert "<ref>foobar</ref {{ignore me}}>" == node


def test_wiki_style_separator():
    """test getter/setter for wiki_style_separator attribute"""
    node = Tag(wraptext("table"), wraptext("\n"))
    assert None is node.wiki_style_separator
    node.wiki_style_separator = "|"
    assert "|" == node.wiki_style_separator
    node.wiki_markup = "{"
    assert "{|\n{" == node
    node2 = Tag(wraptext("table"), wraptext("\n"), wiki_style_separator="|")
    assert "|" == node2.wiki_style_separator


def test_closing_wiki_markup():
    """test getter/setter for closing_wiki_markup attribute"""
    node = Tag(wraptext("table"), wraptext("\n"))
    assert None is node.closing_wiki_markup
    node.wiki_markup = "{|"
    assert "{|" == node.closing_wiki_markup
    node.closing_wiki_markup = "|}"
    assert "|}" == node.closing_wiki_markup
    assert "{|\n|}" == node
    node.wiki_markup = "!!"
    assert "|}" == node.closing_wiki_markup
    assert "!!\n|}" == node
    node.wiki_markup = False
    assert node.closing_wiki_markup is None
    assert "<table>\n</table>" == node
    node2 = Tag(
        wraptext("table"),
        wraptext("\n"),
        attrs=[agen("id", "foo")],
        wiki_markup="{|",
        closing_wiki_markup="|}",
    )
    assert "|}" == node2.closing_wiki_markup
    assert '{| id="foo"\n|}' == node2


def test_has():
    """test Tag.has()"""
    node = Tag(wraptext("ref"), wraptext("cite"), [agen("name", "foo")])
    assert node.has("name") is True
    assert node.has("  name  ") is True
    assert node.has(wraptext("name")) is True
    assert node.has("Name") is False
    assert node.has("foo") is False

    attrs = [
        agen("id", "foo"),
        agenp("class", "bar", "  ", "\n", "\n"),
        agen("foo", "bar"),
        agenpnv("foo", " ", "  \n ", " \t"),
    ]
    node2 = Tag(wraptext("div"), attrs=attrs, self_closing=True)
    assert node2.has("id") is True
    assert node2.has("class") is True
    assert (
        node2.has(attrs[1].pad_first + str(attrs[1].name) + attrs[1].pad_before_eq)
        is True
    )
    assert node2.has(attrs[3]) is True
    assert node2.has(str(attrs[3])) is True
    assert node2.has("idclass") is False
    assert node2.has("id class") is False
    assert node2.has("id=foo") is False


def test_get():
    """test Tag.get()"""
    attrs = [agen("name", "foo")]
    node = Tag(wraptext("ref"), wraptext("cite"), attrs)
    assert attrs[0] is node.get("name")
    assert attrs[0] is node.get("  name  ")
    assert attrs[0] is node.get(wraptext("name"))
    with pytest.raises(ValueError):
        node.get("Name")
    with pytest.raises(ValueError):
        node.get("foo")

    attrs = [
        agen("id", "foo"),
        agenp("class", "bar", "  ", "\n", "\n"),
        agen("foo", "bar"),
        agenpnv("foo", " ", "  \n ", " \t"),
    ]
    node2 = Tag(wraptext("div"), attrs=attrs, self_closing=True)
    assert attrs[0] is node2.get("id")
    assert attrs[1] is node2.get("class")
    assert attrs[1] is node2.get(
        attrs[1].pad_first + str(attrs[1].name) + attrs[1].pad_before_eq
    )
    assert attrs[3] is node2.get(attrs[3])
    assert attrs[3] is node2.get(str(attrs[3]))
    assert attrs[3] is node2.get(" foo")
    with pytest.raises(ValueError):
        node2.get("idclass")
    with pytest.raises(ValueError):
        node2.get("id class")
    with pytest.raises(ValueError):
        node2.get("id=foo")


def test_add():
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
    assert attr1 == node.attributes[0]
    assert attr2 == node.attributes[1]
    assert attr3 == node.attributes[2]
    assert attr4 == node.attributes[3]
    assert attr5 == node.attributes[4]
    assert attr6 == node.attributes[5]
    assert attr7 == node.attributes[6]
    assert attr7 == node.get("name")
    assert_wikicode_equal(
        wrap([Template(wraptext("foobar"))]), node.attributes[5].value
    )
    assert (
        "".join(
            ("<ref", attr1, attr2, attr3, attr4, attr5, attr6, attr7, ">cite</ref>")
        )
        == node
    )
    with pytest.raises(ValueError):
        node.add("name", "foo", quotes="bar")
    with pytest.raises(ValueError):
        node.add("name", "a bc d", quotes=None)


def test_remove():
    """test Tag.remove()"""
    attrs = [
        agen("id", "foo"),
        agenp("class", "bar", "  ", "\n", "\n"),
        agen("foo", "bar"),
        agenpnv("foo", " ", "  \n ", " \t"),
    ]
    node = Tag(wraptext("div"), attrs=attrs, self_closing=True)
    node.remove("class")
    assert '<div id="foo" foo="bar" foo  \n />' == node
    node.remove("foo")
    assert '<div id="foo"/>' == node
    with pytest.raises(ValueError):
        node.remove("foo")
    node.remove("id")
    assert "<div/>" == node

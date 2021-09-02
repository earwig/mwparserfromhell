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
Test cases for the Attribute node extra.
"""

import pytest

from mwparserfromhell.nodes import Template
from mwparserfromhell.nodes.extras import Attribute
from .conftest import assert_wikicode_equal, wrap, wraptext


def test_str():
    """test Attribute.__str__()"""
    node = Attribute(wraptext("foo"))
    assert " foo" == str(node)
    node2 = Attribute(wraptext("foo"), wraptext("bar"))
    assert ' foo="bar"' == str(node2)
    node3 = Attribute(wraptext("a"), wraptext("b"), '"', "", " ", "   ")
    assert 'a =   "b"' == str(node3)
    node4 = Attribute(wraptext("a"), wraptext("b"), "'", "", " ", "   ")
    assert "a =   'b'" == str(node4)
    node5 = Attribute(wraptext("a"), wraptext("b"), None, "", " ", "   ")
    assert "a =   b" == str(node5)
    node6 = Attribute(wraptext("a"), wrap([]), None, " ", "", " ")
    assert " a= " == str(node6)


def test_name():
    """test getter/setter for the name attribute"""
    name = wraptext("id")
    node = Attribute(name, wraptext("bar"))
    assert name is node.name
    node.name = "{{id}}"
    assert_wikicode_equal(wrap([Template(wraptext("id"))]), node.name)


def test_value():
    """test getter/setter for the value attribute"""
    value = wraptext("foo")
    node = Attribute(wraptext("id"), value)
    assert value is node.value
    node.value = "{{bar}}"
    assert_wikicode_equal(wrap([Template(wraptext("bar"))]), node.value)
    node.value = None
    assert None is node.value
    node2 = Attribute(wraptext("id"), wraptext("foo"), None)
    node2.value = "foo bar baz"
    assert_wikicode_equal(wraptext("foo bar baz"), node2.value)
    assert '"' == node2.quotes
    node2.value = 'foo "bar" baz'
    assert_wikicode_equal(wraptext('foo "bar" baz'), node2.value)
    assert "'" == node2.quotes
    node2.value = "foo 'bar' baz"
    assert_wikicode_equal(wraptext("foo 'bar' baz"), node2.value)
    assert '"' == node2.quotes
    node2.value = "fo\"o 'bar' b\"az"
    assert_wikicode_equal(wraptext("fo\"o 'bar' b\"az"), node2.value)
    assert '"' == node2.quotes


def test_quotes():
    """test getter/setter for the quotes attribute"""
    node1 = Attribute(wraptext("id"), wraptext("foo"), None)
    node2 = Attribute(wraptext("id"), wraptext("bar"))
    node3 = Attribute(wraptext("id"), wraptext("foo bar baz"))
    assert None is node1.quotes
    assert '"' == node2.quotes
    node1.quotes = "'"
    node2.quotes = None
    assert "'" == node1.quotes
    assert None is node2.quotes
    with pytest.raises(ValueError):
        node1.__setattr__("quotes", "foobar")
    with pytest.raises(ValueError):
        node3.__setattr__("quotes", None)
    with pytest.raises(ValueError):
        Attribute(wraptext("id"), wraptext("foo bar baz"), None)


def test_padding():
    """test getter/setter for the padding attributes"""
    for pad in ["pad_first", "pad_before_eq", "pad_after_eq"]:
        node = Attribute(wraptext("id"), wraptext("foo"), **{pad: "\n"})
        assert "\n" == getattr(node, pad)
        setattr(node, pad, " ")
        assert " " == getattr(node, pad)
        setattr(node, pad, None)
        assert "" == getattr(node, pad)
        with pytest.raises(ValueError):
            node.__setattr__(pad, True)

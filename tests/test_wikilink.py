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
Test cases for the Wikilink node.
"""

import pytest

from mwparserfromhell.nodes import Text, Wikilink
from .conftest import assert_wikicode_equal, wrap, wraptext


def test_str():
    """test Wikilink.__str__()"""
    node = Wikilink(wraptext("foobar"))
    assert "[[foobar]]" == str(node)
    node2 = Wikilink(wraptext("foo"), wraptext("bar"))
    assert "[[foo|bar]]" == str(node2)


def test_children():
    """test Wikilink.__children__()"""
    node1 = Wikilink(wraptext("foobar"))
    node2 = Wikilink(wraptext("foo"), wrap([Text("bar"), Text("baz")]))
    gen1 = node1.__children__()
    gen2 = node2.__children__()
    assert node1.title == next(gen1)
    assert node2.title == next(gen2)
    assert node2.text == next(gen2)
    with pytest.raises(StopIteration):
        next(gen1)
    with pytest.raises(StopIteration):
        next(gen2)


def test_strip():
    """test Wikilink.__strip__()"""
    node = Wikilink(wraptext("foobar"))
    node2 = Wikilink(wraptext("foo"), wraptext("bar"))
    assert "foobar" == node.__strip__()
    assert "bar" == node2.__strip__()


def test_showtree():
    """test Wikilink.__showtree__()"""
    output = []
    getter, marker = object(), object()
    get = lambda code: output.append((getter, code))
    mark = lambda: output.append(marker)
    node1 = Wikilink(wraptext("foobar"))
    node2 = Wikilink(wraptext("foo"), wraptext("bar"))
    node1.__showtree__(output.append, get, mark)
    node2.__showtree__(output.append, get, mark)
    valid = [
        "[[",
        (getter, node1.title),
        "]]",
        "[[",
        (getter, node2.title),
        "    | ",
        marker,
        (getter, node2.text),
        "]]",
    ]
    assert valid == output


def test_title():
    """test getter/setter for the title attribute"""
    title = wraptext("foobar")
    node1 = Wikilink(title)
    node2 = Wikilink(title, wraptext("baz"))
    assert title is node1.title
    assert title is node2.title
    node1.title = "héhehé"
    node2.title = "héhehé"
    assert_wikicode_equal(wraptext("héhehé"), node1.title)
    assert_wikicode_equal(wraptext("héhehé"), node2.title)


def test_text():
    """test getter/setter for the text attribute"""
    text = wraptext("baz")
    node1 = Wikilink(wraptext("foobar"))
    node2 = Wikilink(wraptext("foobar"), text)
    assert None is node1.text
    assert text is node2.text
    node1.text = "buzz"
    node2.text = None
    assert_wikicode_equal(wraptext("buzz"), node1.text)
    assert None is node2.text

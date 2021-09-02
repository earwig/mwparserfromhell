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
Test cases for the Heading node.
"""

import pytest

from mwparserfromhell.nodes import Heading, Text
from .conftest import assert_wikicode_equal, wrap, wraptext


def test_str():
    """test Heading.__str__()"""
    node = Heading(wraptext("foobar"), 2)
    assert "==foobar==" == str(node)
    node2 = Heading(wraptext(" zzz "), 5)
    assert "===== zzz =====" == str(node2)


def test_children():
    """test Heading.__children__()"""
    node = Heading(wrap([Text("foo"), Text("bar")]), 3)
    gen = node.__children__()
    assert node.title == next(gen)
    with pytest.raises(StopIteration):
        next(gen)


def test_strip():
    """test Heading.__strip__()"""
    node = Heading(wraptext("foobar"), 3)
    assert "foobar" == node.__strip__()


def test_showtree():
    """test Heading.__showtree__()"""
    output = []
    getter = object()
    get = lambda code: output.append((getter, code))
    node1 = Heading(wraptext("foobar"), 3)
    node2 = Heading(wraptext(" baz "), 4)
    node1.__showtree__(output.append, get, None)
    node2.__showtree__(output.append, get, None)
    valid = ["===", (getter, node1.title), "===", "====", (getter, node2.title), "===="]
    assert valid == output


def test_title():
    """test getter/setter for the title attribute"""
    title = wraptext("foobar")
    node = Heading(title, 3)
    assert title is node.title
    node.title = "héhehé"
    assert_wikicode_equal(wraptext("héhehé"), node.title)


def test_level():
    """test getter/setter for the level attribute"""
    node = Heading(wraptext("foobar"), 3)
    assert 3 == node.level
    node.level = 5
    assert 5 == node.level
    with pytest.raises(ValueError):
        node.__setattr__("level", 0)
    with pytest.raises(ValueError):
        node.__setattr__("level", 7)
    with pytest.raises(ValueError):
        node.__setattr__("level", "abc")
    with pytest.raises(ValueError):
        node.__setattr__("level", False)

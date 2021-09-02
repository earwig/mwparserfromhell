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
Test cases for the Argument node.
"""

import pytest

from mwparserfromhell.nodes import Argument, Text
from .conftest import assert_wikicode_equal, wrap, wraptext


def test_str():
    """test Argument.__str__()"""
    node = Argument(wraptext("foobar"))
    assert "{{{foobar}}}" == str(node)
    node2 = Argument(wraptext("foo"), wraptext("bar"))
    assert "{{{foo|bar}}}" == str(node2)


def test_children():
    """test Argument.__children__()"""
    node1 = Argument(wraptext("foobar"))
    node2 = Argument(wraptext("foo"), wrap([Text("bar"), Text("baz")]))
    gen1 = node1.__children__()
    gen2 = node2.__children__()
    assert node1.name is next(gen1)
    assert node2.name is next(gen2)
    assert node2.default is next(gen2)
    with pytest.raises(StopIteration):
        next(gen1)
    with pytest.raises(StopIteration):
        next(gen2)


def test_strip():
    """test Argument.__strip__()"""
    node1 = Argument(wraptext("foobar"))
    node2 = Argument(wraptext("foo"), wraptext("bar"))
    assert node1.__strip__() is None
    assert "bar" == node2.__strip__()


def test_showtree():
    """test Argument.__showtree__()"""
    output = []
    getter, marker = object(), object()
    get = lambda code: output.append((getter, code))
    mark = lambda: output.append(marker)
    node1 = Argument(wraptext("foobar"))
    node2 = Argument(wraptext("foo"), wraptext("bar"))
    node1.__showtree__(output.append, get, mark)
    node2.__showtree__(output.append, get, mark)
    valid = [
        "{{{",
        (getter, node1.name),
        "}}}",
        "{{{",
        (getter, node2.name),
        "    | ",
        marker,
        (getter, node2.default),
        "}}}",
    ]
    assert valid == output


def test_name():
    """test getter/setter for the name attribute"""
    name = wraptext("foobar")
    node1 = Argument(name)
    node2 = Argument(name, wraptext("baz"))
    assert name is node1.name
    assert name is node2.name
    node1.name = "héhehé"
    node2.name = "héhehé"
    assert_wikicode_equal(wraptext("héhehé"), node1.name)
    assert_wikicode_equal(wraptext("héhehé"), node2.name)


def test_default():
    """test getter/setter for the default attribute"""
    default = wraptext("baz")
    node1 = Argument(wraptext("foobar"))
    node2 = Argument(wraptext("foobar"), default)
    assert None is node1.default
    assert default is node2.default
    node1.default = "buzz"
    node2.default = None
    assert_wikicode_equal(wraptext("buzz"), node1.default)
    assert None is node2.default

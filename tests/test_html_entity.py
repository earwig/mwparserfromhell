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
Test cases for the HTMLEntity node.
"""

import pytest

from mwparserfromhell.nodes import HTMLEntity


def test_str():
    """test HTMLEntity.__str__()"""
    node1 = HTMLEntity("nbsp", named=True, hexadecimal=False)
    node2 = HTMLEntity("107", named=False, hexadecimal=False)
    node3 = HTMLEntity("6b", named=False, hexadecimal=True)
    node4 = HTMLEntity("6C", named=False, hexadecimal=True, hex_char="X")
    assert "&nbsp;" == str(node1)
    assert "&#107;" == str(node2)
    assert "&#x6b;" == str(node3)
    assert "&#X6C;" == str(node4)


def test_children():
    """test HTMLEntity.__children__()"""
    node = HTMLEntity("nbsp", named=True, hexadecimal=False)
    gen = node.__children__()
    with pytest.raises(StopIteration):
        next(gen)


def test_strip():
    """test HTMLEntity.__strip__()"""
    node1 = HTMLEntity("nbsp", named=True, hexadecimal=False)
    node2 = HTMLEntity("107", named=False, hexadecimal=False)
    node3 = HTMLEntity("e9", named=False, hexadecimal=True)

    assert "\xa0" == node1.__strip__(normalize=True)
    assert "&nbsp;" == node1.__strip__(normalize=False)
    assert "k" == node2.__strip__(normalize=True)
    assert "&#107;" == node2.__strip__(normalize=False)
    assert "é" == node3.__strip__(normalize=True)
    assert "&#xe9;" == node3.__strip__(normalize=False)


def test_showtree():
    """test HTMLEntity.__showtree__()"""
    output = []
    node1 = HTMLEntity("nbsp", named=True, hexadecimal=False)
    node2 = HTMLEntity("107", named=False, hexadecimal=False)
    node3 = HTMLEntity("e9", named=False, hexadecimal=True)
    node1.__showtree__(output.append, None, None)
    node2.__showtree__(output.append, None, None)
    node3.__showtree__(output.append, None, None)
    res = ["&nbsp;", "&#107;", "&#xe9;"]
    assert res == output


def test_value():
    """test getter/setter for the value attribute"""
    node1 = HTMLEntity("nbsp")
    node2 = HTMLEntity("107")
    node3 = HTMLEntity("e9")
    assert "nbsp" == node1.value
    assert "107" == node2.value
    assert "e9" == node3.value

    node1.value = "ffa4"
    node2.value = 72
    node3.value = "Sigma"
    assert "ffa4" == node1.value
    assert node1.named is False
    assert node1.hexadecimal is True
    assert "72" == node2.value
    assert node2.named is False
    assert node2.hexadecimal is False
    assert "Sigma" == node3.value
    assert node3.named is True
    assert node3.hexadecimal is False

    node1.value = "10FFFF"
    node2.value = 110000
    node2.value = 1114111
    with pytest.raises(ValueError):
        node3.__setattr__("value", "")
    with pytest.raises(ValueError):
        node3.__setattr__("value", "foobar")
    with pytest.raises(ValueError):
        node3.__setattr__("value", True)
    with pytest.raises(ValueError):
        node3.__setattr__("value", -1)
    with pytest.raises(ValueError):
        node1.__setattr__("value", 110000)
    with pytest.raises(ValueError):
        node1.__setattr__("value", "1114112")
    with pytest.raises(ValueError):
        node1.__setattr__("value", "12FFFF")


def test_named():
    """test getter/setter for the named attribute"""
    node1 = HTMLEntity("nbsp")
    node2 = HTMLEntity("107")
    node3 = HTMLEntity("e9")
    assert node1.named is True
    assert node2.named is False
    assert node3.named is False
    node1.named = 1
    node2.named = 0
    node3.named = 0
    assert node1.named is True
    assert node2.named is False
    assert node3.named is False
    with pytest.raises(ValueError):
        node1.__setattr__("named", False)
    with pytest.raises(ValueError):
        node2.__setattr__("named", True)
    with pytest.raises(ValueError):
        node3.__setattr__("named", True)


def test_hexadecimal():
    """test getter/setter for the hexadecimal attribute"""
    node1 = HTMLEntity("nbsp")
    node2 = HTMLEntity("107")
    node3 = HTMLEntity("e9")
    assert node1.hexadecimal is False
    assert node2.hexadecimal is False
    assert node3.hexadecimal is True
    node1.hexadecimal = False
    node2.hexadecimal = True
    node3.hexadecimal = False
    assert node1.hexadecimal is False
    assert node2.hexadecimal is True
    assert node3.hexadecimal is False
    with pytest.raises(ValueError):
        node1.__setattr__("hexadecimal", True)


def test_hex_char():
    """test getter/setter for the hex_char attribute"""
    node1 = HTMLEntity("e9")
    node2 = HTMLEntity("e9", hex_char="X")
    assert "x" == node1.hex_char
    assert "X" == node2.hex_char
    node1.hex_char = "X"
    node2.hex_char = "x"
    assert "X" == node1.hex_char
    assert "x" == node2.hex_char
    with pytest.raises(ValueError):
        node1.__setattr__("hex_char", 123)
    with pytest.raises(ValueError):
        node1.__setattr__("hex_char", "foobar")
    with pytest.raises(ValueError):
        node1.__setattr__("hex_char", True)


def test_normalize():
    """test getter/setter for the normalize attribute"""
    node1 = HTMLEntity("nbsp")
    node2 = HTMLEntity("107")
    node3 = HTMLEntity("e9")
    node4 = HTMLEntity("1f648")
    node5 = HTMLEntity("-2")
    node6 = HTMLEntity("110000", named=False, hexadecimal=True)
    assert "\xa0" == node1.normalize()
    assert "k" == node2.normalize()
    assert "é" == node3.normalize()
    assert "\U0001F648" == node4.normalize()
    with pytest.raises(ValueError):
        node5.normalize()
    with pytest.raises(ValueError):
        node6.normalize()

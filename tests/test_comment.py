# Copyright (C) 2012-2025 Ben Kurtovic <ben.kurtovic@gmail.com>
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
Test cases for the Comment node.
"""

from __future__ import annotations

import pytest

from mwparserfromhell.nodes import Comment


def test_str():
    """test Comment.__str__()"""
    node = Comment("foobar")
    assert "<!--foobar-->" == str(node)


def test_children():
    """test Comment.__children__()"""
    node = Comment("foobar")
    gen = node.__children__()
    with pytest.raises(StopIteration):
        next(gen)


def test_strip():
    """test Comment.__strip__()"""
    node = Comment("foobar")
    assert node.__strip__() is None


def test_showtree():
    """test Comment.__showtree__()"""
    output = []
    node = Comment("foobar")
    node.__showtree__(output.append, None, None)
    assert ["<!--foobar-->"] == output


def test_contents():
    """test getter/setter for the contents attribute"""
    node = Comment("foobar")
    assert "foobar" == node.contents
    node.contents = "barfoo"
    assert "barfoo" == node.contents

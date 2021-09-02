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
Test cases for the ExternalLink node.
"""

import pytest

from mwparserfromhell.nodes import ExternalLink, Text
from .conftest import assert_wikicode_equal, wrap, wraptext


def test_str():
    """test ExternalLink.__str__()"""
    node = ExternalLink(wraptext("http://example.com/"), brackets=False)
    assert "http://example.com/" == str(node)
    node2 = ExternalLink(wraptext("http://example.com/"))
    assert "[http://example.com/]" == str(node2)
    node3 = ExternalLink(wraptext("http://example.com/"), wrap([]))
    assert "[http://example.com/ ]" == str(node3)
    node4 = ExternalLink(wraptext("http://example.com/"), wraptext("Example Web Page"))
    assert "[http://example.com/ Example Web Page]" == str(node4)


def test_children():
    """test ExternalLink.__children__()"""
    node1 = ExternalLink(wraptext("http://example.com/"), brackets=False)
    node2 = ExternalLink(
        wraptext("http://example.com/"), wrap([Text("Example"), Text("Page")])
    )
    gen1 = node1.__children__()
    gen2 = node2.__children__()
    assert node1.url == next(gen1)
    assert node2.url == next(gen2)
    assert node2.title == next(gen2)
    with pytest.raises(StopIteration):
        next(gen1)
    with pytest.raises(StopIteration):
        next(gen2)


def test_strip():
    """test ExternalLink.__strip__()"""
    node1 = ExternalLink(wraptext("http://example.com"), brackets=False)
    node2 = ExternalLink(wraptext("http://example.com"))
    node3 = ExternalLink(wraptext("http://example.com"), wrap([]))
    node4 = ExternalLink(wraptext("http://example.com"), wraptext("Link"))

    assert "http://example.com" == node1.__strip__()
    assert node2.__strip__() is None
    assert node3.__strip__() is None
    assert "Link" == node4.__strip__()


def test_showtree():
    """test ExternalLink.__showtree__()"""
    output = []
    getter, marker = object(), object()
    get = lambda code: output.append((getter, code))
    mark = lambda: output.append(marker)
    node1 = ExternalLink(wraptext("http://example.com"), brackets=False)
    node2 = ExternalLink(wraptext("http://example.com"), wraptext("Link"))
    node1.__showtree__(output.append, get, mark)
    node2.__showtree__(output.append, get, mark)
    valid = [(getter, node1.url), "[", (getter, node2.url), (getter, node2.title), "]"]
    assert valid == output


def test_url():
    """test getter/setter for the url attribute"""
    url = wraptext("http://example.com/")
    node1 = ExternalLink(url, brackets=False)
    node2 = ExternalLink(url, wraptext("Example"))
    assert url is node1.url
    assert url is node2.url
    node1.url = "mailto:héhehé@spam.com"
    node2.url = "mailto:héhehé@spam.com"
    assert_wikicode_equal(wraptext("mailto:héhehé@spam.com"), node1.url)
    assert_wikicode_equal(wraptext("mailto:héhehé@spam.com"), node2.url)


def test_title():
    """test getter/setter for the title attribute"""
    title = wraptext("Example!")
    node1 = ExternalLink(wraptext("http://example.com/"), brackets=False)
    node2 = ExternalLink(wraptext("http://example.com/"), title)
    assert None is node1.title
    assert title is node2.title
    node2.title = None
    assert None is node2.title
    node2.title = "My Website"
    assert_wikicode_equal(wraptext("My Website"), node2.title)


def test_brackets():
    """test getter/setter for the brackets attribute"""
    node1 = ExternalLink(wraptext("http://example.com/"), brackets=False)
    node2 = ExternalLink(wraptext("http://example.com/"), wraptext("Link"))
    assert node1.brackets is False
    assert node2.brackets is True
    node1.brackets = True
    node2.brackets = False
    assert node1.brackets is True
    assert node2.brackets is False
    assert "[http://example.com/]" == str(node1)
    assert "http://example.com/" == str(node2)

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
Test cases for the Parameter node extra.
"""

import pytest

from mwparserfromhell.nodes.extras import Parameter
from .conftest import assert_wikicode_equal, wraptext


def test_str():
    """test Parameter.__str__()"""
    node = Parameter(wraptext("1"), wraptext("foo"), showkey=False)
    assert "foo" == str(node)
    node2 = Parameter(wraptext("foo"), wraptext("bar"))
    assert "foo=bar" == str(node2)


def test_name():
    """test getter/setter for the name attribute"""
    name1 = wraptext("1")
    name2 = wraptext("foobar")
    node1 = Parameter(name1, wraptext("foobar"), showkey=False)
    node2 = Parameter(name2, wraptext("baz"))
    assert name1 is node1.name
    assert name2 is node2.name
    node1.name = "héhehé"
    node2.name = "héhehé"
    assert_wikicode_equal(wraptext("héhehé"), node1.name)
    assert_wikicode_equal(wraptext("héhehé"), node2.name)


def test_value():
    """test getter/setter for the value attribute"""
    value = wraptext("bar")
    node = Parameter(wraptext("foo"), value)
    assert value is node.value
    node.value = "héhehé"
    assert_wikicode_equal(wraptext("héhehé"), node.value)


def test_showkey():
    """test getter/setter for the showkey attribute"""
    node1 = Parameter(wraptext("1"), wraptext("foo"), showkey=False)
    node2 = Parameter(wraptext("foo"), wraptext("bar"))
    assert node1.showkey is False
    assert node2.showkey is True
    node1.showkey = True
    assert node1.showkey is True
    node1.showkey = ""
    assert node1.showkey is False
    with pytest.raises(ValueError):
        node2.__setattr__("showkey", False)

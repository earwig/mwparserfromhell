# Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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
Tests for the utils module, which provides parse_anything().
"""

import pytest

from mwparserfromhell.nodes import Template, Text
from mwparserfromhell.utils import parse_anything
from .conftest import assert_wikicode_equal, wrap, wraptext


@pytest.mark.parametrize(
    "test,valid",
    [
        (wraptext("foobar"), wraptext("foobar")),
        (Template(wraptext("spam")), wrap([Template(wraptext("spam"))])),
        ("fóóbar", wraptext("fóóbar")),
        (b"foob\xc3\xa1r", wraptext("foobár")),
        (123, wraptext("123")),
        (True, wraptext("True")),
        (None, wrap([])),
        ([Text("foo"), Text("bar"), Text("baz")], wraptext("foo", "bar", "baz")),
        (
            [wraptext("foo"), Text("bar"), "baz", 123, 456],
            wraptext("foo", "bar", "baz", "123", "456"),
        ),
        ([[[([[((("foo",),),)], "bar"],)]]], wraptext("foo", "bar")),
    ],
)
def test_parse_anything_valid(test, valid):
    """tests for valid input to utils.parse_anything()"""
    assert_wikicode_equal(valid, parse_anything(test))


@pytest.mark.parametrize(
    "invalid", [Ellipsis, object, object(), type, ["foo", [object]]]
)
def test_parse_anything_invalid(invalid):
    """tests for invalid input to utils.parse_anything()"""
    with pytest.raises(ValueError):
        parse_anything(invalid)

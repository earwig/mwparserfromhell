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
Tests for the Parser class itself, which tokenizes and builds nodes.
"""

import pytest

from mwparserfromhell import parser
from mwparserfromhell.nodes import Tag, Template, Text, Wikilink
from mwparserfromhell.nodes.extras import Parameter
from .conftest import assert_wikicode_equal, wrap, wraptext


@pytest.fixture()
def pyparser():
    """make sure the correct tokenizer is used"""
    restore = parser.use_c
    if parser.use_c:
        parser.use_c = False
    yield
    parser.use_c = restore


def test_use_c(pyparser):
    assert parser.Parser()._tokenizer.USES_C is False


def test_parsing(pyparser):
    """integration test for parsing overall"""
    text = "this is text; {{this|is=a|template={{with|[[links]]|in}}it}}"
    expected = wrap(
        [
            Text("this is text; "),
            Template(
                wraptext("this"),
                [
                    Parameter(wraptext("is"), wraptext("a")),
                    Parameter(
                        wraptext("template"),
                        wrap(
                            [
                                Template(
                                    wraptext("with"),
                                    [
                                        Parameter(
                                            wraptext("1"),
                                            wrap([Wikilink(wraptext("links"))]),
                                            showkey=False,
                                        ),
                                        Parameter(
                                            wraptext("2"), wraptext("in"), showkey=False
                                        ),
                                    ],
                                ),
                                Text("it"),
                            ]
                        ),
                    ),
                ],
            ),
        ]
    )
    actual = parser.Parser().parse(text)
    assert_wikicode_equal(expected, actual)


def test_skip_style_tags(pyparser):
    """test Parser.parse(skip_style_tags=True)"""
    text = "This is an example with ''italics''!"
    a = wrap(
        [
            Text("This is an example with "),
            Tag(wraptext("i"), wraptext("italics"), wiki_markup="''"),
            Text("!"),
        ]
    )
    b = wraptext("This is an example with ''italics''!")

    with_style = parser.Parser().parse(text, skip_style_tags=False)
    without_style = parser.Parser().parse(text, skip_style_tags=True)
    assert_wikicode_equal(a, with_style)
    assert_wikicode_equal(b, without_style)

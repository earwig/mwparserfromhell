# Copyright (C) 2012-2021 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from mwparserfromhell.nodes import (
    Argument,
    Comment,
    ExternalLink,
    Heading,
    HTMLEntity,
    Tag,
    Template,
    Text,
    Wikilink,
)
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode

wrap = lambda L: Wikicode(SmartList(L))
wraptext = lambda *args: wrap([Text(t) for t in args])


def _assert_node_equal(expected, actual):
    """Assert that two Nodes have the same type and have the same data."""
    registry = {
        Argument: _assert_argument_node_equal,
        Comment: _assert_comment_node_equal,
        ExternalLink: _assert_external_link_node_equal,
        Heading: _assert_heading_node_equal,
        HTMLEntity: _assert_html_entity_node_equal,
        Tag: _assert_tag_node_equal,
        Template: _assert_template_node_equal,
        Text: _assert_text_node_equal,
        Wikilink: _assert_wikilink_node_equal,
    }
    # pylint: disable=unidiomatic-typecheck
    assert type(expected) == type(actual)
    registry[type(expected)](expected, actual)


def _assert_argument_node_equal(expected, actual):
    """Assert that two Argument nodes have the same data."""
    assert_wikicode_equal(expected.name, actual.name)
    if expected.default is not None:
        assert_wikicode_equal(expected.default, actual.default)
    else:
        assert actual.default is None


def _assert_comment_node_equal(expected, actual):
    """Assert that two Comment nodes have the same data."""
    assert expected.contents == actual.contents


def _assert_external_link_node_equal(expected, actual):
    """Assert that two ExternalLink nodes have the same data."""
    assert_wikicode_equal(expected.url, actual.url)
    if expected.title is not None:
        assert_wikicode_equal(expected.title, actual.title)
    else:
        assert actual.title is None
    assert expected.brackets is actual.brackets
    assert expected.suppress_space is actual.suppress_space


def _assert_heading_node_equal(expected, actual):
    """Assert that two Heading nodes have the same data."""
    assert_wikicode_equal(expected.title, actual.title)
    assert expected.level == actual.level


def _assert_html_entity_node_equal(expected, actual):
    """Assert that two HTMLEntity nodes have the same data."""
    assert expected.value == actual.value
    assert expected.named is actual.named
    assert expected.hexadecimal is actual.hexadecimal
    assert expected.hex_char == actual.hex_char


def _assert_tag_node_equal(expected, actual):
    """Assert that two Tag nodes have the same data."""
    assert_wikicode_equal(expected.tag, actual.tag)
    if expected.contents is not None:
        assert_wikicode_equal(expected.contents, actual.contents)
    else:
        assert actual.contents is None
    length = len(expected.attributes)
    assert length == len(actual.attributes)
    for i in range(length):
        exp_attr = expected.attributes[i]
        act_attr = actual.attributes[i]
        assert_wikicode_equal(exp_attr.name, act_attr.name)
        if exp_attr.value is not None:
            assert_wikicode_equal(exp_attr.value, act_attr.value)
            assert exp_attr.quotes == act_attr.quotes
        else:
            assert act_attr.value is None
        assert exp_attr.pad_first == act_attr.pad_first
        assert exp_attr.pad_before_eq == act_attr.pad_before_eq
        assert exp_attr.pad_after_eq == act_attr.pad_after_eq
    assert expected.wiki_markup == actual.wiki_markup
    assert expected.self_closing is actual.self_closing
    assert expected.invalid is actual.invalid
    assert expected.implicit is actual.implicit
    assert expected.padding == actual.padding
    assert_wikicode_equal(expected.closing_tag, actual.closing_tag)


def _assert_template_node_equal(expected, actual):
    """Assert that two Template nodes have the same data."""
    assert_wikicode_equal(expected.name, actual.name)
    length = len(expected.params)
    assert length == len(actual.params)
    for i in range(length):
        exp_param = expected.params[i]
        act_param = actual.params[i]
        assert_wikicode_equal(exp_param.name, act_param.name)
        assert_wikicode_equal(exp_param.value, act_param.value)
        assert exp_param.showkey is act_param.showkey


def _assert_text_node_equal(expected, actual):
    """Assert that two Text nodes have the same data."""
    assert expected.value == actual.value


def _assert_wikilink_node_equal(expected, actual):
    """Assert that two Wikilink nodes have the same data."""
    assert_wikicode_equal(expected.title, actual.title)
    if expected.text is not None:
        assert_wikicode_equal(expected.text, actual.text)
    else:
        assert actual.text is None


def assert_wikicode_equal(expected, actual):
    """Assert that two Wikicode objects have the same data."""
    assert isinstance(actual, Wikicode)
    length = len(expected.nodes)
    assert length == len(actual.nodes)
    for i in range(length):
        _assert_node_equal(expected.get(i), actual.get(i))

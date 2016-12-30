# -*- coding: utf-8  -*-
#
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

from __future__ import unicode_literals

from . import tokens, ParserError
from ..compat import str
from ..nodes import (Argument, Comment, ExternalLink, Heading, HTMLEntity, Tag,
                     Template, Text, Wikilink)
from ..nodes.extras import Attribute, Parameter
from ..smart_list import SmartList
from ..wikicode import Wikicode

__all__ = ["Builder"]

_HANDLERS = {
    tokens.Text: lambda self, token: Text(token.text)
}

def _add_handler(token_type):
    """Create a decorator that adds a handler function to the lookup table."""
    def decorator(func):
        """Add a handler function to the lookup table."""
        _HANDLERS[token_type] = func
        return func
    return decorator


class Builder(object):
    """Builds a tree of nodes out of a sequence of tokens.

    To use, pass a list of :class:`.Token`\ s to the :meth:`build` method. The
    list will be exhausted as it is parsed and a :class:`.Wikicode` object
    containing the node tree will be returned.
    """

    def __init__(self):
        self._tokens = []
        self._stacks = []

    def _push(self):
        """Push a new node list onto the stack."""
        self._stacks.append([])

    def _pop(self):
        """Pop the current node list off of the stack.

        The raw node list is wrapped in a :class:`.SmartList` and then in a
        :class:`.Wikicode` object.
        """
        return Wikicode(SmartList(self._stacks.pop()))

    def _write(self, item):
        """Append a node to the current node list."""
        self._stacks[-1].append(item)

    def _handle_parameter(self, default):
        """Handle a case where a parameter is at the head of the tokens.

        *default* is the value to use if no parameter name is defined.
        """
        key = None
        showkey = False
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.TemplateParamEquals):
                key = self._pop()
                showkey = True
                self._push()
            elif isinstance(token, (tokens.TemplateParamSeparator,
                                    tokens.TemplateClose)):
                self._tokens.append(token)
                value = self._pop()
                if key is None:
                    key = Wikicode(SmartList([Text(str(default))]))
                return Parameter(key, value, showkey)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_parameter() missed a close token")

    @_add_handler(tokens.TemplateOpen)
    def _handle_template(self, token):
        """Handle a case where a template is at the head of the tokens."""
        params = []
        default = 1
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.TemplateParamSeparator):
                if not params:
                    name = self._pop()
                param = self._handle_parameter(default)
                params.append(param)
                if not param.showkey:
                    default += 1
            elif isinstance(token, tokens.TemplateClose):
                if not params:
                    name = self._pop()
                return Template(name, params)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_template() missed a close token")

    @_add_handler(tokens.ArgumentOpen)
    def _handle_argument(self, token):
        """Handle a case where an argument is at the head of the tokens."""
        name = None
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.ArgumentSeparator):
                name = self._pop()
                self._push()
            elif isinstance(token, tokens.ArgumentClose):
                if name is not None:
                    return Argument(name, self._pop())
                return Argument(self._pop())
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_argument() missed a close token")

    @_add_handler(tokens.WikilinkOpen)
    def _handle_wikilink(self, token):
        """Handle a case where a wikilink is at the head of the tokens."""
        title = None
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.WikilinkSeparator):
                title = self._pop()
                self._push()
            elif isinstance(token, tokens.WikilinkClose):
                if title is not None:
                    return Wikilink(title, self._pop())
                return Wikilink(self._pop())
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_wikilink() missed a close token")

    @_add_handler(tokens.ExternalLinkOpen)
    def _handle_external_link(self, token):
        """Handle when an external link is at the head of the tokens."""
        brackets, url = token.brackets, None
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.ExternalLinkSeparator):
                url = self._pop()
                self._push()
            elif isinstance(token, tokens.ExternalLinkClose):
                if url is not None:
                    return ExternalLink(url, self._pop(), brackets)
                return ExternalLink(self._pop(), brackets=brackets)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_external_link() missed a close token")

    @_add_handler(tokens.HTMLEntityStart)
    def _handle_entity(self, token):
        """Handle a case where an HTML entity is at the head of the tokens."""
        token = self._tokens.pop()
        if isinstance(token, tokens.HTMLEntityNumeric):
            token = self._tokens.pop()
            if isinstance(token, tokens.HTMLEntityHex):
                text = self._tokens.pop()
                self._tokens.pop()  # Remove HTMLEntityEnd
                return HTMLEntity(text.text, named=False, hexadecimal=True,
                                  hex_char=token.char)
            self._tokens.pop()  # Remove HTMLEntityEnd
            return HTMLEntity(token.text, named=False, hexadecimal=False)
        self._tokens.pop()  # Remove HTMLEntityEnd
        return HTMLEntity(token.text, named=True, hexadecimal=False)

    @_add_handler(tokens.HeadingStart)
    def _handle_heading(self, token):
        """Handle a case where a heading is at the head of the tokens."""
        level = token.level
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.HeadingEnd):
                title = self._pop()
                return Heading(title, level)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_heading() missed a close token")

    @_add_handler(tokens.CommentStart)
    def _handle_comment(self, token):
        """Handle a case where an HTML comment is at the head of the tokens."""
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.CommentEnd):
                contents = self._pop()
                return Comment(contents)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_comment() missed a close token")

    def _handle_attribute(self, start):
        """Handle a case where a tag attribute is at the head of the tokens."""
        name = quotes = None
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.TagAttrEquals):
                name = self._pop()
                self._push()
            elif isinstance(token, tokens.TagAttrQuote):
                quotes = token.char
            elif isinstance(token, (tokens.TagAttrStart, tokens.TagCloseOpen,
                                    tokens.TagCloseSelfclose)):
                self._tokens.append(token)
                if name:
                    value = self._pop()
                else:
                    name, value = self._pop(), None
                return Attribute(name, value, quotes, start.pad_first,
                                 start.pad_before_eq, start.pad_after_eq,
                                 check_quotes=False)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_attribute() missed a close token")

    @_add_handler(tokens.TagOpenOpen)
    def _handle_tag(self, token):
        """Handle a case where a tag is at the head of the tokens."""
        close_tokens = (tokens.TagCloseSelfclose, tokens.TagCloseClose)
        implicit, attrs, contents, closing_tag = False, [], None, None
        wiki_markup, invalid = token.wiki_markup, token.invalid or False
        wiki_style_separator, closing_wiki_markup = None, wiki_markup
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.TagAttrStart):
                attrs.append(self._handle_attribute(token))
            elif isinstance(token, tokens.TagCloseOpen):
                wiki_style_separator = token.wiki_markup
                padding = token.padding or ""
                tag = self._pop()
                self._push()
            elif isinstance(token, tokens.TagOpenClose):
                closing_wiki_markup = token.wiki_markup
                contents = self._pop()
                self._push()
            elif isinstance(token, close_tokens):
                if isinstance(token, tokens.TagCloseSelfclose):
                    closing_wiki_markup = token.wiki_markup
                    tag = self._pop()
                    self_closing = True
                    padding = token.padding or ""
                    implicit = token.implicit or False
                else:
                    self_closing = False
                    closing_tag = self._pop()
                return Tag(tag, contents, attrs, wiki_markup, self_closing,
                           invalid, implicit, padding, closing_tag,
                           wiki_style_separator, closing_wiki_markup)
            else:
                self._write(self._handle_token(token))
        raise ParserError("_handle_tag() missed a close token")

    def _handle_token(self, token):
        """Handle a single token."""
        try:
            return _HANDLERS[type(token)](self, token)
        except KeyError:
            err = "_handle_token() got unexpected {0}"
            raise ParserError(err.format(type(token).__name__))

    def build(self, tokenlist):
        """Build a Wikicode object from a list tokens and return it."""
        self._tokens = tokenlist
        self._tokens.reverse()
        self._push()
        while self._tokens:
            node = self._handle_token(self._tokens.pop())
            self._write(node)
        return self._pop()


del _add_handler

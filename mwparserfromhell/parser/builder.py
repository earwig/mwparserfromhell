# -*- coding: utf-8  -*-
#
# Copyright (C) 2012 Ben Kurtovic <ben.kurtovic@verizon.net>
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

from . import tokens
from ..compat import str
from ..nodes import (Argument, Comment, Heading, HTMLEntity, Tag, Template,
                     Text, Wikilink)
from ..nodes.extras import Attribute, Parameter
from ..smart_list import SmartList
from ..wikicode import Wikicode

__all__ = ["Builder"]

class Builder(object):
    """Combines a sequence of tokens into a tree of ``Wikicode`` objects.

    To use, pass a list of :py:class:`~.Token`\ s to the :py:meth:`build`
    method. The list will be exhausted as it is parsed and a
    :py:class:`~.Wikicode` object will be returned.
    """

    def __init__(self):
        self._tokens = []
        self._stacks = []

    def _wrap(self, nodes):
        """Properly wrap a list of nodes in a ``Wikicode`` object."""
        return Wikicode(SmartList(nodes))

    def _push(self):
        """Push a new node list onto the stack."""
        self._stacks.append([])

    def _pop(self, wrap=True):
        """Pop the current node list off of the stack.

        If *wrap* is ``True``, we will call :py:meth:`_wrap` on the list.
        """
        if wrap:
            return self._wrap(self._stacks.pop())
        return self._stacks.pop()

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
                if not key:
                    key = self._wrap([Text(str(default))])
                return Parameter(key, value, showkey)
            else:
                self._write(self._handle_token(token))

    def _handle_template(self):
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

    def _handle_argument(self):
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

    def _handle_wikilink(self):
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

    def _handle_entity(self):
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

    def _handle_comment(self):
        """Handle a case where a hidden comment is at the head of the tokens."""
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.CommentEnd):
                contents = self._pop()
                return Comment(contents)
            else:
                self._write(self._handle_token(token))

    def _handle_attribute(self):
        """Handle a case where a tag attribute is at the head of the tokens."""
        name, quoted = None, False
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.TagAttrEquals):
                name = self._pop()
                self._push()
            elif isinstance(token, tokens.TagAttrQuote):
                quoted = True
            elif isinstance(token, (tokens.TagAttrStart,
                                    tokens.TagCloseOpen)):
                self._tokens.append(token)
                if name is not None:
                    return Attribute(name, self._pop(), quoted)
                return Attribute(self._pop(), quoted=quoted)
            else:
                self._write(self._handle_token(token))

    def _handle_tag(self, token):
        """Handle a case where a tag is at the head of the tokens."""
        type_, showtag = token.type, token.showtag
        attrs = []
        self._push()
        while self._tokens:
            token = self._tokens.pop()
            if isinstance(token, tokens.TagAttrStart):
                attrs.append(self._handle_attribute())
            elif isinstance(token, tokens.TagCloseOpen):
                open_pad = token.padding
                tag = self._pop()
                self._push()
            elif isinstance(token, tokens.TagCloseSelfclose):
                tag = self._pop()
                return Tag(type_, tag, attrs=attrs, showtag=showtag,
                           self_closing=True, open_padding=token.padding)
            elif isinstance(token, tokens.TagOpenClose):
                contents = self._pop()
            elif isinstance(token, tokens.TagCloseClose):
                return Tag(type_, tag, contents, attrs, showtag, False,
                           open_pad, token.padding)
            else:
                self._write(self._handle_token(token))

    def _handle_token(self, token):
        """Handle a single token."""
        if isinstance(token, tokens.Text):
            return Text(token.text)
        elif isinstance(token, tokens.TemplateOpen):
            return self._handle_template()
        elif isinstance(token, tokens.ArgumentOpen):
            return self._handle_argument()
        elif isinstance(token, tokens.WikilinkOpen):
            return self._handle_wikilink()
        elif isinstance(token, tokens.HTMLEntityStart):
            return self._handle_entity()
        elif isinstance(token, tokens.HeadingStart):
            return self._handle_heading(token)
        elif isinstance(token, tokens.CommentStart):
            return self._handle_comment()
        elif isinstance(token, tokens.TagOpenOpen):
            return self._handle_tag(token)

    def build(self, tokenlist):
        """Build a Wikicode object from a list tokens and return it."""
        self._tokens = tokenlist
        self._tokens.reverse()
        self._push()
        while self._tokens:
            node = self._handle_token(self._tokens.pop())
            self._write(node)
        return self._pop()

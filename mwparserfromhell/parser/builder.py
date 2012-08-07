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

import re

from . import tokens
from .build_stack import BuildStack
from ..nodes import Heading, HTMLEntity, Tag, Template, Text
from ..nodes.extras import Attribute, Parameter

__all__ = ["Builder"]

class Builder(object):
    def __init__(self):
        self._tokens = []
        self._stack = BuildStack()

    def _handle_parameter(self, key):
        showkey = False
        self._stack.push()
        while self._tokens:
            token = self._tokens.pop(0)
            if isinstance(token, tokens.TEMPLATE_PARAM_EQUALS):
                key = self._stack.pop()
                showkey = True
                self._stack.push()
            elif isinstance(token, (tokens.TEMPLATE_PARAM_SEPARATOR,
                                    tokens.TEMPLATE_CLOSE)):
                self._tokens.insert(0, token)
                value = self._stack.pop()
                return Parameter(key, value, showkey)
            else:
                self._stack.write(self._handle_token())

    def _handle_template(self):
        params = []
        int_keys = set()
        int_key_range = {1}
        self._stack.push()
        while self._tokens:
            token = self._tokens.pop(0)
            if isinstance(token, tokens.TEMPLATE_PARAM_SEPARATOR):
                if not params:
                    name = self._stack.pop()
                param = self._handle_parameter(min(int_key_range - int_keys))
                if re.match(r"[1-9][0-9]*$", param.name.strip()):
                    int_keys.add(int(param.name))
                    int_key_range.add(len(int_keys) + 1)
                params.append(param)
            elif isinstance(token, tokens.TEMPLATE_CLOSE):
                if not params:
                    name = self._stack.pop()
                return Template(name, params)
            else:
                self._stack.write(self._handle_token())

    def _handle_entity(self):
        token = self._tokens.pop(0)
        if isinstance(token, tokens.HTML_ENTITY_NUMERIC):
            token = self._tokens.pop(0)
            if isinstance(token, tokens.HTML_ENTITY_HEX):
                token = self._tokens.pop(0)
                return HTMLEntity(token.text, named=False, hexadecimal=True)
            return HTMLEntity(token.text, named=False, hexadecimal=False)
        return HTMLEntity(token.text, named=True, hexadecimal=False)

    def _handle_heading(self, token):
        level = token.level
        self._stack.push()
        while self._tokens:
            token = self._tokens.pop(0)
            if isinstance(token, tokens.HEADING_BLOCK):
                title = self._stack.pop()
                return Heading(title, level)
            else:
                self._stack.write(self._handle_token())

    def _handle_attribute(self):
        name, quoted = None, False
        self._stack.push()
        while self._tokens:
            token = self._tokens.pop(0)
            if isinstance(token, tokens.TAG_ATTR_EQUALS):
                name = self._stack.pop()
                self._stack.push()
            elif isinstance(token, tokens.TAG_ATTR_QUOTE):
                quoted = True
            elif isinstance(token, (tokens.TAG_ATTR_START,
                                    tokens.TAG_CLOSE_OPEN)):
                self._tokens.insert(0, token)
                if name is not None:
                    return Attribute(name, self._stack.pop(), quoted)
                return Attribute(self._stack.pop(), quoted=quoted)
            else:
                self._stack.write(self._handle_token())

    def _handle_tag(self, token):
        type_, showtag = token.type, token.showtag
        attrs = []
        self._stack.push()
        while self._tokens:
            token = self._tokens.pop(0)
            if isinstance(token, tokens.TAG_ATTR_START):
                attrs.append(self._handle_attribute())
            elif isinstance(token, tokens.TAG_CLOSE_OPEN):
                open_pad = token.padding
                tag = self._stack.pop()
                self._stack.push()
            elif isinstance(token, tokens.TAG_CLOSE_SELFCLOSE):
                tag = self._stack.pop()
                return Tag(type_, tag, attrs=attrs, showtag=showtag,
                           self_closing=True, open_padding=token.padding)
            elif isinstance(token, tokens.TAG_OPEN_CLOSE):
                contents = self._stack.pop()
            elif isinstance(token, tokens.TAG_CLOSE_CLOSE):
                return Tag(type_, tag, contents, attrs, showtag, False,
                           open_pad, token.padding)
            else:
                self._stack.write(self._handle_token())

    def _handle_token(self):
        token = self._tokens.pop(0)
        if isinstance(token, tokens.TEXT):
            return Text(token.text)
        elif isinstance(token, tokens.TEMPLATE_OPEN):
            return self._handle_template()
        elif isinstance(token, tokens.HTML_ENTITY_START):
            return self._handle_entity()
        elif isinstance(token, tokens.HEADING_BLOCK):
            return self._handle_heading(token)
        elif isinstance(token, tokens.TAG_OPEN_OPEN):
            return self._handle_tag(token)

    def build(self, tokenlist):
        self._tokens = tokenlist
        self._stack.push()
        while self._tokens:
            self._stack.write(self._handle_token())
        return self._stack.pop()

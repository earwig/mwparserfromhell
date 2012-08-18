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

import htmlentitydefs
import re
import string

from . import contexts
from . import tokens

__all__ = ["Tokenizer"]

class BadRoute(Exception):
    pass

class Tokenizer(object):
    START = object()
    END = object()
    SENTINELS = ["{", "}", "[", "]", "|", "=", "&", END]
    REGEX = r"([{}\[\]|=&;])"

    def __init__(self):
        self._text = None
        self._head = 0
        self._stacks = []

    @property
    def _stack(self):
        return self._stacks[-1][0]

    @property
    def _context(self):
        return self._stacks[-1][1]

    @_context.setter
    def _context(self, value):
        self._stacks[-1][1] = value

    @property
    def _textbuffer(self):
        return self._stacks[-1][2]

    @_textbuffer.setter
    def _textbuffer(self, value):
        self._stacks[-1][2] = value

    def _push(self, context=0):
        self._stacks.append([[], context, []])

    def _push_textbuffer(self):
        if self._textbuffer:
            self._stack.append(tokens.Text(text="".join(self._textbuffer)))
            self._textbuffer = []

    def _pop(self):
        self._push_textbuffer()
        return self._stacks.pop()[0]

    def _write(self, token):
        self._push_textbuffer()
        self._stack.append(token)

    def _write_text(self, text):
        self._textbuffer.append(text)

    def _write_all(self, tokenlist):
        self._push_textbuffer()
        self._stack.extend(tokenlist)

    def _read(self, delta=0, wrap=False):
        index = self._head + delta
        if index < 0 and (not wrap or abs(index) > len(self._text)):
            return self.START
        try:
            return self._text[index]
        except IndexError:
            return self.END

    def _parse_template(self):
        reset = self._head
        self._head += 2
        try:
            template = self._parse(contexts.TEMPLATE_NAME)
        except BadRoute:
            self._head = reset
            self._write_text(self._read())
        else:
            self._write(tokens.TemplateOpen())
            self._write_all(template)
            self._write(tokens.TemplateClose())

    def _verify_template_name(self):
        self._push_textbuffer()
        if self._stack:
            text = [tok for tok in self._stack if isinstance(tok, tokens.Text)]
            text = "".join([token.text for token in text])
            if text.strip() and "\n" in text.strip():
                raise BadRoute(self._pop())

    def _handle_template_param(self):
        if self._context & contexts.TEMPLATE_NAME:
            self._verify_template_name()
            self._context ^= contexts.TEMPLATE_NAME
        if self._context & contexts.TEMPLATE_PARAM_VALUE:
            self._context ^= contexts.TEMPLATE_PARAM_VALUE
        self._context |= contexts.TEMPLATE_PARAM_KEY
        self._write(tokens.TemplateParamSeparator())

    def _handle_template_param_value(self):
        self._context ^= contexts.TEMPLATE_PARAM_KEY
        self._context |= contexts.TEMPLATE_PARAM_VALUE
        self._write(tokens.TemplateParamEquals())

    def _handle_template_end(self):
        if self._context & contexts.TEMPLATE_NAME:
            self._verify_template_name()
        self._head += 1
        return self._pop()

    def _parse_entity(self):
        self._push()
        try:
            self._write(tokens.HTMLEntityStart())
            this = self._read(1)
            if this is self.END:
                raise BadRoute(self._pop())
            numeric = hexadecimal = False
            skip = 0
            if this.startswith("#"):
                numeric = True
                self._write(tokens.HTMLEntityNumeric())
                if this[1:].lower().startswith("x"):
                    hexadecimal = True
                    self._write(tokens.HTMLEntityHex(char=this[1]))
                    skip = 2
                else:
                    skip = 1
            text = this[skip:]
            valid = string.hexdigits if hexadecimal else string.digits
            if not numeric and not hexadecimal:
                valid += string.ascii_letters
            if not text or not all([char in valid for char in text]):
                raise BadRoute(self._pop())
            if self._read(2) != ";":
                raise BadRoute(self._pop())
            if numeric:
                test = int(text, 16) if hexadecimal else int(text)
                if test < 1 or test > 0x10FFFF:
                    raise BadRoute(self._pop())
            else:
                if text not in htmlentitydefs.entitydefs:
                    raise BadRoute(self._pop())
            self._write(tokens.Text(text=text))
            self._write(tokens.HTMLEntityEnd())
        except BadRoute:
            self._write_text(self._read())
        else:
            self._write_all(self._pop())
            self._head += 2

    def _parse(self, context=0):
        self._push(context)
        while True:
            this = self._read()
            if this not in self.SENTINELS:
                self._write_text(this)
                self._head += 1
                continue
            if this is self.END:
                if self._context & contexts.TEMPLATE:
                    raise BadRoute(self._pop())
                return self._pop()
            next = self._read(1)
            if this == next == "{":
                self._parse_template()
            elif this == "|" and self._context & contexts.TEMPLATE:
                self._handle_template_param()
            elif this == "=" and self._context & contexts.TEMPLATE_PARAM_KEY:
                self._handle_template_param_value()
            elif this == next == "}" and self._context & contexts.TEMPLATE:
                return self._handle_template_end()
            elif this == "&":
                self._parse_entity()
            else:
                self._write_text(this)
            self._head += 1

    def tokenize(self, text):
        split = re.split(self.REGEX, text, flags=re.I)
        self._text = [segment for segment in split if segment]
        return self._parse()

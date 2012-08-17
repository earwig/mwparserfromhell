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

    def _write(self, data, text=False):
        if text:
            self._textbuffer.append(data)
            return
        self._push_textbuffer()
        self._stack.append(data)

    def _write_all(self, tokenlist):
        self._push_textbuffer()
        self._stack.extend(tokenlist)

    def _read(self, delta=0, wrap=False):
        index = self._head + delta
        if index < 0 and (not wrap or abs(index) > len(self._text)):
            return self.START
        if index >= len(self._text):
            return self.END
        return self._text[index]

    def _at_head(self, chars):
        length = len(chars)
        if length == 1:
            return self._read() == chars
        return all([self._read(i) == chars[i] for i in xrange(len(chars))])

    def _parse_template(self):
        reset = self._head
        self._head += 2
        try:
            template = self._parse(contexts.TEMPLATE_NAME)
        except BadRoute:
            self._head = reset
            self._write(self._read(), text=True)
        else:
            self._write(tokens.TemplateOpen())
            self._write_all(template)
            self._write(tokens.TemplateClose())

    def _verify_template_name(self):
        self._push_textbuffer()
        if self._stack:
            text = [tok for tok in self._stack if isinstance(tok, tokens.Text)]
            print text
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
        reset = self._head
        self._head += 1
        try:
            self._push()
            self._write(tokens.HTMLEntityStart())
            numeric = hexadecimal = False
            if self._at_head("#"):
                numeric = True
                self._write(tokens.HTMLEntityNumeric())
                if self._read(1).lower() == "x":
                    hexadecimal = True
                    self._write(tokens.HTMLEntityHex(char=self._read(1)))
                    self._head += 2
                else:
                    self._head += 1
            text = []
            valid = string.hexdigits if hexadecimal else string.digits
            if not numeric and not hexadecimal:
                valid += string.ascii_letters
            while True:
                if self._at_head(";"):
                    text = "".join(text)
                    if numeric:
                        test = int(text, 16) if hexadecimal else int(text)
                        if test < 1 or test > 0x10FFFF:
                            raise BadRoute(self._pop())
                    else:
                        if text not in htmlentitydefs.entitydefs:
                            raise BadRoute(self._pop())
                    self._write(tokens.Text(text=text))
                    self._write(tokens.HTMLEntityEnd())
                    break
                if self._read() is self.END or self._read() not in valid:
                    raise BadRoute(self._pop())
                text.append(self._read())
                self._head += 1
        except BadRoute:
            self._head = reset
            self._write(self._read(), text=True)
        else:
            self._write_all(self._pop())

    def _parse(self, context=0):
        self._push(context)
        while True:
            if self._read() not in self.SENTINELS:
                self._write(self._read(), text=True)
                self._head += 1
                continue
            if self._read() is self.END:
                if self._context & contexts.TEMPLATE:
                    raise BadRoute(self._pop())
                return self._pop()
            if self._at_head("{{"):
                self._parse_template()
            elif self._at_head("|") and self._context & contexts.TEMPLATE:
                self._handle_template_param()
            elif self._at_head("=") and self._context & contexts.TEMPLATE_PARAM_KEY:
                self._handle_template_param_value()
            elif self._at_head("}}") and self._context & contexts.TEMPLATE:
                return self._handle_template_end()
            elif self._at_head("&"):
                self._parse_entity()
            else:
                self._write(self._read(), text=True)
            self._head += 1

    def tokenize(self, text):
        self._text = list(text)
        return self._parse()

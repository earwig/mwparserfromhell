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
from math import log
import re
import string

from . import contexts
from . import tokens
from ..compat import htmlentitydefs

__all__ = ["Tokenizer"]

class BadRoute(Exception):
    pass


class Tokenizer(object):
    START = object()
    END = object()
    MARKERS = ["{", "}", "[", "]", "<", ">", "|", "=", "&", "#", "*", ";", ":",
               "/", "-", "\n", END]
    regex = re.compile(r"([{}\[\]<>|=&#*;:/\-\n])", flags=re.IGNORECASE)

    def __init__(self):
        self._text = None
        self._head = 0
        self._stacks = []
        self._global = 0

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

    def _fail_route(self):
        self._pop()
        raise BadRoute()

    def _write(self, token):
        self._push_textbuffer()
        self._stack.append(token)

    def _write_text(self, text):
        self._textbuffer.append(text)

    def _write_all(self, tokenlist):
        if tokenlist and isinstance(tokenlist[0], tokens.Text):
            self._write_text(tokenlist.pop(0).text)
        self._push_textbuffer()
        self._stack.extend(tokenlist)

    def _read(self, delta=0, wrap=False, strict=False):
        index = self._head + delta
        if index < 0 and (not wrap or abs(index) > len(self._text)):
            return self.START
        try:
            return self._text[index]
        except IndexError:
            if strict:
                self._fail_route()
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
                self._fail_route()

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

    def _parse_heading(self):
        self._global |= contexts.GL_HEADING
        reset = self._head
        self._head += 1
        best = 1
        while self._read() == "=":
            best += 1
            self._head += 1
        context = contexts.HEADING_LEVEL_1 << min(best - 1, 5)

        try:
            title, level = self._parse(context)
        except BadRoute:
            self._head = reset + best - 1
            self._write_text("=" * best)
        else:
            self._write(tokens.HeadingStart(level=level))
            if level < best:
                self._write_text("=" * (best - level))
            self._write_all(title)
            self._write(tokens.HeadingEnd())
        finally:
            self._global ^= contexts.GL_HEADING

    def _handle_heading_end(self):
        reset = self._head
        self._head += 1
        best = 1
        while self._read() == "=":
            best += 1
            self._head += 1
        current = int(log(self._context / contexts.HEADING_LEVEL_1, 2)) + 1
        level = min(current, min(best, 6))

        try:
            after, after_level = self._parse(self._context)
        except BadRoute:
            if level < best:
                self._write_text("=" * (best - level))
            self._head = reset + best - 1
            return self._pop(), level
        else:
            self._write_text("=" * best)
            self._write_all(after)
            return self._pop(), after_level

    def _really_parse_entity(self):
        self._write(tokens.HTMLEntityStart())
        self._head += 1

        this = self._read(strict=True)
        if this == "#":
            numeric = True
            self._write(tokens.HTMLEntityNumeric())
            self._head += 1
            this = self._read(strict=True)
            if this[0].lower() == "x":
                hexadecimal = True
                self._write(tokens.HTMLEntityHex(char=this[0]))
                this = this[1:]
                if not this:
                    self._fail_route()
            else:
                hexadecimal = False
        else:
            numeric = hexadecimal = False

        valid = string.hexdigits if hexadecimal else string.digits
        if not numeric and not hexadecimal:
            valid += string.ascii_letters
        if not all([char in valid for char in this]):
            self._fail_route()

        self._head += 1
        if self._read() != ";":
            self._fail_route()
        if numeric:
            test = int(this, 16) if hexadecimal else int(this)
            if test < 1 or test > 0x10FFFF:
                self._fail_route()
        else:
            if this not in htmlentitydefs.entitydefs:
                self._fail_route()

        self._write(tokens.Text(text=this))
        self._write(tokens.HTMLEntityEnd())

    def _parse_entity(self):
        reset = self._head
        self._push()
        try:
            self._really_parse_entity()
        except BadRoute:
            self._head = reset
            self._write_text(self._read())
        else:
            self._write_all(self._pop())

    def _parse(self, context=0):
        self._push(context)
        while True:
            this = self._read()
            if this not in self.MARKERS:
                self._write_text(this)
                self._head += 1
                continue
            if this is self.END:
                if self._context & (contexts.TEMPLATE | contexts.HEADING):
                    self._fail_route()
                return self._pop()
            prev, next = self._read(-1), self._read(1)
            if this == next == "{":
                self._parse_template()
            elif this == "|" and self._context & contexts.TEMPLATE:
                self._handle_template_param()
            elif this == "=" and self._context & contexts.TEMPLATE_PARAM_KEY:
                self._handle_template_param_value()
            elif this == next == "}" and self._context & contexts.TEMPLATE:
                return self._handle_template_end()
            elif (prev == "\n" or prev == self.START) and this == "=" and not self._global & contexts.GL_HEADING:
                self._parse_heading()
            elif this == "=" and self._context & contexts.HEADING:
                return self._handle_heading_end()
            elif this == "\n" and self._context & contexts.HEADING:
                self._fail_route()
            elif this == "&":
                self._parse_entity()
            else:
                self._write_text(this)
            self._head += 1

    def tokenize(self, text):
        split = self.regex.split(text)
        self._text = [segment for segment in split if segment]
        return self._parse()

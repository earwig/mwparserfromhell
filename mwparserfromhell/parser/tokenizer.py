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

from . import tokens

__all__ = ["Tokenizer"]

class Tokenizer(object):
    START = object()
    END = object()

    def __init__(self):
        self._text = None
        self._head = 0
        self._stacks = []

        self._modifiers = []

    def _push(self):
        self._stacks.append([])

    def _pop(self):
        return self._stacks.pop()

    def _write(self, token, stack=None):
        if stack is None:
            stack = self._stacks[-1]
        if not stack:
            stack.append(token)
            return
        last = stack[-1]
        if isinstance(token, tokens.Text) and isinstance(last, tokens.Text):
            last.text += token.text
        else:
            stack.append(token)

    def _read(self, delta=0, wrap=False):
        index = self._head + delta
        if index < 0 and (not wrap or abs(index) > len(self._text)):
            return self.START
        if index >= len(self._text):
            return self.END
        return self._text[index]

    def _parse_until(self, stop):
        self._push()
        while True:
            if self._read() in (stop, self.END):
                return self._pop()
            else:
                self._write(tokens.Text(text=self._read()))
            self._head += 1

    def tokenize(self, text):
        self._text = list(text)
        return self._parse_until(stop=self.END)

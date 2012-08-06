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
from ..nodes import Template, Text
from ..nodes.extras import Parameter
from ..smart_list import SmartList
from ..wikicode import Wikicode

__all__ = ["Builder"]

class Builder(object):
    def __init__(self):
        self._tokens = []
        self._stack = BuildStack()

    def _pop(self):
        return Wikicode(SmartList(stack.pop()))

    def _handle_parameter(self, key):
        showkey = False
        self._stack.push()
        while self._tokens:
            token = self._tokens.pop(0)
            if isinstance(token, tokens.TEMPLATE_PARAM_EQUALS):
                key = self._pop()
                showkey = True
                self._stack.push()
            elif isinstance(token, (tokens.TEMPLATE_PARAM_SEPARATOR,
                                  tokens.TEMPLATE_CLOSE)):
                self._tokens.insert(0, token)
                value = self._pop()
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
                    name = self._pop()
                param = self._handle_parameter(min(int_key_range - int_keys))
                if re.match(r"[1-9][0-9]*$", param.key.strip()):
                    int_keys.add(int(param.key))
                    int_key_range.add(len(int_keys) + 1)
                params.append(param)
            elif isinstance(token, tokens.TEMPLATE_CLOSE):
                if not params:
                    name = self._pop()
                return Template(name, params)
            else:
                self._stack.write(self._handle_token())

    def _handle_token(self):
        token = self._tokens.pop(0)
        if isinstance(token, tokens.TEXT):
            return Text(token.text)
        elif isinstance(token, tokens.TEMPLATE_OPEN):
            return self._handle_template()

    def build(self, tokens):
        self._tokens = tokens
        self._stack.push()
        while self._tokens:
            self._stack.write(self._handle_token())
        return self._pop()

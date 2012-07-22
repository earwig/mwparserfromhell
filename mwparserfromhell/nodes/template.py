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

from mwparserfromhell.nodes import HTMLEntity, Node
from mwparserfromhell.nodes.extras import Parameter
from mwparserfromhell.utils import parse_anything

__all__ = ["Template"]

class Template(Node):
    def __init__(self, name, params=None):
        self._name = name
        if params:
            self._params = params
        else:
            self._params = []

    def __unicode__(self):
        if self.params:
            params = u"|".join([unicode(param) for param in self.params])
            return "{{" + unicode(self.name) + "|" + params + "}}"
        else:
            return "{{" + unicode(self.name) + "}}"

    def _surface_escape(self, code, char):
        replacement = HTMLEntity(value=ord(char))
        for node in code.filter_text(recursive=False):
            if char in node:
                code.replace(node, node.replace(char, replacement))

    def _blank_param_value(self, value):                                            # TODO
        pass  # MAKE VALUE CONTAIN ABSOLUTELY TWO TEXT NODES: FIRST IS SPACING BEFORE CHUNK AND SECOND IS SPACING AFTER CHUNK

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return self._params

    def has_param(self, name, ignore_empty=True):
        name = name.strip() if isinstance(name, basestring) else unicode(name)
        for param in self.params:
            if param.name.strip() == name:
                if ignore_empty and not param.value.strip():
                    continue
                return True
        return False

    def get(self, name):
        name = name.strip() if isinstance(name, basestring) else unicode(name)
        for param in self.params:
            if param.name.strip() == name:
                return param
        raise ValueError(name)

    def add(self, name, value, showkey=None):
        name, value = parse_anything(name), parse_anything(value)
        self._surface_escape(value, "|")

        if self.has_param(name):
            self.remove(name, keep_field=True)
            existing = self.get(name)
            if showkey is None:  # Infer showkey from current value
                showkey = existing.showkey
            if not showkey:
                self._surface_escape(value, "=")
            nodes = existing.value.nodes
            existing.value = parse_anything([nodes[0], value, nodes[1]])
            return existing

        if showkey is None:
            try:
                int(name)
            except ValueError:
                showkey = False
            else:
                showkey = True
        if not showkey:
            self._surface_escape(value, "=")
        param = Parameter(name, value, showkey)                                     # CONFORM TO FORMATTING CONVENTIONS?
        self.params.append(param)
        return param

    def remove(self, name, keep_field=False):                                       # DON'T MESS UP NUMBERING WITH show_key = False AND keep_field = False
        name = name.strip() if isinstance(name, basestring) else unicode(name)
        for param in self.params:
            if param.name.strip() == name:
                if keep_field:
                    return self._blank_param_value(param.value)
                else:
                    return self.params.remove(param)
        raise ValueError(name)

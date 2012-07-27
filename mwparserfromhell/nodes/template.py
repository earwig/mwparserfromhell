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

from collections import defaultdict
import re

from mwparserfromhell.nodes import HTMLEntity, Node, Text
from mwparserfromhell.nodes.extras import Parameter
from mwparserfromhell.utils import parse_anything

__all__ = ["Template"]

FLAGS = re.DOTALL | re.UNICODE

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

    def _blank_param_value(self, value):
        match = re.search("^(\s*).*?(\s*)$", unicode(value), FLAGS)
        value.nodes = [Text(match.group(1)), Text(match.group(2))]

    def _select_theory(self, theories):
        if theories:
            best = max(theories.values())
            confidence = float(best) / sum(theories.values())
            if confidence > 0.75:
                return theories.keys()[theories.values().index(best)]

    def _get_spacing_conventions(self):
        before_theories = defaultdict(lambda: 0)
        after_theories = defaultdict(lambda: 0)
        for param in self.params:
            match = re.search("^(\s*).*?(\s*)$", unicode(param.value), FLAGS)
            before, after = match.group(1), match.group(2)
            before_theories[before] += 1
            after_theories[after] += 1

        before = self._select_theory(before_theories)
        after = self._select_theory(after_theories)
        return before, after

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

    def add(self, name, value, showkey=None, force_nonconformity=False):
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
            if force_nonconformity:
                existing.value = value
            else:
                existing.value = parse_anything([nodes[0], value, nodes[1]])
            return existing

        if showkey is None:
            try:
                int(name)
                showkey = True
            except ValueError:
                showkey = False
        if not showkey:
            self._surface_escape(value, "=")
        if not force_nonconformity:
            before, after = self._get_spacing_conventions()
            if before and after:
                value = parse_anything([before, value, after])
            elif before:
                value = parse_anything([before, value])
            elif after:
                value = parse_anything([value, after])
        param = Parameter(name, value, showkey)
        self.params.append(param)
        return param

    def remove(self, name, keep_field=False, force_no_field=False):
        name = name.strip() if isinstance(name, basestring) else unicode(name)
        for i, param in enumerate(self.params):
            if param.name.strip() == name:
                if keep_field:
                    return self._blank_param_value(param.value)
                dependent = [not after.showkey for after in self.params[i+1:]]
                if any(dependent) and not param.showkey and not force_no_field:
                    return self._blank_param_value(param.value)
                return self.params.remove(param)
        raise ValueError(name)

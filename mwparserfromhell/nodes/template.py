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
from collections import defaultdict
import re

from . import HTMLEntity, Node, Text
from .extras import Parameter
from ..utils import parse_anything
from ..compat import str, bytes, basestring

__all__ = ["Template"]

FLAGS = re.DOTALL | re.UNICODE

class Template(Node):
    def __init__(self, name, params=None):
        super(Template, self).__init__()
        self._name = name
        if params:
            self._params = params
        else:
            self._params = []

    def __unicode__(self):
        if self.params:
            params = "|".join([str(param) for param in self.params])
            return "{{" + str(self.name) + "|" + params + "}}"
        else:
            return "{{" + str(self.name) + "}}"

    def __iternodes__(self, getter):
        yield None, self
        for child in getter(self.name):
            yield self.name, child
        for param in self.params:
            if param.showkey:
                for child in getter(param.name):
                    yield param.name, child
            for child in getter(param.value):
                yield param.value, child

    def __showtree__(self, write, get, mark):
        write("{{")
        get(self.name)
        for param in self.params:
            write("    | ")
            mark()
            get(param.name)
            write("    = ")
            mark()
            get(param.value)
        write("}}")

    def _surface_escape(self, code, char):
        replacement = HTMLEntity(value=ord(char))
        for node in code.filter_text(recursive=False):
            if char in node:
                code.replace(node, node.replace(char, replacement))

    def _blank_param_value(self, value):
        match = re.search(r"^(\s*).*?(\s*)$", str(value), FLAGS)
        value.nodes = [Text(match.group(1)), Text(match.group(2))]

    def _select_theory(self, theories):
        if theories:
            best = max(theories.values())
            confidence = float(best) / sum(theories.values())
            if confidence > 0.75:
                return tuple(theories.keys())[tuple(theories.values()).index(best)]

    def _get_spacing_conventions(self):
        before_theories = defaultdict(lambda: 0)
        after_theories = defaultdict(lambda: 0)
        for param in self.params:
            match = re.search(r"^(\s*).*?(\s*)$", str(param.value), FLAGS)
            before, after = match.group(1), match.group(2)
            before_theories[before] += 1
            after_theories[after] += 1

        before = self._select_theory(before_theories)
        after = self._select_theory(after_theories)
        return before, after

    def _remove_with_field(self, param, i, name):
        if param.showkey:
            following = self.params[i+1:]
            better_matches = [after.name.strip() == name and not after.showkey for after in following]
            if any(better_matches):
                return False
        return True

    def _remove_without_field(self, param, i, force_no_field):
        if not param.showkey and not force_no_field:
            dependents = [not after.showkey for after in self.params[i+1:]]
            if any(dependents):
                return False
        return True

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return self._params

    @name.setter
    def name(self, value):
        self._name = parse_anything(value)

    def has_param(self, name, ignore_empty=True):
        name = name.strip() if isinstance(name, basestring) else str(name)
        for param in self.params:
            if param.name.strip() == name:
                if ignore_empty and not param.value.strip():
                    continue
                return True
        return False

    def get(self, name):
        name = name.strip() if isinstance(name, basestring) else str(name)
        for param in reversed(self.params):
            if param.name.strip() == name:
                return param
        raise ValueError(name)

    def add(self, name, value, showkey=None, force_nonconformity=False):
        name, value = parse_anything(name), parse_anything(value)
        self._surface_escape(value, "|")

        if self.has_param(name):
            self.remove(name, keep_field=True)
            existing = self.get(name)
            if showkey is not None:
                if not showkey:
                    self._surface_escape(value, "=")
                existing.showkey = showkey
            nodes = existing.value.nodes
            if force_nonconformity:
                existing.value = value
            else:
                existing.value = parse_anything([nodes[0], value, nodes[1]])
            return existing

        if showkey is None:
            try:
                int_name = int(str(name))
            except ValueError:
                showkey = True
            else:
                int_keys = set()
                for param in self.params:
                    if not param.showkey:
                        if re.match(r"[1-9][0-9]*$", param.name.strip()):
                            int_keys.add(int(str(param.name)))
                expected = min(set(range(1, len(int_keys) + 2)) - int_keys)
                if expected == int_name:
                    showkey = False
                else:
                    showkey = True
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
        name = name.strip() if isinstance(name, basestring) else str(name)
        removed = False
        for i, param in enumerate(self.params):
            if param.name.strip() == name:
                if keep_field:
                    if self._remove_with_field(param, i, name):
                        self._blank_param_value(param.value)
                        keep_field = False
                    else:
                        self.params.remove(param)
                else:
                    if self._remove_without_field(param, i, force_no_field):
                        self.params.remove(param)
                    else:
                        self._blank_param_value(param.value)
                if not removed:
                    removed = True
        if not removed:
            raise ValueError(name)

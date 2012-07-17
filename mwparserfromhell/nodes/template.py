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

from mwparserfromhell.nodes import Node
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

    def _blank_param_value(self, value):                                            # TODO
        pass

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return self._params

    def has_param(self, name):
        name = name.strip() if isinstance(name, basestring) else unicode(name)
        for param in self.params:
            if param.name.strip() == name:
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
        surface_text = value.filter_text(recursive=False)
        for node in surface_text:
            value.replace(node, node.replace("|", "&#124;"))

        if showkey is None:
            if any(["=" in node for node in surface_text]):
                showkey = True
            else:
                try:
                    int(name)
                except ValueError:
                    showkey = False
                else:
                    showkey = True
        elif not showkey:
            for node in surface_text:
                value.replace(node, node.replace("=", "&#124;"))

        if self.has_param(name):
            self.remove_param(name, keep_field=True)
            existing = self.get_param(name).value
            self.get_param(name).value = value                                      # CONFORM TO FORMATTING?
        else:
            self.params.append(Parameter(name, value, showkey))                     # CONFORM TO FORMATTING CONVENTIONS?

    def remove(self, name, keep_field=False):                                       # DON'T MESS UP NUMBERING WITH show_key = False AND keep_field = False
        name = name.strip() if isinstance(name, basestring) else unicode(name)
        for param in self.params:
            if param.name.strip() == name:
                if keep_field:
                    return self._blank_param_value(param.value)
                else:
                    return self.params.remove(param)
        raise ValueError(name)

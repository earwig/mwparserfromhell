# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>
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
from ..compat import str
from ..utils import parse_anything

__all__ = ["Template"]

FLAGS = re.DOTALL | re.UNICODE

class Template(Node):
    """Represents a template in wikicode, like ``{{foo}}``."""

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
        """Return *code* with *char* escaped as an HTML entity.

        The main use of this is to escape pipes (``|``) or equal signs (``=``)
        in parameter names or values so they are not mistaken for new
        parameters.
        """
        replacement = str(HTMLEntity(value=ord(char)))
        for node in code.filter_text(recursive=False):
            if char in node:
                code.replace(node, node.replace(char, replacement), False)

    def _blank_param_value(self, value):
        """Remove the content from *value* while keeping its whitespace.

        Replace *value*\ 's nodes with two text nodes, the first containing
        whitespace from before its content and the second containing whitespace
        from after its content.
        """
        match = re.search(r"^(\s*).*?(\s*)$", str(value), FLAGS)
        value.nodes = [Text(match.group(1)), Text(match.group(2))]

    def _select_theory(self, theories):
        """Return the most likely spacing convention given different options.

        Given a dictionary of convention options as keys and their occurance as
        values, return the convention that occurs the most, or ``None`` if
        there is no clear preferred style.
        """
        if theories:
            values = tuple(theories.values())
            best = max(values)
            confidence = float(best) / sum(values)
            if confidence >= 0.75:
                return tuple(theories.keys())[values.index(best)]

    def _get_spacing_conventions(self, use_names):
        """Try to determine the whitespace conventions for parameters.

        This will examine the existing parameters and use
        :py:meth:`_select_theory` to determine if there are any preferred
        styles for how much whitespace to put before or after the value.
        """
        before_theories = defaultdict(lambda: 0)
        after_theories = defaultdict(lambda: 0)
        for param in self.params:
            if use_names:
                component = str(param.name)
            else:
                component = str(param.value)
            match = re.search(r"^(\s*).*?(\s*)$", component, FLAGS)
            before, after = match.group(1), match.group(2)
            before_theories[before] += 1
            after_theories[after] += 1

        before = self._select_theory(before_theories)
        after = self._select_theory(after_theories)
        return before, after

    def _remove_with_field(self, param, i, name):
        """Return True if a parameter name should be kept, otherwise False."""
        if param.showkey:
            following = self.params[i+1:]
            better_matches = [after.name.strip() == name and not after.showkey for after in following]
            if any(better_matches):
                return False
        return True

    def _remove_without_field(self, param, i):
        """Return False if a parameter name should be kept, otherwise True."""
        if not param.showkey:
            dependents = [not after.showkey for after in self.params[i+1:]]
            if any(dependents):
                return False
        return True

    def _remove_exact(self, needle, keep_field):
        """Remove a specific parameter, *needle*, from the template."""
        for i, param in enumerate(self.params):
            if param is needle:
                if keep_field or not self._remove_without_field(param, i):
                    self._blank_param_value(param.value)
                else:
                    self.params.pop(i)
                return

    @property
    def name(self):
        """The name of the template, as a :py:class:`~.Wikicode` object."""
        return self._name

    @property
    def params(self):
        """The list of parameters contained within the template."""
        return self._params

    @name.setter
    def name(self, value):
        self._name = parse_anything(value)

    def has(self, name, ignore_empty=True):
        """Return ``True`` if any parameter in the template is named *name*.

        With *ignore_empty*, ``False`` will be returned even if the template
        contains a parameter with the name *name*, if the parameter's value
        is empty. Note that a template may have multiple parameters with the
        same name, but only the last one is read by the MediaWiki parser.
        """
        name = str(name).strip()
        for param in self.params:
            if param.name.strip() == name:
                if ignore_empty and not param.value.strip():
                    continue
                return True
        return False

    has_param = lambda self, name, ignore_empty=True: \
                self.has(name, ignore_empty)
    has_param.__doc__ = "Alias for :py:meth:`has`."

    def get(self, name):
        """Get the parameter whose name is *name*.

        The returned object is a :py:class:`~.Parameter` instance. Raises
        :py:exc:`ValueError` if no parameter has this name. Since multiple
        parameters can have the same name, we'll return the last match, since
        the last parameter is the only one read by the MediaWiki parser.
        """
        name = str(name).strip()
        for param in reversed(self.params):
            if param.name.strip() == name:
                return param
        raise ValueError(name)

    def add(self, name, value, showkey=None, before=None,
            preserve_spacing=True):
        """Add a parameter to the template with a given *name* and *value*.

        *name* and *value* can be anything parasable by
        :py:func:`.utils.parse_anything`; pipes and equal signs are
        automatically escaped from *value* when appropriate.

        If *showkey* is given, this will determine whether or not to show the
        parameter's name (e.g., ``{{foo|bar}}``'s parameter has a name of
        ``"1"`` but it is hidden); otherwise, we'll make a safe and intelligent
        guess.

        If *name* is already a parameter in the template, we'll replace its
        value while keeping the same whitespace around it. We will also try to
        guess the dominant spacing convention when adding a new parameter using
        :py:meth:`_get_spacing_conventions`.

        If *before* is given (either a :py:class:`~.Parameter` object or a
        name), then we will place the parameter immediately before this one.
        Otherwise, it will be added at the end. If *before* is a name and
        exists multiple times in the template, we will place it before the last
        occurance. If *before* is not in the template, :py:exc:`ValueError` is
        raised. The argument is ignored if the new parameter already exists.

        If *preserve_spacing* is ``False``, we will avoid preserving spacing
        conventions when changing the value of an existing parameter or when
        adding a new one.
        """
        name, value = parse_anything(name), parse_anything(value)
        self._surface_escape(value, "|")

        if self.has(name):
            self.remove(name, keep_field=True)
            existing = self.get(name)
            if showkey is not None:
                existing.showkey = showkey
            if not existing.showkey:
                self._surface_escape(value, "=")
            nodes = existing.value.nodes
            if preserve_spacing:
                for i in range(2):  # Ignore empty text nodes
                    if not nodes[i]:
                        nodes[i] = None
                existing.value = parse_anything([nodes[0], value, nodes[1]])
            else:
                existing.value = value
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

        if preserve_spacing:
            before_n, after_n = self._get_spacing_conventions(use_names=True)
            before_v, after_v = self._get_spacing_conventions(use_names=False)
            name = parse_anything([before_n, name, after_n])
            value = parse_anything([before_v, value, after_v])

        param = Parameter(name, value, showkey)
        if before:
            if not isinstance(before, Parameter):
                before = self.get(before)
            self.params.insert(self.params.index(before), param)
        else:
            self.params.append(param)
        return param

    def remove(self, param, keep_field=False):
        """Remove a parameter from the template, identified by *param*.

        If *param* is a :py:class:`.Parameter` object, it will be matched
        exactly, otherwise it will be treated like the *name* argument to
        :py:meth:`has` and :py:meth:`get`.

        If *keep_field* is ``True``, we will keep the parameter's name, but
        blank its value. Otherwise, we will remove the parameter completely
        *unless* other parameters are dependent on it (e.g. removing ``bar``
        from ``{{foo|bar|baz}}`` is unsafe because ``{{foo|baz}}`` is not what
        we expected, so ``{{foo||baz}}`` will be produced instead).

        If the parameter shows up multiple times in the template and *param* is
        not a :py:class:`.Parameter` object, we will remove all instances of it
        (and keep only one if *keep_field* is ``True`` - the first instance if
        none have dependents, otherwise the one with dependents will be kept).
        """
        if isinstance(param, Parameter):
            return self._remove_exact(param, keep_field)
        name = str(param).strip()
        removed = False
        to_remove = []
        for i, param in enumerate(self.params):
            if param.name.strip() == name:
                if keep_field:
                    if self._remove_with_field(param, i, name):
                        self._blank_param_value(param.value)
                        keep_field = False
                    else:
                        to_remove.append(i)
                else:
                    if self._remove_without_field(param, i):
                        to_remove.append(i)
                    else:
                        self._blank_param_value(param.value)
                if not removed:
                    removed = True
        if not removed:
            raise ValueError(name)
        for i in reversed(to_remove):
            self.params.pop(i)

# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from ._base import Node
from .html_entity import HTMLEntity
from .text import Text
from .extras import Parameter
from ..utils import parse_anything

__all__ = ["Template"]

FLAGS = re.DOTALL | re.UNICODE
# Used to allow None as a valid fallback value
_UNSET = object()

class Template(Node):
    """Represents a template in wikicode, like ``{{foo}}``."""

    def __init__(self, name, params=None):
        super().__init__()
        self.name = name
        if params:
            self._params = params
        else:
            self._params = []

    def __str__(self):
        if self.params:
            params = "|".join([str(param) for param in self.params])
            return "{{" + str(self.name) + "|" + params + "}}"
        return "{{" + str(self.name) + "}}"

    def __children__(self):
        yield self.name
        for param in self.params:
            if param.showkey:
                yield param.name
            yield param.value

    def __strip__(self, **kwargs):
        if kwargs.get("keep_template_params"):
            parts = [param.value.strip_code(**kwargs) for param in self.params]
            return " ".join(part for part in parts if part)
        return None

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

    @staticmethod
    def _surface_escape(code, char):
        """Return *code* with *char* escaped as an HTML entity.

        The main use of this is to escape pipes (``|``) or equal signs (``=``)
        in parameter names or values so they are not mistaken for new
        parameters.
        """
        replacement = str(HTMLEntity(value=ord(char)))
        for node in code.filter_text(recursive=False):
            if char in node:
                code.replace(node, node.replace(char, replacement), False)

    @staticmethod
    def _select_theory(theories):
        """Return the most likely spacing convention given different options.

        Given a dictionary of convention options as keys and their occurrence
        as values, return the convention that occurs the most, or ``None`` if
        there is no clear preferred style.
        """
        if theories:
            values = tuple(theories.values())
            best = max(values)
            confidence = float(best) / sum(values)
            if confidence > 0.5:
                return tuple(theories.keys())[values.index(best)]
        return None

    @staticmethod
    def _blank_param_value(value):
        """Remove the content from *value* while keeping its whitespace.

        Replace *value*\\ 's nodes with two text nodes, the first containing
        whitespace from before its content and the second containing whitespace
        from after its content.
        """
        sval = str(value)
        if sval.isspace():
            before, after = "", sval
        else:
            match = re.search(r"^(\s*).*?(\s*)$", sval, FLAGS)
            before, after = match.group(1), match.group(2)
        value.nodes = [Text(before), Text(after)]

    def _get_spacing_conventions(self, use_names):
        """Try to determine the whitespace conventions for parameters.

        This will examine the existing parameters and use
        :meth:`_select_theory` to determine if there are any preferred styles
        for how much whitespace to put before or after the value.
        """
        before_theories = defaultdict(lambda: 0)
        after_theories = defaultdict(lambda: 0)
        for param in self.params:
            if not param.showkey:
                continue
            if use_names:
                component = str(param.name)
            else:
                component = str(param.value)
            match = re.search(r"^(\s*).*?(\s*)$", component, FLAGS)
            before, after = match.group(1), match.group(2)
            if not use_names and component.isspace() and "\n" in before:
                # If the value is empty, we expect newlines in the whitespace
                # to be after the content, not before it:
                before, after = before.split("\n", 1)
                after = "\n" + after
            before_theories[before] += 1
            after_theories[after] += 1

        before = self._select_theory(before_theories)
        after = self._select_theory(after_theories)
        return before, after

    def _fix_dependendent_params(self, i):
        """Unhide keys if necessary after removing the param at index *i*."""
        if not self.params[i].showkey:
            for param in self.params[i + 1:]:
                if not param.showkey:
                    param.showkey = True

    def _remove_exact(self, needle, keep_field):
        """Remove a specific parameter, *needle*, from the template."""
        for i, param in enumerate(self.params):
            if param is needle:
                if keep_field:
                    self._blank_param_value(param.value)
                else:
                    self._fix_dependendent_params(i)
                    self.params.pop(i)
                return
        raise ValueError(needle)

    def _should_remove(self, i, name):
        """Look ahead for a parameter with the same name, but hidden.

        If one exists, we should remove the given one rather than blanking it.
        """
        if self.params[i].showkey:
            following = self.params[i + 1:]
            better_matches = [after.name.strip() == name and not after.showkey
                              for after in following]
            return any(better_matches)
        return False

    @property
    def name(self):
        """The name of the template, as a :class:`.Wikicode` object."""
        return self._name

    @property
    def params(self):
        """The list of parameters contained within the template."""
        return self._params

    @name.setter
    def name(self, value):
        self._name = parse_anything(value)

    def has(self, name, ignore_empty=False):
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

    def has_param(self, name, ignore_empty=False):
        """Alias for :meth:`has`."""
        return self.has(name, ignore_empty)

    def get(self, name, default=_UNSET):
        """Get the parameter whose name is *name*.

        The returned object is a :class:`.Parameter` instance. Raises
        :exc:`ValueError` if no parameter has this name. If *default* is set,
        returns that instead. Since multiple parameters can have the same name,
        we'll return the last match, since the last parameter is the only one
        read by the MediaWiki parser.
        """
        name = str(name).strip()
        for param in reversed(self.params):
            if param.name.strip() == name:
                return param
        if default is _UNSET:
            raise ValueError(name)
        return default

    def __getitem__(self, name):
        return self.get(name)

    def add(self, name, value, showkey=None, before=None,
            preserve_spacing=True):
        """Add a parameter to the template with a given *name* and *value*.

        *name* and *value* can be anything parsable by
        :func:`.utils.parse_anything`; pipes and equal signs are automatically
        escaped from *value* when appropriate.

        If *name* is already a parameter in the template, we'll replace its
        value.

        If *showkey* is given, this will determine whether or not to show the
        parameter's name (e.g., ``{{foo|bar}}``'s parameter has a name of
        ``"1"`` but it is hidden); otherwise, we'll make a safe and intelligent
        guess.

        If *before* is given (either a :class:`.Parameter` object or a name),
        then we will place the parameter immediately before this one.
        Otherwise, it will be added at the end. If *before* is a name and
        exists multiple times in the template, we will place it before the last
        occurrence. If *before* is not in the template, :exc:`ValueError` is
        raised. The argument is ignored if *name* is an existing parameter.

        If *preserve_spacing* is ``True``, we will try to preserve whitespace
        conventions around the parameter, whether it is new or we are updating
        an existing value. It is disabled for parameters with hidden keys,
        since MediaWiki doesn't strip whitespace in this case.
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
            if preserve_spacing and existing.showkey:
                for i in range(2):  # Ignore empty text nodes
                    if not nodes[i]:
                        nodes[i] = None
                existing.value = parse_anything([nodes[0], value, nodes[1]])
            else:
                existing.value = value
            return existing

        if showkey is None:
            if Parameter.can_hide_key(name):
                int_name = int(str(name))
                int_keys = set()
                for param in self.params:
                    if not param.showkey:
                        int_keys.add(int(str(param.name)))
                expected = min(set(range(1, len(int_keys) + 2)) - int_keys)
                if expected == int_name:
                    showkey = False
                else:
                    showkey = True
            else:
                showkey = True
        if not showkey:
            self._surface_escape(value, "=")

        if preserve_spacing and showkey:
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

    def __setitem__(self, name, value):
        return self.add(name, value)

    def remove(self, param, keep_field=False):
        """Remove a parameter from the template, identified by *param*.

        If *param* is a :class:`.Parameter` object, it will be matched exactly,
        otherwise it will be treated like the *name* argument to :meth:`has`
        and :meth:`get`.

        If *keep_field* is ``True``, we will keep the parameter's name, but
        blank its value. Otherwise, we will remove the parameter completely.

        When removing a parameter with a hidden name, subsequent parameters
        with hidden names will be made visible. For example, removing ``bar``
        from ``{{foo|bar|baz}}`` produces ``{{foo|2=baz}}`` because
        ``{{foo|baz}}`` is incorrect.

        If the parameter shows up multiple times in the template and *param* is
        not a :class:`.Parameter` object, we will remove all instances of it
        (and keep only one if *keep_field* is ``True`` - either the one with a
        hidden name, if it exists, or the first instance).
        """
        if isinstance(param, Parameter):
            self._remove_exact(param, keep_field)
            return

        name = str(param).strip()
        removed = False
        to_remove = []

        for i, par in enumerate(self.params):
            if par.name.strip() == name:
                if keep_field:
                    if self._should_remove(i, name):
                        to_remove.append(i)
                    else:
                        self._blank_param_value(par.value)
                        keep_field = False
                else:
                    self._fix_dependendent_params(i)
                    to_remove.append(i)
                if not removed:
                    removed = True

        if not removed:
            raise ValueError(name)
        for i in reversed(to_remove):
            self.params.pop(i)

    def __delitem__(self, param):
        return self.remove(param)

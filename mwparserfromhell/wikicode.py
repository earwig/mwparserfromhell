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
import sys

from .nodes import Heading, Node, Tag, Template, Text
from .string_mixin import StringMixIn
from .utils import parse_anything

__all__ = ["Wikicode"]

FLAGS = re.IGNORECASE | re.DOTALL | re.UNICODE

class Wikicode(StringMixIn):
    """A ``Wikicode`` is a container for nodes that functions like a string.
    """

    def __init__(self, nodes):
        super(Wikicode, self).__init__()
        self._nodes = nodes

    def __unicode__(self):
        return "".join([unicode(node) for node in self.nodes])

    def _get_children(self, node):
        """Iterate over all descendants of a given node, including itself.

        This is implemented by the __iternodes__() generator of Node classes,
        which by default yields itself and nothing more.
        """
        for context, child in node.__iternodes__(self._get_all_nodes):
            yield child

    def _get_context(self, node, obj):
        """Return a ``Wikicode`` that contains ``obj`` in its descendants.

        The closest (shortest distance from ``node``) suitable ``Wikicode``
        will be returned, or ``None`` if the ``obj`` is the ``node`` itself.

        Raises ``ValueError`` if ``obj`` is not within ``node``.
        """
        for context, child in node.__iternodes__(self._get_all_nodes):
            if child is obj:
                return context
        raise ValueError(obj)

    def _get_all_nodes(self, code):
        """Iterate over all of our descendant nodes.

        This is implemented by calling :py:meth:`_get_children` on every node
        in our node list (:py:attr:`self.nodes <nodes>`).
        """
        for node in code.nodes:
            for child in self._get_children(node):
                yield child

    def _is_equivalent(self, obj, node):
        """Return ``True`` if obj and node are equivalent, otherwise ``False``.
        """
        if isinstance(obj, Node):
            if node is obj:
                return True
        else:
            if node == obj:
                return True
        return False

    def _contains(self, nodes, obj):
        if isinstance(obj, Node):
            for node in nodes:
                if node is obj:
                    return True
        else:
            if obj in nodes:
                return True
        return False

    def _do_search(self, obj, recursive, callback, context, *args, **kwargs):
        if recursive:
            for i, node in enumerate(context.nodes):
                if self._is_equivalent(obj, node):
                    return callback(context, i, *args, **kwargs)
                if self._contains(self._get_children(node), obj):
                    context = self._get_context(node, obj)
                    return self._do_search(obj, recursive, callback, context,
                                           *args, **kwargs)
            raise ValueError(obj)

        callback(context, self.index(obj, recursive=False), *args, **kwargs)

    def _get_tree(self, code, lines, marker, indent):
        def write(*args):
            if lines and lines[-1] is marker:  # Continue from the last line
                lines.pop()  # Remove the marker
                last = lines.pop()
                lines.append(last + " ".join(args))
            else:
                lines.append(" " * 6 * indent + " ".join(args))

        get = lambda code: self._get_tree(code, lines, marker, indent + 1)
        mark = lambda: lines.append(marker)
        for node in code.nodes:
            node.__showtree__(write, get, mark)
        return lines

    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = value

    def get(self, index):
        return self.nodes[index]

    def set(self, index, value):
        nodes = parse_anything(value).nodes
        if len(nodes) > 1:
            raise ValueError("Cannot coerce multiple nodes into one index")
        if index >= len(self.nodes) or -1 * index > len(self.nodes):
            raise IndexError("List assignment index out of range")
        self.nodes.pop(index)
        if nodes:
            self.nodes[index] = nodes[0]

    def index(self, obj, recursive=False):
        if recursive:
            for i, node in enumerate(self.nodes):
                if self._contains(self._get_children(node), obj):
                    return i
            raise ValueError(obj)

        for i, node in enumerate(self.nodes):
            if self._is_equivalent(obj, node):
                return i
        raise ValueError(obj)

    def insert(self, index, value):
        nodes = parse_anything(value).nodes
        for node in reversed(nodes):
            self.nodes.insert(index, node)

    def insert_before(self, obj, value, recursive=True):
        callback = lambda self, i, value: self.insert(i, value)
        self._do_search(obj, recursive, callback, self, value)

    def insert_after(self, obj, value, recursive=True):
        callback = lambda self, i, value: self.insert(i + 1, value)
        self._do_search(obj, recursive, callback, self, value)

    def replace(self, obj, value, recursive=True):
        def callback(self, i, value):
            self.nodes.pop(i)
            self.insert(i, value)

        self._do_search(obj, recursive, callback, self, value)

    def append(self, value):
        nodes = parse_anything(value).nodes
        for node in nodes:
            self.nodes.append(node)

    def remove(self, obj, recursive=True):
        callback = lambda self, i: self.nodes.pop(i)
        self._do_search(obj, recursive, callback, self)

    def ifilter(self, recursive=False, matches=None, flags=FLAGS,
                forcetype=None):
        if recursive:
            nodes = self._get_all_nodes(self)
        else:
            nodes = self.nodes
        for node in nodes:
            if not forcetype or isinstance(node, forcetype):
                if not matches or re.search(matches, unicode(node), flags):
                    yield node

    def ifilter_templates(self, recursive=False, matches=None, flags=FLAGS):
        return self.filter(recursive, matches, flags, forcetype=Template)

    def ifilter_text(self, recursive=False, matches=None, flags=FLAGS):
        return self.filter(recursive, matches, flags, forcetype=Text)

    def ifilter_tags(self, recursive=False, matches=None, flags=FLAGS):
        return self.ifilter(recursive, matches, flags, forcetype=Tag)

    def filter(self, recursive=False, matches=None, flags=FLAGS,
               forcetype=None):
        return list(self.ifilter(recursive, matches, flags, forcetype))

    def filter_templates(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_templates(recursive, matches, flags))

    def filter_text(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_text(recursive, matches, flags))

    def filter_tags(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_tags(recursive, matches, flags))

    def get_sections(self, flat=True, matches=None, levels=None, flags=FLAGS,
                     include_headings=True):
        if matches:
            matches = r"^(=+?)\s*" + matches + r"\s*\1$"
        headings = self.filter(recursive=True, matches=matches, flags=flags,
                                forcetype=Heading)
        if levels:
            headings = [head for head in headings if head.level in levels]

        sections = []
        buffers = [[sys.maxint, 0]]
        i = 0
        while i < len(self.nodes):
            if self.nodes[i] in headings:
                this = self.nodes[i].level
                for (level, start) in buffers:
                    if not flat or this <= level:
                        buffers.remove([level, start])
                        sections.append(self.nodes[start:i])
                buffers.append([this, i])
                if not include_headings:
                    i += 1
            i += 1
        for (level, start) in buffers:
            if start != i:
                sections.append(self.nodes[start:i])
        return sections

    def strip_code(self, normalize=True, collapse=True):
        nodes = []
        for node in self.nodes:
            stripped = node.__strip__(normalize, collapse)
            if stripped:
                nodes.append(unicode(stripped))

        if collapse:
            stripped = u"".join(nodes).strip("\n")
            while "\n\n\n" in stripped:
                stripped = stripped.replace("\n\n\n", "\n\n")
            return stripped
        else:
            return u"".join(nodes)

    def get_tree(self):
        marker = object()  # Random object we can find with certainty in a list
        return "\n".join(self._get_tree(self, [], marker, 0))

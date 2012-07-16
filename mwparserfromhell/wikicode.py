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

import mwparserfromhell
from mwparserfromhell.nodes import HTMLEntity, Node, Template, Text
from mwparserfromhell.string_mixin import StringMixIn

__all__ = ["Wikicode"]

FLAGS = re.I | re.S | re.U

class Wikicode(StringMixIn):
    def __init__(self, nodes):
        self._nodes = nodes

    def __unicode__(self):
        return "".join([unicode(node) for node in self.nodes])

    def _nodify(self, value):
        if isinstance(value, Wikicode):
            return value.nodes
        if isinstance(value, Node):
            return [value]
        if isinstance(value, basestring):
            return mwparserfromhell.parse(value).nodes

        try:
            nodelist = list(value)
        except TypeError:
            error = "Needs string, Node, iterable of Nodes, or Wikicode object, but got {0}: {1}"
            raise ValueError(error.format(type(value), value))
        if not all([isinstance(node, Node) for node in nodelist]):
            error = "Was passed an interable {0}, but it did not contain all Nodes: {1}"
            raise ValueError(error.format(type(value), value))
        return nodelist

    def _get_children(self, node):
        yield node
        if isinstance(node, Template):
            for child in self._get_all_nodes(node.name):
                yield child
            for param in node.params:
                if param.showkey:
                    for child in self._get_all_nodes(param.name):
                        yield child
                for child in self._get_all_nodes(param.value):
                    yield child

    def _get_all_nodes(self, code):
        for node in code.nodes:
            for child in self._get_children(node):
                yield child

    def _is_equivalent(self, obj, node):
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

    def _do_search(self, obj, value, recursive, callback, context=None):
        if recursive:
            nodes = context.nodes if context else self.nodes
            for i, node in enumerate(nodes):
                if self._is_equivalent(obj, node):
                    return callback(self, value, i)
                if self._contains(self._get_children(node), obj):
                    return self._do_search(obj, value, recursive, callback,
                                           context=node)
            raise ValueError(obj)

        callback(self, value, self.index(obj, recursive=False))

    def _get_tree(self, code, lines, marker=None, indent=0):
        def write(*args):
            if lines and lines[-1] is marker:  # Continue from the last line
                lines.pop()  # Remove the marker
                last = lines.pop()
                lines.append(last + " ".join(args))
            else:
                lines.append("      " * indent + " ".join(args))

        for node in code.nodes:
            if isinstance(node, Template):
                write("{{", )
                self._get_tree(node.name, lines, marker, indent + 1)
                for param in node.params:
                    write("    | ")
                    lines.append(marker)  # Continue from this line
                    self._get_tree(param.name, lines, marker, indent + 1)
                    write("    = ")
                    lines.append(marker)  # Continue from this line
                    self._get_tree(param.value, lines, marker, indent + 1)
                write("}}")
            elif isinstance(node, Text):
                write(unicode(node))
            else:
                raise NotImplementedError(node)
        return lines

    @property
    def nodes(self):
        return self._nodes

    def get(self, index):
        return self.nodes[index]

    def set(self, index, value):
        nodes = self._nodify(value)
        if len(nodes) > 1:
            raise ValueError("Cannot coerce multiple nodes into one index")
        if index >= len(self.nodes) or -1 * index > len(self.nodes):
            raise IndexError("List assignment index out of range")
        self.nodex.pop(index)
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
        nodes = self._nodify(value)
        for node in reversed(nodes):
            self.nodes.insert(index, node)

    def insert_before(self, obj, value, recursive=True):
        callback = lambda self, value, i: self.insert(i, value)
        self._do_search(obj, value, recursive, callback)

    def insert_after(self, obj, value, recursive=True):
        callback = lambda self, value, i: self.insert(i + 1, value)
        self._do_search(obj, value, recursive, callback)

    def replace(self, obj, value, recursive=True):
        def callback(self, value, i):
            self.nodes.pop(i)
            self.insert(i, value)

        self._do_search(obj, value, recursive, callback)

    def append(self, value):
        nodes = self._nodify(value)
        for node in nodes:
            self.nodes.append(node)

    def remove(self, obj, recursive=True):
        if recursive:
            for i, node in enumerate(self.nodes):
                if self._is_equivalent(obj, node):
                    return self.nodes.pop(i)
                if self._contains(self._get_children(node), obj):
                    return node.remove(obj, recursive=True)
            raise ValueError(obj)

        return self.nodes.pop(self.index(obj))

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

    def filter(self, recursive=False, matches=None, flags=FLAGS,
               forcetype=None):
        return list(self.ifilter(recursive, matches, flags, forcetype))

    def filter_templates(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_templates(recursive, matches, flags))

    def filter_text(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_text(recursive, matches, flags))

    def strip_code(self, normalize=True):
        nodes = []
        for node in self.nodes:
            if isinstance(node, Text):
                nodes.append(node)
            elif isinstance(node, HTMLEntity):
                if normalize:
                    nodes.append(node.normalize())
                else:
                    nodes.append(node)

        return u" ".join(nodes)

    def get_tree(self):
        marker = object()  # Random object we can find with certainty in a list
        return "\n".join(self._get_tree(self, [], marker))

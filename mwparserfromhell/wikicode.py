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

from mwparserfromhell.nodes import (
    Heading, HTMLEntity, Node, Tag, Template, Text
)
from mwparserfromhell.string_mixin import StringMixIn
from mwparserfromhell.utils import parse_anything

__all__ = ["Wikicode"]

FLAGS = re.IGNORECASE | re.DOTALL | re.UNICODE

class Wikicode(StringMixIn):
    def __init__(self, nodes):
        self._nodes = nodes

    def __unicode__(self):
        return "".join([unicode(node) for node in self.nodes])

    def _iterate_over_children(self, node):
        yield (None, node)
        if isinstance(node, Heading):
            for child in self._get_all_nodes(node.title):
                yield (node.title, child)
        elif isinstance(node, Tag):
            if node.showtag:
                for child in self._get_all_nodes(node.tag):
                    yield (node.tag, tag)
                for attr in node.attrs:
                    for child in self._get_all_nodes(attr.name):
                        yield (attr.name, child)
                    if attr.value:
                        for child in self._get_all_nodes(attr.value):
                            yield (attr.value, child)
            for child in self._get_all_nodes(node.contents):
                yield (node.contents, child)
        elif isinstance(node, Template):
            for child in self._get_all_nodes(node.name):
                yield (node.name, child)
            for param in node.params:
                if param.showkey:
                    for child in self._get_all_nodes(param.name):
                        yield (param.name, child)
                for child in self._get_all_nodes(param.value):
                    yield (param.value, child)

    def _get_children(self, node):
        for context, child in self._iterate_over_children(node):
            yield child

    def _get_context(self, node, obj):
        for context, child in self._iterate_over_children(node):
            if child is obj:
                return context
        raise ValueError(obj)

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

    def _get_tree(self, code, lines, marker=None, indent=0):
        def write(*args):
            if lines and lines[-1] is marker:  # Continue from the last line
                lines.pop()  # Remove the marker
                last = lines.pop()
                lines.append(last + " ".join(args))
            else:
                lines.append(" " * 6 * indent + " ".join(args))

        for node in code.nodes:
            if isinstance(node, Heading):
                write("=" * node.level)
                self._get_tree(node.title, lines, marker, indent + 1)
                write("=" * node.level)
            elif isinstance(node, Tag):
                tagnodes = node.tag.nodes
                if (not node.attrs and len(tagnodes) == 1 and
                        isinstance(tagnodes[0], Text)):
                    write("<" + unicode(tagnodes[0]) + ">")
                else:
                    write("<")
                    self._get_tree(node.tag, lines, marker, indent + 1)
                    for attr in node.attrs:
                        self._get_tree(attr.name, lines, marker, indent + 1)
                        if not attr.value:
                            continue
                        write("    = ")
                        lines.append(marker)  # Continue from this line
                        self._get_tree(attr.value, lines, marker, indent + 1)
                    write(">")
                self._get_tree(node.contents, lines, marker, indent + 1)
                if len(tagnodes) == 1 and isinstance(tagnodes[0], Text):
                    write("</" + unicode(tagnodes[0]) + ">")
                else:
                    write("</")
                    self._get_tree(node.tag, lines, marker, indent + 1)
                    write(">")
            elif isinstance(node, Template):
                write("{{")
                self._get_tree(node.name, lines, marker, indent + 1)
                for param in node.params:
                    write("    | ")
                    lines.append(marker)  # Continue from this line
                    self._get_tree(param.name, lines, marker, indent + 1)
                    write("    = ")
                    lines.append(marker)  # Continue from this line
                    self._get_tree(param.value, lines, marker, indent + 1)
                write("}}")
            else:
                write(unicode(node))
        return lines

    @property
    def nodes(self):
        return self._nodes

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

    def filter(self, recursive=False, matches=None, flags=FLAGS,
               forcetype=None):
        return list(self.ifilter(recursive, matches, flags, forcetype))

    def filter_templates(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_templates(recursive, matches, flags))

    def filter_text(self, recursive=False, matches=None, flags=FLAGS):
        return list(self.ifilter_text(recursive, matches, flags))

    def strip_code(self, normalize=True, collapse=True):
        nodes = []
        for node in self.nodes:
            stripped = node.__strip__(normalize)
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
        return "\n".join(self._get_tree(self, [], marker))

# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@gmail.com>
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
from collections import deque
from itertools import chain
import re

from .compat import py3k, range, str
from .nodes import (Argument, Comment, ExternalLink, Heading, HTMLEntity,
                    Node, Tag, Template, Text, Wikilink)
from .string_mixin import StringMixIn
from .utils import parse_anything

__all__ = ["Wikicode"]

FLAGS = re.IGNORECASE | re.DOTALL | re.UNICODE

class Wikicode(StringMixIn):
    """A ``Wikicode`` is a container for nodes that operates like a string.

    Additionally, it contains methods that can be used to extract data from or
    modify the nodes, implemented in an interface similar to a list. For
    example, :py:meth:`index` can get the index of a node in the list, and
    :py:meth:`insert` can add a new node at that index. The :py:meth:`filter()
    <ifilter>` series of functions is very useful for extracting and iterating
    over, for example, all of the templates in the object.
    """

    def __init__(self, nodes):
        super(Wikicode, self).__init__()
        self._nodes = nodes

    def __unicode__(self):
        return "".join([str(node) for node in self.nodes])

    @staticmethod
    def _get_children(node, contexts=False, parent=None):
        """Iterate over all child :py:class:`.Node`\ s of a given *node*."""
        yield (parent, node) if contexts else node
        for code in node.__children__():
            for child in code.nodes:
                for result in Wikicode._get_children(child, contexts, code):
                    yield result

    @staticmethod
    def _slice_replace(code, index, old, new):
        """Replace the string *old* with *new* across *index* in *code*."""
        nodes = [str(node) for node in code.get(index)]
        substring = "".join(nodes).replace(old, new)
        code.nodes[index] = parse_anything(substring).nodes

    def _do_strong_search(self, obj, recursive=True):
        """Search for the specific element *obj* within the node list.

        *obj* can be either a :py:class:`.Node` or a :py:class:`.Wikicode`
        object. If found, we return a tuple (*context*, *index*) where
        *context* is the :py:class:`.Wikicode` that contains *obj* and *index*
        is its index there, as a :py:class:`slice`. Note that if *recursive* is
        ``False``, *context* will always be ``self`` (since we only look for
        *obj* among immediate descendants), but if *recursive* is ``True``,
        then it could be any :py:class:`.Wikicode` contained by a node within
        ``self``. If *obj* is not found, :py:exc:`ValueError` is raised.
        """
        mkslice = lambda i: slice(i, i + 1)
        if isinstance(obj, Node):
            if not recursive:
                return self, mkslice(self.index(obj))
            for i, node in enumerate(self.nodes):
                for context, child in self._get_children(node, contexts=True):
                    if obj is child:
                        if not context:
                            context = self
                        return context, mkslice(context.index(child))
        else:
            context, ind = self._do_strong_search(obj.get(0), recursive)
            for i in range(1, len(obj.nodes)):
                if obj.get(i) is not context.get(ind.start + i):
                    break
            else:
                return context, slice(ind.start, ind.start + len(obj.nodes))
        raise ValueError(obj)

    def _do_weak_search(self, obj, recursive):
        """Search for an element that looks like *obj* within the node list.

        This follows the same rules as :py:meth:`_do_strong_search` with some
        differences. *obj* is treated as a string that might represent any
        :py:class:`.Node`, :py:class:`.Wikicode`, or combination of the two
        present in the node list. Thus, matching is weak (using string
        comparisons) rather than strong (using ``is``). Because multiple nodes
        can match *obj*, the result is a list of tuples instead of just one
        (however, :py:exc:`ValueError` is still raised if nothing is found).
        Individual matches will never overlap.

        The tuples contain a new first element, *exact*, which is ``True`` if
        we were able to match *obj* exactly to one or more adjacent nodes, or
        ``False`` if we found *obj* inside a node or incompletely spanning
        multiple nodes.
        """
        obj = parse_anything(obj)
        if not obj or obj not in self:
            raise ValueError(obj)
        results = []
        contexts = [self]
        while contexts:
            context = contexts.pop()
            i = len(context.nodes) - 1
            while i >= 0:
                node = context.get(i)
                if obj.get(-1) == node:
                    for j in range(-len(obj.nodes), -1):
                        if obj.get(j) != context.get(i + j + 1):
                            break
                    else:
                        i -= len(obj.nodes) - 1
                        index = slice(i, i + len(obj.nodes))
                        results.append((True, context, index))
                elif recursive and obj in node:
                    contexts.extend(node.__children__())
                i -= 1
        if not results:
            if not recursive:
                raise ValueError(obj)
            results.append((False, self, slice(0, len(self.nodes))))
        return results

    def _get_tree(self, code, lines, marker, indent):
        """Build a tree to illustrate the way the Wikicode object was parsed.

        The method that builds the actual tree is ``__showtree__`` of ``Node``
        objects. *code* is the ``Wikicode`` object to build a tree for. *lines*
        is the list to append the tree to, which is returned at the end of the
        method. *marker* is some object to be used to indicate that the builder
        should continue on from the last line instead of starting a new one; it
        should be any object that can be tested for with ``is``. *indent* is
        the starting indentation.
        """
        def write(*args):
            """Write a new line following the proper indentation rules."""
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

    @classmethod
    def _build_filter_methods(cls, **meths):
        """Given Node types, build the corresponding i?filter shortcuts.

        The should be given as keys storing the method's base name paired
        with values storing the corresponding :py:class:`~.Node` type. For
        example, the dict may contain the pair ``("templates", Template)``,
        which will produce the methods :py:meth:`ifilter_templates` and
        :py:meth:`filter_templates`, which are shortcuts for
        :py:meth:`ifilter(forcetype=Template) <ifilter>` and
        :py:meth:`filter(forcetype=Template) <filter>`, respectively. These
        shortcuts are added to the class itself, with an appropriate docstring.
        """
        doc = """Iterate over {0}.

        This is equivalent to :py:meth:`{1}` with *forcetype* set to
        :py:class:`~{2.__module__}.{2.__name__}`.
        """
        make_ifilter = lambda ftype: (lambda self, **kw:
                                      self.ifilter(forcetype=ftype, **kw))
        make_filter = lambda ftype: (lambda self, **kw:
                                     self.filter(forcetype=ftype, **kw))
        for name, ftype in (meths.items() if py3k else meths.iteritems()):
            ifilter = make_ifilter(ftype)
            filter = make_filter(ftype)
            ifilter.__doc__ = doc.format(name, "ifilter", ftype)
            filter.__doc__ = doc.format(name, "filter", ftype)
            setattr(cls, "ifilter_" + name, ifilter)
            setattr(cls, "filter_" + name, filter)

    @property
    def nodes(self):
        """A list of :py:class:`~.Node` objects.

        This is the internal data actually stored within a
        :py:class:`~.Wikicode` object.
        """
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        if not isinstance(value, list):
            value = parse_anything(value).nodes
        self._nodes = value

    def get(self, index):
        """Return the *index*\ th node within the list of nodes."""
        return self.nodes[index]

    def set(self, index, value):
        """Set the ``Node`` at *index* to *value*.

        Raises :py:exc:`IndexError` if *index* is out of range, or
        :py:exc:`ValueError` if *value* cannot be coerced into one
        :py:class:`~.Node`. To insert multiple nodes at an index, use
        :py:meth:`get` with either :py:meth:`remove` and :py:meth:`insert` or
        :py:meth:`replace`.
        """
        nodes = parse_anything(value).nodes
        if len(nodes) > 1:
            raise ValueError("Cannot coerce multiple nodes into one index")
        if index >= len(self.nodes) or -1 * index > len(self.nodes):
            raise IndexError("List assignment index out of range")
        if nodes:
            self.nodes[index] = nodes[0]
        else:
            self.nodes.pop(index)

    def index(self, obj, recursive=False):
        """Return the index of *obj* in the list of nodes.

        Raises :py:exc:`ValueError` if *obj* is not found. If *recursive* is
        ``True``, we will look in all nodes of ours and their descendants, and
        return the index of our direct descendant node within *our* list of
        nodes. Otherwise, the lookup is done only on direct descendants.
        """
        strict = isinstance(obj, Node)
        equivalent = (lambda o, n: o is n) if strict else (lambda o, n: o == n)
        for i, node in enumerate(self.nodes):
            if recursive:
                for child in self._get_children(node):
                    if equivalent(obj, child):
                        return i
            elif equivalent(obj, node):
                    return i
        raise ValueError(obj)

    def insert(self, index, value):
        """Insert *value* at *index* in the list of nodes.

        *value* can be anything parasable by :py:func:`.parse_anything`, which
        includes strings or other :py:class:`~.Wikicode` or :py:class:`~.Node`
        objects.
        """
        nodes = parse_anything(value).nodes
        for node in reversed(nodes):
            self.nodes.insert(index, node)

    def insert_before(self, obj, value, recursive=True):
        """Insert *value* immediately before *obj*.

        *obj* can be either a string, a :py:class:`~.Node`, or another
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). If *obj* is a string, we will operate on all instances
        of that string within the code, otherwise only on the specific instance
        given. *value* can be anything parasable by :py:func:`.parse_anything`.
        If *recursive* is ``True``, we will try to find *obj* within our child
        nodes even if it is not a direct descendant of this
        :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        if isinstance(obj, (Node, Wikicode)):
            context, index = self._do_strong_search(obj, recursive)
            context.insert(index.start, value)
        else:
            for exact, context, index in self._do_weak_search(obj, recursive):
                if exact:
                    context.insert(index.start, value)
                else:
                    obj = str(obj)
                    self._slice_replace(context, index, obj, str(value) + obj)

    def insert_after(self, obj, value, recursive=True):
        """Insert *value* immediately after *obj*.

        *obj* can be either a string, a :py:class:`~.Node`, or another
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). If *obj* is a string, we will operate on all instances
        of that string within the code, otherwise only on the specific instance
        given. *value* can be anything parasable by :py:func:`.parse_anything`.
        If *recursive* is ``True``, we will try to find *obj* within our child
        nodes even if it is not a direct descendant of this
        :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        if isinstance(obj, (Node, Wikicode)):
            context, index = self._do_strong_search(obj, recursive)
            context.insert(index.stop, value)
        else:
            for exact, context, index in self._do_weak_search(obj, recursive):
                if exact:
                    context.insert(index.stop, value)
                else:
                    obj = str(obj)
                    self._slice_replace(context, index, obj, obj + str(value))

    def replace(self, obj, value, recursive=True):
        """Replace *obj* with *value*.

        *obj* can be either a string, a :py:class:`~.Node`, or another
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). If *obj* is a string, we will operate on all instances
        of that string within the code, otherwise only on the specific instance
        given. *value* can be anything parasable by :py:func:`.parse_anything`.
        If *recursive* is ``True``, we will try to find *obj* within our child
        nodes even if it is not a direct descendant of this
        :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        if isinstance(obj, (Node, Wikicode)):
            context, index = self._do_strong_search(obj, recursive)
            for i in range(index.start, index.stop):
                context.nodes.pop(index.start)
            context.insert(index.start, value)
        else:
            for exact, context, index in self._do_weak_search(obj, recursive):
                if exact:
                    for i in range(index.start, index.stop):
                        context.nodes.pop(index.start)
                    context.insert(index.start, value)
                else:
                    self._slice_replace(context, index, str(obj), str(value))

    def append(self, value):
        """Insert *value* at the end of the list of nodes.

        *value* can be anything parasable by :py:func:`.parse_anything`.
        """
        nodes = parse_anything(value).nodes
        for node in nodes:
            self.nodes.append(node)

    def remove(self, obj, recursive=True):
        """Remove *obj* from the list of nodes.

        *obj* can be either a string, a :py:class:`~.Node`, or another
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). If *obj* is a string, we will operate on all instances
        of that string within the code, otherwise only on the specific instance
        given. If *recursive* is ``True``, we will try to find *obj* within our
        child nodes even if it is not a direct descendant of this
        :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        if isinstance(obj, (Node, Wikicode)):
            context, index = self._do_strong_search(obj, recursive)
            for i in range(index.start, index.stop):
                context.nodes.pop(index.start)
        else:
            for exact, context, index in self._do_weak_search(obj, recursive):
                if exact:
                    for i in range(index.start, index.stop):
                        context.nodes.pop(index.start)
                else:
                    self._slice_replace(context, index, str(obj), "")

    def matches(self, other):
        """Do a loose equivalency test suitable for comparing page names.

        *other* can be any string-like object, including
        :py:class:`~.Wikicode`, or a tuple of these. This operation is
        symmetric; both sides are adjusted. Specifically, whitespace and markup
        is stripped and the first letter's case is normalized. Typical usage is
        ``if template.name.matches("stub"): ...``.
        """
        cmp = lambda a, b: (a[0].upper() + a[1:] == b[0].upper() + b[1:]
                            if a and b else a == b)
        this = self.strip_code().strip()
        if isinstance(other, (tuple, list)):
            for obj in other:
                that = parse_anything(obj).strip_code().strip()
                if cmp(this, that):
                    return True
            return False
        that = parse_anything(other).strip_code().strip()
        return cmp(this, that)

    def ifilter(self, recursive=True, matches=None, flags=FLAGS,
                forcetype=None):
        """Iterate over nodes in our list matching certain conditions.

        If *recursive* is ``True``, we will iterate over our children and all
        of their descendants, otherwise just our immediate children. If
        *forcetype* is given, only nodes that are instances of this type are
        yielded. *matches* can be used to further restrict the nodes, either as
        a function (taking a single :py:class:`.Node` and returning a boolean)
        or a regular expression (matched against the node's string
        representation with :py:func:`re.search`). If *matches* is a regex, the
        flags passed to :py:func:`re.search` are :py:const:`re.IGNORECASE`,
        :py:const:`re.DOTALL`, and :py:const:`re.UNICODE`, but custom flags can
        be specified by passing *flags*.
        """
        if matches and not callable(matches):
            pat, matches = matches, lambda obj: re.search(pat, str(obj), flags)
        if recursive:
            getter = self._get_children
            nodes = chain.from_iterable(getter(n) for n in self.nodes)
        else:
            nodes = self.nodes
        for node in nodes:
            if not forcetype or isinstance(node, forcetype):
                if not matches or matches(node):
                    yield node

    def filter(self, recursive=True, matches=None, flags=FLAGS,
               forcetype=None):
        """Return a list of nodes within our list matching certain conditions.

        This is equivalent to calling :py:func:`list` on :py:meth:`ifilter`.
        """
        return list(self.ifilter(recursive, matches, flags, forcetype))

    def get_sections(self, levels=None, matches=None, flags=FLAGS, flat=False,
                     include_lead=None, include_headings=True):
        """Return a list of sections within the page.

        Sections are returned as :py:class:`~.Wikicode` objects with a shared
        node list (implemented using :py:class:`~.SmartList`) so that changes
        to sections are reflected in the parent Wikicode object.

        Each section contains all of its subsections, unless *flat* is
        ``True``. If *levels* is given, it should be a iterable of integers;
        only sections whose heading levels are within it will be returned. If
        *matches* is given, it should be a regex to be matched against the
        titles of section headings; only sections whose headings match the
        regex will be included. *flags* can be used to override the default
        regex flags (see :py:meth:`ifilter`) if *matches* is used.

        If *include_lead* is ``True``, the first, lead section (without a
        heading) will be included in the list; ``False`` will not include it;
        the default will include it only if no specific *levels* were given. If
        *include_headings* is ``True``, the section's beginning
        :py:class:`~.Heading` object will be included; otherwise, this is
        skipped.
        """
        if matches:
            matches = r"^(=+?)\s*" + matches + r"\s*\1$"
        headings = self.filter_headings(recursive=False, matches=matches,
                                        flags=flags)
        if levels:
            headings = [head for head in headings if head.level in levels]

        sections = []
        if include_lead or not (include_lead is not None or matches or levels):
            iterator = self.ifilter_headings(recursive=False)
            try:
                first = self.index(next(iterator))
                sections.append(Wikicode(self.nodes[:first]))
            except StopIteration:  # No headings in page
                sections.append(Wikicode(self.nodes[:]))

        for heading in headings:
            start = self.index(heading)
            i = start + 1
            if not include_headings:
                start += 1
            while i < len(self.nodes):
                node = self.nodes[i]
                if isinstance(node, Heading):
                    if flat or node.level <= heading.level:
                        break
                i += 1
            sections.append(Wikicode(self.nodes[start:i]))
        return sections

    def strip_code(self, normalize=True, collapse=True):
        """Return a rendered string without unprintable code such as templates.

        The way a node is stripped is handled by the
        :py:meth:`~.Node.__showtree__` method of :py:class:`~.Node` objects,
        which generally return a subset of their nodes or ``None``. For
        example, templates and tags are removed completely, links are stripped
        to just their display part, headings are stripped to just their title.
        If *normalize* is ``True``, various things may be done to strip code
        further, such as converting HTML entities like ``&Sigma;``, ``&#931;``,
        and ``&#x3a3;`` to ``Σ``. If *collapse* is ``True``, we will try to
        remove excess whitespace as well (three or more newlines are converted
        to two, for example).
        """
        nodes = []
        for node in self.nodes:
            stripped = node.__strip__(normalize, collapse)
            if stripped:
                nodes.append(str(stripped))

        if collapse:
            stripped = "".join(nodes).strip("\n")
            while "\n\n\n" in stripped:
                stripped = stripped.replace("\n\n\n", "\n\n")
            return stripped
        else:
            return "".join(nodes)

    def get_tree(self):
        """Return a hierarchical tree representation of the object.

        The representation is a string makes the most sense printed. It is
        built by calling :py:meth:`_get_tree` on the
        :py:class:`~.Wikicode` object and its children recursively. The end
        result may look something like the following::

            >>> text = "Lorem ipsum {{foo|bar|{{baz}}|spam=eggs}}"
            >>> print mwparserfromhell.parse(text).get_tree()
            Lorem ipsum
            {{
                  foo
                | 1
                = bar
                | 2
                = {{
                        baz
                  }}
                | spam
                = eggs
            }}
        """
        marker = object()  # Random object we can find with certainty in a list
        return "\n".join(self._get_tree(self, [], marker, 0))

Wikicode._build_filter_methods(
    arguments=Argument, comments=Comment, external_links=ExternalLink,
    headings=Heading, html_entities=HTMLEntity, tags=Tag, templates=Template,
    text=Text, wikilinks=Wikilink)

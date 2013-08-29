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
import re

from .compat import maxsize, py3k, str
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

    def _get_children(self, node):
        """Iterate over all descendants of a given *node*, including itself.

        This is implemented by the ``__iternodes__()`` generator of ``Node``
        classes, which by default yields itself and nothing more.
        """
        for context, child in node.__iternodes__(self._get_all_nodes):
            yield child

    def _get_all_nodes(self, code):
        """Iterate over all of our descendant nodes.

        This is implemented by calling :py:meth:`_get_children` on every node
        in our node list (:py:attr:`self.nodes <nodes>`).
        """
        for node in code.nodes:
            for child in self._get_children(node):
                yield child

    def _is_equivalent(self, obj, node):
        """Return ``True`` if *obj* and *node* are equivalent, else ``False``.

        If *obj* is a ``Node``, the function will test whether they are the
        same object, otherwise it will compare them with ``==``.
        """
        return (node is obj) if isinstance(obj, Node) else (node == obj)

    def _contains(self, nodes, obj):
        """Return ``True`` if *obj* is inside of *nodes*, else ``False``.

        If *obj* is a ``Node``, we will only return ``True`` if *obj* is
        actually in the list (and not just a node that equals it). Otherwise,
        the test is simply ``obj in nodes``.
        """
        if isinstance(obj, Node):
            for node in nodes:
                if node is obj:
                    return True
            return False
        return obj in nodes

    def _do_search(self, obj, recursive, context=None, literal=None):
        """Return some info about the location of *obj* within *context*.

        If *recursive* is ``True``, we'll look within *context* (``self`` by
        default) and its descendants, otherwise just *context*. We raise
        :py:exc:`ValueError` if *obj* isn't found. The return data is a list of
        3-tuples (*type*, *context*, *data*) where *type* is *obj*\ 's best
        type resolution (either ``Node``, ``Wikicode``, or ``str``), *context*
        is the closest ``Wikicode`` encompassing it, and *data* is either a
        ``Node``, a list of ``Node``\ s, or ``None`` depending on *type*.
        """
        if not context:
            context = self
            literal = isinstance(obj, (Node, Wikicode))
            obj = parse_anything(obj)
            if not obj or obj not in self:
                raise ValueError(obj)
            if len(obj.nodes) == 1:
                obj = obj.get(0)

        compare = lambda a, b: (a is b) if literal else (a == b)
        results = []
        i = 0
        while i < len(context.nodes):
            node = context.get(i)
            if isinstance(obj, Node) and compare(obj, node):
                results.append((Node, context, node))
            elif isinstance(obj, Wikicode) and compare(obj.get(0), node):
                for j in range(1, len(obj.nodes)):
                    if not compare(obj.get(j), context.get(i + j)):
                        break
                else:
                    nodes = list(context.nodes[i:i + len(obj.nodes)])
                    results.append((Wikicode, context, nodes))
                    i += len(obj.nodes) - 1
            elif recursive:
                contexts = node.__iternodes__(self._get_all_nodes)
                processed = []
                for code in (ctx for ctx, child in contexts):
                    if code and code not in processed and obj in code:
                        search = self._do_search(obj, recursive, code, literal)
                        results.extend(search)
                        processed.append(code)
            i += 1

        if not results and not literal and recursive:
            results.append((str, context, None))
        if not results and context is self:
            raise ValueError(obj)
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
        """Insert *value* at *index* in the list of nodes.

        *value* can be anything parasable by :py:func:`.parse_anything`, which
        includes strings or other :py:class:`~.Wikicode` or :py:class:`~.Node`
        objects.
        """
        nodes = parse_anything(value).nodes
        for node in reversed(nodes):
            self.nodes.insert(index, node)

    def insert_before(self, obj, value, recursive=True):
        """Insert *value* immediately before *obj* in the list of nodes.

        *obj* can be either a string, a :py:class:`~.Node`, or other
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). *value* can be anything parasable by
        :py:func:`.parse_anything`. If *recursive* is ``True``, we will try to
        find *obj* within our child nodes even if it is not a direct descendant
        of this :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        for restype, context, data in self._do_search(obj, recursive):
            if restype in (Node, Wikicode):
                i = context.index(data if restype is Node else data[0], False)
                context.insert(i, value)
            else:
                obj = str(obj)
                context.nodes = str(context).replace(obj, str(value) + obj)

    def insert_after(self, obj, value, recursive=True):
        """Insert *value* immediately after *obj* in the list of nodes.

        *obj* can be either a string, a :py:class:`~.Node`, or other
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). *value* can be anything parasable by
        :py:func:`.parse_anything`. If *recursive* is ``True``, we will try to
        find *obj* within our child nodes even if it is not a direct descendant
        of this :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        for restype, context, data in self._do_search(obj, recursive):
            if restype in (Node, Wikicode):
                i = context.index(data if restype is Node else data[-1], False)
                context.insert(i + 1, value)
            else:
                obj = str(obj)
                context.nodes = str(context).replace(obj, obj + str(value))

    def replace(self, obj, value, recursive=True):
        """Replace *obj* with *value* in the list of nodes.

        *obj* can be either a string, a :py:class:`~.Node`, or other
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). *value* can be anything parasable by
        :py:func:`.parse_anything`. If *recursive* is ``True``, we will try to
        find *obj* within our child nodes even if it is not a direct descendant
        of this :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        for restype, context, data in self._do_search(obj, recursive):
            if restype is Node:
                i = context.index(data, False)
                context.nodes.pop(i)
                context.insert(i, value)
            elif restype is Wikicode:
                i = context.index(data[0], False)
                for _ in data:
                    context.nodes.pop(i)
                context.insert(i, value)
            else:
                context.nodes = str(context).replace(str(obj), str(value))

    def append(self, value):
        """Insert *value* at the end of the list of nodes.

        *value* can be anything parasable by :py:func:`.parse_anything`.
        """
        nodes = parse_anything(value).nodes
        for node in nodes:
            self.nodes.append(node)

    def remove(self, obj, recursive=True):
        """Remove *obj* from the list of nodes.

        *obj* can be either a string, a :py:class:`~.Node`, or other
        :py:class:`~.Wikicode` object (as created by :py:meth:`get_sections`,
        for example). If *recursive* is ``True``, we will try to find *obj*
        within our child nodes even if it is not a direct descendant of this
        :py:class:`~.Wikicode` object. If *obj* is not found,
        :py:exc:`ValueError` is raised.
        """
        for restype, context, data in self._do_search(obj, recursive):
            if restype is Node:
                context.nodes.pop(context.index(data, False))
            elif restype is Wikicode:
                i = context.index(data[0], False)
                for _ in data:
                    context.nodes.pop(i)
            else:
                context.nodes = str(context).replace(str(obj), "")

    def matches(self, other):
        """Do a loose equivalency test suitable for comparing page names.

        *other* can be any string-like object, including
        :py:class:`~.Wikicode`. This operation is symmetric; both sides are
        adjusted. Specifically, whitespace and markup is stripped and the first
        letter's case is normalized. Typical usage is
        ``if template.name.matches("stub"): ...``.
        """
        this = self.strip_code().strip()
        that = parse_anything(other).strip_code().strip()
        if not this or not that:
            return this == that
        return this[0].upper() + this[1:] == that[0].upper() + that[1:]

    def ifilter(self, recursive=True, matches=None, flags=FLAGS,
                forcetype=None):
        """Iterate over nodes in our list matching certain conditions.

        If *recursive* is ``True``, we will iterate over our children and all
        descendants of our children, otherwise just our immediate children. If
        *matches* is given, we will only yield the nodes that match the given
        regular expression (with :py:func:`re.search`). The default flags used
        are :py:const:`re.IGNORECASE`, :py:const:`re.DOTALL`, and
        :py:const:`re.UNICODE`, but custom flags can be specified by passing
        *flags*. If *forcetype* is given, only nodes that are instances of this
        type are yielded.
        """
        for node in (self._get_all_nodes(self) if recursive else self.nodes):
            if not forcetype or isinstance(node, forcetype):
                if not matches or re.search(matches, str(node), flags):
                    yield node

    def filter(self, recursive=True, matches=None, flags=FLAGS,
               forcetype=None):
        """Return a list of nodes within our list matching certain conditions.

        This is equivalent to calling :py:func:`list` on :py:meth:`ifilter`.
        """
        return list(self.ifilter(recursive, matches, flags, forcetype))

    def get_sections(self, levels=None, matches=None, flags=FLAGS,
                     include_lead=None, include_headings=True):
        """Return a list of sections within the page.

        Sections are returned as :py:class:`~.Wikicode` objects with a shared
        node list (implemented using :py:class:`~.SmartList`) so that changes
        to sections are reflected in the parent Wikicode object.

        Each section contains all of its subsections. If *levels* is given, it
        should be a iterable of integers; only sections whose heading levels
        are within it will be returned. If *matches* is given, it should be a
        regex to be matched against the titles of section headings; only
        sections whose headings match the regex will be included. *flags* can
        be used to override the default regex flags (see :py:meth:`ifilter`) if
        *matches* is used.

        If *include_lead* is ``True``, the first, lead section (without a
        heading) will be included in the list; ``False`` will not include it;
        the default will include it only if no specific *levels* were given. If
        *include_headings* is ``True``, the section's beginning
        :py:class:`~.Heading` object will be included; otherwise, this is
        skipped.
        """
        if matches:
            matches = r"^(=+?)\s*" + matches + r"\s*\1$"
        headings = self.filter_headings()
        filtered = self.filter_headings(matches=matches, flags=flags)
        if levels:
            filtered = [head for head in filtered if head.level in levels]

        if matches or include_lead is False or (not include_lead and levels):
            buffers = []
        else:
            buffers = [(maxsize, 0)]
        sections = []
        i = 0
        while i < len(self.nodes):
            if self.nodes[i] in headings:
                this = self.nodes[i].level
                for (level, start) in buffers:
                    if this <= level:
                        sections.append(Wikicode(self.nodes[start:i]))
                buffers = [buf for buf in buffers if buf[0] < this]
                if self.nodes[i] in filtered:
                    if not include_headings:
                        i += 1
                        if i >= len(self.nodes):
                            break
                    buffers.append((this, i))
            i += 1
        for (level, start) in buffers:
            if start != i:
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

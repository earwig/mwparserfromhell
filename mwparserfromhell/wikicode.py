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
import re

from .compat import maxsize, str
from .nodes import Heading, Node, Tag, Template, Text, Wikilink
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

    def _get_context(self, node, obj):
        """Return a ``Wikicode`` that contains *obj* in its descendants.

        The closest (shortest distance from *node*) suitable ``Wikicode`` will
        be returned, or ``None`` if the *obj* is the *node* itself.

        Raises ``ValueError`` if *obj* is not within *node*.
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
        """Return ``True`` if *obj* and *node* are equivalent, else ``False``.

        If *obj* is a ``Node``, the function will test whether they are the
        same object, otherwise it will compare them with ``==``.
        """
        if isinstance(obj, Node):
            if node is obj:
                return True
        else:
            if node == obj:
                return True
        return False

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

    def _do_search(self, obj, recursive, callback, context, *args, **kwargs):
        """Look within *context* for *obj*, executing *callback* if found.

        If *recursive* is ``True``, we'll look within context and its
        descendants, otherwise we'll just execute callback. We raise
        :py:exc:`ValueError` if *obj* isn't in our node list or context. If
        found, *callback* is passed the context, the index of the node within
        the context, and whatever were passed as ``*args`` and ``**kwargs``.
        """
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

    @property
    def nodes(self):
        """A list of :py:class:`~.Node` objects.

        This is the internal data actually stored within a
        :py:class:`~.Wikicode` object.
        """
        return self._nodes

    @nodes.setter
    def nodes(self, value):
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
        self.nodes.pop(index)
        if nodes:
            self.nodes[index] = nodes[0]

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

        *obj* can be either a string or a :py:class:`~.Node`. *value* can be
        anything parasable by :py:func:`.parse_anything`. If *recursive* is
        ``True``, we will try to find *obj* within our child nodes even if it
        is not a direct descendant of this :py:class:`~.Wikicode` object. If
        *obj* is not in the node list, :py:exc:`ValueError` is raised.
        """
        callback = lambda self, i, value: self.insert(i, value)
        self._do_search(obj, recursive, callback, self, value)

    def insert_after(self, obj, value, recursive=True):
        """Insert *value* immediately after *obj* in the list of nodes.

        *obj* can be either a string or a :py:class:`~.Node`. *value* can be
        anything parasable by :py:func:`.parse_anything`. If *recursive* is
        ``True``, we will try to find *obj* within our child nodes even if it
        is not a direct descendant of this :py:class:`~.Wikicode` object. If
        *obj* is not in the node list, :py:exc:`ValueError` is raised.
        """
        callback = lambda self, i, value: self.insert(i + 1, value)
        self._do_search(obj, recursive, callback, self, value)

    def replace(self, obj, value, recursive=True):
        """Replace *obj* with *value* in the list of nodes.

        *obj* can be either a string or a :py:class:`~.Node`. *value* can be
        anything parasable by :py:func:`.parse_anything`. If *recursive* is
        ``True``, we will try to find *obj* within our child nodes even if it
        is not a direct descendant of this :py:class:`~.Wikicode` object. If
        *obj* is not in the node list, :py:exc:`ValueError` is raised.
        """
        def callback(self, i, value):
            self.nodes.pop(i)
            self.insert(i, value)

        self._do_search(obj, recursive, callback, self, value)

    def append(self, value):
        """Insert *value* at the end of the list of nodes.

        *value* can be anything parasable by :py:func:`.parse_anything`.
        """
        nodes = parse_anything(value).nodes
        for node in nodes:
            self.nodes.append(node)

    def remove(self, obj, recursive=True):
        """Remove *obj* from the list of nodes.

        *obj* can be either a string or a :py:class:`~.Node`. If *recursive* is
        ``True``, we will try to find *obj* within our child nodes even if it
        is not a direct descendant of this :py:class:`~.Wikicode` object. If
        *obj* is not in the node list, :py:exc:`ValueError` is raised.
        """
        callback = lambda self, i: self.nodes.pop(i)
        self._do_search(obj, recursive, callback, self)

    def ifilter(self, recursive=False, matches=None, flags=FLAGS,
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
        if recursive:
            nodes = self._get_all_nodes(self)
        else:
            nodes = self.nodes
        for node in nodes:
            if not forcetype or isinstance(node, forcetype):
                if not matches or re.search(matches, str(node), flags):
                    yield node

    def ifilter_links(self, recursive=False, matches=None, flags=FLAGS):
        """Iterate over wikilink nodes.

        This is equivalent to :py:meth:`ifilter` with *forcetype* set to
        :py:class:`~.Wikilink`.
        """
        return self.ifilter(recursive, matches, flags, forcetype=Wikilink)

    def ifilter_templates(self, recursive=False, matches=None, flags=FLAGS):
        """Iterate over template nodes.

        This is equivalent to :py:meth:`ifilter` with *forcetype* set to
        :py:class:`~.Template`.
        """
        return self.filter(recursive, matches, flags, forcetype=Template)

    def ifilter_text(self, recursive=False, matches=None, flags=FLAGS):
        """Iterate over text nodes.

        This is equivalent to :py:meth:`ifilter` with *forcetype* set to
        :py:class:`~.nodes.Text`.
        """
        return self.filter(recursive, matches, flags, forcetype=Text)

    def ifilter_tags(self, recursive=False, matches=None, flags=FLAGS):
        """Iterate over tag nodes.

        This is equivalent to :py:meth:`ifilter` with *forcetype* set to
        :py:class:`~.Tag`.
        """
        return self.ifilter(recursive, matches, flags, forcetype=Tag)

    def filter(self, recursive=False, matches=None, flags=FLAGS,
               forcetype=None):
        """Return a list of nodes within our list matching certain conditions.

        This is equivalent to calling :py:func:`list` on :py:meth:`ifilter`.
        """
        return list(self.ifilter(recursive, matches, flags, forcetype))

    def filter_links(self, recursive=False, matches=None, flags=FLAGS):
        """Return a list of wikilink nodes.

        This is equivalent to calling :py:func:`list` on
        :py:meth:`ifilter_links`.
        """
        return list(self.ifilter_links(recursive, matches, flags))

    def filter_templates(self, recursive=False, matches=None, flags=FLAGS):
        """Return a list of template nodes.

        This is equivalent to calling :py:func:`list` on
        :py:meth:`ifilter_templates`.
        """
        return list(self.ifilter_templates(recursive, matches, flags))

    def filter_text(self, recursive=False, matches=None, flags=FLAGS):
        """Return a list of text nodes.

        This is equivalent to calling :py:func:`list` on
        :py:meth:`ifilter_text`.
        """
        return list(self.ifilter_text(recursive, matches, flags))

    def filter_tags(self, recursive=False, matches=None, flags=FLAGS):
        """Return a list of tag nodes.

        This is equivalent to calling :py:func:`list` on
        :py:meth:`ifilter_tags`.
        """
        return list(self.ifilter_tags(recursive, matches, flags))

    def get_sections(self, flat=True, matches=None, levels=None, flags=FLAGS,
                     include_headings=True):
        """Return a list of sections within the page.

        Sections are returned as :py:class:`~.Wikicode` objects with a shared
        node list (implemented using :py:class:`~.SmartList`) so that changes
        to sections are reflected in the parent Wikicode object.

        With *flat* as ``True``, each returned section contains all of its
        subsections within the :py:class:`~.Wikicode`; otherwise, the returned
        sections contain only the section up to the next heading, regardless of
        its size. If *matches* is given, it should be a regex to matched
        against the titles of section headings; only sections whose headings
        match the regex will be included. If *levels* is given, it should be a =
        list of integers; only sections whose heading levels are within the
        list will be returned. If *include_headings* is ``True``, the section's
        literal :py:class:`~.Heading` object will be included in returned
        :py:class:`~.Wikicode` objects; otherwise, this is skipped.
        """
        if matches:
            matches = r"^(=+?)\s*" + matches + r"\s*\1$"
        headings = self.filter(recursive=True, matches=matches, flags=flags,
                                forcetype=Heading)
        if levels:
            headings = [head for head in headings if head.level in levels]

        sections = []
        buffers = [[maxsize, 0]]
        i = 0
        while i < len(self.nodes):
            if self.nodes[i] in headings:
                this = self.nodes[i].level
                for (level, start) in buffers:
                    if not flat or this <= level:
                        buffers.remove([level, start])
                        sections.append(Wikicode(self.nodes[start:i]))
                buffers.append([this, i])
                if not include_headings:
                    i += 1
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

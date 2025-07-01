# Copyright (C) 2012-2025 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from __future__ import annotations

import re
from collections.abc import Generator, Iterable
from enum import Enum
from itertools import chain
from typing import Any, Callable, Literal, TypeVar, cast, overload

from .nodes import (
    Argument,
    Comment,
    ExternalLink,
    Heading,
    HTMLEntity,
    Node,
    Tag,
    Template,
    Text,
    Wikilink,
)
from .smart_list.list_proxy import ListProxy
from .string_mixin import StringMixIn
from .utils import parse_anything

__all__ = ["Wikicode"]

FLAGS = re.IGNORECASE | re.DOTALL

N = TypeVar("N", bound=Node)


class Recurse(Enum):
    RECURSE_OTHERS = 2


class Wikicode(StringMixIn):
    """A ``Wikicode`` is a container for nodes that operates like a string.

    Additionally, it contains methods that can be used to extract data from or
    modify the nodes, implemented in an interface similar to a list. For
    example, :meth:`index` can get the index of a node in the list, and
    :meth:`insert` can add a new node at that index. The :meth:`filter()
    <ifilter>` series of functions is very useful for extracting and iterating
    over, for example, all of the templates in the object.
    """

    RECURSE_OTHERS = Recurse.RECURSE_OTHERS

    def __init__(self, nodes: list[Node]):
        super().__init__()
        self._nodes = nodes

    def __str__(self) -> str:
        return "".join([str(node) for node in self.nodes])

    @overload
    @staticmethod
    def _get_children(
        node: Node,
        contexts: Literal[False] = False,
        restrict: type | None = None,
        parent: Wikicode | None = None,
    ) -> Generator[Node]: ...

    @overload
    @staticmethod
    def _get_children(
        node: Node,
        contexts: Literal[True],
        restrict: type | None = None,
        parent: Wikicode | None = None,
    ) -> Generator[tuple[Wikicode | None, Node]]: ...

    @staticmethod
    def _get_children(
        node: Node,
        contexts: bool = False,
        restrict: type | None = None,
        parent: Wikicode | None = None,
    ) -> Generator[tuple[Wikicode | None, Node] | Node]:
        """Iterate over all child :class:`.Node`\\ s of a given *node*."""
        yield (parent, node) if contexts else node
        if restrict and isinstance(node, restrict):
            return
        for code in node.__children__():
            for child in code.nodes:
                sub = Wikicode._get_children(child, contexts, restrict, code)
                yield from sub

    @staticmethod
    def _slice_replace(code: Wikicode, index: slice, old: str, new: str) -> None:
        """Replace the string *old* with *new* across *index* in *code*."""
        nodes = [str(node) for node in code.get(index)]
        substring = "".join(nodes).replace(old, new)
        code.nodes[index] = parse_anything(substring).nodes

    @staticmethod
    def _build_matcher(
        matches: Callable[[N], bool | re.Match[str] | None] | re.Pattern | str | None,
        flags: int,
    ) -> Callable[[N], bool | re.Match[str] | None]:
        """Helper for :meth:`_indexed_ifilter` and others.

        If *matches* is a function, return it. If it's a regex, return a
        wrapper around it that can be called with a node to do a search. If
        it's ``None``, return a function that always returns ``True``.
        """
        if matches:
            if callable(matches):
                return matches
            else:
                return lambda obj: re.search(matches, str(obj), flags)
        else:
            return lambda obj: True

    def _indexed_ifilter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[N], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        forcetype: type[N] | None = None,
    ) -> Generator[tuple[int, N]]:
        """Iterate over nodes and their corresponding indices in the node list.

        The arguments are interpreted as for :meth:`ifilter`. For each tuple
        ``(i, node)`` yielded by this method, ``self.index(node) == i``. Note
        that if *recursive* is ``True``, ``self.nodes[i]`` might not be the
        node itself, but will still contain it.
        """
        match = self._build_matcher(matches, flags)
        inodes: Iterable[tuple[int, Node]]
        if recursive:
            restrict = forcetype if recursive == self.RECURSE_OTHERS else None

            def getter(i: int, node: Node) -> Generator[tuple[int, Node]]:
                for ch in self._get_children(node, restrict=restrict):
                    yield (i, cast(Node, ch))

            inodes = chain(*(getter(i, n) for i, n in enumerate(self.nodes)))
        else:
            inodes = enumerate(self.nodes)
        for i, node in inodes:
            if (forcetype is None or isinstance(node, forcetype)) and match(
                cast(N, node)
            ):
                yield (i, cast(N, node))

    def _is_child_wikicode(self, obj: Wikicode, recursive: bool = True) -> bool:
        """Return whether the given :class:`.Wikicode` is a descendant."""

        def deref(nodes):
            if isinstance(nodes, ListProxy):
                return nodes._parent  # pylint: disable=protected-access
            return nodes

        target = deref(obj.nodes)
        if target is deref(self.nodes):
            return True
        if recursive:
            todo = [self]
            while todo:
                code = todo.pop()
                if target is deref(code.nodes):
                    return True
                for node in code.nodes:
                    todo += list(node.__children__())
        return False

    def _do_strong_search(
        self, obj: Node | Wikicode, recursive: bool = True
    ) -> tuple[Wikicode, slice]:
        """Search for the specific element *obj* within the node list.

        *obj* can be either a :class:`.Node` or a :class:`.Wikicode` object. If
        found, we return a tuple (*context*, *index*) where *context* is the
        :class:`.Wikicode` that contains *obj* and *index* is its index there,
        as a :class:`slice`. Note that if *recursive* is ``False``, *context*
        will always be ``self`` (since we only look for *obj* among immediate
        descendants), but if *recursive* is ``True``, then it could be any
        :class:`.Wikicode` contained by a node within ``self``. If *obj* is not
        found, :exc:`ValueError` is raised.
        """
        if isinstance(obj, Wikicode):
            if not self._is_child_wikicode(obj, recursive):
                raise ValueError(obj)
            return obj, slice(0, len(obj.nodes))

        elif isinstance(obj, Node):

            def mkslice(i):
                return slice(i, i + 1)

            if not recursive:
                return self, mkslice(self.index(obj))
            for node in self.nodes:
                for context, child in self._get_children(node, contexts=True):
                    if obj is child:
                        if not context:
                            context = self
                        return context, mkslice(context.index(child))
            raise ValueError(obj)

        else:
            raise TypeError(obj)

    def _do_weak_search(
        self, obj: Any, recursive: bool
    ) -> list[tuple[bool, Wikicode, slice]]:
        """Search for an element that looks like *obj* within the node list.

        This follows the same rules as :meth:`_do_strong_search` with some
        differences. *obj* is treated as a string that might represent any
        :class:`.Node`, :class:`.Wikicode`, or combination of the two present
        in the node list. Thus, matching is weak (using string comparisons)
        rather than strong (using ``is``). Because multiple nodes can match
        *obj*, the result is a list of tuples instead of just one (however,
        :exc:`ValueError` is still raised if nothing is found). Individual
        matches will never overlap.

        The tuples contain a new first element, *exact*, which is ``True`` if
        we were able to match *obj* exactly to one or more adjacent nodes, or
        ``False`` if we found *obj* inside a node or incompletely spanning
        multiple nodes.
        """
        obj = parse_anything(obj)
        if not obj or obj not in self:
            raise ValueError(obj)
        results = []
        contexts: list[Wikicode] = [self]
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

    def _get_tree(
        self, code: Wikicode, lines: list[str], marker: Any, indent: int
    ) -> list[str]:
        """Build a tree to illustrate the way the Wikicode object was parsed.

        The method that builds the actual tree is ``__showtree__`` of ``Node``
        objects. *code* is the ``Wikicode`` object to build a tree for. *lines*
        is the list to append the tree to, which is returned at the end of the
        method. *marker* is some object to be used to indicate that the builder
        should continue on from the last line instead of starting a new one; it
        should be any object that can be tested for with ``is``. *indent* is
        the starting indentation.
        """

        def write(*args: str) -> None:
            """Write a new line following the proper indentation rules."""
            if lines and lines[-1] is marker:  # Continue from the last line
                lines.pop()  # Remove the marker
                last = lines.pop()
                lines.append(last + " ".join(args))
            else:
                lines.append(" " * 6 * indent + " ".join(args))

        def get(code: Wikicode):
            self._get_tree(code, lines, marker, indent + 1)

        def mark():
            return lines.append(marker)

        for node in code.nodes:
            node.__showtree__(write, get, mark)
        return lines

    @property
    def nodes(self) -> list[Node]:
        """A list of :class:`.Node` objects.

        This is the internal data actually stored within a :class:`.Wikicode`
        object.
        """
        return self._nodes

    @nodes.setter
    def nodes(self, value: list[Node] | Any) -> None:
        if not isinstance(value, list):
            value = parse_anything(value).nodes
        self._nodes = value

    @overload
    def get(self, index: int) -> Node: ...

    @overload
    def get(self, index: slice) -> list[Node]: ...

    def get(self, index):
        """Return the *index*\\ th node within the list of nodes."""
        return self.nodes[index]

    def set(self, index: int, value: Any) -> None:
        """Set the ``Node`` at *index* to *value*.

        Raises :exc:`IndexError` if *index* is out of range, or
        :exc:`ValueError` if *value* cannot be coerced into one :class:`.Node`.
        To insert multiple nodes at an index, use :meth:`get` with either
        :meth:`remove` and :meth:`insert` or :meth:`replace`.
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

    def contains(self, obj: Node | Wikicode | str) -> bool:
        """Return whether this Wikicode object contains *obj*.

        If *obj* is a :class:`.Node` or :class:`.Wikicode` object, then we
        search for it exactly among all of our children, recursively.
        Otherwise, this method just uses :meth:`.__contains__` on the string.
        """
        if not isinstance(obj, (Node, Wikicode)):
            return obj in self
        try:
            self._do_strong_search(obj, recursive=True)
        except ValueError:
            return False
        return True

    def index(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, obj: Node | Wikicode | str, recursive: bool = False
    ) -> int:
        """Return the index of *obj* in the list of nodes.

        Raises :exc:`ValueError` if *obj* is not found. If *recursive* is
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

    def get_ancestors(self, obj: Node | Wikicode) -> list[Node]:
        """Return a list of all ancestor nodes of the :class:`.Node` *obj*.

        The list is ordered from the most shallow ancestor (greatest great-
        grandparent) to the direct parent. The node itself is not included in
        the list. For example::

            >>> text = "{{a|{{b|{{c|{{d}}}}}}}}"
            >>> code = mwparserfromhell.parse(text)
            >>> node = code.filter_templates(matches=lambda n: n == "{{d}}")[0]
            >>> code.get_ancestors(node)
            ['{{a|{{b|{{c|{{d}}}}}}}}', '{{b|{{c|{{d}}}}}}', '{{c|{{d}}}}']

        Will return an empty list if *obj* is at the top level of this Wikicode
        object. Will raise :exc:`ValueError` if it wasn't found.
        """

        def _get_ancestors(code: Wikicode, needle: Node) -> list[Node] | None:
            for node in code.nodes:
                if node is needle:
                    return []
                for code in node.__children__():
                    ancestors = _get_ancestors(code, needle)
                    if ancestors is not None:
                        return [node] + ancestors
            return None

        if isinstance(obj, Wikicode):
            obj = obj.get(0)
        elif not isinstance(obj, Node):
            raise ValueError(obj)

        ancestors = _get_ancestors(self, obj)
        if ancestors is None:
            raise ValueError(obj)
        return ancestors

    def get_parent(self, obj: Node | Wikicode) -> Node | None:
        """Return the direct parent node of the :class:`.Node` *obj*.

        This function is equivalent to calling :meth:`.get_ancestors` and
        taking the last element of the resulting list. Will return None if
        the node exists but does not have a parent; i.e., it is at the top
        level of the Wikicode object.
        """
        ancestors = self.get_ancestors(obj)
        return ancestors[-1] if ancestors else None

    def insert(self, index: int, value: Any) -> None:
        """Insert *value* at *index* in the list of nodes.

        *value* can be anything parsable by :func:`.parse_anything`, which
        includes strings or other :class:`.Wikicode` or :class:`.Node` objects.
        """
        nodes = parse_anything(value).nodes
        for node in reversed(nodes):
            self.nodes.insert(index, node)

    def insert_before(
        self, obj: Node | Wikicode | str, value: Any, recursive: bool = True
    ) -> None:
        """Insert *value* immediately before *obj*.

        *obj* can be either a string, a :class:`.Node`, or another
        :class:`.Wikicode` object (as created by :meth:`get_sections`, for
        example). If *obj* is a string, we will operate on all instances of
        that string within the code, otherwise only on the specific instance
        given. *value* can be anything parsable by :func:`.parse_anything`. If
        *recursive* is ``True``, we will try to find *obj* within our child
        nodes even if it is not a direct descendant of this :class:`.Wikicode`
        object. If *obj* is not found, :exc:`ValueError` is raised.
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

    def insert_after(
        self, obj: Node | Wikicode | str, value: Any, recursive: bool = True
    ) -> None:
        """Insert *value* immediately after *obj*.

        *obj* can be either a string, a :class:`.Node`, or another
        :class:`.Wikicode` object (as created by :meth:`get_sections`, for
        example). If *obj* is a string, we will operate on all instances of
        that string within the code, otherwise only on the specific instance
        given. *value* can be anything parsable by :func:`.parse_anything`. If
        *recursive* is ``True``, we will try to find *obj* within our child
        nodes even if it is not a direct descendant of this :class:`.Wikicode`
        object. If *obj* is not found, :exc:`ValueError` is raised.
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

    def replace(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, obj: Node | Wikicode | str, value: Any, recursive: bool = True
    ) -> None:
        """Replace *obj* with *value*.

        *obj* can be either a string, a :class:`.Node`, or another
        :class:`.Wikicode` object (as created by :meth:`get_sections`, for
        example). If *obj* is a string, we will operate on all instances of
        that string within the code, otherwise only on the specific instance
        given. *value* can be anything parsable by :func:`.parse_anything`.
        If *recursive* is ``True``, we will try to find *obj* within our child
        nodes even if it is not a direct descendant of this :class:`.Wikicode`
        object. If *obj* is not found, :exc:`ValueError` is raised.
        """
        if isinstance(obj, (Node, Wikicode)):
            context, index = self._do_strong_search(obj, recursive)
            for _ in range(index.start, index.stop):
                context.nodes.pop(index.start)
            context.insert(index.start, value)
        else:
            for exact, context, index in self._do_weak_search(obj, recursive):
                if exact:
                    for _ in range(index.start, index.stop):
                        context.nodes.pop(index.start)
                    context.insert(index.start, value)
                else:
                    self._slice_replace(context, index, str(obj), str(value))

    def append(self, value: Any) -> None:
        """Insert *value* at the end of the list of nodes.

        *value* can be anything parsable by :func:`.parse_anything`.
        """
        nodes = parse_anything(value).nodes
        for node in nodes:
            self.nodes.append(node)

    def remove(self, obj: Node | Wikicode | str, recursive: bool = True) -> None:
        """Remove *obj* from the list of nodes.

        *obj* can be either a string, a :class:`.Node`, or another
        :class:`.Wikicode` object (as created by :meth:`get_sections`, for
        example). If *obj* is a string, we will operate on all instances of
        that string within the code, otherwise only on the specific instance
        given. If *recursive* is ``True``, we will try to find *obj* within our
        child nodes even if it is not a direct descendant of this
        :class:`.Wikicode` object. If *obj* is not found, :exc:`ValueError` is
        raised.
        """
        if isinstance(obj, (Node, Wikicode)):
            context, index = self._do_strong_search(obj, recursive)
            for _ in range(index.start, index.stop):
                context.nodes.pop(index.start)
        else:
            for exact, context, index in self._do_weak_search(obj, recursive):
                if exact:
                    for _ in range(index.start, index.stop):
                        context.nodes.pop(index.start)
                else:
                    self._slice_replace(context, index, str(obj), "")

    def matches(
        self,
        other: Node | Wikicode | str | bytes | Iterable[Node | Wikicode | str | bytes],
    ) -> bool:
        """Do a loose equivalency test suitable for comparing page names.

        *other* can be any string-like object, including :class:`.Wikicode`, or
        an iterable of these. This operation is symmetric; both sides are
        adjusted. Specifically, whitespace and markup is stripped and the first
        letter's case is normalized. Typical usage is
        ``if template.name.matches("stub"): ...``.
        """

        def normalize(s: str) -> str:
            return (s[0].upper() + s[1:]).replace("_", " ") if s else s

        this = normalize(self.strip_code().strip())

        if isinstance(other, (str, bytes, Wikicode, Node)):
            that = parse_anything(other).strip_code().strip()
            return this == normalize(that)

        for obj in other:
            that = parse_anything(obj).strip_code().strip()
            if this == normalize(that):
                return True
        return False

    @overload
    def ifilter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Node], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        forcetype: None = None,
    ) -> Generator[Node]: ...

    @overload
    def ifilter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[N], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        *,
        forcetype: type[N],
    ) -> Generator[N]: ...

    def ifilter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[N], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        forcetype: type[N] | None = None,
    ) -> Generator[N]:
        """Iterate over nodes in our list matching certain conditions.

        If *forcetype* is given, only nodes that are instances of this type (or
        tuple of types) are yielded. Setting *recursive* to ``True`` will
        iterate over all children and their descendants. ``RECURSE_OTHERS``
        will only iterate over children that are not the instances of
        *forcetype*. ``False`` will only iterate over immediate children.

        ``RECURSE_OTHERS`` can be used to iterate over all un-nested templates,
        even if they are inside of HTML tags, like so:

            >>> code = mwparserfromhell.parse("{{foo}}<b>{{foo|{{bar}}}}</b>")
            >>> code.filter_templates(code.RECURSE_OTHERS)
            ["{{foo}}", "{{foo|{{bar}}}}"]

        *matches* can be used to further restrict the nodes, either as a
        function (taking a single :class:`.Node` and returning a boolean) or a
        regular expression (matched against the node's string representation
        with :func:`re.search`). If *matches* is a regex, the flags passed to
        :func:`re.search` are :const:`re.IGNORECASE`, :const:`re.DOTALL`, and
        :const:`re.UNICODE`, but custom flags can be specified by passing
        *flags*.
        """
        gen = self._indexed_ifilter(recursive, matches, flags, forcetype)
        return (node for i, node in gen)

    def ifilter_arguments(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Argument], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Argument]:
        """Iterate over arguments.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~argument.Argument`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Argument
        )

    def ifilter_comments(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Comment], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Comment]:
        """Iterate over comments.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~comment.Comment`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Comment
        )

    def ifilter_external_links(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[ExternalLink], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[ExternalLink]:
        """Iterate over external links.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~external_link.ExternalLink`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=ExternalLink
        )

    def ifilter_headings(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Heading], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Heading]:
        """Iterate over headings.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~heading.Heading`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Heading
        )

    def ifilter_html_entities(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[HTMLEntity], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[HTMLEntity]:
        """Iterate over HTML entities.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~html_entity.HTMLEntity`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=HTMLEntity
        )

    def ifilter_tags(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Tag], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Tag]:
        """Iterate over tags.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~tag.Tag`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Tag
        )

    def ifilter_templates(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Template], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Template]:
        """Iterate over templates.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~template.Template`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Template
        )

    def ifilter_text(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Text], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Text]:
        """Iterate over text.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~text.Text`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Text
        )

    def ifilter_wikilinks(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Wikilink], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> Generator[Wikilink]:
        """Iterate over wikilinks.

        This is equivalent to :meth:`ifilter` with *forcetype* set to
        :class:`~wikilink.Wikilink`.
        """
        return self.ifilter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Wikilink
        )

    @overload
    def filter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Node], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        forcetype: None = None,
    ) -> list[Node]: ...

    @overload
    def filter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[N], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        *,
        forcetype: type[N],
    ) -> list[N]: ...

    def filter(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[N], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        forcetype: type[N] | None = None,
    ) -> list[N]:
        """Return a list of nodes within our list matching certain conditions.

        This is equivalent to calling :func:`list` on :meth:`ifilter`.
        """
        gen = self.ifilter(  # pyright: ignore[reportCallIssue]
            recursive=recursive,
            matches=matches,
            flags=flags,
            forcetype=forcetype,  # pyright: ignore[reportArgumentType]
        )
        return list(gen)

    def filter_arguments(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Argument], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Argument]:
        """Iterate over arguments.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~argument.Argument`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Argument
        )

    def filter_comments(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Comment], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Comment]:
        """Iterate over comments.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~comment.Comment`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Comment
        )

    def filter_external_links(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[ExternalLink], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[ExternalLink]:
        """Iterate over external links.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~external_link.ExternalLink`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=ExternalLink
        )

    def filter_headings(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Heading], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Heading]:
        """Iterate over headings.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~heading.Heading`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Heading
        )

    def filter_html_entities(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[HTMLEntity], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[HTMLEntity]:
        """Iterate over HTML entities.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~html_entity.HTMLEntity`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=HTMLEntity
        )

    def filter_tags(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Tag], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Tag]:
        """Iterate over tags.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~tag.Tag`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Tag
        )

    def filter_templates(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Template], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Template]:
        """Iterate over templates.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~template.Template`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Template
        )

    def filter_text(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Text], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Text]:
        """Iterate over text.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~text.Text`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Text
        )

    def filter_wikilinks(
        self,
        recursive: bool | Literal[Recurse.RECURSE_OTHERS] = True,
        matches: Callable[[Wikilink], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
    ) -> list[Wikilink]:
        """Iterate over wikilinks.

        This is equivalent to :meth:`filter` with *forcetype* set to
        :class:`~wikilink.Wikilink`.
        """
        return self.filter(
            recursive=recursive, matches=matches, flags=flags, forcetype=Wikilink
        )

    def get_sections(
        self,
        levels: Iterable[int] | None = None,
        matches: Callable[[Node], bool] | re.Pattern | str | None = None,
        flags: int = FLAGS,
        flat: bool = False,
        include_lead: bool | None = None,
        include_headings: bool = True,
    ) -> list[Wikicode]:
        """Return a list of sections within the page.

        Sections are returned as :class:`.Wikicode` objects with a shared node
        list (implemented using :class:`.SmartList`) so that changes to
        sections are reflected in the parent Wikicode object.

        Each section contains all of its subsections, unless *flat* is
        ``True``. If *levels* is given, it should be a iterable of integers;
        only sections whose heading levels are within it will be returned. If
        *matches* is given, it should be either a function or a regex; only
        sections whose headings match it (without the surrounding equal signs)
        will be included. *flags* can be used to override the default regex
        flags (see :meth:`ifilter`) if a regex *matches* is used.

        If *include_lead* is ``True``, the first, lead section (without a
        heading) will be included in the list; ``False`` will not include it;
        the default will include it only if no specific *levels* were given. If
        *include_headings* is ``True``, the section's beginning
        :class:`.Heading` object will be included; otherwise, this is skipped.
        """
        title_matcher = self._build_matcher(matches, flags)

        def matcher(heading):
            return title_matcher(heading.title) and (
                not levels or heading.level in levels
            )

        iheadings = self._indexed_ifilter(recursive=False, forcetype=Heading)
        sections = []  # Tuples of (index_of_first_node, section)
        # Tuples of (index, heading), where index and heading.level are both
        # monotonically increasing
        open_headings: list[tuple[int, Heading]] = []

        # Add the lead section if appropriate:
        if include_lead or not (include_lead is not None or matches or levels):
            itr = self._indexed_ifilter(recursive=False, forcetype=Heading)
            try:
                first = next(itr)[0]
                sections.append((0, Wikicode(self.nodes[:first])))
            except StopIteration:  # No headings in page
                sections.append((0, Wikicode(self.nodes[:])))

        # Iterate over headings, adding sections to the list as they end:
        for i, heading in iheadings:
            if flat:  # With flat, all sections close at the next heading
                newly_closed, open_headings = open_headings, []
            else:  # Otherwise, figure out which sections have closed, if any
                closed_start_index = len(open_headings)
                for j, (start, last_heading) in enumerate(open_headings):
                    if heading.level <= last_heading.level:
                        closed_start_index = j
                        break
                newly_closed = open_headings[closed_start_index:]
                del open_headings[closed_start_index:]
            for start, closed_heading in newly_closed:
                if matcher(closed_heading):
                    sections.append((start, Wikicode(self.nodes[start:i])))
            start = i if include_headings else (i + 1)
            open_headings.append((start, heading))

        # Add any remaining open headings to the list of sections:
        for start, heading in open_headings:
            if matcher(heading):
                sections.append((start, Wikicode(self.nodes[start:])))

        # Ensure that earlier sections are earlier in the returned list:
        return [section for i, section in sorted(sections)]

    def strip_code(
        self,
        normalize: bool = True,
        collapse: bool = True,
        keep_template_params: bool = False,
    ) -> str:
        """Return a rendered string without unprintable code such as templates.

        The way a node is stripped is handled by the
        :meth:`~.Node.__strip__` method of :class:`.Node` objects, which
        generally return a subset of their nodes or ``None``. For example,
        templates and tags are removed completely, links are stripped to just
        their display part, headings are stripped to just their title.

        If *normalize* is ``True``, various things may be done to strip code
        further, such as converting HTML entities like ``&Sigma;``, ``&#931;``,
        and ``&#x3a3;`` to ``Σ``. If *collapse* is ``True``, we will try to
        remove excess whitespace as well (three or more newlines are converted
        to two, for example). If *keep_template_params* is ``True``, then
        template parameters will be preserved in the output (normally, they are
        removed completely).
        """
        kwargs = {
            "normalize": normalize,
            "collapse": collapse,
            "keep_template_params": keep_template_params,
        }

        nodes = []
        for node in self.nodes:
            stripped = node.__strip__(**kwargs)
            if stripped:
                nodes.append(str(stripped))

        if collapse:
            stripped = "".join(nodes).strip("\n")
            while "\n\n\n" in stripped:
                stripped = stripped.replace("\n\n\n", "\n\n")
            return stripped
        return "".join(nodes)

    def get_tree(self) -> str:
        """Return a hierarchical tree representation of the object.

        The representation is a string makes the most sense printed. It is
        built by calling :meth:`_get_tree` on the :class:`.Wikicode` object and
        its children recursively. The end result may look something like the
        following::

            >>> text = "Lorem ipsum {{foo|bar|{{baz}}|spam=eggs}}"
            >>> print(mwparserfromhell.parse(text).get_tree())
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

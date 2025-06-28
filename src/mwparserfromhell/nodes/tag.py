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

from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Callable

from ..definitions import is_visible
from ..utils import parse_anything
from ._base import Node
from .extras import Attribute

if TYPE_CHECKING:
    from ..wikicode import Wikicode

__all__ = ["Tag"]


class Tag(Node):
    """Represents an HTML-style tag in wikicode, like ``<ref>``."""

    def __init__(
        self,
        tag: Any,
        contents: Any = None,
        attrs: list[Attribute] | None = None,
        wiki_markup: str | None = None,
        self_closing: bool = False,
        invalid: bool = False,
        implicit: bool = False,
        padding: str = "",
        closing_tag: Wikicode | None = None,
        wiki_style_separator: str | None = None,
        closing_wiki_markup: str | None = None,
    ):
        super().__init__()
        self._attrs: list[Attribute]
        self._closing_wiki_markup: str | None

        self.tag = tag
        self.contents = contents
        self._attrs = attrs if attrs else []
        self._closing_wiki_markup = None
        self.wiki_markup = wiki_markup
        self.self_closing = self_closing
        self.invalid = invalid
        self.implicit = implicit
        self.padding = padding
        if closing_tag is not None:
            self.closing_tag = closing_tag
        self.wiki_style_separator = wiki_style_separator
        if closing_wiki_markup is not None:
            self.closing_wiki_markup = closing_wiki_markup

    def __str__(self) -> str:
        if self.wiki_markup:
            if self.attributes:
                attrs = "".join([str(attr) for attr in self.attributes])
            else:
                attrs = ""
            padding = self.padding or ""
            separator = self.wiki_style_separator or ""
            if self.self_closing:
                return self.wiki_markup + attrs + padding + separator
            close = self.closing_wiki_markup or ""
            return (
                self.wiki_markup
                + attrs
                + padding
                + separator
                + str(self.contents)
                + close
            )

        result = ("</" if self.invalid else "<") + str(self.tag)
        if self.attributes:
            result += "".join([str(attr) for attr in self.attributes])
        if self.self_closing:
            result += self.padding + (">" if self.implicit else "/>")
        else:
            result += self.padding + ">" + str(self.contents)
            result += "</" + str(self.closing_tag) + ">"
        return result

    def __children__(self) -> Generator[Wikicode, None, None]:
        if not self.wiki_markup:
            yield self.tag
        for attr in self.attributes:
            yield attr.name
            if attr.value is not None:
                yield attr.value
        if not self.self_closing:
            yield self.contents
            if not self.wiki_markup and self.closing_tag:
                yield self.closing_tag

    def __strip__(self, **kwargs: Any) -> str | None:
        if self.contents and is_visible(str(self.tag)):
            return self.contents.strip_code(**kwargs)
        return None

    def __showtree__(
        self,
        write: Callable[[str], None],
        get: Callable[[Wikicode], None],
        mark: Callable[[], None],
    ) -> None:
        write("</" if self.invalid else "<")
        get(self.tag)
        for attr in self.attributes:
            get(attr.name)
            if not attr.value:
                continue
            write("    = ")
            mark()
            get(attr.value)
        if self.self_closing:
            write(">" if self.implicit else "/>")
        else:
            write(">")
            get(self.contents)
            write("</")
            get(self.closing_tag)
            write(">")

    @property
    def tag(self) -> Wikicode:
        """The tag itself, as a :class:`.Wikicode` object."""
        return self._tag

    @tag.setter
    def tag(self, value: Any) -> None:
        self._tag = self._closing_tag = parse_anything(value)

    @property
    def contents(self) -> Wikicode:
        """The contents of the tag, as a :class:`.Wikicode` object."""
        return self._contents

    @contents.setter
    def contents(self, value: Any) -> None:
        self._contents = parse_anything(value)

    @property
    def attributes(self) -> list[Attribute]:
        """The list of attributes affecting the tag.

        Each attribute is an instance of :class:`.Attribute`.
        """
        return self._attrs

    @property
    def wiki_markup(self) -> str | None:
        """The wikified version of a tag to show instead of HTML.

        If set to a value, this will be displayed instead of the brackets.
        For example, set to ``''`` to replace ``<i>`` or ``----`` to replace
        ``<hr>``.
        """
        return self._wiki_markup

    @wiki_markup.setter
    def wiki_markup(self, value: str | None) -> None:
        self._wiki_markup = str(value) if value else None
        if not value or not self.closing_wiki_markup:
            self._closing_wiki_markup = self._wiki_markup

    @property
    def self_closing(self) -> bool:
        """Whether the tag is self-closing with no content (like ``<br/>``)."""
        return self._self_closing

    @self_closing.setter
    def self_closing(self, value: bool) -> None:
        self._self_closing = bool(value)

    @property
    def invalid(self) -> bool:
        """Whether the tag starts with a backslash after the opening bracket.

        This makes the tag look like a lone close tag. It is technically
        invalid and is only parsable Wikicode when the tag itself is
        single-only, like ``<br>`` and ``<img>``. See
        :func:`.definitions.is_single_only`.
        """
        return self._invalid

    @invalid.setter
    def invalid(self, value: bool) -> None:
        self._invalid = bool(value)

    @property
    def implicit(self) -> bool:
        """Whether the tag is implicitly self-closing, with no ending slash.

        This is only possible for specific "single" tags like ``<br>`` and
        ``<li>``. See :func:`.definitions.is_single`. This field only has an
        effect if :attr:`self_closing` is also ``True``.
        """
        return self._implicit

    @implicit.setter
    def implicit(self, value: bool) -> None:
        self._implicit = bool(value)

    @property
    def padding(self) -> str:
        """Spacing to insert before the first closing ``>``."""
        return self._padding

    @padding.setter
    def padding(self, value: str | None) -> None:
        if not value:
            self._padding = ""
        else:
            value = str(value)
            if not value.isspace():
                raise ValueError("padding must be entirely whitespace")
            self._padding = value

    @property
    def closing_tag(self) -> Wikicode:
        """The closing tag, as a :class:`.Wikicode` object.

        This will usually equal :attr:`tag`, unless there is additional
        spacing, comments, or the like.
        """
        return self._closing_tag

    @closing_tag.setter
    def closing_tag(self, value: Any) -> None:
        self._closing_tag = parse_anything(value)

    @property
    def wiki_style_separator(self) -> str | None:
        """The separator between the padding and content in a wiki markup tag.

        Essentially the wiki equivalent of the TagCloseOpen.
        """
        return self._wiki_style_separator

    @wiki_style_separator.setter
    def wiki_style_separator(self, value: str | None) -> None:
        self._wiki_style_separator = str(value) if value else None

    @property
    def closing_wiki_markup(self) -> str | None:
        """The wikified version of the closing tag to show instead of HTML.

        If set to a value, this will be displayed instead of the close tag
        brackets. If the tag is :attr:`self_closing`, this is not displayed.
        If :attr:`wiki_markup` is set and this has not been set, this is set
        to the value of :attr:`wiki_markup`. If this has been set and
        :attr:`wiki_markup` is set to a ``False`` value, this is set to
        ``None``.
        """
        return self._closing_wiki_markup

    @closing_wiki_markup.setter
    def closing_wiki_markup(self, value: str | None) -> None:
        self._closing_wiki_markup = str(value) if value else None

    def has(self, name: str | Attribute | Wikicode) -> bool:
        """Return whether any attribute in the tag has the given *name*.

        Note that a tag may have multiple attributes with the same name, but
        only the last one is read by the MediaWiki parser.
        """
        for attr in self.attributes:
            if attr.name == name.strip():
                return True
        return False

    def get(self, name: str | Attribute | Wikicode) -> Attribute:
        """Get the attribute with the given *name*.

        The returned object is a :class:`.Attribute` instance. Raises
        :exc:`ValueError` if no attribute has this name. Since multiple
        attributes can have the same name, we'll return the last match, since
        all but the last are ignored by the MediaWiki parser.
        """
        for attr in reversed(self.attributes):
            if attr.name == name.strip():
                return attr
        raise ValueError(name)

    def add(
        self,
        name: Any,
        value: Any = None,
        quotes: str | None = '"',
        pad_first: str = " ",
        pad_before_eq: str = "",
        pad_after_eq: str = "",
    ) -> Attribute:
        """Add an attribute with the given *name* and *value*.

        *name* and *value* can be anything parsable by
        :func:`.utils.parse_anything`; *value* can be omitted if the attribute
        is valueless. If *quotes* is not ``None``, it should be a string
        (either ``"`` or ``'``) that *value* will be wrapped in (this is
        recommended). ``None`` is only legal if *value* contains no spacing.

        *pad_first*, *pad_before_eq*, and *pad_after_eq* are whitespace used as
        padding before the name, before the equal sign (or after the name if no
        value), and after the equal sign (ignored if no value), respectively.
        """
        if value is not None:
            value = parse_anything(value)
        quotes = Attribute.coerce_quotes(quotes)
        attr = Attribute(parse_anything(name), value, quotes)
        attr.pad_first = pad_first
        attr.pad_before_eq = pad_before_eq
        attr.pad_after_eq = pad_after_eq
        self.attributes.append(attr)
        return attr

    def remove(self, name: str) -> None:
        """Remove all attributes with the given *name*.

        Raises :exc:`ValueError` if none were found.
        """
        attrs = [attr for attr in self.attributes if attr.name == name.strip()]
        if not attrs:
            raise ValueError(name)
        for attr in attrs:
            self.attributes.remove(attr)

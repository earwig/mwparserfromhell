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
from math import log
import re
import string

from . import contexts
from . import tokens
from ..compat import htmlentities

__all__ = ["Tokenizer"]

class BadRoute(Exception):
    """Raised internally when the current tokenization route is invalid."""
    pass


class Tokenizer(object):
    """Creates a list of tokens from a string of wikicode."""
    START = object()
    END = object()
    MARKERS = ["{", "}", "[", "]", "<", ">", "|", "=", "&", "#", "*", ";", ":",
               "/", "-", "!", "\n", END]
    regex = re.compile(r"([{}\[\]<>|=&#*;:/\-!\n])", flags=re.IGNORECASE)

    def __init__(self):
        self._text = None
        self._head = 0
        self._stacks = []
        self._global = 0

    @property
    def _stack(self):
        """The current token stack."""
        return self._stacks[-1][0]

    @property
    def _context(self):
        """The current token context."""
        return self._stacks[-1][1]

    @_context.setter
    def _context(self, value):
        self._stacks[-1][1] = value

    @property
    def _textbuffer(self):
        """The current textbuffer."""
        return self._stacks[-1][2]

    @_textbuffer.setter
    def _textbuffer(self, value):
        self._stacks[-1][2] = value

    def _push(self, context=0):
        """Add a new token stack, context, and textbuffer to the list."""
        self._stacks.append([[], context, []])

    def _push_textbuffer(self):
        """Push the textbuffer onto the stack as a Text node and clear it."""
        if self._textbuffer:
            self._stack.append(tokens.Text(text="".join(self._textbuffer)))
            self._textbuffer = []

    def _pop(self, keep_context=False):
        """Pop the current stack/context/textbuffer, returing the stack.

        If *keep_context is ``True``, then we will replace the underlying
        stack's context with the current stack's.
        """
        self._push_textbuffer()
        if keep_context:
            context = self._context
            stack = self._stacks.pop()[0]
            self._context = context
            return stack
        return self._stacks.pop()[0]

    def _fail_route(self):
        """Fail the current tokenization route.

        Discards the current stack/context/textbuffer and raises
        :py:exc:`~.BadRoute`.
        """
        self._pop()
        raise BadRoute()

    def _write(self, token):
        """Write a token to the end of the current token stack."""
        self._push_textbuffer()
        self._stack.append(token)

    def _write_first(self, token):
        """Write a token to the beginning of the current token stack."""
        self._push_textbuffer()
        self._stack.insert(0, token)

    def _write_text(self, text):
        """Write text to the current textbuffer."""
        self._textbuffer.append(text)

    def _write_all(self, tokenlist):
        """Write a series of tokens to the current stack at once."""
        if tokenlist and isinstance(tokenlist[0], tokens.Text):
            self._write_text(tokenlist.pop(0).text)
        self._push_textbuffer()
        self._stack.extend(tokenlist)

    def _write_text_then_stack(self, text):
        """Pop the current stack, write *text*, and then write the stack."""
        stack = self._pop()
        self._write_text(text)
        if stack:
            self._write_all(stack)
        self._head -= 1

    def _read(self, delta=0, wrap=False, strict=False):
        """Read the value at a relative point in the wikicode.

        The value is read from :py:attr:`self._head <_head>` plus the value of
        *delta* (which can be negative). If *wrap* is ``False``, we will not
        allow attempts to read from the end of the string if ``self._head +
        delta`` is negative. If *strict* is ``True``, the route will be failed
        (with :py:meth:`_fail_route`) if we try to read from past the end of
        the string; otherwise, :py:attr:`self.END <END>` is returned. If we try
        to read from before the start of the string, :py:attr:`self.START
        <START>` is returned.
        """
        index = self._head + delta
        if index < 0 and (not wrap or abs(index) > len(self._text)):
            return self.START
        try:
            return self._text[index]
        except IndexError:
            if strict:
                self._fail_route()
            return self.END

    def _parse_template_or_argument(self):
        """Parse a template or argument at the head of the wikicode string."""
        self._head += 2
        braces = 2
        while self._read() == "{":
            braces += 1
            self._head += 1
        self._push()

        while braces:
            if braces == 1:
                return self._write_text_then_stack("{")
            if braces == 2:
                try:
                    self._parse_template()
                except BadRoute:
                    return self._write_text_then_stack("{{")
                break
            try:
                self._parse_argument()
                braces -= 3
            except BadRoute:
                try:
                    self._parse_template()
                    braces -= 2
                except BadRoute:
                    return self._write_text_then_stack("{" * braces)
            if braces:
                self._head += 1

        self._write_all(self._pop())

    def _parse_template(self):
        """Parse a template at the head of the wikicode string."""
        reset = self._head
        try:
            template = self._parse(contexts.TEMPLATE_NAME)
        except BadRoute:
            self._head = reset
            raise
        else:
            self._write_first(tokens.TemplateOpen())
            self._write_all(template)
            self._write(tokens.TemplateClose())

    def _parse_argument(self):
        """Parse an argument at the head of the wikicode string."""
        reset = self._head
        try:
            argument = self._parse(contexts.ARGUMENT_NAME)
        except BadRoute:
            self._head = reset
            raise
        else:
            self._write_first(tokens.ArgumentOpen())
            self._write_all(argument)
            self._write(tokens.ArgumentClose())

    def _verify_safe(self, unsafes):
        """Verify that there are no unsafe characters in the current stack.

        The route will be failed if the name contains any element of *unsafes*
        in it (not merely at the beginning or end). This is used when parsing a
        template name or parameter key, which cannot contain newlines.
        """
        self._push_textbuffer()
        if self._stack:
            text = [tok for tok in self._stack if isinstance(tok, tokens.Text)]
            text = "".join([token.text for token in text]).strip()
            if text and any([unsafe in text for unsafe in unsafes]):
                self._fail_route()

    def _handle_template_param(self):
        """Handle a template parameter at the head of the string."""
        if self._context & contexts.TEMPLATE_NAME:
            self._verify_safe(["\n", "{", "}", "[", "]"])
            self._context ^= contexts.TEMPLATE_NAME
        elif self._context & contexts.TEMPLATE_PARAM_VALUE:
            self._context ^= contexts.TEMPLATE_PARAM_VALUE
        elif self._context & contexts.TEMPLATE_PARAM_KEY:
            self._write_all(self._pop(keep_context=True))
        self._context |= contexts.TEMPLATE_PARAM_KEY
        self._write(tokens.TemplateParamSeparator())
        self._push(self._context)

    def _handle_template_param_value(self):
        """Handle a template parameter's value at the head of the string."""
        try:
            self._verify_safe(["\n", "{{", "}}"])
        except BadRoute:
            self._pop()
            raise
        else:
            self._write_all(self._pop(keep_context=True))
        self._context ^= contexts.TEMPLATE_PARAM_KEY
        self._context |= contexts.TEMPLATE_PARAM_VALUE
        self._write(tokens.TemplateParamEquals())

    def _handle_template_end(self):
        """Handle the end of a template at the head of the string."""
        if self._context & contexts.TEMPLATE_NAME:
            self._verify_safe(["\n", "{", "}", "[", "]"])
        elif self._context & contexts.TEMPLATE_PARAM_KEY:
            self._write_all(self._pop(keep_context=True))
        self._head += 1
        return self._pop()

    def _handle_argument_separator(self):
        """Handle the separator between an argument's name and default."""
        self._verify_safe(["\n", "{{", "}}"])
        self._context ^= contexts.ARGUMENT_NAME
        self._context |= contexts.ARGUMENT_DEFAULT
        self._write(tokens.ArgumentSeparator())

    def _handle_argument_end(self):
        """Handle the end of an argument at the head of the string."""
        if self._context & contexts.ARGUMENT_NAME:
            self._verify_safe(["\n", "{{", "}}"])
        self._head += 2
        return self._pop()

    def _parse_wikilink(self):
        """Parse an internal wikilink at the head of the wikicode string."""
        self._head += 2
        reset = self._head - 1
        try:
            wikilink = self._parse(contexts.WIKILINK_TITLE)
        except BadRoute:
            self._head = reset
            self._write_text("[[")
        else:
            self._write(tokens.WikilinkOpen())
            self._write_all(wikilink)
            self._write(tokens.WikilinkClose())

    def _handle_wikilink_separator(self):
        """Handle the separator between a wikilink's title and its text."""
        self._verify_safe(["\n", "{", "}", "[", "]"])
        self._context ^= contexts.WIKILINK_TITLE
        self._context |= contexts.WIKILINK_TEXT
        self._write(tokens.WikilinkSeparator())

    def _handle_wikilink_end(self):
        """Handle the end of a wikilink at the head of the string."""
        if self._context & contexts.WIKILINK_TITLE:
            self._verify_safe(["\n", "{", "}", "[", "]"])
        self._head += 1
        return self._pop()

    def _parse_heading(self):
        """Parse a section heading at the head of the wikicode string."""
        self._global |= contexts.GL_HEADING
        reset = self._head
        self._head += 1
        best = 1
        while self._read() == "=":
            best += 1
            self._head += 1
        context = contexts.HEADING_LEVEL_1 << min(best - 1, 5)

        try:
            title, level = self._parse(context)
        except BadRoute:
            self._head = reset + best - 1
            self._write_text("=" * best)
        else:
            self._write(tokens.HeadingStart(level=level))
            if level < best:
                self._write_text("=" * (best - level))
            self._write_all(title)
            self._write(tokens.HeadingEnd())
        finally:
            self._global ^= contexts.GL_HEADING

    def _handle_heading_end(self):
        """Handle the end of a section heading at the head of the string."""
        reset = self._head
        self._head += 1
        best = 1
        while self._read() == "=":
            best += 1
            self._head += 1
        current = int(log(self._context / contexts.HEADING_LEVEL_1, 2)) + 1
        level = min(current, min(best, 6))

        try:
            after, after_level = self._parse(self._context)
        except BadRoute:
            if level < best:
                self._write_text("=" * (best - level))
            self._head = reset + best - 1
            return self._pop(), level
        else:
            self._write_text("=" * best)
            self._write_all(after)
            return self._pop(), after_level

    def _really_parse_entity(self):
        """Actually parse an HTML entity and ensure that it is valid."""
        self._write(tokens.HTMLEntityStart())
        self._head += 1

        this = self._read(strict=True)
        if this == "#":
            numeric = True
            self._write(tokens.HTMLEntityNumeric())
            self._head += 1
            this = self._read(strict=True)
            if this[0].lower() == "x":
                hexadecimal = True
                self._write(tokens.HTMLEntityHex(char=this[0]))
                this = this[1:]
                if not this:
                    self._fail_route()
            else:
                hexadecimal = False
        else:
            numeric = hexadecimal = False

        valid = string.hexdigits if hexadecimal else string.digits
        if not numeric and not hexadecimal:
            valid += string.ascii_letters
        if not all([char in valid for char in this]):
            self._fail_route()

        self._head += 1
        if self._read() != ";":
            self._fail_route()
        if numeric:
            test = int(this, 16) if hexadecimal else int(this)
            if test < 1 or test > 0x10FFFF:
                self._fail_route()
        else:
            if this not in htmlentities.entitydefs:
                self._fail_route()

        self._write(tokens.Text(text=this))
        self._write(tokens.HTMLEntityEnd())

    def _parse_entity(self):
        """Parse an HTML entity at the head of the wikicode string."""
        reset = self._head
        self._push()
        try:
            self._really_parse_entity()
        except BadRoute:
            self._head = reset
            self._write_text(self._read())
        else:
            self._write_all(self._pop())

    def _parse_comment(self):
        """Parse an HTML comment at the head of the wikicode string."""
        self._head += 4
        reset = self._head - 1
        try:
            comment = self._parse(contexts.COMMENT)
        except BadRoute:
            self._head = reset
            self._write_text("<!--")
        else:
            self._write(tokens.CommentStart())
            self._write_all(comment)
            self._write(tokens.CommentEnd())
            self._head += 2

    def _parse(self, context=0):
        """Parse the wikicode string, using *context* for when to stop."""
        self._push(context)
        while True:
            this = self._read()
            if this not in self.MARKERS:
                self._write_text(this)
                self._head += 1
                continue
            if this is self.END:
                fail = (contexts.TEMPLATE | contexts.ARGUMENT |
                        contexts.HEADING | contexts.COMMENT)
                if self._context & fail:
                    self._fail_route()
                return self._pop()
            next = self._read(1)
            if self._context & contexts.COMMENT:
                if this == next == "-" and self._read(2) == ">":
                    return self._pop()
                else:
                    self._write_text(this)
            elif this == next == "{":
                self._parse_template_or_argument()
            elif this == "|" and self._context & contexts.TEMPLATE:
                self._handle_template_param()
            elif this == "=" and self._context & contexts.TEMPLATE_PARAM_KEY:
                self._handle_template_param_value()
            elif this == next == "}" and self._context & contexts.TEMPLATE:
                return self._handle_template_end()
            elif this == "|" and self._context & contexts.ARGUMENT_NAME:
                self._handle_argument_separator()
            elif this == next == "}" and self._context & contexts.ARGUMENT:
                if self._read(2) == "}":
                    return self._handle_argument_end()
                else:
                    self._write_text("}")
            elif this == next == "[":
                if not self._context & contexts.WIKILINK_TITLE:
                    self._parse_wikilink()
                else:
                    self._write_text("[")
            elif this == "|" and self._context & contexts.WIKILINK_TITLE:
                self._handle_wikilink_separator()
            elif this == next == "]" and self._context & contexts.WIKILINK:
                return self._handle_wikilink_end()
            elif this == "=" and not self._global & contexts.GL_HEADING:
                if self._read(-1) in ("\n", self.START):
                    self._parse_heading()
                else:
                    self._write_text("=")
            elif this == "=" and self._context & contexts.HEADING:
                return self._handle_heading_end()
            elif this == "\n" and self._context & contexts.HEADING:
                self._fail_route()
            elif this == "&":
                self._parse_entity()
            elif this == "<" and next == "!":
                if self._read(2) == self._read(3) == "-":
                    self._parse_comment()
                else:
                    self._write_text(this)
            else:
                self._write_text(this)
            self._head += 1

    def tokenize(self, text):
        """Build a list of tokens from a string of wikicode and return it."""
        split = self.regex.split(text)
        self._text = [segment for segment in split if segment]
        return self._parse()

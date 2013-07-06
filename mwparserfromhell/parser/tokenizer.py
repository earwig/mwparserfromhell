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
from math import log
import re

from . import contexts, tokens
from ..compat import htmlentities
from ..tag_defs import is_parsable

__all__ = ["Tokenizer"]

class BadRoute(Exception):
    """Raised internally when the current tokenization route is invalid."""
    pass


class _TagOpenData(object):
    """Stores data about an HTML open tag, like ``<ref name="foo">``."""
    CX_NAME =        1 << 0
    CX_ATTR_READY =  1 << 1
    CX_ATTR_NAME =   1 << 2
    CX_ATTR_VALUE =  1 << 3
    CX_QUOTED =      1 << 4
    CX_NOTE_SPACE =  1 << 5
    CX_NOTE_EQUALS = 1 << 6
    CX_NOTE_QUOTE =  1 << 7

    def __init__(self):
        self.context = self.CX_NAME
        self.padding_buffer = []
        self.reset = 0


class Tokenizer(object):
    """Creates a list of tokens from a string of wikicode."""
    USES_C = False
    START = object()
    END = object()
    MARKERS = ["{", "}", "[", "]", "<", ">", "|", "=", "&", "#", "*", ";", ":",
               "/", "\\", '"', "-", "!", "\n", END]
    MAX_DEPTH = 40
    MAX_CYCLES = 100000
    regex = re.compile(r"([{}\[\]<>|=&#*;:/\\\"\-!\n])", flags=re.IGNORECASE)
    tag_splitter = re.compile(r"([\s\"\\])")

    def __init__(self):
        self._text = None
        self._head = 0
        self._stacks = []
        self._global = 0
        self._depth = 0
        self._cycles = 0

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
        self._depth += 1
        self._cycles += 1

    def _push_textbuffer(self):
        """Push the textbuffer onto the stack as a Text node and clear it."""
        if self._textbuffer:
            self._stack.append(tokens.Text(text="".join(self._textbuffer)))
            self._textbuffer = []

    def _pop(self, keep_context=False):
        """Pop the current stack/context/textbuffer, returing the stack.

        If *keep_context* is ``True``, then we will replace the underlying
        stack's context with the current stack's.
        """
        self._push_textbuffer()
        self._depth -= 1
        if keep_context:
            context = self._context
            stack = self._stacks.pop()[0]
            self._context = context
            return stack
        return self._stacks.pop()[0]

    def _can_recurse(self):
        """Return whether or not our max recursion depth has been exceeded."""
        return self._depth < self.MAX_DEPTH and self._cycles < self.MAX_CYCLES

    def _fail_route(self):
        """Fail the current tokenization route.

        Discards the current stack/context/textbuffer and raises
        :py:exc:`~.BadRoute`.
        """
        self._pop()
        raise BadRoute()

    def _emit(self, token):
        """Write a token to the end of the current token stack."""
        self._push_textbuffer()
        self._stack.append(token)

    def _emit_first(self, token):
        """Write a token to the beginning of the current token stack."""
        self._push_textbuffer()
        self._stack.insert(0, token)

    def _emit_text(self, text):
        """Write text to the current textbuffer."""
        self._textbuffer.append(text)

    def _emit_all(self, tokenlist):
        """Write a series of tokens to the current stack at once."""
        if tokenlist and isinstance(tokenlist[0], tokens.Text):
            self._emit_text(tokenlist.pop(0).text)
        self._push_textbuffer()
        self._stack.extend(tokenlist)

    def _emit_text_then_stack(self, text):
        """Pop the current stack, write *text*, and then write the stack."""
        stack = self._pop()
        self._emit_text(text)
        if stack:
            self._emit_all(stack)
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
            self._head += 1
            braces += 1
        self._push()

        while braces:
            if braces == 1:
                return self._emit_text_then_stack("{")
            if braces == 2:
                try:
                    self._parse_template()
                except BadRoute:
                    return self._emit_text_then_stack("{{")
                break
            try:
                self._parse_argument()
                braces -= 3
            except BadRoute:
                try:
                    self._parse_template()
                    braces -= 2
                except BadRoute:
                    return self._emit_text_then_stack("{" * braces)
            if braces:
                self._head += 1

        self._emit_all(self._pop())
        if self._context & contexts.FAIL_NEXT:
            self._context ^= contexts.FAIL_NEXT

    def _parse_template(self):
        """Parse a template at the head of the wikicode string."""
        reset = self._head
        try:
            template = self._parse(contexts.TEMPLATE_NAME)
        except BadRoute:
            self._head = reset
            raise
        self._emit_first(tokens.TemplateOpen())
        self._emit_all(template)
        self._emit(tokens.TemplateClose())

    def _parse_argument(self):
        """Parse an argument at the head of the wikicode string."""
        reset = self._head
        try:
            argument = self._parse(contexts.ARGUMENT_NAME)
        except BadRoute:
            self._head = reset
            raise
        self._emit_first(tokens.ArgumentOpen())
        self._emit_all(argument)
        self._emit(tokens.ArgumentClose())

    def _handle_template_param(self):
        """Handle a template parameter at the head of the string."""
        if self._context & contexts.TEMPLATE_NAME:
            self._context ^= contexts.TEMPLATE_NAME
        elif self._context & contexts.TEMPLATE_PARAM_VALUE:
            self._context ^= contexts.TEMPLATE_PARAM_VALUE
        elif self._context & contexts.TEMPLATE_PARAM_KEY:
            self._emit_all(self._pop(keep_context=True))
        self._context |= contexts.TEMPLATE_PARAM_KEY
        self._emit(tokens.TemplateParamSeparator())
        self._push(self._context)

    def _handle_template_param_value(self):
        """Handle a template parameter's value at the head of the string."""
        self._emit_all(self._pop(keep_context=True))
        self._context ^= contexts.TEMPLATE_PARAM_KEY
        self._context |= contexts.TEMPLATE_PARAM_VALUE
        self._emit(tokens.TemplateParamEquals())

    def _handle_template_end(self):
        """Handle the end of a template at the head of the string."""
        if self._context & contexts.TEMPLATE_PARAM_KEY:
            self._emit_all(self._pop(keep_context=True))
        self._head += 1
        return self._pop()

    def _handle_argument_separator(self):
        """Handle the separator between an argument's name and default."""
        self._context ^= contexts.ARGUMENT_NAME
        self._context |= contexts.ARGUMENT_DEFAULT
        self._emit(tokens.ArgumentSeparator())

    def _handle_argument_end(self):
        """Handle the end of an argument at the head of the string."""
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
            self._emit_text("[[")
        else:
            if self._context & contexts.FAIL_NEXT:
                self._context ^= contexts.FAIL_NEXT
            self._emit(tokens.WikilinkOpen())
            self._emit_all(wikilink)
            self._emit(tokens.WikilinkClose())

    def _handle_wikilink_separator(self):
        """Handle the separator between a wikilink's title and its text."""
        self._context ^= contexts.WIKILINK_TITLE
        self._context |= contexts.WIKILINK_TEXT
        self._emit(tokens.WikilinkSeparator())

    def _handle_wikilink_end(self):
        """Handle the end of a wikilink at the head of the string."""
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
            self._emit_text("=" * best)
        else:
            self._emit(tokens.HeadingStart(level=level))
            if level < best:
                self._emit_text("=" * (best - level))
            self._emit_all(title)
            self._emit(tokens.HeadingEnd())
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

        try:  # Try to check for a heading closure after this one
            after, after_level = self._parse(self._context)
        except BadRoute:
            if level < best:
                self._emit_text("=" * (best - level))
            self._head = reset + best - 1
            return self._pop(), level
        else:  # Found another closure
            self._emit_text("=" * best)
            self._emit_all(after)
            return self._pop(), after_level

    def _really_parse_entity(self):
        """Actually parse an HTML entity and ensure that it is valid."""
        self._emit(tokens.HTMLEntityStart())
        self._head += 1

        this = self._read(strict=True)
        if this == "#":
            numeric = True
            self._emit(tokens.HTMLEntityNumeric())
            self._head += 1
            this = self._read(strict=True)
            if this[0].lower() == "x":
                hexadecimal = True
                self._emit(tokens.HTMLEntityHex(char=this[0]))
                this = this[1:]
                if not this:
                    self._fail_route()
            else:
                hexadecimal = False
        else:
            numeric = hexadecimal = False

        valid = "0123456789abcdefABCDEF" if hexadecimal else "0123456789"
        if not numeric and not hexadecimal:
            valid += "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
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

        self._emit(tokens.Text(text=this))
        self._emit(tokens.HTMLEntityEnd())

    def _parse_entity(self):
        """Parse an HTML entity at the head of the wikicode string."""
        reset = self._head
        self._push()
        try:
            self._really_parse_entity()
        except BadRoute:
            self._head = reset
            self._emit_text(self._read())
        else:
            self._emit_all(self._pop())

    def _parse_comment(self):
        """Parse an HTML comment at the head of the wikicode string."""
        self._head += 4
        reset = self._head - 1
        try:
            comment = self._parse(contexts.COMMENT)
        except BadRoute:
            self._head = reset
            self._emit_text("<!--")
        else:
            self._emit(tokens.CommentStart())
            self._emit_all(comment)
            self._emit(tokens.CommentEnd())
            self._head += 2

    def _parse_tag(self):
        """Parse an HTML tag at the head of the wikicode string."""
        reset = self._head
        self._head += 1
        try:
            tag = self._really_parse_tag()
        except BadRoute:
            self._head = reset
            self._emit_text("<")
        else:
            self._emit_all(tag)

    def _really_parse_tag(self):
        """Actually parse an HTML tag, starting with the open (``<foo>``)."""
        data = _TagOpenData()
        self._push(contexts.TAG_OPEN)
        self._emit(tokens.TagOpenOpen(showtag=True))
        while True:
            this, next = self._read(), self._read(1)
            can_exit = (not data.context & (data.CX_QUOTED | data.CX_NAME) or
                        data.context & data.CX_NOTE_SPACE)
            if this is self.END:
                if self._context & contexts.TAG_ATTR:
                    if data.context & data.CX_QUOTED:
                        # Unclosed attribute quote: reset, don't die
                        data.context = data.CX_ATTR_VALUE
                        self._pop()
                        self._head = data.reset
                        continue
                    self._pop()
                self._fail_route()
            elif this == ">" and can_exit:
                self._handle_tag_close_open(data, tokens.TagCloseOpen)
                self._context = contexts.TAG_BODY
                if is_parsable(self._stack[1].text):
                    return self._parse(push=False)
                return self._handle_blacklisted_tag()
            elif this == "/" and next == ">" and can_exit:
                self._handle_tag_close_open(data, tokens.TagCloseSelfclose)
                return self._pop()
            else:
                self._handle_tag_data(data, this)
            self._head += 1

    def _push_tag_buffer(self, data):
        """Write a pending tag attribute from *data* to the stack."""
        if data.context & data.CX_QUOTED:
            self._emit_first(tokens.TagAttrQuote())
            self._emit_all(self._pop())
        buf = data.padding_buffer
        while len(buf) < 3:
            buf.append("")
        self._emit_first(tokens.TagAttrStart(pad_after_eq=buf.pop(),
            pad_before_eq=buf.pop(), pad_first=buf.pop()))
        self._emit_all(self._pop())
        data.padding_buffer = []

    def _handle_tag_data(self, data, text):
        """Handle all sorts of *text* data inside of an HTML open tag."""
        for chunk in self.tag_splitter.split(text):
            if not chunk:
                continue
            if data.context & data.CX_NAME:
                if chunk in self.MARKERS or chunk.isspace():
                    self._fail_route()  # Tags must start with text, not spaces
                data.context = data.CX_NOTE_SPACE
            elif chunk.isspace():
                self._handle_tag_space(data, chunk)
                continue
            elif data.context & data.CX_NOTE_SPACE:
                if data.context & data.CX_QUOTED:
                    data.context = data.CX_ATTR_VALUE
                    self._pop()
                    self._head = data.reset - 1  # Will be auto-incremented
                    return  # Break early
                self._fail_route()
            elif data.context & data.CX_ATTR_READY:
                data.context = data.CX_ATTR_NAME
                self._push(contexts.TAG_ATTR)
            elif data.context & data.CX_ATTR_NAME:
                if chunk == "=":
                    if not data.context & data.CX_NOTE_EQUALS:
                        data.padding_buffer.append("")  # No padding before '='
                    data.context = data.CX_ATTR_VALUE | data.CX_NOTE_QUOTE
                    self._emit(tokens.TagAttrEquals())
                    continue
                if data.context & data.CX_NOTE_EQUALS:
                    self._push_tag_buffer(data)
                    data.padding_buffer.append("")  # No padding before tag
                    data.context = data.CX_ATTR_NAME
                    self._push(contexts.TAG_ATTR)
            elif data.context & data.CX_ATTR_VALUE:
                escaped = self._read(-1) == "\\" and self._read(-2) != "\\"
                if data.context & data.CX_NOTE_QUOTE:
                    data.context ^= data.CX_NOTE_QUOTE
                    if chunk == '"' and not escaped:
                        data.context |= data.CX_QUOTED
                        self._push(self._context)
                        data.reset = self._head
                        continue
                elif data.context & data.CX_QUOTED:
                    if chunk == '"' and not escaped:
                        data.context |= data.CX_NOTE_SPACE
                        continue
            self._handle_tag_text(chunk)

    def _handle_tag_space(self, data, text):
        """Handle whitespace (*text*) inside of an HTML open tag."""
        ctx = data.context
        end_of_value = ctx & data.CX_ATTR_VALUE and not ctx & (data.CX_QUOTED | data.CX_NOTE_QUOTE)
        if end_of_value or (ctx & data.CX_QUOTED and ctx & data.CX_NOTE_SPACE):
            self._push_tag_buffer(data)
            data.context = data.CX_ATTR_READY
        elif ctx & data.CX_NOTE_SPACE:
            data.context = data.CX_ATTR_READY
        elif ctx & data.CX_ATTR_NAME:
            data.context |= data.CX_NOTE_EQUALS
        if ctx & data.CX_QUOTED and not ctx & data.CX_NOTE_SPACE:
            self._emit_text(text)
        else:
            data.padding_buffer.append(text)

    def _handle_tag_text(self, text):
        """Handle regular *text* inside of an HTML open tag."""
        next = self._read(1)
        if not self._can_recurse() or text not in self.MARKERS:
            self._emit_text(text)
        elif text == next == "{":
            self._parse_template_or_argument()
        elif text == next == "[":
            self._parse_wikilink()
        elif text == "<":
            self._parse_tag()
        else:
            self._emit_text(text)

    def _handle_blacklisted_tag(self):
        """Handle the body of an HTML tag that is parser-blacklisted."""
        while True:
            this, next = self._read(), self._read(1)
            self._head += 1
            if this is self.END:
                self._fail_route()
            elif this == "<" and next == "/":
                self._handle_tag_open_close()
                return self._parse(push=False)
            else:
                self._emit_text(this)

    def _handle_tag_close_open(self, data, token):
        """Handle the closing of a open tag (``<foo>``)."""
        if data.context & (data.CX_ATTR_NAME | data.CX_ATTR_VALUE):
            self._push_tag_buffer(data)
        padding = data.padding_buffer[0] if data.padding_buffer else ""
        self._emit(token(padding=padding))
        self._head += 1

    def _handle_tag_open_close(self):
        """Handle the opening of a closing tag (``</foo>``)."""
        self._emit(tokens.TagOpenClose())
        self._push(contexts.TAG_CLOSE)
        self._head += 1

    def _handle_tag_close_close(self):
        """Handle the ending of a closing tag (``</foo>``)."""
        strip = lambda tok: tok.text.rstrip().lower()
        closing = self._pop()
        if len(closing) != 1 or (not isinstance(closing[0], tokens.Text) or
                                 strip(closing[0]) != strip(self._stack[1])):
            self._fail_route()
        self._emit_all(closing)
        self._emit(tokens.TagCloseClose())
        return self._pop()

    def _verify_safe(self, this):
        """Make sure we are not trying to write an invalid character."""
        context = self._context
        if context & contexts.FAIL_NEXT:
            return False
        if context & contexts.WIKILINK_TITLE:
            if this == "]" or this == "{":
                self._context |= contexts.FAIL_NEXT
            elif this == "\n" or this == "[" or this == "}":
                return False
            return True
        elif context & contexts.TEMPLATE_NAME:
            if this == "{" or this == "}" or this == "[":
                self._context |= contexts.FAIL_NEXT
                return True
            if this == "]":
                return False
            if this == "|":
                return True
            if context & contexts.HAS_TEXT:
                if context & contexts.FAIL_ON_TEXT:
                    if this is self.END or not this.isspace():
                        return False
                else:
                    if this == "\n":
                        self._context |= contexts.FAIL_ON_TEXT
            elif this is self.END or not this.isspace():
                self._context |= contexts.HAS_TEXT
            return True
        elif context & contexts.TAG_CLOSE:
            return this != "<"
        else:
            if context & contexts.FAIL_ON_EQUALS:
                if this == "=":
                    return False
            elif context & contexts.FAIL_ON_LBRACE:
                if this == "{" or (self._read(-1) == self._read(-2) == "{"):
                    if context & contexts.TEMPLATE:
                        self._context |= contexts.FAIL_ON_EQUALS
                    else:
                        self._context |= contexts.FAIL_NEXT
                    return True
                self._context ^= contexts.FAIL_ON_LBRACE
            elif context & contexts.FAIL_ON_RBRACE:
                if this == "}":
                    if context & contexts.TEMPLATE:
                        self._context |= contexts.FAIL_ON_EQUALS
                    else:
                        self._context |= contexts.FAIL_NEXT
                    return True
                self._context ^= contexts.FAIL_ON_RBRACE
            elif this == "{":
                self._context |= contexts.FAIL_ON_LBRACE
            elif this == "}":
                self._context |= contexts.FAIL_ON_RBRACE
            return True

    def _parse(self, context=0, push=True):
        """Parse the wikicode string, using *context* for when to stop."""
        unsafe = (contexts.TEMPLATE_NAME | contexts.WIKILINK_TITLE |
                  contexts.TEMPLATE_PARAM_KEY | contexts.ARGUMENT_NAME |
                  contexts.TAG_CLOSE)
        fail = (contexts.TEMPLATE | contexts.ARGUMENT | contexts.WIKILINK |
                contexts.HEADING | contexts.COMMENT | contexts.TAG)
        double_fail = (contexts.TEMPLATE_PARAM_KEY | contexts.TAG_CLOSE)

        if push:
            self._push(context)
        while True:
            this = self._read()
            if self._context & unsafe:
                if not self._verify_safe(this):
                    if self._context & double_fail:
                        self._pop()
                    self._fail_route()
            if this not in self.MARKERS:
                self._emit_text(this)
                self._head += 1
                continue
            if this is self.END:
                if self._context & fail:
                    if self._context & double_fail:
                        self._pop()
                    self._fail_route()
                return self._pop()
            next = self._read(1)
            if self._context & contexts.COMMENT:
                if this == next == "-" and self._read(2) == ">":
                    return self._pop()
                else:
                    self._emit_text(this)
            elif this == next == "{":
                if self._can_recurse():
                    self._parse_template_or_argument()
                else:
                    self._emit_text("{")
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
                    self._emit_text("}")
            elif this == next == "[":
                if not self._context & contexts.WIKILINK_TITLE and self._can_recurse():
                    self._parse_wikilink()
                else:
                    self._emit_text("[")
            elif this == "|" and self._context & contexts.WIKILINK_TITLE:
                self._handle_wikilink_separator()
            elif this == next == "]" and self._context & contexts.WIKILINK:
                return self._handle_wikilink_end()
            elif this == "=" and not self._global & contexts.GL_HEADING:
                if self._read(-1) in ("\n", self.START):
                    self._parse_heading()
                else:
                    self._emit_text("=")
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
                    self._emit_text(this)
            elif this == "<" and next == "/" and self._context & contexts.TAG_BODY:
                self._handle_tag_open_close()
            elif this == "<":
                if not self._context & contexts.TAG_CLOSE and self._can_recurse():
                    self._parse_tag()
                else:
                    self._emit_text("<")
            elif this == ">" and self._context & contexts.TAG_CLOSE:
                return self._handle_tag_close_close()
            else:
                self._emit_text(this)
            self._head += 1

    def tokenize(self, text):
        """Build a list of tokens from a string of wikicode and return it."""
        split = self.regex.split(text)
        self._text = [segment for segment in split if segment]
        return self._parse()

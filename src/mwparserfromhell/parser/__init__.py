# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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

"""
This package contains the actual wikicode parser, split up into two main
modules: the :mod:`.tokenizer` and the :mod:`.builder`. This module joins them
together into one interface.
"""

from .builder import Builder
from .errors import ParserError

try:
    from ._tokenizer import CTokenizer

    use_c = True
except ImportError:
    from .tokenizer import Tokenizer

    CTokenizer = None
    use_c = False

__all__ = ["use_c", "Parser", "ParserError"]


class Parser:
    """Represents a parser for wikicode.

    Actual parsing is a two-step process: first, the text is split up into a
    series of tokens by the :class:`.Tokenizer`, and then the tokens are
    converted into trees of :class:`.Wikicode` objects and :class:`.Node`\\ s
    by the :class:`.Builder`.

    Instances of this class or its dependents (:class:`.Tokenizer` and
    :class:`.Builder`) should not be shared between threads. :meth:`parse` can
    be called multiple times as long as it is not done concurrently. In
    general, there is no need to do this because parsing should be done through
    :func:`mwparserfromhell.parse`, which creates a new :class:`.Parser` object
    as necessary.
    """

    def __init__(self):
        if use_c and CTokenizer:
            self._tokenizer = CTokenizer()
        else:
            from .tokenizer import Tokenizer

            self._tokenizer = Tokenizer()
        self._builder = Builder()

    def parse(self, text, context=0, skip_style_tags=False):
        """Parse *text*, returning a :class:`.Wikicode` object tree.

        If given, *context* will be passed as a starting context to the parser.
        This is helpful when this function is used inside node attribute
        setters. For example, :class:`.ExternalLink`\\ 's
        :attr:`~.ExternalLink.url` setter sets *context* to
        :mod:`contexts.EXT_LINK_URI <.contexts>` to prevent the URL itself
        from becoming an :class:`.ExternalLink`.

        If *skip_style_tags* is ``True``, then ``''`` and ``'''`` will not be
        parsed, but instead will be treated as plain text.

        If there is an internal error while parsing, :exc:`.ParserError` will
        be raised.
        """
        tokens = self._tokenizer.tokenize(text, context, skip_style_tags)
        code = self._builder.build(tokens)
        return code

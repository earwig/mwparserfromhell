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

"""
This package contains the actual wikicode parser, split up into two main
modules: the :py:mod:`~.tokenizer` and the :py:mod:`~.builder`. This module
joins them together under one interface.
"""

from .builder import Builder
from .tokenizer import Tokenizer
try:
    from ._tokenizer import CTokenizer
    use_c = True
except ImportError:
    CTokenizer = None
    use_c = False

__all__ = ["use_c", "Parser"]

class Parser(object):
    """Represents a parser for wikicode.

    Actual parsing is a two-step process: first, the text is split up into a
    series of tokens by the :py:class:`~.Tokenizer`, and then the tokens are
    converted into trees of :py:class:`~.Wikicode` objects and
    :py:class:`~.Node`\ s by the :py:class:`~.Builder`.
    """

    def __init__(self):
        if use_c and CTokenizer:
            self._tokenizer = CTokenizer()
        else:
            self._tokenizer = Tokenizer()
        self._builder = Builder()

    def parse(self, text, context=0):
        """Parse *text*, returning a :py:class:`~.Wikicode` object tree."""
        tokens = self._tokenizer.tokenize(text, context)
        code = self._builder.build(tokens)
        return code

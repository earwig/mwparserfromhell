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

"""
This module contains the token definitions that are used as an intermediate
parsing data type - they are stored in a flat list, with each token being
identified by its type and optional attributes. The token list is generated in
a syntactically valid form by the :py:class:`~.Tokenizer`, and then converted
into the :py:class`~.Wikicode` tree by the :py:class:`~.Builder`.
"""

from __future__ import unicode_literals

from ..compat import basestring, py3k

__all__ = ["Token"]

class Token(object):
    """A token stores the semantic meaning of a unit of wikicode."""

    def __init__(self, **kwargs):
        super(Token, self).__setattr__("_kwargs", kwargs)

    def __repr__(self):
        args = []
        for key, value in self._kwargs.items():
            if isinstance(value, basestring) and len(value) > 100:
                args.append(key + "=" + repr(value[:97] + "..."))
            else:
                args.append(key + "=" + repr(value))
        return "{0}({1})".format(type(self).__name__, ", ".join(args))

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._kwargs == other._kwargs
        return False

    def __getattr__(self, key):
        return self._kwargs[key]

    def __setattr__(self, key, value):
        self._kwargs[key] = value

    def __delattr__(self, key):
        del self._kwargs[key]

def make(name):
    """Create a new Token class using ``type()`` and add it to ``__all__``."""
    token = type(name if py3k else name.encode("utf8"), (Token,), {})
    globals()[name] = token
    __all__.append(name)

make("Text")

make("TemplateOpen")                                                # {{
make("TemplateParamSeparator")                                      # |
make("TemplateParamEquals")                                         # =
make("TemplateClose")                                               # }}

make("ArgumentOpen")                                                # {{{
make("ArgumentSeparator")                                           # |
make("ArgumentClose")                                               # }}}

make("WikilinkOpen")                                                # [[
make("WikilinkSeparator")                                           # |
make("WikilinkClose")                                               # ]]

make("HTMLEntityStart")                                             # &
make("HTMLEntityNumeric")                                           # #
make("HTMLEntityHex")                                               # x
make("HTMLEntityEnd")                                               # ;

make("HeadingStart")                                                # =...
make("HeadingEnd")                                                  # =...

make("CommentStart")                                                # <!--
make("CommentEnd")                                                  # -->

make("TagOpenOpen")                                                 # <
make("TagAttrStart")
make("TagAttrEquals")                                               # =
make("TagAttrQuote")                                                # "
make("TagCloseOpen")                                                # >
make("TagCloseSelfclose")                                           # />
make("TagOpenClose")                                                # </
make("TagCloseClose")                                               # >

del make

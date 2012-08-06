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

__all__ = ["Token"]

class Token(object):
    def __init__(self, **kwargs):
        self.__kwargs = kwargs

    def __getattr__(self, key):
        return self.__kwargs[key]

    def __setattr__(self, key, value):
        self.__kwargs[key] = value

    def __delattr__(self, key):
        del self.__kwargs[key]


def make(name):
    __all__.append(name)
    return type(name, (Token,), {})

TEXT = make("TEXT")

TEMPLATE_OPEN = make("TEMPLATE_OPEN")                               # {{
TEMPLATE_PARAM_SEPARATOR = make("TEMPLATE_PARAM_SEPARATOR")         # |
TEMPLATE_PARAM_EQUALS = make("TEMPLATE_PARAM_EQUALS")               # =
TEMPLATE_CLOSE = make("TEMPLATE_CLOSE")                             # }}

HTML_ENTITY_START = make("HTML_ENTITY_START")                       # &
HTML_ENTITY_NUMERIC = make("HTML_ENTITY_NUMERIC")                   # #
HTML_ENTITY_HEX = make("HTML_ENTITY_HEX")                           # x
HTML_ENTITY_END = make("HTML_ENTITY_END")                           # ;

HEADING_BLOCK = make("HEADING_BLOCK")                               # =...

TAG_OPEN_OPEN = make("TAG_OPEN_OPEN")                               # <
TAG_ATTR_EQUALS = make("TAG_ATTR_EQUALS")                           # =
TAG_ATTR_QUOTE = make("TAG_ATTR_QUOTE")                             # "
TAG_CLOSE_OPEN = make("TAG_CLOSE_OPEN")                             # >
TAG_CLOSE_SELFCLOSE = make("TAG_CLOSE_SELFCLOSE")                   # />
TAG_OPEN_CLOSE = make("TAG_OPEN_CLOSE")                             # </
TAG_CLOSE_CLOSE = make("TAG_CLOSE_CLOSE")                           # >

del make

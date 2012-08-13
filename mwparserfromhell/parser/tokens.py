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
        super(Token, self).__setattr__("_kwargs", kwargs)

    def __getattr__(self, key):
        return self._kwargs[key]

    def __setattr__(self, key, value):
        self._kwargs[key] = value

    def __delattr__(self, key):
        del self._kwargs[key]


def make(name):
    __all__.append(name)
    return type(name, (Token,), {})

Text = make("Text")

TemplateOpen = make("TemplateOpen")                                 # {{
TemplateParamSeparator = make("TemplateParamSeparator")             # |
TemplateParamEquals = make("TemplateParamEquals")                   # =
TemplateClose = make("TemplateClose")                               # }}

HTMLEntityStart = make("HTMLEntityStart")                           # &
HTMLEntityNumeric = make("HTMLEntityNumeric")                       # #
HTMLEntityHex = make("HTMLEntityHex")                               # x
HTMLEntityEnd = make("HTMLEntityEnd")                               # ;

HeadingBlock = make("HeadingBlock")                                 # =...

TagOpenOpen = make("TagOpenOpen")                                   # <
TagAttrStart = make("TagAttrStart")
TagAttrEquals = make("TagAttrEquals")                               # =
TagAttrQuote = make("TagAttrQuote")                                 # "
TagCloseOpen = make("TagCloseOpen")                                 # >
TagCloseSelfclose = make("TagCloseSelfclose")                       # />
TagOpenClose = make("TagOpenClose")                                 # </
TagCloseClose = make("TagCloseClose")                               # >

del make

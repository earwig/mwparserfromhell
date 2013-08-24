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
This module contains various "context" definitions, which are essentially flags
set during the tokenization process, either on the current parse stack (local
contexts) or affecting all stacks (global contexts). They represent the context
the tokenizer is in, such as inside a template's name definition, or inside a
level-two heading. This is used to determine what tokens are valid at the
current point and also if the current parsing route is invalid.

The tokenizer stores context as an integer, with these definitions bitwise OR'd
to set them, AND'd to check if they're set, and XOR'd to unset them. The
advantage of this is that contexts can have sub-contexts (as ``FOO == 0b11``
will cover ``BAR == 0b10`` and ``BAZ == 0b01``).

Local (stack-specific) contexts:

* :py:const:`TEMPLATE`

    * :py:const:`TEMPLATE_NAME`
    * :py:const:`TEMPLATE_PARAM_KEY`
    * :py:const:`TEMPLATE_PARAM_VALUE`

* :py:const:`ARGUMENT`

    * :py:const:`ARGUMENT_NAME`
    * :py:const:`ARGUMENT_DEFAULT`

* :py:const:`WIKILINK`

    * :py:const:`WIKILINK_TITLE`
    * :py:const:`WIKILINK_TEXT`

* :py:const:`EXT_LINK`

    * :py:const:`EXT_LINK_URI`
    * :py:const:`EXT_LINK_TITLE`
    * :py:const:`EXT_LINK_BRACKETS`

* :py:const:`HEADING`

    * :py:const:`HEADING_LEVEL_1`
    * :py:const:`HEADING_LEVEL_2`
    * :py:const:`HEADING_LEVEL_3`
    * :py:const:`HEADING_LEVEL_4`
    * :py:const:`HEADING_LEVEL_5`
    * :py:const:`HEADING_LEVEL_6`

* :py:const:`TAG`

    * :py:const:`TAG_OPEN`
    * :py:const:`TAG_ATTR`
    * :py:const:`TAG_BODY`
    * :py:const:`TAG_CLOSE`

* :py:const:`STYLE`

    * :py:const:`STYLE_ITALICS`
    * :py:const:`STYLE_BOLD`
    * :py:const:`STYLE_PASS_AGAIN`
    * :py:const:`STYLE_SECOND_PASS`

* :py:const:`DL_TERM`

* :py:const:`SAFETY_CHECK`

    * :py:const:`HAS_TEXT`
    * :py:const:`FAIL_ON_TEXT`
    * :py:const:`FAIL_NEXT`
    * :py:const:`FAIL_ON_LBRACE`
    * :py:const:`FAIL_ON_RBRACE`
    * :py:const:`FAIL_ON_EQUALS`

Global contexts:

* :py:const:`GL_HEADING`

Aggregate contexts:

* :py:const:`FAIL`
* :py:const:`UNSAFE`
* :py:const:`DOUBLE`
* :py:const:`INVALID_LINK`

"""

# Local contexts:

TEMPLATE_NAME =        1 << 0
TEMPLATE_PARAM_KEY =   1 << 1
TEMPLATE_PARAM_VALUE = 1 << 2
TEMPLATE = TEMPLATE_NAME + TEMPLATE_PARAM_KEY + TEMPLATE_PARAM_VALUE

ARGUMENT_NAME =    1 << 3
ARGUMENT_DEFAULT = 1 << 4
ARGUMENT = ARGUMENT_NAME + ARGUMENT_DEFAULT

WIKILINK_TITLE = 1 << 5
WIKILINK_TEXT =  1 << 6
WIKILINK = WIKILINK_TITLE + WIKILINK_TEXT

EXT_LINK_URI      = 1 << 7
EXT_LINK_TITLE    = 1 << 8
EXT_LINK_BRACKETS = 1 << 9
EXT_LINK = EXT_LINK_URI + EXT_LINK_TITLE + EXT_LINK_BRACKETS

HEADING_LEVEL_1 = 1 << 10
HEADING_LEVEL_2 = 1 << 11
HEADING_LEVEL_3 = 1 << 12
HEADING_LEVEL_4 = 1 << 13
HEADING_LEVEL_5 = 1 << 14
HEADING_LEVEL_6 = 1 << 15
HEADING = (HEADING_LEVEL_1 + HEADING_LEVEL_2 + HEADING_LEVEL_3 +
           HEADING_LEVEL_4 + HEADING_LEVEL_5 + HEADING_LEVEL_6)

TAG_OPEN =  1 << 16
TAG_ATTR =  1 << 17
TAG_BODY =  1 << 18
TAG_CLOSE = 1 << 19
TAG = TAG_OPEN + TAG_ATTR + TAG_BODY + TAG_CLOSE

STYLE_ITALICS =      1 << 20
STYLE_BOLD =         1 << 21
STYLE_PASS_AGAIN =   1 << 22
STYLE_SECOND_PASS =  1 << 23
STYLE = STYLE_ITALICS + STYLE_BOLD + STYLE_PASS_AGAIN + STYLE_SECOND_PASS

DL_TERM = 1 << 24

HAS_TEXT =       1 << 25
FAIL_ON_TEXT =   1 << 26
FAIL_NEXT  =     1 << 27
FAIL_ON_LBRACE = 1 << 28
FAIL_ON_RBRACE = 1 << 29
FAIL_ON_EQUALS = 1 << 30
SAFETY_CHECK = (HAS_TEXT + FAIL_ON_TEXT + FAIL_NEXT + FAIL_ON_LBRACE +
                FAIL_ON_RBRACE + FAIL_ON_EQUALS)

# Global contexts:

GL_HEADING = 1 << 0

# Aggregate contexts:

FAIL = TEMPLATE + ARGUMENT + WIKILINK + EXT_LINK_TITLE + HEADING + TAG + STYLE
UNSAFE = (TEMPLATE_NAME + WIKILINK + EXT_LINK_TITLE + TEMPLATE_PARAM_KEY +
          ARGUMENT_NAME + TAG_CLOSE)
DOUBLE = TEMPLATE_PARAM_KEY + TAG_CLOSE
INVALID_LINK = TEMPLATE_NAME + ARGUMENT_NAME + WIKILINK + EXT_LINK

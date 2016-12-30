# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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

* :const:`TEMPLATE`

    * :const:`TEMPLATE_NAME`
    * :const:`TEMPLATE_PARAM_KEY`
    * :const:`TEMPLATE_PARAM_VALUE`

* :const:`ARGUMENT`

    * :const:`ARGUMENT_NAME`
    * :const:`ARGUMENT_DEFAULT`

* :const:`WIKILINK`

    * :const:`WIKILINK_TITLE`
    * :const:`WIKILINK_TEXT`

* :const:`EXT_LINK`

    * :const:`EXT_LINK_URI`
    * :const:`EXT_LINK_TITLE`

* :const:`HEADING`

    * :const:`HEADING_LEVEL_1`
    * :const:`HEADING_LEVEL_2`
    * :const:`HEADING_LEVEL_3`
    * :const:`HEADING_LEVEL_4`
    * :const:`HEADING_LEVEL_5`
    * :const:`HEADING_LEVEL_6`

* :const:`TAG`

    * :const:`TAG_OPEN`
    * :const:`TAG_ATTR`
    * :const:`TAG_BODY`
    * :const:`TAG_CLOSE`

* :const:`STYLE`

    * :const:`STYLE_ITALICS`
    * :const:`STYLE_BOLD`
    * :const:`STYLE_PASS_AGAIN`
    * :const:`STYLE_SECOND_PASS`

* :const:`DL_TERM`

* :const:`SAFETY_CHECK`

    * :const:`HAS_TEXT`
    * :const:`FAIL_ON_TEXT`
    * :const:`FAIL_NEXT`
    * :const:`FAIL_ON_LBRACE`
    * :const:`FAIL_ON_RBRACE`
    * :const:`FAIL_ON_EQUALS`
    * :const:`HAS_TEMPLATE`

* :const:`TABLE`

    * :const:`TABLE_OPEN`
    * :const:`TABLE_CELL_OPEN`
    * :const:`TABLE_CELL_STYLE`
    * :const:`TABLE_TD_LINE`
    * :const:`TABLE_TH_LINE`
    * :const:`TABLE_CELL_LINE_CONTEXTS`

Global contexts:

* :const:`GL_HEADING`

Aggregate contexts:

* :const:`FAIL`
* :const:`UNSAFE`
* :const:`DOUBLE`
* :const:`NO_WIKILINKS`
* :const:`NO_EXT_LINKS`

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
EXT_LINK = EXT_LINK_URI + EXT_LINK_TITLE

HEADING_LEVEL_1 = 1 << 9
HEADING_LEVEL_2 = 1 << 10
HEADING_LEVEL_3 = 1 << 11
HEADING_LEVEL_4 = 1 << 12
HEADING_LEVEL_5 = 1 << 13
HEADING_LEVEL_6 = 1 << 14
HEADING = (HEADING_LEVEL_1 + HEADING_LEVEL_2 + HEADING_LEVEL_3 +
           HEADING_LEVEL_4 + HEADING_LEVEL_5 + HEADING_LEVEL_6)

TAG_OPEN =  1 << 15
TAG_ATTR =  1 << 16
TAG_BODY =  1 << 17
TAG_CLOSE = 1 << 18
TAG = TAG_OPEN + TAG_ATTR + TAG_BODY + TAG_CLOSE

STYLE_ITALICS =      1 << 19
STYLE_BOLD =         1 << 20
STYLE_PASS_AGAIN =   1 << 21
STYLE_SECOND_PASS =  1 << 22
STYLE = STYLE_ITALICS + STYLE_BOLD + STYLE_PASS_AGAIN + STYLE_SECOND_PASS

DL_TERM = 1 << 23

HAS_TEXT =       1 << 24
FAIL_ON_TEXT =   1 << 25
FAIL_NEXT  =     1 << 26
FAIL_ON_LBRACE = 1 << 27
FAIL_ON_RBRACE = 1 << 28
FAIL_ON_EQUALS = 1 << 29
HAS_TEMPLATE =   1 << 30
SAFETY_CHECK = (HAS_TEXT + FAIL_ON_TEXT + FAIL_NEXT + FAIL_ON_LBRACE +
                FAIL_ON_RBRACE + FAIL_ON_EQUALS + HAS_TEMPLATE)

TABLE_OPEN =       1 << 31
TABLE_CELL_OPEN =  1 << 32
TABLE_CELL_STYLE = 1 << 33
TABLE_ROW_OPEN =   1 << 34
TABLE_TD_LINE =    1 << 35
TABLE_TH_LINE =    1 << 36
TABLE_CELL_LINE_CONTEXTS = TABLE_TD_LINE + TABLE_TH_LINE + TABLE_CELL_STYLE
TABLE = (TABLE_OPEN + TABLE_CELL_OPEN + TABLE_CELL_STYLE + TABLE_ROW_OPEN +
         TABLE_TD_LINE + TABLE_TH_LINE)

# Global contexts:

GL_HEADING = 1 << 0

# Aggregate contexts:

FAIL = (TEMPLATE + ARGUMENT + WIKILINK + EXT_LINK_TITLE + HEADING + TAG +
        STYLE + TABLE)
UNSAFE = (TEMPLATE_NAME + WIKILINK_TITLE + EXT_LINK_TITLE +
          TEMPLATE_PARAM_KEY + ARGUMENT_NAME + TAG_CLOSE)
DOUBLE = TEMPLATE_PARAM_KEY + TAG_CLOSE + TABLE_ROW_OPEN
NO_WIKILINKS = TEMPLATE_NAME + ARGUMENT_NAME + WIKILINK_TITLE + EXT_LINK_URI
NO_EXT_LINKS = TEMPLATE_NAME + ARGUMENT_NAME + WIKILINK_TITLE + EXT_LINK

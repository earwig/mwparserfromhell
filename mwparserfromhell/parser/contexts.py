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
This module contains various "context" definitions, which are essentially flags
set during the tokenization process, either on the current parse stack (local
contexts) or affecting all stacks (global contexts). They represent the context
the tokenizer is in, such as inside a template's name definition, or inside a
heading of level two. This is used to determine what tokens are valid at the
current point and also if the current parsing route is invalid.

The tokenizer stores context as an integer, with these definitions bitwise OR'd
to add them, AND'd to check if they're set, and XOR'd to remove them. The
advantage of this is that contexts can have sub-contexts (as FOO == 0b11 will
cover BAR == 0b10 and BAZ == 0b01).

Local (stack-specific) contexts:

* TEMPLATE
** TEMPLATE_NAME
** TEMPLATE_PARAM_KEY
** TEMPLATE_PARAM_VALUE
* HEADING
** HEADING_LEVEL_1
** HEADING_LEVEL_2
** HEADING_LEVEL_3
** HEADING_LEVEL_4
** HEADING_LEVEL_5
** HEADING_LEVEL_6

Global contexts:

* GL_HEADING
"""

# Local contexts:

TEMPLATE =              0b000000111
TEMPLATE_NAME =         0b000000001
TEMPLATE_PARAM_KEY =    0b000000010
TEMPLATE_PARAM_VALUE =  0b000000100

HEADING =               0b111111000
HEADING_LEVEL_1 =       0b000001000
HEADING_LEVEL_2 =       0b000010000
HEADING_LEVEL_3 =       0b000100000
HEADING_LEVEL_4 =       0b001000000
HEADING_LEVEL_5 =       0b010000000
HEADING_LEVEL_6 =       0b100000000


# Global contexts:

GL_HEADING = 0b1

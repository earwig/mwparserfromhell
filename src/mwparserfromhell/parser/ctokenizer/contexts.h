/*
Copyright (C) 2012-2017 Ben Kurtovic <ben.kurtovic@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#pragma once

/* Local contexts */

#define LC_TEMPLATE                 0x0000000000000007
#define LC_TEMPLATE_NAME            0x0000000000000001
#define LC_TEMPLATE_PARAM_KEY       0x0000000000000002
#define LC_TEMPLATE_PARAM_VALUE     0x0000000000000004

#define LC_ARGUMENT                 0x0000000000000018
#define LC_ARGUMENT_NAME            0x0000000000000008
#define LC_ARGUMENT_DEFAULT         0x0000000000000010

#define LC_WIKILINK                 0x0000000000000060
#define LC_WIKILINK_TITLE           0x0000000000000020
#define LC_WIKILINK_TEXT            0x0000000000000040

#define LC_EXT_LINK                 0x0000000000000180
#define LC_EXT_LINK_URI             0x0000000000000080
#define LC_EXT_LINK_TITLE           0x0000000000000100

#define LC_HEADING                  0x0000000000007E00
#define LC_HEADING_LEVEL_1          0x0000000000000200
#define LC_HEADING_LEVEL_2          0x0000000000000400
#define LC_HEADING_LEVEL_3          0x0000000000000800
#define LC_HEADING_LEVEL_4          0x0000000000001000
#define LC_HEADING_LEVEL_5          0x0000000000002000
#define LC_HEADING_LEVEL_6          0x0000000000004000

#define LC_TAG                      0x0000000000078000
#define LC_TAG_OPEN                 0x0000000000008000
#define LC_TAG_ATTR                 0x0000000000010000
#define LC_TAG_BODY                 0x0000000000020000
#define LC_TAG_CLOSE                0x0000000000040000

#define LC_STYLE                    0x0000000000780000
#define LC_STYLE_ITALICS            0x0000000000080000
#define LC_STYLE_BOLD               0x0000000000100000
#define LC_STYLE_PASS_AGAIN         0x0000000000200000
#define LC_STYLE_SECOND_PASS        0x0000000000400000

#define LC_DLTERM                   0x0000000000800000

#define LC_SAFETY_CHECK             0x000000007F000000
#define LC_HAS_TEXT                 0x0000000001000000
#define LC_FAIL_ON_TEXT             0x0000000002000000
#define LC_FAIL_NEXT                0x0000000004000000
#define LC_FAIL_ON_LBRACE           0x0000000008000000
#define LC_FAIL_ON_RBRACE           0x0000000010000000
#define LC_FAIL_ON_EQUALS           0x0000000020000000
#define LC_HAS_TEMPLATE             0x0000000040000000

#define LC_TABLE                    0x0000001F80000000
#define LC_TABLE_CELL_LINE_CONTEXTS 0x0000001A00000000
#define LC_TABLE_OPEN               0x0000000080000000
#define LC_TABLE_CELL_OPEN          0x0000000100000000
#define LC_TABLE_CELL_STYLE         0x0000000200000000
#define LC_TABLE_ROW_OPEN           0x0000000400000000
#define LC_TABLE_TD_LINE            0x0000000800000000
#define LC_TABLE_TH_LINE            0x0000001000000000

#define LC_HTML_ENTITY              0x0000002000000000

/* Global contexts */

#define GL_HEADING 0x1

/* Aggregate contexts */

#define AGG_FAIL                                                                       \
    (LC_TEMPLATE | LC_ARGUMENT | LC_WIKILINK | LC_EXT_LINK_TITLE | LC_HEADING |        \
     LC_TAG | LC_STYLE | LC_TABLE_OPEN)
#define AGG_UNSAFE                                                                     \
    (LC_TEMPLATE_NAME | LC_WIKILINK_TITLE | LC_EXT_LINK_TITLE |                        \
     LC_TEMPLATE_PARAM_KEY | LC_ARGUMENT_NAME)
#define AGG_DOUBLE (LC_TEMPLATE_PARAM_KEY | LC_TAG_CLOSE | LC_TABLE_ROW_OPEN)
#define AGG_NO_WIKILINKS                                                               \
    (LC_TEMPLATE_NAME | LC_ARGUMENT_NAME | LC_WIKILINK_TITLE | LC_EXT_LINK_URI)
#define AGG_NO_EXT_LINKS                                                               \
    (LC_TEMPLATE_NAME | LC_ARGUMENT_NAME | LC_WIKILINK_TITLE | LC_EXT_LINK)

/* Tag contexts */

#define TAG_NAME        0x01
#define TAG_ATTR_READY  0x02
#define TAG_ATTR_NAME   0x04
#define TAG_ATTR_VALUE  0x08
#define TAG_QUOTED      0x10
#define TAG_NOTE_SPACE  0x20
#define TAG_NOTE_EQUALS 0x40
#define TAG_NOTE_QUOTE  0x80

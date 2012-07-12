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

from mwparserfromhell.nodes import Template, Text
from mwparserfromhell.nodes.extras import Parameter
from mwparserfromhell.wikicode import Wikicode

__all__ = ["DemoParser"]

class DemoParser(object):
    def _tokenize(self, text):
        return text

    def parse(self, text):
        text = u"This is a {{test}} message with a {{template|with|foo={{params}}}}."

        node1 = Text(u"This is a ")
        node2 = Template(Wikicode([Text(u"test")]))
        node3 = Text(u" message with a ")
        node4_param1_name = Wikicode([Text(u"1")])
        node4_param1_value = Wikicode([Text(u"with")])
        node4_param1 = Parameter(node4_param1_name, node4_param1_value, showkey=False)
        node4_param2_name = Wikicode([Text(u"foo")])
        node4_param2_value = Wikicode([Template(Wikicode([Text(u"params")]))])
        node4_param2 = Parameter(node4_param2_name, node4_param2_value, showkey=True)
        node4 = Template(Wikicode([Text(u"template")]), [node4_param1, node4_param2])
        node5 = Text(u".")
        parsed = Wikicode([node1, node2, node3, node4, node5])
        return parsed

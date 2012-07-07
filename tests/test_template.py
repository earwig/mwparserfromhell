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

from itertools import permutations
import unittest

from mwparserfromhell.parameter import Parameter
from mwparserfromhell.template import Template

class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.name = "foo"
        self.bar = Parameter("1", "bar")
        self.baz = Parameter("2", "baz")
        self.eggs = Parameter("eggs", "spam")
        self.params = [self.bar, self.baz, self.eggs]

    def test_construct(self):
        Template(self.name)
        Template(self.name, self.params)
        Template(name=self.name)
        Template(name=self.name, params=self.params)

    def test_name(self):
        templates = [
            Template(self.name),
            Template(self.name, self.params),
            Template(name=self.name),
            Template(name=self.name, params=self.params)
        ]
        for template in templates:
            self.assertEqual(template.name, self.name)

    def test_params(self):
        for template in (Template(self.name), Template(name=self.name)):
            self.assertEqual(template.params, [])
        for template in (Template(self.name, self.params),
                         Template(name=self.name, params=self.params)):
            self.assertEqual(template.params, self.params)

    def test_getitem(self):
        template = Template(name=self.name, params=self.params)
        self.assertIs(template[0], self.bar)
        self.assertIs(template[1], self.baz)
        self.assertIs(template[2], self.eggs)
        self.assertIs(template["1"], self.bar)
        self.assertIs(template["2"], self.baz)
        self.assertIs(template["eggs"], self.eggs)

    def test_render(self):
        tests = [
            (Template(self.name), "{{foo}}"),
            (Template(self.name, self.params), "{{foo|bar|baz|eggs=spam}}")
        ]
        for template, rendered in tests:
            self.assertEqual(template.render(), rendered)

    def test_repr(self):
        correct1=  'Template(name=foo, params={})'
        correct2 = 'Template(name=foo, params={"1": "bar", "2": "baz", "eggs": "spam"})'
        tests = [(Template(self.name), correct1),
                 (Template(self.name, self.params), correct2)]
        for template, correct in tests:
            self.assertEqual(repr(template), correct)
            self.assertEqual(str(template), correct)

    def test_cmp(self):
        tmp1 = Template(self.name)
        tmp2 = Template(name=self.name)
        tmp3 = Template(self.name, [])
        tmp4 = Template(name=self.name, params=[])
        tmp5 = Template(self.name, self.params)
        tmp6 = Template(name=self.name, params=self.params)

        for tmpA, tmpB in permutations((tmp1, tmp2, tmp3, tmp4), 2):
            self.assertEqual(tmpA, tmpB)

        for tmpA, tmpB in permutations((tmp5, tmp6), 2):
            self.assertEqual(tmpA, tmpB)

        for tmpA in (tmp5, tmp6):
            for tmpB in (tmp1, tmp2, tmp3, tmp4):
                self.assertNotEqual(tmpA, tmpB)
                self.assertNotEqual(tmpB, tmpA)

if __name__ == "__main__":
    unittest.main(verbosity=2)

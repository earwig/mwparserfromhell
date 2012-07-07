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

import unittest

from mwparserfromhell.parameter import Parameter
from mwparserfromhell.template import Template

class TestParameter(unittest.TestCase):
    def setUp(self):
        self.name = "foo"
        self.value1 = "bar"
        self.value2 = "{{spam}}"
        self.value3 = "bar{{spam}}"
        self.value4 = "embedded {{eggs|spam|baz=buz}} {{goes}} here"
        self.templates2 = [Template("spam")]
        self.templates3 = [Template("spam")]
        self.templates4 = [Template("eggs", [Parameter("1", "spam"),
                                             Parameter("baz", "buz")]),
                           Template("goes")]

    def test_construct(self):
        Parameter(self.name, self.value1)
        Parameter(self.name, self.value2, self.templates2)
        Parameter(name=self.name, value=self.value3)
        Parameter(name=self.name, value=self.value4, templates=self.templates4)

    def test_name(self):
        params = [
            Parameter(self.name, self.value1),
            Parameter(self.name, self.value2, self.templates2),
            Parameter(name=self.name, value=self.value3),
            Parameter(name=self.name, value=self.value4,
                      templates=self.templates4)
        ]
        for param in params:
            self.assertEqual(param.name, self.name)

    def test_value(self):
        tests = [
            (Parameter(self.name, self.value1), self.value1),
            (Parameter(self.name, self.value2, self.templates2), self.value2),
            (Parameter(name=self.name, value=self.value3), self.value3),
            (Parameter(name=self.name, value=self.value4,
                       templates=self.templates4), self.value4)
        ]
        for param, correct in tests:
            self.assertEqual(param.value, correct)

    def test_templates(self):
        tests = [
            (Parameter(self.name, self.value3, self.templates3),
             self.templates3),
            (Parameter(name=self.name, value=self.value4,
                       templates=self.templates4), self.templates4)
        ]
        for param, correct in tests:
            self.assertEqual(param.templates, correct)

    def test_magic(self):
        params = [Parameter(self.name, self.value1),
                  Parameter(self.name, self.value2, self.templates2),
                  Parameter(self.name, self.value3, self.templates3),
                  Parameter(self.name, self.value4, self.templates4)]
        for param in params:
            self.assertEqual(repr(param), repr(param.value))
            self.assertEqual(str(param), str(param.value))
            self.assertIs(param < "eggs", param.value < "eggs")
            self.assertIs(param <= "bar{{spam}}", param.value <= "bar{{spam}}")
            self.assertIs(param == "bar", param.value == "bar")
            self.assertIs(param != "bar", param.value != "bar")
            self.assertIs(param > "eggs", param.value > "eggs")
            self.assertIs(param >= "bar{{spam}}", param.value >= "bar{{spam}}")
            self.assertEquals(bool(param), bool(param.value))
            self.assertEquals(len(param), len(param.value))
            self.assertEquals(list(param), list(param.value))
            self.assertEquals(param[2], param.value[2])
            self.assertEquals(list(reversed(param)),
                              list(reversed(param.value)))
            self.assertIs("bar" in param, "bar" in param.value)
            self.assertEquals(param + "test", param.value + "test")
            self.assertEquals("test" + param, "test" + param.value)
            # add param
            # add template left
            # add template right

            self.assertEquals(param * 3, Parameter(param.name, param.value * 3,
                                                   param.templates * 3))
            self.assertEquals(3 * param, Parameter(param.name, 3 * param.value,
                                                   3 * param.templates))

            # add param inplace
            # add template implace
            # add str inplace
            # multiply int inplace
            self.assertIsInstance(param, Parameter)
            self.assertIsInstance(param.value, str)

if __name__ == "__main__":
    unittest.main(verbosity=2)

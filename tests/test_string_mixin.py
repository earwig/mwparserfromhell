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

from __future__ import unicode_literals
import unittest

from mwparserfromhell.compat import py3k, str
from mwparserfromhell.string_mixin import StringMixIn

class _FakeString(StringMixIn):
    def __init__(self, data):
        self._data = data

    def __unicode__(self):
        return self._data


class TestStringMixIn(unittest.TestCase):
    """Test cases for the StringMixIn class."""
    def test_docs(self):
        """make sure the various functions of StringMixIn have docstrings"""
        methods = [
            "capitalize", "center", "count", "encode", "endswith",
            "expandtabs", "find", "format", "index", "isalnum", "isalpha",
            "isdecimal", "isdigit", "islower", "isnumeric", "isspace",
            "istitle", "isupper", "join", "ljust", "lstrip", "partition",
            "replace", "rfind", "rindex", "rjust", "rpartition", "rsplit",
            "rstrip", "split", "splitlines", "startswith", "strip", "swapcase",
            "title", "translate", "upper", "zfill"]
        if not py3k:
            methods.append("decode")
        for meth in methods:
            expected = getattr(str, meth).__doc__
            actual = getattr(StringMixIn, meth).__doc__
            self.assertEquals(expected, actual)

    def test_types(self):
        """make sure StringMixIns convert to different types correctly"""
        pass

    def test_comparisons(self):
        """make sure comparison operators work"""
        str1 = _FakeString("this is a fake string")
        str2 = _FakeString("this is a fake string")
        str3 = _FakeString("fake string, this is")
        str4 = "this is a fake string"
        str5 = "fake string, this is"

        self.assertFalse(str1 > str2)
        self.assertTrue(str1 >= str2)
        self.assertTrue(str1 == str2)
        self.assertFalse(str1 != str2)
        self.assertFalse(str1 < str2)
        self.assertTrue(str1 <= str2)

        self.assertTrue(str1 > str3)
        self.assertTrue(str1 >= str3)
        self.assertFalse(str1 == str3)
        self.assertTrue(str1 != str3)
        self.assertFalse(str1 < str3)
        self.assertFalse(str1 <= str3)

        self.assertFalse(str1 > str4)
        self.assertTrue(str1 >= str4)
        self.assertTrue(str1 == str4)
        self.assertFalse(str1 != str4)
        self.assertFalse(str1 < str4)
        self.assertTrue(str1 <= str4)

        self.assertTrue(str1 > str5)
        self.assertTrue(str1 >= str5)
        self.assertFalse(str1 == str5)
        self.assertTrue(str1 != str5)
        self.assertFalse(str1 < str5)
        self.assertFalse(str1 <= str5)

    def test_operators(self):
        """make sure string addition and multiplication work"""
        pass

    def test_other_magics(self):
        """test other magically implemented features, like len() and iter()"""
        pass

    def test_other_methods(self):
        """test the remaining non-magic methods of StringMixIn"""
        pass

if __name__ == "__main__":
    unittest.main(verbosity=2)

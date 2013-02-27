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
from types import GeneratorType
import unittest

from mwparserfromhell.compat import bytes, py3k, range, str
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
        fstr = _FakeString("fake string")
        self.assertEquals(str(fstr), "fake string")
        self.assertEquals(bytes(fstr), b"fake string")
        if py3k:
            self.assertEquals(repr(fstr), "'fake string'")
        else:
            self.assertEquals(repr(fstr), b"u'fake string'")

        self.assertIsInstance(str(fstr), str)
        self.assertIsInstance(bytes(fstr), bytes)
        if py3k:
            self.assertIsInstance(repr(fstr), str)
        else:
            self.assertIsInstance(repr(fstr), bytes)

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

    def test_other_magics(self):
        """test other magically implemented features, like len() and iter()"""
        str1 = _FakeString("fake string")
        str2 = _FakeString("")
        expected = ["f", "a", "k", "e", " ", "s", "t", "r", "i", "n", "g"]

        self.assertTrue(str1)
        self.assertFalse(str2)
        self.assertEquals(11, len(str1))
        self.assertEquals(0, len(str2))

        out = []
        for ch in str1:
            out.append(ch)
        self.assertEquals(expected, out)

        out = []
        for ch in str2:
            out.append(ch)
        self.assertEquals([], out)

        gen1 = iter(str1)
        gen2 = iter(str2)
        self.assertIsInstance(gen1, GeneratorType)
        self.assertIsInstance(gen2, GeneratorType)

        out = []
        for i in range(len(str1)):
            out.append(gen1.next())
        self.assertRaises(StopIteration, gen1.next)
        self.assertEquals(expected, out)
        self.assertRaises(StopIteration, gen2.next)

        self.assertEquals("f", str1[0])
        self.assertEquals(" ", str1[4])
        self.assertEquals("g", str1[10])
        self.assertEquals("n", str1[-2])
        self.assertRaises(IndexError, lambda: str1[11])
        self.assertRaises(IndexError, lambda: str2[0])

        self.assertTrue("k" in str1)
        self.assertTrue("fake" in str1)
        self.assertTrue("str" in str1)
        self.assertTrue("" in str1)
        self.assertTrue("" in str2)
        self.assertFalse("real" in str1)
        self.assertFalse("s" in str2)

    def test_other_methods(self):
        """test the remaining non-magic methods of StringMixIn"""
        fstr = _FakeString("fake string")

        self.assertEquals("Fake string", fstr.capitalize())

        self.assertEquals("  fake string  ", fstr.center(15))
        self.assertEquals("  fake string   ", fstr.center(16))
        self.assertEquals("qqfake stringqq", fstr.center(15, "q"))

        self.assertEquals(1, fstr.count("e"))
        self.assertEquals(0, fstr.count("z"))
        self.assertEquals(1, fstr.count("r", 7))
        self.assertEquals(0, fstr.count("r", 8))
        self.assertEquals(1, fstr.count("r", 5, 9))
        self.assertEquals(0, fstr.count("r", 5, 7))

        if not py3k:
            self.assertEquals(fstr, fstr.decode())
            self.assertEquals("𐌲𐌿𐍄", '\\U00010332\\U0001033f\\U00010344'.decode("unicode_escape"))

        self.assertEquals(b"fake string", fstr.encode())
        self.assertEquals(b"\xF0\x90\x8C\xB2\xF0\x90\x8C\xBF\xF0\x90\x8D\x84",
                          "𐌲𐌿𐍄".encode("utf8"))
        self.assertRaises(UnicodeEncodeError, "𐌲𐌿𐍄".encode)
        self.assertRaises(UnicodeEncodeError, "𐌲𐌿𐍄".encode, "ascii")
        self.assertRaises(UnicodeEncodeError, "𐌲𐌿𐍄".encode, "ascii", "strict")
        self.assertEquals("", "𐌲𐌿𐍄".encode("ascii", "ignore"))

        self.assertTrue(fstr.endswith("ing"))
        self.assertFalse(fstr.endswith("ingh"))

        methods = [
            "expandtabs", "find", "format", "index", "isalnum", "isalpha",
            "isdecimal", "isdigit", "islower", "isnumeric", "isspace",
            "istitle", "isupper", "join", "ljust", "lstrip", "partition",
            "replace", "rfind", "rindex", "rjust", "rpartition", "rsplit",
            "rstrip", "split", "splitlines", "startswith", "strip", "swapcase",
            "title", "translate", "upper", "zfill"]

if __name__ == "__main__":
    unittest.main(verbosity=2)

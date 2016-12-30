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

from __future__ import unicode_literals
from sys import getdefaultencoding
from types import GeneratorType

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mwparserfromhell.compat import bytes, py3k, py32, range, str
from mwparserfromhell.string_mixin import StringMixIn

class _FakeString(StringMixIn):
    def __init__(self, data):
        self._data = data

    def __unicode__(self):
        return self._data


class TestStringMixIn(unittest.TestCase):
    """Test cases for the StringMixIn class."""

    def test_docs(self):
        """make sure the various methods of StringMixIn have docstrings"""
        methods = [
            "capitalize", "center", "count", "encode", "endswith",
            "expandtabs", "find", "format", "index", "isalnum", "isalpha",
            "isdecimal", "isdigit", "islower", "isnumeric", "isspace",
            "istitle", "isupper", "join", "ljust", "lower", "lstrip",
            "partition", "replace", "rfind", "rindex", "rjust", "rpartition",
            "rsplit", "rstrip", "split", "splitlines", "startswith", "strip",
            "swapcase", "title", "translate", "upper", "zfill"]
        if py3k:
            if not py32:
                methods.append("casefold")
            methods.extend(["format_map", "isidentifier", "isprintable",
                            "maketrans"])
        else:
            methods.append("decode")
        for meth in methods:
            expected = getattr("foo", meth).__doc__
            actual = getattr(_FakeString("foo"), meth).__doc__
            self.assertEqual(expected, actual)

    def test_types(self):
        """make sure StringMixIns convert to different types correctly"""
        fstr = _FakeString("fake string")
        self.assertEqual(str(fstr), "fake string")
        self.assertEqual(bytes(fstr), b"fake string")
        if py3k:
            self.assertEqual(repr(fstr), "'fake string'")
        else:
            self.assertEqual(repr(fstr), b"u'fake string'")

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

        self.assertFalse(str5 > str1)
        self.assertFalse(str5 >= str1)
        self.assertFalse(str5 == str1)
        self.assertTrue(str5 != str1)
        self.assertTrue(str5 < str1)
        self.assertTrue(str5 <= str1)

    def test_other_magics(self):
        """test other magically implemented features, like len() and iter()"""
        str1 = _FakeString("fake string")
        str2 = _FakeString("")
        expected = ["f", "a", "k", "e", " ", "s", "t", "r", "i", "n", "g"]

        self.assertTrue(str1)
        self.assertFalse(str2)
        self.assertEqual(11, len(str1))
        self.assertEqual(0, len(str2))

        out = []
        for ch in str1:
            out.append(ch)
        self.assertEqual(expected, out)

        out = []
        for ch in str2:
            out.append(ch)
        self.assertEqual([], out)

        gen1 = iter(str1)
        gen2 = iter(str2)
        self.assertIsInstance(gen1, GeneratorType)
        self.assertIsInstance(gen2, GeneratorType)

        out = []
        for i in range(len(str1)):
            out.append(next(gen1))
        self.assertRaises(StopIteration, next, gen1)
        self.assertEqual(expected, out)
        self.assertRaises(StopIteration, next, gen2)

        self.assertEqual("gnirts ekaf", "".join(list(reversed(str1))))
        self.assertEqual([], list(reversed(str2)))

        self.assertEqual("f", str1[0])
        self.assertEqual(" ", str1[4])
        self.assertEqual("g", str1[10])
        self.assertEqual("n", str1[-2])
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
        str1 = _FakeString("fake string")
        self.assertEqual("Fake string", str1.capitalize())

        self.assertEqual("  fake string  ", str1.center(15))
        self.assertEqual("  fake string   ", str1.center(16))
        self.assertEqual("qqfake stringqq", str1.center(15, "q"))

        self.assertEqual(1, str1.count("e"))
        self.assertEqual(0, str1.count("z"))
        self.assertEqual(1, str1.count("r", 7))
        self.assertEqual(0, str1.count("r", 8))
        self.assertEqual(1, str1.count("r", 5, 9))
        self.assertEqual(0, str1.count("r", 5, 7))

        if not py3k:
            str2 = _FakeString("fo")
            self.assertEqual(str1, str1.decode())
            actual = _FakeString("\\U00010332\\U0001033f\\U00010344")
            self.assertEqual("𐌲𐌿𐍄", actual.decode("unicode_escape"))
            self.assertRaises(UnicodeError, str2.decode, "punycode")
            self.assertEqual("", str2.decode("punycode", "ignore"))

        str3 = _FakeString("𐌲𐌿𐍄")
        actual = b"\xF0\x90\x8C\xB2\xF0\x90\x8C\xBF\xF0\x90\x8D\x84"
        self.assertEqual(b"fake string", str1.encode())
        self.assertEqual(actual, str3.encode("utf-8"))
        self.assertEqual(actual, str3.encode(encoding="utf-8"))
        if getdefaultencoding() == "ascii":
            self.assertRaises(UnicodeEncodeError, str3.encode)
        elif getdefaultencoding() == "utf-8":
            self.assertEqual(actual, str3.encode())
        self.assertRaises(UnicodeEncodeError, str3.encode, "ascii")
        self.assertRaises(UnicodeEncodeError, str3.encode, "ascii", "strict")
        if getdefaultencoding() == "ascii":
            self.assertRaises(UnicodeEncodeError, str3.encode, errors="strict")
        elif getdefaultencoding() == "utf-8":
            self.assertEqual(actual, str3.encode(errors="strict"))
        self.assertEqual(b"", str3.encode("ascii", "ignore"))
        if getdefaultencoding() == "ascii":
            self.assertEqual(b"", str3.encode(errors="ignore"))
        elif getdefaultencoding() == "utf-8":
            self.assertEqual(actual, str3.encode(errors="ignore"))

        self.assertTrue(str1.endswith("ing"))
        self.assertFalse(str1.endswith("ingh"))

        str4 = _FakeString("\tfoobar")
        self.assertEqual("fake string", str1)
        self.assertEqual("        foobar", str4.expandtabs())
        self.assertEqual("    foobar", str4.expandtabs(4))

        self.assertEqual(3, str1.find("e"))
        self.assertEqual(-1, str1.find("z"))
        self.assertEqual(7, str1.find("r", 7))
        self.assertEqual(-1, str1.find("r", 8))
        self.assertEqual(7, str1.find("r", 5, 9))
        self.assertEqual(-1, str1.find("r", 5, 7))

        str5 = _FakeString("foo{0}baz")
        str6 = _FakeString("foo{abc}baz")
        str7 = _FakeString("foo{0}{abc}buzz")
        str8 = _FakeString("{0}{1}")
        self.assertEqual("fake string", str1.format())
        self.assertEqual("foobarbaz", str5.format("bar"))
        self.assertEqual("foobarbaz", str6.format(abc="bar"))
        self.assertEqual("foobarbazbuzz", str7.format("bar", abc="baz"))
        self.assertRaises(IndexError, str8.format, "abc")

        if py3k:
            self.assertEqual("fake string", str1.format_map({}))
            self.assertEqual("foobarbaz", str6.format_map({"abc": "bar"}))
            self.assertRaises(ValueError, str5.format_map, {0: "abc"})

        self.assertEqual(3, str1.index("e"))
        self.assertRaises(ValueError, str1.index, "z")
        self.assertEqual(7, str1.index("r", 7))
        self.assertRaises(ValueError, str1.index, "r", 8)
        self.assertEqual(7, str1.index("r", 5, 9))
        self.assertRaises(ValueError, str1.index, "r", 5, 7)

        str9 = _FakeString("foobar")
        str10 = _FakeString("foobar123")
        str11 = _FakeString("foo bar")
        self.assertTrue(str9.isalnum())
        self.assertTrue(str10.isalnum())
        self.assertFalse(str11.isalnum())

        self.assertTrue(str9.isalpha())
        self.assertFalse(str10.isalpha())
        self.assertFalse(str11.isalpha())

        str12 = _FakeString("123")
        str13 = _FakeString("\u2155")
        str14 = _FakeString("\u00B2")
        self.assertFalse(str9.isdecimal())
        self.assertTrue(str12.isdecimal())
        self.assertFalse(str13.isdecimal())
        self.assertFalse(str14.isdecimal())

        self.assertFalse(str9.isdigit())
        self.assertTrue(str12.isdigit())
        self.assertFalse(str13.isdigit())
        self.assertTrue(str14.isdigit())

        if py3k:
            self.assertTrue(str9.isidentifier())
            self.assertTrue(str10.isidentifier())
            self.assertFalse(str11.isidentifier())
            self.assertFalse(str12.isidentifier())

        str15 = _FakeString("")
        str16 = _FakeString("FooBar")
        self.assertTrue(str9.islower())
        self.assertFalse(str15.islower())
        self.assertFalse(str16.islower())

        self.assertFalse(str9.isnumeric())
        self.assertTrue(str12.isnumeric())
        self.assertTrue(str13.isnumeric())
        self.assertTrue(str14.isnumeric())

        if py3k:
            str16B = _FakeString("\x01\x02")
            self.assertTrue(str9.isprintable())
            self.assertTrue(str13.isprintable())
            self.assertTrue(str14.isprintable())
            self.assertTrue(str15.isprintable())
            self.assertFalse(str16B.isprintable())

        str17 = _FakeString(" ")
        str18 = _FakeString("\t     \t \r\n")
        self.assertFalse(str1.isspace())
        self.assertFalse(str9.isspace())
        self.assertTrue(str17.isspace())
        self.assertTrue(str18.isspace())

        str19 = _FakeString("This Sentence Looks Like A Title")
        str20 = _FakeString("This sentence doesn't LookLikeATitle")
        self.assertFalse(str15.istitle())
        self.assertTrue(str19.istitle())
        self.assertFalse(str20.istitle())

        str21 = _FakeString("FOOBAR")
        self.assertFalse(str9.isupper())
        self.assertFalse(str15.isupper())
        self.assertTrue(str21.isupper())

        self.assertEqual("foobar", str15.join(["foo", "bar"]))
        self.assertEqual("foo123bar123baz", str12.join(("foo", "bar", "baz")))

        self.assertEqual("fake string    ", str1.ljust(15))
        self.assertEqual("fake string     ", str1.ljust(16))
        self.assertEqual("fake stringqqqq", str1.ljust(15, "q"))

        str22 = _FakeString("ß")
        self.assertEqual("", str15.lower())
        self.assertEqual("foobar", str16.lower())
        self.assertEqual("ß", str22.lower())
        if py3k and not py32:
            self.assertEqual("", str15.casefold())
            self.assertEqual("foobar", str16.casefold())
            self.assertEqual("ss", str22.casefold())

        str23 = _FakeString("  fake string  ")
        self.assertEqual("fake string", str1.lstrip())
        self.assertEqual("fake string  ", str23.lstrip())
        self.assertEqual("ke string", str1.lstrip("abcdef"))

        self.assertEqual(("fa", "ke", " string"), str1.partition("ke"))
        self.assertEqual(("fake string", "", ""), str1.partition("asdf"))

        str24 = _FakeString("boo foo moo")
        self.assertEqual("real string", str1.replace("fake", "real"))
        self.assertEqual("bu fu moo", str24.replace("oo", "u", 2))

        self.assertEqual(3, str1.rfind("e"))
        self.assertEqual(-1, str1.rfind("z"))
        self.assertEqual(7, str1.rfind("r", 7))
        self.assertEqual(-1, str1.rfind("r", 8))
        self.assertEqual(7, str1.rfind("r", 5, 9))
        self.assertEqual(-1, str1.rfind("r", 5, 7))

        self.assertEqual(3, str1.rindex("e"))
        self.assertRaises(ValueError, str1.rindex, "z")
        self.assertEqual(7, str1.rindex("r", 7))
        self.assertRaises(ValueError, str1.rindex, "r", 8)
        self.assertEqual(7, str1.rindex("r", 5, 9))
        self.assertRaises(ValueError, str1.rindex, "r", 5, 7)

        self.assertEqual("    fake string", str1.rjust(15))
        self.assertEqual("     fake string", str1.rjust(16))
        self.assertEqual("qqqqfake string", str1.rjust(15, "q"))

        self.assertEqual(("fa", "ke", " string"), str1.rpartition("ke"))
        self.assertEqual(("", "", "fake string"), str1.rpartition("asdf"))

        str25 = _FakeString("   this is a   sentence with  whitespace ")
        actual = ["this", "is", "a", "sentence", "with", "whitespace"]
        self.assertEqual(actual, str25.rsplit())
        self.assertEqual(actual, str25.rsplit(None))
        actual = ["", "", "", "this", "is", "a", "", "", "sentence", "with",
                  "", "whitespace", ""]
        self.assertEqual(actual, str25.rsplit(" "))
        actual = ["   this is a", "sentence", "with", "whitespace"]
        self.assertEqual(actual, str25.rsplit(None, 3))
        actual = ["   this is a   sentence with", "", "whitespace", ""]
        self.assertEqual(actual, str25.rsplit(" ", 3))
        if py3k and not py32:
            actual = ["   this is a", "sentence", "with", "whitespace"]
            self.assertEqual(actual, str25.rsplit(maxsplit=3))

        self.assertEqual("fake string", str1.rstrip())
        self.assertEqual("  fake string", str23.rstrip())
        self.assertEqual("fake stri", str1.rstrip("ngr"))

        actual = ["this", "is", "a", "sentence", "with", "whitespace"]
        self.assertEqual(actual, str25.split())
        self.assertEqual(actual, str25.split(None))
        actual = ["", "", "", "this", "is", "a", "", "", "sentence", "with",
                  "", "whitespace", ""]
        self.assertEqual(actual, str25.split(" "))
        actual = ["this", "is", "a", "sentence with  whitespace "]
        self.assertEqual(actual, str25.split(None, 3))
        actual = ["", "", "", "this is a   sentence with  whitespace "]
        self.assertEqual(actual, str25.split(" ", 3))
        if py3k and not py32:
            actual = ["this", "is", "a", "sentence with  whitespace "]
            self.assertEqual(actual, str25.split(maxsplit=3))

        str26 = _FakeString("lines\nof\ntext\r\nare\r\npresented\nhere")
        self.assertEqual(["lines", "of", "text", "are", "presented", "here"],
                          str26.splitlines())
        self.assertEqual(["lines\n", "of\n", "text\r\n", "are\r\n",
                           "presented\n", "here"], str26.splitlines(True))

        self.assertTrue(str1.startswith("fake"))
        self.assertFalse(str1.startswith("faker"))

        self.assertEqual("fake string", str1.strip())
        self.assertEqual("fake string", str23.strip())
        self.assertEqual("ke stri", str1.strip("abcdefngr"))

        self.assertEqual("fOObAR", str16.swapcase())

        self.assertEqual("Fake String", str1.title())

        if py3k:
            table1 = StringMixIn.maketrans({97: "1", 101: "2", 105: "3",
                                            111: "4", 117: "5"})
            table2 = StringMixIn.maketrans("aeiou", "12345")
            table3 = StringMixIn.maketrans("aeiou", "12345", "rts")
            self.assertEqual("f1k2 str3ng", str1.translate(table1))
            self.assertEqual("f1k2 str3ng", str1.translate(table2))
            self.assertEqual("f1k2 3ng", str1.translate(table3))
        else:
            table = {97: "1", 101: "2", 105: "3", 111: "4", 117: "5"}
            self.assertEqual("f1k2 str3ng", str1.translate(table))

        self.assertEqual("", str15.upper())
        self.assertEqual("FOOBAR", str16.upper())

        self.assertEqual("123", str12.zfill(3))
        self.assertEqual("000123", str12.zfill(6))

if __name__ == "__main__":
    unittest.main(verbosity=2)

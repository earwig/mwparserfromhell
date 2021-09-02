# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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
Test cases for the StringMixIn class.
"""

import sys
from types import GeneratorType

import pytest

from mwparserfromhell.string_mixin import StringMixIn


class _FakeString(StringMixIn):
    def __init__(self, data):
        self._data = data

    def __str__(self):
        return self._data


@pytest.mark.parametrize(
    "method",
    [
        "capitalize",
        "casefold",
        "center",
        "count",
        "encode",
        "endswith",
        "expandtabs",
        "find",
        "format",
        "format_map",
        "index",
        "isalnum",
        "isalpha",
        "isdecimal",
        "isdigit",
        "isidentifier",
        "islower",
        "isnumeric",
        "isprintable",
        "isspace",
        "istitle",
        "isupper",
        "join",
        "ljust",
        "lower",
        "lstrip",
        "maketrans",
        "partition",
        "replace",
        "rfind",
        "rindex",
        "rjust",
        "rpartition",
        "rsplit",
        "rstrip",
        "split",
        "splitlines",
        "startswith",
        "strip",
        "swapcase",
        "title",
        "translate",
        "upper",
        "zfill",
    ],
)
def test_docs(method):
    """make sure the various methods of StringMixIn have docstrings"""
    expected = getattr("foo", method).__doc__
    actual = getattr(_FakeString("foo"), method).__doc__
    assert expected == actual


def test_types():
    """make sure StringMixIns convert to different types correctly"""
    fstr = _FakeString("fake string")
    assert str(fstr) == "fake string"
    assert bytes(fstr) == b"fake string"
    assert repr(fstr) == "'fake string'"

    assert isinstance(str(fstr), str)
    assert isinstance(bytes(fstr), bytes)
    assert isinstance(repr(fstr), str)


def test_comparisons():
    """make sure comparison operators work"""
    str1 = _FakeString("this is a fake string")
    str2 = _FakeString("this is a fake string")
    str3 = _FakeString("fake string, this is")
    str4 = "this is a fake string"
    str5 = "fake string, this is"

    assert str1 <= str2
    assert str1 >= str2
    assert str1 == str2
    assert str1 == str2
    assert str1 >= str2
    assert str1 <= str2

    assert str1 > str3
    assert str1 >= str3
    assert str1 != str3
    assert str1 != str3
    assert str1 >= str3
    assert str1 > str3

    assert str1 <= str4
    assert str1 >= str4
    assert str1 == str4
    assert str1 == str4
    assert str1 >= str4
    assert str1 <= str4

    assert str5 <= str1
    assert str5 < str1
    assert str5 != str1
    assert str5 != str1
    assert str5 < str1
    assert str5 <= str1


def test_other_magics():
    """test other magically implemented features, like len() and iter()"""
    str1 = _FakeString("fake string")
    str2 = _FakeString("")
    expected = ["f", "a", "k", "e", " ", "s", "t", "r", "i", "n", "g"]

    assert bool(str1) is True
    assert bool(str2) is False
    assert 11 == len(str1)
    assert 0 == len(str2)

    out = []
    for ch in str1:
        out.append(ch)
    assert expected == out

    out = []
    for ch in str2:
        out.append(ch)
    assert [] == out

    gen1 = iter(str1)
    gen2 = iter(str2)
    assert isinstance(gen1, GeneratorType)
    assert isinstance(gen2, GeneratorType)

    out = []
    for _ in range(len(str1)):
        out.append(next(gen1))
    with pytest.raises(StopIteration):
        next(gen1)
    assert expected == out
    with pytest.raises(StopIteration):
        next(gen2)

    assert "gnirts ekaf" == "".join(list(reversed(str1)))
    assert [] == list(reversed(str2))

    assert "f" == str1[0]
    assert " " == str1[4]
    assert "g" == str1[10]
    assert "n" == str1[-2]
    with pytest.raises(IndexError):
        str1[11]
    with pytest.raises(IndexError):
        str2[0]

    assert "k" in str1
    assert "fake" in str1
    assert "str" in str1
    assert "" in str1
    assert "" in str2
    assert "real" not in str1
    assert "s" not in str2


def test_other_methods():
    """test the remaining non-magic methods of StringMixIn"""
    str1 = _FakeString("fake string")
    assert "Fake string" == str1.capitalize()

    assert "  fake string  " == str1.center(15)
    assert "  fake string   " == str1.center(16)
    assert "qqfake stringqq" == str1.center(15, "q")

    assert 1 == str1.count("e")
    assert 0 == str1.count("z")
    assert 1 == str1.count("r", 7)
    assert 0 == str1.count("r", 8)
    assert 1 == str1.count("r", 5, 9)
    assert 0 == str1.count("r", 5, 7)

    str3 = _FakeString("𐌲𐌿𐍄")
    actual = b"\xF0\x90\x8C\xB2\xF0\x90\x8C\xBF\xF0\x90\x8D\x84"
    assert b"fake string" == str1.encode()
    assert actual == str3.encode("utf-8")
    assert actual == str3.encode(encoding="utf-8")
    if sys.getdefaultencoding() == "ascii":
        with pytest.raises(UnicodeEncodeError):
            str3.encode()
    elif sys.getdefaultencoding() == "utf-8":
        assert actual == str3.encode()
    with pytest.raises(UnicodeEncodeError):
        str3.encode("ascii")
    with pytest.raises(UnicodeEncodeError):
        str3.encode("ascii", "strict")
    if sys.getdefaultencoding() == "ascii":
        with pytest.raises(UnicodeEncodeError):
            str3.encode("ascii", errors="strict")
    elif sys.getdefaultencoding() == "utf-8":
        assert actual == str3.encode(errors="strict")
    assert b"" == str3.encode("ascii", "ignore")
    if sys.getdefaultencoding() == "ascii":
        assert b"" == str3.encode(errors="ignore")
    elif sys.getdefaultencoding() == "utf-8":
        assert actual == str3.encode(errors="ignore")

    assert str1.endswith("ing") is True
    assert str1.endswith("ingh") is False

    str4 = _FakeString("\tfoobar")
    assert "fake string" == str1
    assert "        foobar" == str4.expandtabs()
    assert "    foobar" == str4.expandtabs(4)

    assert 3 == str1.find("e")
    assert -1 == str1.find("z")
    assert 7 == str1.find("r", 7)
    assert -1 == str1.find("r", 8)
    assert 7 == str1.find("r", 5, 9)
    assert -1 == str1.find("r", 5, 7)

    str5 = _FakeString("foo{0}baz")
    str6 = _FakeString("foo{abc}baz")
    str7 = _FakeString("foo{0}{abc}buzz")
    str8 = _FakeString("{0}{1}")
    assert "fake string" == str1.format()
    assert "foobarbaz" == str5.format("bar")
    assert "foobarbaz" == str6.format(abc="bar")
    assert "foobarbazbuzz" == str7.format("bar", abc="baz")
    with pytest.raises(IndexError):
        str8.format("abc")

    assert "fake string" == str1.format_map({})
    assert "foobarbaz" == str6.format_map({"abc": "bar"})
    with pytest.raises(ValueError):
        str5.format_map({0: "abc"})

    assert 3 == str1.index("e")
    with pytest.raises(ValueError):
        str1.index("z")
    assert 7 == str1.index("r", 7)
    with pytest.raises(ValueError):
        str1.index("r", 8)
    assert 7 == str1.index("r", 5, 9)
    with pytest.raises(ValueError):
        str1.index("r", 5, 7)
    str9 = _FakeString("foobar")
    str10 = _FakeString("foobar123")
    str11 = _FakeString("foo bar")
    assert str9.isalnum() is True
    assert str10.isalnum() is True
    assert str11.isalnum() is False

    assert str9.isalpha() is True
    assert str10.isalpha() is False
    assert str11.isalpha() is False

    str12 = _FakeString("123")
    str13 = _FakeString("\u2155")
    str14 = _FakeString("\u00B2")
    assert str9.isdecimal() is False
    assert str12.isdecimal() is True
    assert str13.isdecimal() is False
    assert str14.isdecimal() is False

    assert str9.isdigit() is False
    assert str12.isdigit() is True
    assert str13.isdigit() is False
    assert str14.isdigit() is True

    assert str9.isidentifier() is True
    assert str10.isidentifier() is True
    assert str11.isidentifier() is False
    assert str12.isidentifier() is False

    str15 = _FakeString("")
    str16 = _FakeString("FooBar")
    assert str9.islower() is True
    assert str15.islower() is False
    assert str16.islower() is False

    assert str9.isnumeric() is False
    assert str12.isnumeric() is True
    assert str13.isnumeric() is True
    assert str14.isnumeric() is True

    str16B = _FakeString("\x01\x02")
    assert str9.isprintable() is True
    assert str13.isprintable() is True
    assert str14.isprintable() is True
    assert str15.isprintable() is True
    assert str16B.isprintable() is False

    str17 = _FakeString(" ")
    str18 = _FakeString("\t     \t \r\n")
    assert str1.isspace() is False
    assert str9.isspace() is False
    assert str17.isspace() is True
    assert str18.isspace() is True

    str19 = _FakeString("This Sentence Looks Like A Title")
    str20 = _FakeString("This sentence doesn't LookLikeATitle")
    assert str15.istitle() is False
    assert str19.istitle() is True
    assert str20.istitle() is False

    str21 = _FakeString("FOOBAR")
    assert str9.isupper() is False
    assert str15.isupper() is False
    assert str21.isupper() is True

    assert "foobar" == str15.join(["foo", "bar"])
    assert "foo123bar123baz" == str12.join(("foo", "bar", "baz"))

    assert "fake string    " == str1.ljust(15)
    assert "fake string     " == str1.ljust(16)
    assert "fake stringqqqq" == str1.ljust(15, "q")

    str22 = _FakeString("ß")
    assert "" == str15.lower()
    assert "foobar" == str16.lower()
    assert "ß" == str22.lower()
    assert "" == str15.casefold()
    assert "foobar" == str16.casefold()
    assert "ss" == str22.casefold()

    str23 = _FakeString("  fake string  ")
    assert "fake string" == str1.lstrip()
    assert "fake string  " == str23.lstrip()
    assert "ke string" == str1.lstrip("abcdef")

    assert ("fa", "ke", " string") == str1.partition("ke")
    assert ("fake string", "", "") == str1.partition("asdf")

    str24 = _FakeString("boo foo moo")
    assert "real string" == str1.replace("fake", "real")
    assert "bu fu moo" == str24.replace("oo", "u", 2)

    assert 3 == str1.rfind("e")
    assert -1 == str1.rfind("z")
    assert 7 == str1.rfind("r", 7)
    assert -1 == str1.rfind("r", 8)
    assert 7 == str1.rfind("r", 5, 9)
    assert -1 == str1.rfind("r", 5, 7)

    assert 3 == str1.rindex("e")
    with pytest.raises(ValueError):
        str1.rindex("z")
    assert 7 == str1.rindex("r", 7)
    with pytest.raises(ValueError):
        str1.rindex("r", 8)
    assert 7 == str1.rindex("r", 5, 9)
    with pytest.raises(ValueError):
        str1.rindex("r", 5, 7)
    assert "    fake string" == str1.rjust(15)
    assert "     fake string" == str1.rjust(16)
    assert "qqqqfake string" == str1.rjust(15, "q")

    assert ("fa", "ke", " string") == str1.rpartition("ke")
    assert ("", "", "fake string") == str1.rpartition("asdf")

    str25 = _FakeString("   this is a   sentence with  whitespace ")
    actual = ["this", "is", "a", "sentence", "with", "whitespace"]
    assert actual == str25.rsplit()
    assert actual == str25.rsplit(None)
    actual = [
        "",
        "",
        "",
        "this",
        "is",
        "a",
        "",
        "",
        "sentence",
        "with",
        "",
        "whitespace",
        "",
    ]
    assert actual == str25.rsplit(" ")
    actual = ["   this is a", "sentence", "with", "whitespace"]
    assert actual == str25.rsplit(None, 3)
    actual = ["   this is a   sentence with", "", "whitespace", ""]
    assert actual == str25.rsplit(" ", 3)
    actual = ["   this is a", "sentence", "with", "whitespace"]
    assert actual == str25.rsplit(maxsplit=3)

    assert "fake string" == str1.rstrip()
    assert "  fake string" == str23.rstrip()
    assert "fake stri" == str1.rstrip("ngr")

    actual = ["this", "is", "a", "sentence", "with", "whitespace"]
    assert actual == str25.split()
    assert actual == str25.split(None)
    actual = [
        "",
        "",
        "",
        "this",
        "is",
        "a",
        "",
        "",
        "sentence",
        "with",
        "",
        "whitespace",
        "",
    ]
    assert actual == str25.split(" ")
    actual = ["this", "is", "a", "sentence with  whitespace "]
    assert actual == str25.split(None, 3)
    actual = ["", "", "", "this is a   sentence with  whitespace "]
    assert actual == str25.split(" ", 3)
    actual = ["this", "is", "a", "sentence with  whitespace "]
    assert actual == str25.split(maxsplit=3)

    str26 = _FakeString("lines\nof\ntext\r\nare\r\npresented\nhere")
    assert ["lines", "of", "text", "are", "presented", "here"] == str26.splitlines()
    assert [
        "lines\n",
        "of\n",
        "text\r\n",
        "are\r\n",
        "presented\n",
        "here",
    ] == str26.splitlines(True)

    assert str1.startswith("fake") is True
    assert str1.startswith("faker") is False

    assert "fake string" == str1.strip()
    assert "fake string" == str23.strip()
    assert "ke stri" == str1.strip("abcdefngr")

    assert "fOObAR" == str16.swapcase()

    assert "Fake String" == str1.title()

    table1 = StringMixIn.maketrans({97: "1", 101: "2", 105: "3", 111: "4", 117: "5"})
    table2 = StringMixIn.maketrans("aeiou", "12345")
    table3 = StringMixIn.maketrans("aeiou", "12345", "rts")
    assert "f1k2 str3ng" == str1.translate(table1)
    assert "f1k2 str3ng" == str1.translate(table2)
    assert "f1k2 3ng" == str1.translate(table3)

    assert "" == str15.upper()
    assert "FOOBAR" == str16.upper()

    assert "123" == str12.zfill(3)
    assert "000123" == str12.zfill(6)

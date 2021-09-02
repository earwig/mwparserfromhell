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
Test cases for the Token class and its subclasses.
"""

import pytest

from mwparserfromhell.parser import tokens


@pytest.mark.parametrize("name", tokens.__all__)
def test_issubclass(name):
    """check that all classes within the tokens module are really Tokens"""
    klass = getattr(tokens, name)
    assert issubclass(klass, tokens.Token) is True
    assert isinstance(klass(), klass)
    assert isinstance(klass(), tokens.Token)


def test_attributes():
    """check that Token attributes can be managed properly"""
    token1 = tokens.Token()
    token2 = tokens.Token(foo="bar", baz=123)

    assert "bar" == token2.foo
    assert 123 == token2.baz
    assert token1.foo is None
    assert token2.bar is None

    token1.spam = "eggs"
    token2.foo = "ham"
    del token2.baz

    assert "eggs" == token1.spam
    assert "ham" == token2.foo
    assert token2.baz is None
    with pytest.raises(KeyError):
        token2.__delattr__("baz")


def test_repr():
    """check that repr() on a Token works as expected"""
    token1 = tokens.Token()
    token2 = tokens.Token(foo="bar", baz=123)
    token3 = tokens.Text(text="earwig" * 100)
    hundredchars = ("earwig" * 100)[:97] + "..."

    assert "Token()" == repr(token1)
    assert repr(token2) in ("Token(foo='bar', baz=123)", "Token(baz=123, foo='bar')")
    assert "Text(text='" + hundredchars + "')" == repr(token3)


def test_equality():
    """check that equivalent tokens are considered equal"""
    token1 = tokens.Token()
    token2 = tokens.Token()
    token3 = tokens.Token(foo="bar", baz=123)
    token4 = tokens.Text(text="asdf")
    token5 = tokens.Text(text="asdf")
    token6 = tokens.TemplateOpen(text="asdf")

    assert token1 == token2
    assert token2 == token1
    assert token4 == token5
    assert token5 == token4
    assert token1 != token3
    assert token2 != token3
    assert token4 != token6
    assert token5 != token6


@pytest.mark.parametrize(
    "token",
    [tokens.Token(), tokens.Token(foo="bar", baz=123), tokens.Text(text="earwig")],
)
def test_repr_equality(token):
    """check that eval(repr(token)) == token"""
    assert token == eval(repr(token), vars(tokens))

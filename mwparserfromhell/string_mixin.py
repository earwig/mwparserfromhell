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

__all__ = ["StringMixIn"]

def inheritdoc(method):
    method.__doc__ = getattr(unicode, method.func_name).__doc__
    return method


class StringMixIn(object):
    def __str__(self):
        return unicode(self).encode("utf8")

    def __repr__(self):
        return repr(unicode(self))

    def __lt__(self, other):
        if isinstance(other, StringMixIn):
            return unicode(self) < unicode(other)
        return unicode(self) < other

    def __le__(self, other):
        if isinstance(other, StringMixIn):
            return unicode(self) <= unicode(other)
        return unicode(self) <= other

    def __eq__(self, other):
        if isinstance(other, StringMixIn):
            return unicode(self) == unicode(other)
        return unicode(self) == other

    def __ne__(self, other):
        if isinstance(other, StringMixIn):
            return unicode(self) != unicode(other)
        return unicode(self) != other

    def __gt__(self, other):
        if isinstance(other, StringMixIn):
            return unicode(self) > unicode(other)
        return unicode(self) > other

    def __ge__(self, other):
        if isinstance(other, StringMixIn):
            return unicode(self) >= unicode(other)
        return unicode(self) >= other

    def __nonzero__(self):
        return bool(unicode(self))

    def __unicode__(self):
        raise NotImplementedError()

    def __len__(self):
        return len(unicode(self))

    def __iter__(self):
        for char in unicode(self):
            yield char

    def __getitem__(self, key):
        return unicode(self)[key]

    def __contains__(self, item):
        if isinstance(item, StringMixIn):
            return unicode(item) in unicode(self)
        return item in unicode(self)

    @inheritdoc
    def capitalize(self):
        return unicode(self).capitalize()

    @inheritdoc
    def center(self, width, fillchar=None):
        return unicode(self).center(width, fillchar)

    @inheritdoc
    def count(self, sub=None, start=None, end=None):
        return unicode(self).count(sub, start, end)

    @inheritdoc
    def decode(self, encoding=None, errors=None):
        return unicode(self).decode(encoding, errors)

    @inheritdoc
    def encode(self, encoding=None, errors=None):
        return unicode(self).encode(encoding, errors)

    @inheritdoc
    def endswith(self, prefix, start=None, end=None):
        return unicode(self).endswith(prefix, start, end)

    @inheritdoc
    def expandtabs(self, tabsize=None):
        return unicode(self).expandtabs(tabsize)

    @inheritdoc
    def find(self, sub=None, start=None, end=None):
        return unicode(self).find(sub, start, end)

    @inheritdoc
    def format(self, *args, **kwargs):
        return unicode(self).format(*args, **kwargs)

    @inheritdoc
    def index(self, sub=None, start=None, end=None):
        return unicode(self).index(sub, start, end)

    @inheritdoc
    def isalnum(self):
        return unicode(self).isalnum()

    @inheritdoc
    def isalpha(self):
        return unicode(self).isalpha()

    @inheritdoc
    def isdecimal(self):
        return unicode(self).isdecimal()

    @inheritdoc
    def isdigit(self):
        return unicode(self).isdigit()

    @inheritdoc
    def islower(self):
        return unicode(self).islower()

    @inheritdoc
    def isnumeric(self):
        return unicode(self).isnumeric()

    @inheritdoc
    def isspace(self):
        return unicode(self).isspace()

    @inheritdoc
    def istitle(self):
        return unicode(self).istitle()

    @inheritdoc
    def isupper(self):
        return unicode(self).isupper()

    @inheritdoc
    def join(self, iterable):
        return unicode(self).join(iterable)

    @inheritdoc
    def ljust(self, width, fillchar=None):
        return unicode(self).ljust(width, fillchar)

    @inheritdoc
    def lower(self):
        return unicode(self).lower()

    @inheritdoc
    def lstrip(self, chars=None):
        return unicode(self).lstrip(chars)

    @inheritdoc
    def partition(self, sep):
        return unicode(self).partition(sep)

    @inheritdoc
    def replace(self, old, new, count):
        return unicode(self).replace(old, new, count)

    @inheritdoc
    def rfind(self, sub=None, start=None, end=None):
        return unicode(self).rfind(sub, start, end)

    @inheritdoc
    def rindex(self, sub=None, start=None, end=None):
        return unicode(self).rindex(sub, start, end)

    @inheritdoc
    def rjust(self, width, fillchar=None):
        return unicode(self).rjust(width, fillchar)

    @inheritdoc
    def rpartition(self, sep):
        return unicode(self).rpartition(sep)

    @inheritdoc
    def rsplit(self, sep=None, maxsplit=None):
        return unicode(self).rsplit(sep, maxsplit)

    @inheritdoc
    def rstrip(self, chars=None):
        return unicode(self).rstrip(chars)

    @inheritdoc
    def split(self, sep=None, maxsplit=None):
        return unicode(self).split(sep, maxsplit)

    @inheritdoc
    def splitlines(self, keepends=None):
        return unicode(self).splitlines(keepends)

    @inheritdoc
    def startswith(self, prefix, start=None, end=None):
        return unicode(self).startswith(prefix, start, end)

    @inheritdoc
    def strip(self, chars=None):
        return unicode(self).strip(chars)

    @inheritdoc
    def swapcase(self):
        return unicode(self).swapcase()

    @inheritdoc
    def title(self):
        return unicode(self).title()

    @inheritdoc
    def translate(self, table, deletechars=None):
        return unicode(self).translate(table, deletechars)

    @inheritdoc
    def upper(self):
        return unicode(self).upper()

    @inheritdoc
    def zfill(self, width):
        return unicode(self).zfill(width)


del inheritdoc

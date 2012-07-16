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

class StringMixIn(unicode):
    def __str__(self):
        return unicode(self).encode("utf8")

    def __repr__(self):
        return repr(unicode(self))

    def __unicode__(self):
        raise NotImplementedError()

    def __lt__(self, other):
        if isinstance(other, StringMixin):
            return unicode(self) < unicode(other)
        return unicode(self) < other

    def __le__(self, other):
        if isinstance(other, StringMixin):
            return unicode(self) <= unicode(other)
        return unicode(self) <= other

    def __eq__(self, other):
        if isinstance(other, StringMixin):
            return unicode(self) == unicode(other)
        return unicode(self) == other

    def __ne__(self, other):
        if isinstance(other, StringMixin):
            return unicode(self) != unicode(other)
        return unicode(self) != other

    def __gt__(self, other):
        if isinstance(other, StringMixin):
            return unicode(self) > unicode(other)
        return unicode(self) > other

    def __ge__(self, other):
        if isinstance(other, StringMixin):
            return unicode(self) >= unicode(other)
        return unicode(self) >= other

    def __nonzero__(self):
        return bool(unicode(self))

    def __len__(self):
        return len(unicode(self))

    def __iter__(self):
        for char in unicode(self):
            yield char

    def __getitem__(self, index):
        return unicode(self)[index]

    def __contains__(self, item):
        if isinstance(item, StringMixIn):
            return unicode(item) in unicode(self)
        return item in unicode(self)

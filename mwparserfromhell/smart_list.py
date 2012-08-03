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

import sys

__all__ = ["SmartList"]

class SmartList(list):
    def __init__(self, iterable=None):
        if iterable:
            super(SmartList, self).__init__(iterable)
        else:
            super(SmartList, self).__init__()
        self._children = {}

    def __getitem__(self, key):
        if not isinstance(key, slice):
            return super(SmartList, self).__getitem__(key)
        sliceinfo = [key.start, key.stop, 1 if not key.step else key.step]
        child = _ListProxy(self, sliceinfo)
        self._children[id(child)] = (child, sliceinfo)
        return child

    def __setitem__(self, key, item):
        if not isinstance(key, slice):
            return super(SmartList, self).__setitem__(key, item)
        item = list(item)
        super(SmartList, self).__setitem__(key, item)
        diff = len(item) - key.stop + key.start
        if diff:
            for child, (start, stop, step) in self._children.itervalues():
                if start >= key.stop:
                    self._children[id(child)][1][0] += diff
                if stop >= key.stop and stop != sys.maxint:
                    self._children[id(child)][1][1] += diff

    __delitem__

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def __setslice__(self, start, stop, iterable):
        self.__setitem__(slice(start, stop), iterable)

    def __delslice__(self, start, stop):
        self.__delitem__(slice(start, stop))

    __add__

    __radd__

    __iadd__

    __mul__

    __rmul__

    __imul__

    def append(self, item):
        super(SmartList, self).append(item)
        for child, (start, stop, step) in self._children.itervalues():
            if stop >= len(self) - 1 and stop != sys.maxint:
                self._children[id(child)][1][1] += 1

    count

    index

    extend

    insert

    pop

    remove

    reverse

    sort


class _ListProxy(list):
    def __init__(self, parent, sliceinfo):
        super(_ListProxy, self).__init__()
        self._parent = parent
        self._sliceinfo = sliceinfo

    def __repr__(self):
        return repr(self._render())

    __lt__

    __le__

    __eq__

    __ne__

    __gt__

    __ge__

    __nonzero__

    def __len__(self):
        return (self._stop - self._start) / self._step

    def __getitem__(self, key):
        return self._render()[key]

    def __setitem__(self, key, item):
        if isinstance(key, slice):
            adjusted = slice(key.start + self._start, key.stop + self._stop,
                             key.step)
            self._parent[adjusted] = item
        else:
            self._parent[self._start + index] = item

    __delitem__

    def __iter__(self):
        i = self._start
        while i < self._stop:
            yield self._parent[i]
            i += self._step

    def __reversed__(self):
        i = self._stop - 1
        while i >= self._start:
            yield self._parent[i]
            i -= self._step

    def __contains__(self, item):
        return item in self._render()

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def __setslice__(self, start, stop, iterable):
        self.__setitem__(slice(start, stop), iterable)

    def __delslice__(self, start, stop):
        self.__delitem__(slice(start, stop))

    __add__

    __radd__

    __iadd__

    __mul__

    __rmul__

    __imul__

    @property
    def _start(self):
        return self._sliceinfo[0]

    @property
    def _stop(self):
        return self._sliceinfo[1]

    @property
    def _step(self):
        return self._sliceinfo[2]

    def _render(self):
        return self._parent[self._start:self._stop:self._step]

    def append(self, item):
        self._parent.insert(self._stop, item)

    def count(self, item):
        return self._render().count(item)

    def index(self, item, start=None, stop=None):
        if start is not None:
            if stop is not None:
                return self._render().index(item, start, stop)
            return self._render().index(item, start)
        return self._render().index(item)

    def extend(self, item):
        self._parent[self._stop:self._stop] = item

    def insert(self, index, item):
        self._parent.insert(self._start + index, item)

    pop

    remove

    def reverse(self):
        item = self._render()
        item.reverse()
        self._parent[self._start:self._stop:self._step] = item

    def sort(self, cmp=None, key=None, reverse=None):
        item = self._render()
        if cmp is not None:
            if key is not None:
                if reverse is not None:
                    item.sort(cmp, key, reverse)
                else:
                    item.sort(cmp, key)
            else:
                item.sort(cmp)
        else:
            item.sort()
        self._parent[self._start:self._stop:self._step] = item

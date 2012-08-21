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

from __future__ import unicode_literals

from .compat import maxsize, py3k

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
                if stop >= key.stop and stop != maxsize:
                    self._children[id(child)][1][1] += diff

    def __delitem__(self, key):
        super(SmartList, self).__delitem__(key)
        if not isinstance(key, slice):
            key = slice(key, key + 1)
        diff = key.stop - key.start
        for child, (start, stop, step) in self._children.itervalues():
            if start > key.start:
                self._children[id(child)][1][0] -= diff
            if stop >= key.stop:
                self._children[id(child)][1][1] -= diff

    if not py3k:
        def __getslice__(self, start, stop):
            return self.__getitem__(slice(start, stop))

        def __setslice__(self, start, stop, iterable):
            self.__setitem__(slice(start, stop), iterable)

        def __delslice__(self, start, stop):
            self.__delitem__(slice(start, stop))

    def __add__(self, other):
        return SmartList(list(self) + other)

    def __radd__(self, other):
        return SmartList(other + list(self))

    def __iadd__(self, other):
        self.extend(other)
        return self

    def append(self, item):
        head = len(self)
        self[head:head] = [item]

    def extend(self, item):
        head = len(self)
        self[head:head] = item

    def insert(self, index, item):
        self[index:index] = [item]

    def pop(self, index=None):
        if index is None:
            index = len(self) - 1
        item = self[index]
        del self[index]
        return item

    def remove(self, item):
        del self[self.index(item)]

    def reverse(self):
        copy = list(self)
        for child in self._children:
            child._parent = copy
        super(SmartList, self).reverse()

    def sort(self, cmp=None, key=None, reverse=None):
        copy = list(self)
        for child in self._children:
            child._parent = copy
        if cmp is not None:
            if key is not None:
                if reverse is not None:
                    super(SmartList, self).sort(cmp, key, reverse)
                else:
                    super(SmartList, self).sort(cmp, key)
            else:
                super(SmartList, self).sort(cmp)
        else:
            super(SmartList, self).sort()


class _ListProxy(list):
    def __init__(self, parent, sliceinfo):
        super(_ListProxy, self).__init__()
        self._parent = parent
        self._sliceinfo = sliceinfo

    def __repr__(self):
        return repr(self._render())

    def __lt__(self, other):
        if isinstance(other, _ListProxy):
            return self._render() < list(other)
        return self._render() < other

    def __le__(self, other):
        if isinstance(other, _ListProxy):
            return self._render() <= list(other)
        return self._render() <= other

    def __eq__(self, other):
        if isinstance(other, _ListProxy):
            return self._render() == list(other)
        return self._render() == other

    def __ne__(self, other):
        if isinstance(other, _ListProxy):
            return self._render() != list(other)
        return self._render() != other

    def __gt__(self, other):
        if isinstance(other, _ListProxy):
            return self._render() > list(other)
        return self._render() > other

    def __ge__(self, other):
        if isinstance(other, _ListProxy):
            return self._render() >= list(other)
        return self._render() >= other

    if py3k:
        def __bool__(self):
            return bool(self._render())
    else:
        def __nonzero__(self):
            return bool(self._render())

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
            self._parent[self._start + key] = item

    def __delitem__(self, key):
        if isinstance(key, slice):
            adjusted = slice(key.start + self._start, key.stop + self._stop,
                             key.step)
            del self._parent[adjusted]
        else:
            del self._parent[self._start + key]

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

    if not py3k:
        def __getslice__(self, start, stop):
            return self.__getitem__(slice(start, stop))

        def __setslice__(self, start, stop, iterable):
            self.__setitem__(slice(start, stop), iterable)

        def __delslice__(self, start, stop):
            self.__delitem__(slice(start, stop))

    def __add__(self, other):
        return SmartList(list(self) + other)

    def __radd__(self, other):
        return SmartList(other + list(self))

    def __iadd__(self, other):
        self.extend(other)
        return self

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
        return list(self._parent)[self._start:self._stop:self._step]

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

    def pop(self, index=None):
        if index is None:
            index = len(self) - 1
        return self._parent.pop(self._start + index)

    def remove(self, item):
        index = self.index(item)
        del self._parent[index]

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

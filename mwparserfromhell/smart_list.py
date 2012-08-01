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

    def __getslice__(self, start, stop):
        sublist = super(SmartList, self).__getslice__(start, stop)
        sliceinfo = [start, stop, 1]
        child = _ListProxy(self, sliceinfo)
        self._children[id(child)] = (child, sliceinfo)
        return child

    # def __setslice__(self, start, stop):

    def append(self, obj):
        super(SmartList, self).append(obj)
        for child, (start, stop, step) in self._children.itervalues():
            if stop >= len(self) - 1 and stop != sys.maxint:
                self._children[id(child)][1][1] += 1


class _ListProxy(list):
    def __init__(self, parent, sliceinfo):
        super(_ListProxy, self).__init__()
        self._parent = parent
        self._sliceinfo = sliceinfo

    def __len__(self):
        return (self._stop - self._start) / self._step

    def __iter__(self):
        i = self._start
        while i < self._stop:
            yield self._parent[i]
            i += self._step

    def __getitem__(self, index):
        return self._render()[index]

    def __getslice__(self, start, stop):
        return self._render()[start:stop]

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

    def append(self, obj):
        self._parent.insert(self._stop, obj)

    def insert(self, index, obj):
        self._parent.insert(self._start + index, obj)

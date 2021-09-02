# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
# Copyright (C) 2019-2020 Yuri Astrakhan <YuriAstrakhan@gmail.com>
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

from .utils import _SliceNormalizerMixIn, inheritdoc


class ListProxy(_SliceNormalizerMixIn, list):
    """Implement the ``list`` interface by getting elements from a parent.

    This is created by a :class:`.SmartList` object when slicing. It does not
    actually store the list at any time; instead, whenever the list is needed,
    it builds it dynamically using the :meth:`_render` method.
    """

    def __init__(self, parent, sliceinfo):
        super().__init__()
        self._parent = parent
        self._sliceinfo = sliceinfo

    def __repr__(self):
        return repr(self._render())

    def __lt__(self, other):
        if isinstance(other, ListProxy):
            return self._render() < list(other)
        return self._render() < other

    def __le__(self, other):
        if isinstance(other, ListProxy):
            return self._render() <= list(other)
        return self._render() <= other

    def __eq__(self, other):
        if isinstance(other, ListProxy):
            return self._render() == list(other)
        return self._render() == other

    def __ne__(self, other):
        if isinstance(other, ListProxy):
            return self._render() != list(other)
        return self._render() != other

    def __gt__(self, other):
        if isinstance(other, ListProxy):
            return self._render() > list(other)
        return self._render() > other

    def __ge__(self, other):
        if isinstance(other, ListProxy):
            return self._render() >= list(other)
        return self._render() >= other

    def __bool__(self):
        return bool(self._render())

    def __len__(self):
        return max((self._stop - self._start) // self._step, 0)

    def __getitem__(self, key):
        if isinstance(key, slice):
            key = self._normalize_slice(key, clamp=True)
            keystart = min(self._start + key.start, self._stop)
            keystop = min(self._start + key.stop, self._stop)
            adjusted = slice(keystart, keystop, key.step)
            return self._parent[adjusted]
        return self._render()[key]

    def __setitem__(self, key, item):
        if isinstance(key, slice):
            key = self._normalize_slice(key, clamp=True)
            keystart = min(self._start + key.start, self._stop)
            keystop = min(self._start + key.stop, self._stop)
            adjusted = slice(keystart, keystop, key.step)
            self._parent[adjusted] = item
        else:
            length = len(self)
            if key < 0:
                key = length + key
            if key < 0 or key >= length:
                raise IndexError("list assignment index out of range")
            self._parent[self._start + key] = item

    def __delitem__(self, key):
        if isinstance(key, slice):
            key = self._normalize_slice(key, clamp=True)
            keystart = min(self._start + key.start, self._stop)
            keystop = min(self._start + key.stop, self._stop)
            adjusted = slice(keystart, keystop, key.step)
            del self._parent[adjusted]
        else:
            length = len(self)
            if key < 0:
                key = length + key
            if key < 0 or key >= length:
                raise IndexError("list assignment index out of range")
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

    def __add__(self, other):
        return type(self._parent)(list(self) + other)

    def __radd__(self, other):
        return type(self._parent)(other + list(self))

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __mul__(self, other):
        return type(self._parent)(list(self) * other)

    def __rmul__(self, other):
        return type(self._parent)(other * list(self))

    def __imul__(self, other):
        self.extend(list(self) * (other - 1))
        return self

    @property
    def _start(self):
        """The starting index of this list, inclusive."""
        return self._sliceinfo[0]

    @property
    def _stop(self):
        """The ending index of this list, exclusive."""
        if self._sliceinfo[1] is None:
            return len(self._parent)
        return self._sliceinfo[1]

    @property
    def _step(self):
        """The number to increase the index by between items."""
        return self._sliceinfo[2]

    def _render(self):
        """Return the actual list from the stored start/stop/step."""
        return list(self._parent)[self._start : self._stop : self._step]

    @inheritdoc
    def append(self, item):
        self._parent.insert(self._stop, item)

    @inheritdoc
    def count(self, item):
        return self._render().count(item)

    @inheritdoc
    def index(self, item, start=None, stop=None):
        if start is not None:
            if stop is not None:
                return self._render().index(item, start, stop)
            return self._render().index(item, start)
        return self._render().index(item)

    @inheritdoc
    def extend(self, item):
        self._parent[self._stop : self._stop] = item

    @inheritdoc
    def insert(self, index, item):
        if index < 0:
            index = len(self) + index
        self._parent.insert(self._start + index, item)

    @inheritdoc
    def pop(self, index=None):
        length = len(self)
        if index is None:
            index = length - 1
        elif index < 0:
            index = length + index
        if index < 0 or index >= length:
            raise IndexError("pop index out of range")
        return self._parent.pop(self._start + index)

    @inheritdoc
    def remove(self, item):
        index = self.index(item)
        del self._parent[self._start + index]

    @inheritdoc
    def reverse(self):
        item = self._render()
        item.reverse()
        self._parent[self._start : self._stop : self._step] = item

    @inheritdoc
    def sort(self, key=None, reverse=None):
        item = self._render()
        kwargs = {}
        if key is not None:
            kwargs["key"] = key
        if reverse is not None:
            kwargs["reverse"] = reverse
        item.sort(**kwargs)
        self._parent[self._start : self._stop : self._step] = item

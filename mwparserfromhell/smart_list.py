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

"""
This module contains the :class:`.SmartList` type, as well as its
:class:`._ListProxy` child, which together implement a list whose sublists
reflect changes made to the main list, and vice-versa.
"""

from __future__ import unicode_literals
from sys import maxsize
from weakref import ref

from .compat import py3k

__all__ = ["SmartList"]

def inheritdoc(method):
    """Set __doc__ of *method* to __doc__ of *method* in its parent class.

    Since this is used on :class:`.SmartList`, the "parent class" used is
    ``list``. This function can be used as a decorator.
    """
    method.__doc__ = getattr(list, method.__name__).__doc__
    return method


class _SliceNormalizerMixIn(object):
    """MixIn that provides a private method to normalize slices."""

    def _normalize_slice(self, key, clamp=False):
        """Return a slice equivalent to the input *key*, standardized."""
        if key.start is None:
            start = 0
        else:
            start = (len(self) + key.start) if key.start < 0 else key.start
        if key.stop is None or key.stop == maxsize:
            stop = len(self) if clamp else None
        else:
            stop = (len(self) + key.stop) if key.stop < 0 else key.stop
        return slice(start, stop, key.step or 1)


class SmartList(_SliceNormalizerMixIn, list):
    """Implements the ``list`` interface with special handling of sublists.

    When a sublist is created (by ``list[i:j]``), any changes made to this
    list (such as the addition, removal, or replacement of elements) will be
    reflected in the sublist, or vice-versa, to the greatest degree possible.
    This is implemented by having sublists - instances of the
    :class:`._ListProxy` type - dynamically determine their elements by storing
    their slice info and retrieving that slice from the parent. Methods that
    change the size of the list also change the slice info. For example::

        >>> parent = SmartList([0, 1, 2, 3])
        >>> parent
        [0, 1, 2, 3]
        >>> child = parent[2:]
        >>> child
        [2, 3]
        >>> child.append(4)
        >>> child
        [2, 3, 4]
        >>> parent
        [0, 1, 2, 3, 4]
    """

    def __init__(self, iterable=None):
        if iterable:
            super(SmartList, self).__init__(iterable)
        else:
            super(SmartList, self).__init__()
        self._children = {}

    def __getitem__(self, key):
        if not isinstance(key, slice):
            return super(SmartList, self).__getitem__(key)
        key = self._normalize_slice(key, clamp=False)
        sliceinfo = [key.start, key.stop, key.step]
        child = _ListProxy(self, sliceinfo)
        child_ref = ref(child, self._delete_child)
        self._children[id(child_ref)] = (child_ref, sliceinfo)
        return child

    def __setitem__(self, key, item):
        if not isinstance(key, slice):
            return super(SmartList, self).__setitem__(key, item)
        item = list(item)
        super(SmartList, self).__setitem__(key, item)
        key = self._normalize_slice(key, clamp=True)
        diff = len(item) + (key.start - key.stop) // key.step
        if not diff:
            return
        values = self._children.values if py3k else self._children.itervalues
        for child, (start, stop, step) in values():
            if start > key.stop:
                self._children[id(child)][1][0] += diff
            if stop is not None and stop >= key.stop:
                self._children[id(child)][1][1] += diff

    def __delitem__(self, key):
        super(SmartList, self).__delitem__(key)
        if isinstance(key, slice):
            key = self._normalize_slice(key, clamp=True)
        else:
            key = slice(key, key + 1, 1)
        diff = (key.stop - key.start) // key.step
        values = self._children.values if py3k else self._children.itervalues
        for child, (start, stop, step) in values():
            if start > key.start:
                self._children[id(child)][1][0] -= diff
            if stop is not None and stop >= key.stop:
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

    def _delete_child(self, child_ref):
        """Remove a child reference that is about to be garbage-collected."""
        del self._children[id(child_ref)]

    def _detach_children(self):
        """Remove all children and give them independent parent copies."""
        children = [val[0] for val in self._children.values()]
        for child in children:
            child()._parent = list(self)
        self._children.clear()

    @inheritdoc
    def append(self, item):
        head = len(self)
        self[head:head] = [item]

    @inheritdoc
    def extend(self, item):
        head = len(self)
        self[head:head] = item

    @inheritdoc
    def insert(self, index, item):
        self[index:index] = [item]

    @inheritdoc
    def pop(self, index=None):
        if index is None:
            index = len(self) - 1
        item = self[index]
        del self[index]
        return item

    @inheritdoc
    def remove(self, item):
        del self[self.index(item)]

    @inheritdoc
    def reverse(self):
        self._detach_children()
        super(SmartList, self).reverse()

    if py3k:
        @inheritdoc
        def sort(self, key=None, reverse=None):
            self._detach_children()
            kwargs = {}
            if key is not None:
                kwargs["key"] = key
            if reverse is not None:
                kwargs["reverse"] = reverse
            super(SmartList, self).sort(**kwargs)
    else:
        @inheritdoc
        def sort(self, cmp=None, key=None, reverse=None):
            self._detach_children()
            kwargs = {}
            if cmp is not None:
                kwargs["cmp"] = cmp
            if key is not None:
                kwargs["key"] = key
            if reverse is not None:
                kwargs["reverse"] = reverse
            super(SmartList, self).sort(**kwargs)


class _ListProxy(_SliceNormalizerMixIn, list):
    """Implement the ``list`` interface by getting elements from a parent.

    This is created by a :class:`.SmartList` object when slicing. It does not
    actually store the list at any time; instead, whenever the list is needed,
    it builds it dynamically using the :meth:`_render` method.
    """

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
        return (self._stop - self._start) // self._step

    def __getitem__(self, key):
        if isinstance(key, slice):
            key = self._normalize_slice(key, clamp=True)
            keystart = min(self._start + key.start, self._stop)
            keystop = min(self._start + key.stop, self._stop)
            adjusted = slice(keystart, keystop, key.step)
            return self._parent[adjusted]
        else:
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

    def __mul__(self, other):
        return SmartList(list(self) * other)

    def __rmul__(self, other):
        return SmartList(other * list(self))

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
        return list(self._parent)[self._start:self._stop:self._step]

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
        self._parent[self._stop:self._stop] = item

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
        self._parent[self._start:self._stop:self._step] = item

    if py3k:
        @inheritdoc
        def sort(self, key=None, reverse=None):
            item = self._render()
            kwargs = {}
            if key is not None:
                kwargs["key"] = key
            if reverse is not None:
                kwargs["reverse"] = reverse
            item.sort(**kwargs)
            self._parent[self._start:self._stop:self._step] = item
    else:
        @inheritdoc
        def sort(self, cmp=None, key=None, reverse=None):
            item = self._render()
            kwargs = {}
            if cmp is not None:
                kwargs["cmp"] = cmp
            if key is not None:
                kwargs["key"] = key
            if reverse is not None:
                kwargs["reverse"] = reverse
            item.sort(**kwargs)
            self._parent[self._start:self._stop:self._step] = item


del inheritdoc

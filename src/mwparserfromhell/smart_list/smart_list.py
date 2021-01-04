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

from weakref import ref

from .list_proxy import ListProxy
from .utils import _SliceNormalizerMixIn, inheritdoc


class SmartList(_SliceNormalizerMixIn, list):
    """Implements the ``list`` interface with special handling of sublists.

    When a sublist is created (by ``list[i:j]``), any changes made to this
    list (such as the addition, removal, or replacement of elements) will be
    reflected in the sublist, or vice-versa, to the greatest degree possible.
    This is implemented by having sublists - instances of the
    :class:`.ListProxy` type - dynamically determine their elements by storing
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
            super().__init__(iterable)
        else:
            super().__init__()
        self._children = {}

    def __getitem__(self, key):
        if not isinstance(key, slice):
            return super().__getitem__(key)
        key = self._normalize_slice(key, clamp=False)
        sliceinfo = [key.start, key.stop, key.step]
        child = ListProxy(self, sliceinfo)
        child_ref = ref(child, self._delete_child)
        self._children[id(child_ref)] = (child_ref, sliceinfo)
        return child

    def __setitem__(self, key, item):
        if not isinstance(key, slice):
            super().__setitem__(key, item)
            return
        item = list(item)
        super().__setitem__(key, item)
        key = self._normalize_slice(key, clamp=True)
        diff = len(item) + (key.start - key.stop) // key.step
        if not diff:
            return
        for child, (start, stop, _step) in self._children.values():
            if start > key.stop:
                self._children[id(child)][1][0] += diff
            if stop is not None and stop >= key.stop:
                self._children[id(child)][1][1] += diff

    def __delitem__(self, key):
        super().__delitem__(key)
        if isinstance(key, slice):
            key = self._normalize_slice(key, clamp=True)
        else:
            key = slice(key, key + 1, 1)
        diff = (key.stop - key.start) // key.step
        for child, (start, stop, _step) in self._children.values():
            if start > key.start:
                self._children[id(child)][1][0] -= diff
            if stop is not None and stop >= key.stop:
                self._children[id(child)][1][1] -= diff

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
        super().reverse()

    @inheritdoc
    def sort(self, key=None, reverse=None):
        self._detach_children()
        kwargs = {}
        if key is not None:
            kwargs["key"] = key
        if reverse is not None:
            kwargs["reverse"] = reverse
        super().sort(**kwargs)

from _weakref import ref

from .ListProxy import _ListProxy
from .utils import _SliceNormalizerMixIn, inheritdoc
from ..compat import py3k


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

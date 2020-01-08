# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from _weakref import ref
from typing import Tuple

from .utils import inheritdoc
from ..compat import py3k


class ListStore:
    def __init__(self, iterator=None, attach=False):
        if attach:
            self.data = iterator
        else:
            self.data = [] if iterator is None else list(iterator)
        self.slices = {}

    def attach_slice(self, slc):
        slc_ref = ref(slc, self.detach_slice_ref)
        self.slices[id(slc_ref)] = slc_ref

    def detach_slice_ref(self, slice_ref):
        """Remove a child reference that is about to be garbage-collected."""
        del self.slices[id(slice_ref)]

    def detach_slice(self, slc_to_delete):
        """
        :type slc_to_delete: SmartSlice
        """
        for sid, slc_ref in self.slices.items():
            # slc: Slice
            slc = slc_ref()
            if slc is not None and slc is slc_to_delete:
                del self.slices[sid]
                break


class SmartSlice:
    def __init__(self, store, start, stop, step):
        assert step is not None and step != 0
        assert start is None or stop is None or start <= stop
        # self._store: Store
        self._store = store
        # self._start: Union[int, None]
        self._start = start
        # self._stop: Union[int, None]
        self._stop = stop
        # self._step: int
        self._step = step

        self._store.attach_slice(self)

    def _update_indexes(self, start, stop, shift):
        if shift:
            for slc_ref in self._store.slices.values():
                # slc: SmartSlice
                slc = slc_ref()
                if slc is not None:
                    if slc._start is not None and stop < slc._start:
                        slc._start += shift
                    if slc._stop is not None and start <= slc._stop:
                        slc._stop += shift

    def _render(self):
        """Return the actual list from the stored start/stop/step."""
        if self._start is None:
            if self._stop is None:
                return self._store.data[::self._step]
            else:
                return self._store.data[:self._stop:self._step]
        elif self._stop is None:
            return self._store.data[self._start::self._step]
        else:
            return self._store.data[self._start:self._stop:self._step]

    def _adjust(self, start, stop, step, materialize=False):
        """
        :rtype: Tuple[int, int, int, int, int]
        """
        int_start = 0 if self._start is None else self._start
        int_stop = len(self._store.data) if self._stop is None else self._stop

        if self._step > 0:
            if start is None:
                _start = self._start
            else:
                _start = min(int_stop, max(int_start, (
                    int_start if start >= 0 else int_stop) + start))

            if stop is None:
                _stop = self._stop
            else:
                _stop = min(int_stop, max(int_start, (
                    int_start if stop >= 0 else int_stop) + stop))

            _step = self._step if step is None else (self._step * step)
        else:
            raise ValueError("Not implemented")
            # _start = stop if self._start is None else (
            #     self._stop if stop is None else (self._stop + stop))
            # _stop = stop if self._stop is None else (
            #     self._stop if stop is None else (self._stop + stop))
            # _step = self._step if step is None else (self._step * step)

        if materialize:
            if _start is None:
                _start = int_start
            if _stop is None:
                _stop = int_stop

        rng_start = _start if self._start is None else int_start
        rng_stop = _stop if self._stop is None else int_stop
        return _start, _stop, _step, rng_start, rng_stop

    def _adjust_pos(self, pos, validate):
        """
        :type pos: int
        :type validate: bool
        :rtype: int
        """
        assert isinstance(pos, int)
        int_start = 0 if self._start is None else self._start
        int_stop = len(self._store.data) if self._stop is None else self._stop

        if self._step > 0:
            _pos = (int_start if pos >= 0 else int_stop) + pos
        else:
            raise ValueError("Not implemented")

        if validate and not (int_start <= _pos < int_stop):
            raise IndexError('list index out of range')

        return _pos

    # def _delete_child(self, child_ref):
    #     """Remove a child reference that is about to be garbage-collected."""
    #     del self._children[id(child_ref)]
    #
    # def _detach_children(self):
    #     """Remove all children and give them independent parent copies."""
    #     children = [val[0] for val in self._children.values()]
    #     for child in children:
    #         child()._parent = list(self)
    #     self._children.clear()

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step, _, _ = self._adjust(key.start, key.stop, key.step)
            if start is not None and stop is not None and start > stop:
                stop = start
            return SmartSlice(self._store, start, stop, step)
        elif isinstance(key, int):
            return self._store.data[self._adjust_pos(key, True)]
        else:
            raise TypeError('list indices must be integers or slices, not '
                            + type(key).__name__)

    def __setitem__(self, key, item):
        old_size = len(self._store.data)

        if isinstance(key, slice):
            start, stop, step, rng_start, rng_stop = self._adjust(key.start, key.stop,
                                                                  key.step, True)
            self._store.data[start:stop:step] = item
            self._update_indexes(start, stop, len(self._store.data) - old_size)
        elif isinstance(key, int):
            self._store.data[self._adjust_pos(key, True)] = item
        else:
            raise TypeError('list indices must be integers or slices, not '
                            + type(key).__name__)

    def __delitem__(self, key):
        old_size = len(self._store.data)
        if isinstance(key, slice):
            start, stop, step, _, _ = self._adjust(key.start, key.stop, key.step, True)
            del self._store.data[start:stop:step]
        elif isinstance(key, int):
            start = stop = self._adjust_pos(key, True)
            del self._store.data[start]
        else:
            raise TypeError('list indices must be integers or slices, not '
                            + type(key).__name__)

        self._update_indexes(start, stop, len(self._store.data) - old_size)

    if not py3k:
        def __getslice__(self, start, stop):
            return self.__getitem__(slice(start, stop))

        def __setslice__(self, start, stop, iterable):
            self.__setitem__(slice(start, stop), iterable)

        def __delslice__(self, start, stop):
            self.__delitem__(slice(start, stop))

    def __iter__(self):
        start = self._start
        stop = self._stop
        if start is None:
            start = 0 if self._step > 0 else (len(self._store.data) - 1)
        slc = SmartSlice(self._store, start, stop, self._step)
        while True:
            i = slc._start
            if self._step > 0:
                if i >= (len(self._store.data) if self._stop is None else self._stop):
                    break
            elif i <= (-1 if self._stop is None else self._stop):
                break
            value = self._store.data[i]
            slc._start += self._step
            yield value

    def __reversed__(self):
        start = self._start
        stop = self._stop
        if stop is None:
            stop = len(self._store.data)
        slc = SmartSlice(self._store, start, stop, self._step)
        while True:
            i = slc._stop
            if self._step > 0:
                if i <= (0 if self._start is None else self._start):
                    break
            elif i >= (len(self._store.data) if self._start is None else self._start):
                break
            value = self._store.data[i - 1]
            slc._stop -= self._step
            yield value

    def __repr__(self):
        return repr(self._render())

    def __lt__(self, other):
        if isinstance(other, SmartSlice):
            return self._render() < other._render()
        return self._render() < other

    def __le__(self, other):
        if isinstance(other, SmartSlice):
            return self._render() <= other._render()
        return self._render() <= other

    def __eq__(self, other):
        if isinstance(other, SmartSlice):
            return self._render() == other._render()
        return self._render() == other

    def __ne__(self, other):
        if isinstance(other, SmartSlice):
            return self._render() != other._render()
        return self._render() != other

    def __gt__(self, other):
        if isinstance(other, SmartSlice):
            return self._render() > other._render()
        return self._render() > other

    def __ge__(self, other):
        if isinstance(other, SmartSlice):
            return self._render() >= other._render()
        return self._render() >= other

    def __bool__(self):
        return bool(self._render())

    def __len__(self):
        size = len(self._store.data) if self._stop is None else self._stop
        if self._start is not None:
            size -= self._start
        return max(0, size // abs(self._step))

    def __mul__(self, other):
        return smart_list(self._render() * other)

    def __rmul__(self, other):
        return smart_list(other * self._render())

    def __imul__(self, other):
        self.extend(self._render() * (other - 1))
        return self

    def __contains__(self, item):
        return item in self._render()

    def __add__(self, other):
        return smart_list(self._render() + other)

    def __radd__(self, other):
        return smart_list(other + self._render())

    def __iadd__(self, other):
        self.extend(other)
        return self

    @inheritdoc
    def append(self, item):
        size = len(self)
        self[size:size] = [item]

    @inheritdoc
    def extend(self, item):
        size = len(self)
        self[size:size] = item

    @inheritdoc
    def insert(self, index, item):
        start, stop, step, rng_start, rng_stop = self._adjust(index, index, 1, True)
        self._store.data.insert(start, item)
        self._update_indexes(start, stop, 1)

    @inheritdoc
    def pop(self, index=None):
        start = 0 if self._start is None else self._start
        size = len(self)
        if index is None:
            index = size - 1
        elif index < 0:
            index = size + index
        if index < 0 or index >= size:
            raise IndexError("pop index out of range")
        pos = start + index
        result = self._store.data.pop(pos)
        self._update_indexes(pos, pos, -1)
        return result

    @inheritdoc
    def remove(self, item):
        index = self.index(item)
        del self[index]

    @inheritdoc
    def reverse(self):
        if self._start is None and self._stop is None and self._step == 1:
            self._store.data.reverse()
        else:
            vals = self._render()
            vals.reverse()
            self[:] = vals

        # values = self._render()
        # self._store.detach_slice(self)
        # self._store = Store(values, attach=True)
        # self._store.attach_slice(self)
        # self._start = None
        # self._stop = None
        # self._step = 1

    @inheritdoc
    def count(self, item):
        return self._render().count(item)

    @inheritdoc
    def index(self, item, start=None, stop=None):
        if start is None:
            return self._render().index(item)
        elif stop is None:
            return self._render().index(item, start)
        else:
            return self._render().index(item, start, stop)

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
            self._store.data[self._start:self._stop:self._step] = item
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
            self._store.data[self._start:self._stop:self._step] = item


def smart_list(iterator=None):
    return SmartSlice(ListStore(iterator), None, None, 1)

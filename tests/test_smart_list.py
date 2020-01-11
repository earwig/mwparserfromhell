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

from __future__ import unicode_literals

import unittest

from mwparserfromhell.compat import py3k, range
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.smart_list.ListProxy import _ListProxy



class TestSmartList(unittest.TestCase):
    """Test cases for the SmartList class and its child, _ListProxy."""

    def _test_get_set_del_item(self, builder, assertEqualIter):
        """Run tests on __get/set/delitem__ of a list built with *builder*."""
        def assign(L, s1, s2, s3, val):
            L[s1:s2:s3] = val

        def delete(L, s1):
            del L[s1]

        list1 = builder([0, 1, 2, 3, "one", "two"])
        list2 = builder(list(range(10)))

        self.assertEqual(1, list1[1])
        self.assertEqual("one", list1[-2])
        assertEqualIter([2, 3], list1[2:4])
        self.assertRaises(IndexError, lambda: list1[6])
        self.assertRaises(IndexError, lambda: list1[-7])

        assertEqualIter([0, 1, 2], list1[:3])
        assertEqualIter([0, 1, 2, 3, "one", "two"], list1[:])
        assertEqualIter([3, "one", "two"], list1[3:])
        assertEqualIter([3, "one", "two"], list1[3:100])
        assertEqualIter(["one", "two"], list1[-2:])
        assertEqualIter([0, 1], list1[:-4])
        assertEqualIter([], list1[6:])
        assertEqualIter([], list1[4:2])

        assertEqualIter([0, 2, "one"], list1[0:5:2])
        assertEqualIter([0, 2], list1[0:-3:2])
        assertEqualIter([0, 1, 2, 3, "one", "two"], list1[::])
        assertEqualIter([2, 3, "one", "two"], list1[2::])
        assertEqualIter([0, 1, 2, 3], list1[:4:])
        assertEqualIter([2, 3], list1[2:4:])
        assertEqualIter([0, 2, 4, 6, 8], list2[::2])
        assertEqualIter([2, 5, 8], list2[2::3])
        assertEqualIter([0, 3], list2[:6:3])
        assertEqualIter([2, 5, 8], list2[-8:9:3])
        assertEqualIter([], list2[100000:1000:-100])

        list1[3] = 100
        self.assertEqual(100, list1[3])
        list1[-3] = 101
        assertEqualIter([0, 1, 2, 101, "one", "two"], list1)
        list1[5:] = [6, 7, 8]
        assertEqualIter([6, 7, 8], list1[5:])
        assertEqualIter([0, 1, 2, 101, "one", 6, 7, 8], list1)
        list1[2:4] = [-1, -2, -3, -4, -5]
        assertEqualIter([0, 1, -1, -2, -3, -4, -5, "one", 6, 7, 8], list1)
        list1[0:-3] = [99]
        assertEqualIter([99, 6, 7, 8], list1)
        list2[0:6:2] = [100, 102, 104]
        assertEqualIter([100, 1, 102, 3, 104, 5, 6, 7, 8, 9], list2)
        list2[::3] = [200, 203, 206, 209]
        assertEqualIter([200, 1, 102, 203, 104, 5, 206, 7, 8, 209], list2)
        list2[::] = range(7)
        assertEqualIter([0, 1, 2, 3, 4, 5, 6], list2)
        self.assertRaises(ValueError, assign, list2, 0, 5, 2,
                          [100, 102, 104, 106])
        with self.assertRaises(IndexError):
            list2[7] = "foo"
        with self.assertRaises(IndexError):
            list2[-8] = "foo"

        del list2[2]
        assertEqualIter([0, 1, 3, 4, 5, 6], list2)
        del list2[-3]
        assertEqualIter([0, 1, 3, 5, 6], list2)
        self.assertRaises(IndexError, delete, list2, 100)
        self.assertRaises(IndexError, delete, list2, -6)
        list2[:] = range(10)
        del list2[3:6]
        assertEqualIter([0, 1, 2, 6, 7, 8, 9], list2)
        del list2[-2:]
        assertEqualIter([0, 1, 2, 6, 7], list2)
        del list2[:2]
        assertEqualIter([2, 6, 7], list2)
        list2[:] = range(10)
        del list2[2:8:2]
        assertEqualIter([0, 1, 3, 5, 7, 8, 9], list2)

    def _test_add_radd_iadd(self, builder, assertEqualIter):
        """Run tests on __r/i/add__ of a list built with *builder*."""
        list1 = builder(range(5))
        list2 = builder(range(5, 10))
        assertEqualIter([0, 1, 2, 3, 4, 5, 6], list1 + [5, 6])
        assertEqualIter([0, 1, 2, 3, 4], list1)
        self.assertEqual(list(range(10)), list1 + list2)
        assertEqualIter([-2, -1, 0, 1, 2, 3, 4], [-2, -1] + list1)
        assertEqualIter([0, 1, 2, 3, 4], list1)
        list1 += ["foo", "bar", "baz"]
        assertEqualIter([0, 1, 2, 3, 4, "foo", "bar", "baz"], list1)

    def _test_other_magic_methods(self, builder, assertEqualIter):
        """Run tests on other magic methods of a list built with *builder*."""
        list1 = builder([0, 1, 2, 3, "one", "two"])
        list2 = builder([])
        list3 = builder([0, 2, 3, 4])
        list4 = builder([0, 1, 2])

        if py3k:
            self.assertEqual("[0, 1, 2, 3, 'one', 'two']", str(list1))
            self.assertEqual(b"\x00\x01\x02", bytes(list4))
            self.assertEqual("[0, 1, 2, 3, 'one', 'two']", repr(list1))
        else:
            self.assertEqual("[0, 1, 2, 3, u'one', u'two']", unicode(list1))
            self.assertEqual(b"[0, 1, 2, 3, u'one', u'two']", str(list1))
            self.assertEqual(b"[0, 1, 2, 3, u'one', u'two']", repr(list1))

        self.assertLess(list1, list3)
        self.assertLessEqual(list1, list3)
        self.assertNotEqual(list1, list3)
        self.assertNotEqual(list1, list3)
        self.assertLessEqual(list1, list3)
        self.assertLess(list1, list3)

        other1 = [0, 2, 3, 4]
        self.assertLess(list1, other1)
        self.assertLessEqual(list1, other1)
        self.assertNotEqual(list1, other1)
        self.assertNotEqual(list1, other1)
        self.assertLessEqual(list1, other1)
        self.assertLess(list1, other1)

        other2 = [0, 0, 1, 2]
        self.assertGreaterEqual(list1, other2)
        self.assertGreater(list1, other2)
        self.assertNotEqual(list1, other2)
        self.assertNotEqual(list1, other2)
        self.assertGreater(list1, other2)
        self.assertGreaterEqual(list1, other2)

        other3 = [0, 1, 2, 3, "one", "two"]
        self.assertGreaterEqual(list1, other3)
        self.assertLessEqual(list1, other3)
        assertEqualIter(list1, other3)
        assertEqualIter(list1, other3)
        self.assertLessEqual(list1, other3)
        self.assertGreaterEqual(list1, other3)

        self.assertTrue(bool(list1))
        self.assertFalse(bool(list2))

        self.assertEqual(6, len(list1))
        self.assertEqual(0, len(list2))

        out = []
        for obj in list1:
            out.append(obj)
        assertEqualIter([0, 1, 2, 3, "one", "two"], out)

        out = []
        for ch in list2:
            out.append(ch)
        assertEqualIter([], out)

        gen1 = iter(list1)
        out = []
        for i in range(len(list1)):
            out.append(next(gen1))
        self.assertRaises(StopIteration, next, gen1)
        assertEqualIter([0, 1, 2, 3, "one", "two"], out)
        gen2 = iter(list2)
        self.assertRaises(StopIteration, next, gen2)

        # TODO: might need to test an iterator rather than list
        assertEqualIter(["two", "one", 3, 2, 1, 0], list(reversed(list1)))
        assertEqualIter([], list(reversed(list2)))

        self.assertIn("one", list1)
        self.assertIn(3, list1)
        self.assertNotIn(10, list1)
        self.assertNotIn(0, list2)

        assertEqualIter([], list2 * 5)
        assertEqualIter([], 5 * list2)
        assertEqualIter([0, 1, 2, 0, 1, 2, 0, 1, 2], list4 * 3)
        assertEqualIter([0, 1, 2, 0, 1, 2, 0, 1, 2], 3 * list4)
        list4 *= 2
        assertEqualIter([0, 1, 2, 0, 1, 2], list4)

    def _test_list_methods(self, builder, assertEqualIter):
        """Run tests on the public methods of a list built with *builder*."""
        list1 = builder(range(5))
        list2 = builder(["foo"])
        list3 = builder([("a", 5), ("d", 2), ("b", 8), ("c", 3)])

        list1.append(5)
        list1.append(1)
        list1.append(2)
        assertEqualIter([0, 1, 2, 3, 4, 5, 1, 2], list1)

        self.assertEqual(0, list1.count(6))
        self.assertEqual(2, list1.count(1))

        list1.extend(range(5, 8))
        assertEqualIter([0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 7], list1)

        self.assertEqual(1, list1.index(1))
        self.assertEqual(6, list1.index(1, 3))
        self.assertEqual(6, list1.index(1, 3, 7))
        self.assertRaises(ValueError, list1.index, 1, 3, 5)

        list1.insert(0, -1)
        assertEqualIter([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 7], list1)
        list1.insert(-1, 6.5)
        assertEqualIter([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5, 7], list1)
        list1.insert(13, 8)
        assertEqualIter([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5, 7, 8], list1)

        self.assertEqual(8, list1.pop())
        self.assertEqual(7, list1.pop())
        assertEqualIter([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5], list1)
        self.assertEqual(-1, list1.pop(0))
        self.assertEqual(5, list1.pop(5))
        self.assertEqual(6.5, list1.pop(-1))
        assertEqualIter([0, 1, 2, 3, 4, 1, 2, 5, 6], list1)
        self.assertEqual("foo", list2.pop())
        self.assertRaises(IndexError, list2.pop)
        assertEqualIter([], list2)

        list1.remove(6)
        assertEqualIter([0, 1, 2, 3, 4, 1, 2, 5], list1)
        list1.remove(1)
        assertEqualIter([0, 2, 3, 4, 1, 2, 5], list1)
        list1.remove(1)
        assertEqualIter([0, 2, 3, 4, 2, 5], list1)
        self.assertRaises(ValueError, list1.remove, 1)

        list1.reverse()
        assertEqualIter([5, 2, 4, 3, 2, 0], list1)

        list1.sort()
        assertEqualIter([0, 2, 2, 3, 4, 5], list1)
        list1.sort(reverse=True)
        assertEqualIter([5, 4, 3, 2, 2, 0], list1)
        if not py3k:
            func = lambda x, y: abs(3 - x) - abs(3 - y)  # Distance from 3
            list1.sort(cmp=func)
            assertEqualIter([3, 4, 2, 2, 5, 0], list1)
            list1.sort(cmp=func, reverse=True)
            assertEqualIter([0, 5, 4, 2, 2, 3], list1)
        list3.sort(key=lambda i: i[1])
        assertEqualIter([("d", 2), ("c", 3), ("a", 5), ("b", 8)], list3)
        list3.sort(key=lambda i: i[1], reverse=True)
        assertEqualIter([("b", 8), ("a", 5), ("c", 3), ("d", 2)], list3)

    @staticmethod
    def _dispatch_test_for_children(meth, assertEqualIter):
        """Run a test method on various different types of children."""
        meth(lambda L: SmartList(list(L))[:], assertEqualIter)
        meth(lambda L: SmartList([999] + list(L))[1:], assertEqualIter)
        meth(lambda L: SmartList(list(L) + [999])[:-1], assertEqualIter)
        meth(lambda L: SmartList([101, 102] + list(L) + [201, 202])[2:-2], assertEqualIter)

    def test_docs(self):
        """make sure the methods of SmartList/_ListProxy have docstrings"""
        methods = ["append", "count", "extend", "index", "insert", "pop",
                   "remove", "reverse", "sort"]
        for meth in methods:
            expected = getattr(list, meth).__doc__
            smartlist_doc = getattr(SmartList, meth).__doc__
            listproxy_doc = getattr(_ListProxy, meth).__doc__
            self.assertEqual(expected, smartlist_doc)
            self.assertEqual(expected, listproxy_doc)

    def test_doctest(self):
        """make sure the test embedded in SmartList's docstring passes"""
        parent = SmartList([0, 1, 2, 3])
        self.assertEqual([0, 1, 2, 3], parent)
        child = parent[2:]
        self.assertEqual([2, 3], child)
        child.append(4)
        self.assertEqual([2, 3, 4], child)
        self.assertEqual([0, 1, 2, 3, 4], parent)

    def test_parent_get_set_del(self):
        """make sure SmartList's getitem/setitem/delitem work"""
        self._test_get_set_del_item(SmartList, self.assertEqual)
        self._test_get_set_del_item(SmartList, self.assertEqualIterator)

    def test_parent_add(self):
        """make sure SmartList's add/radd/iadd work"""
        self._test_add_radd_iadd(SmartList, self.assertEqual)
        self._test_add_radd_iadd(SmartList, self.assertEqualIterator)

    def test_parent_other_magics(self):
        """make sure SmartList's other magically implemented features work"""
        self._test_other_magic_methods(SmartList, self.assertEqual)
        self._test_other_magic_methods(SmartList, self.assertEqualIterator)

    def test_parent_methods(self):
        """make sure SmartList's non-magic methods work, like append()"""
        self._test_list_methods(SmartList, self.assertEqual)
        self._test_list_methods(SmartList, self.assertEqualIterator)

    def test_child_get_set_del(self):
        """make sure _ListProxy's getitem/setitem/delitem work"""
        self._dispatch_test_for_children(self._test_get_set_del_item, self.assertEqual)
        self._dispatch_test_for_children(self._test_get_set_del_item, self.assertEqualIterator)

    def test_child_add(self):
        """make sure _ListProxy's add/radd/iadd work"""
        self._dispatch_test_for_children(self._test_add_radd_iadd, self.assertEqual)
        self._dispatch_test_for_children(self._test_add_radd_iadd, self.assertEqualIterator)

    def test_child_other_magics(self):
        """make sure _ListProxy's other magically implemented features work"""
        self._dispatch_test_for_children(self._test_other_magic_methods, self.assertEqual)
        self._dispatch_test_for_children(self._test_other_magic_methods, self.assertEqualIterator)

    def test_child_methods(self):
        """make sure _ListProxy's non-magic methods work, like append()"""
        self._dispatch_test_for_children(self._test_list_methods, self.assertEqual)
        self._dispatch_test_for_children(self._test_list_methods, self.assertEqualIterator)

    def _test_influence(self, assertEqualIter):
        """make sure changes are propagated from parents to children"""
        parent = SmartList([0, 1, 2, 3, 4, 5])
        child1 = parent[2:]
        child2 = parent[2:5]
        assertEqualIter([0, 1, 2, 3, 4, 5], parent)
        assertEqualIter([2, 3, 4, 5], child1)
        assertEqualIter([2, 3, 4], child2)
        self.assertEqual(2, len(parent._children))

        parent.append(6)
        child1.append(7)
        child2.append(4.5)
        assertEqualIter([0, 1, 2, 3, 4, 4.5, 5, 6, 7], parent)
        assertEqualIter([2, 3, 4, 4.5, 5, 6, 7], child1)
        assertEqualIter([2, 3, 4, 4.5], child2)

        parent.insert(0, -1)
        parent.insert(4, 2.5)
        parent.insert(10, 6.5)
        assertEqualIter([-1, 0, 1, 2, 2.5, 3, 4, 4.5, 5, 6, 6.5, 7], parent)
        assertEqualIter([2, 2.5, 3, 4, 4.5, 5, 6, 6.5, 7], child1)
        assertEqualIter([2, 2.5, 3, 4, 4.5], child2)

        self.assertEqual(7, parent.pop())
        self.assertEqual(6.5, child1.pop())
        self.assertEqual(4.5, child2.pop())
        assertEqualIter([-1, 0, 1, 2, 2.5, 3, 4, 5, 6], parent)
        assertEqualIter([2, 2.5, 3, 4, 5, 6], child1)
        assertEqualIter([2, 2.5, 3, 4], child2)

        parent.remove(-1)
        child1.remove(2.5)
        assertEqualIter([0, 1, 2, 3, 4, 5, 6], parent)
        assertEqualIter([2, 3, 4, 5, 6], child1)
        assertEqualIter([2, 3, 4], child2)

        self.assertEqual(0, parent.pop(0))
        assertEqualIter([1, 2, 3, 4, 5, 6], parent)
        assertEqualIter([2, 3, 4, 5, 6], child1)
        assertEqualIter([2, 3, 4], child2)

        child2.reverse()
        assertEqualIter([1, 4, 3, 2, 5, 6], parent)
        assertEqualIter([4, 3, 2, 5, 6], child1)
        assertEqualIter([4, 3, 2], child2)

        parent.extend([7, 8])
        child1.extend([8.1, 8.2])
        child2.extend([1.9, 1.8])
        assertEqualIter([1, 4, 3, 2, 1.9, 1.8, 5, 6, 7, 8, 8.1, 8.2], parent)
        assertEqualIter([4, 3, 2, 1.9, 1.8, 5, 6, 7, 8, 8.1, 8.2], child1)
        assertEqualIter([4, 3, 2, 1.9, 1.8], child2)

        child3 = parent[9:]
        assertEqualIter([8, 8.1, 8.2], child3)

        del parent[8:]
        assertEqualIter([1, 4, 3, 2, 1.9, 1.8, 5, 6], parent)
        assertEqualIter([4, 3, 2, 1.9, 1.8, 5, 6], child1)
        assertEqualIter([4, 3, 2, 1.9, 1.8], child2)
        assertEqualIter([], child3)
        self.assertEqual(0, len(child3))

        del child1
        assertEqualIter([1, 4, 3, 2, 1.9, 1.8, 5, 6], parent)
        assertEqualIter([4, 3, 2, 1.9, 1.8], child2)
        assertEqualIter([], child3)
        self.assertEqual(2, len(parent._children))

        del child3
        assertEqualIter([1, 4, 3, 2, 1.9, 1.8, 5, 6], parent)
        assertEqualIter([4, 3, 2, 1.9, 1.8], child2)
        self.assertEqual(1, len(parent._children))

        parent.remove(1.9)
        parent.remove(1.8)
        assertEqualIter([1, 4, 3, 2, 5, 6], parent)
        assertEqualIter([4, 3, 2], child2)

        parent.reverse()
        assertEqualIter([6, 5, 2, 3, 4, 1], parent)
        assertEqualIter([4, 3, 2], child2)
        self.assertEqual(0, len(parent._children))

    def test_influence(self):
        self._test_influence(self.assertEqual)
        self._test_influence(self.assertEqualIterator)

    @staticmethod
    def _test_get_slice(builder, assertEqualIter):
        lst = builder([0, 1, 2])
        assertEqualIter(lst, [0, 1, 2])
        assertEqualIter(lst[:], [0, 1, 2])
        assertEqualIter(lst[0:0], [])
        assertEqualIter(lst[0:1], [0])
        assertEqualIter(lst[0:2], [0, 1])
        assertEqualIter(lst[0:3], [0, 1, 2])
        assertEqualIter(lst[0:4], [0, 1, 2])  # bug in iteration
        assertEqualIter(lst[0:], [0, 1, 2])
        assertEqualIter(lst[1:1], [])
        assertEqualIter(lst[1:2], [1])
        assertEqualIter(lst[1:3], [1, 2])
        assertEqualIter(lst[1:4], [1, 2])  # bug in iteration
        assertEqualIter(lst[1:], [1, 2])
        assertEqualIter(lst[2:], [2])
        assertEqualIter(lst[3:], [])
        assertEqualIter(lst[4:], [])
        assertEqualIter(lst[-1:], [2])
        assertEqualIter(lst[-2:], [1, 2])
        assertEqualIter(lst[-3:], [0, 1, 2])
        assertEqualIter(lst[-4:], [0, 1, 2])  # bug in list and iteration
        assertEqualIter(lst[:-1], [0, 1])
        assertEqualIter(lst[:-2], [0])
        assertEqualIter(lst[:-3], [])
        assertEqualIter(lst[:-4], [])  # bug in list
        assertEqualIter(lst[1:-1], [1])
        assertEqualIter(lst[1:-2], [])
        assertEqualIter(lst[1:-3], [])
        assertEqualIter(lst[1:-4], [])  # bug in list
        assertEqualIter(lst[-1:-1], [])
        assertEqualIter(lst[-2:-1], [1])
        assertEqualIter(lst[-3:-1], [0, 1])
        assertEqualIter(lst[-4:-1], [0, 1])  # bug in list and iteration
        assertEqualIter(lst[-3:-1], [0, 1])
        assertEqualIter(lst[-3:-2], [0])
        assertEqualIter(lst[-3:-3], [])
        assertEqualIter(lst[-3:-4], [])  # bug in list

        # step == 2
        assertEqualIter(lst[::2], [0, 2])
        assertEqualIter(lst[0::2], [0, 2])
        assertEqualIter(lst[1::2], [1])
        assertEqualIter(lst[2::2], [2])
        assertEqualIter(lst[3::2], [])
        assertEqualIter(lst[4::2], [])

        # step < 0 -- all of these are not working correctly
        assertEqualIter(lst[::-1], [2, 1, 0])
        assertEqualIter(lst[0::-1], [0])
        assertEqualIter(lst[1::-1], [1, 0])
        assertEqualIter(lst[2::-1], [2, 1, 0])
        assertEqualIter(lst[3::-1], [2, 1, 0])
        assertEqualIter(lst[4::-1], [2, 1, 0])
        assertEqualIter(lst[::-2], [2, 0])
        assertEqualIter(lst[0::-2], [0])
        assertEqualIter(lst[1::-2], [1])
        assertEqualIter(lst[2::-2], [2, 0])
        assertEqualIter(lst[3::-2], [2, 0])
        assertEqualIter(lst[4::-2], [2, 0])

    def test_get_slice(self):
        self._test_get_slice(list, self.assertEqual)  # test against built-in list
        self._test_get_slice(SmartList, self.assertEqual)

    def test_get_slice_iterator(self):
        self._test_get_slice(list, self.assertEqualIterator)  # test against built-in list
        self._test_get_slice(SmartList, self.assertEqualIterator)

    def assertEqualIterator(self, iter1, iter2):
        if py3k:
            from itertools import zip_longest
        else:
            from itertools import izip_longest as zip_longest

        for a, b in zip_longest(iter1, iter2, fillvalue='__END_OF_LIST__'):
            self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)

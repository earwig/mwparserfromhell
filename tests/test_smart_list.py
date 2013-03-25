# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>
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
from mwparserfromhell.smart_list import SmartList, _ListProxy

class TestSmartList(unittest.TestCase):
    """Test cases for the SmartList class and its child, _ListProxy."""

    def _test_get_set_del_item(self, builder):
        """Run tests on __get/set/delitem__ of a list built with *builder*."""
        def assign(L, s1, s2, s3, val):
            L[s1:s2:s3] = val
        def delete(L, s1):
            del L[s1]

        list1 = builder([0, 1, 2, 3, "one", "two"])
        list2 = builder(list(range(10)))

        self.assertEquals(1, list1[1])
        self.assertEquals("one", list1[-2])
        self.assertEquals([2, 3], list1[2:4])
        self.assertRaises(IndexError, lambda: list1[6])
        self.assertRaises(IndexError, lambda: list1[-7])

        self.assertEquals([0, 1, 2], list1[:3])
        self.assertEquals([0, 1, 2, 3, "one", "two"], list1[:])
        self.assertEquals([3, "one", "two"], list1[3:])
        self.assertEquals(["one", "two"], list1[-2:])
        self.assertEquals([0, 1], list1[:-4])
        self.assertEquals([], list1[6:])
        self.assertEquals([], list1[4:2])

        self.assertEquals([0, 2, "one"], list1[0:5:2])
        self.assertEquals([0, 2], list1[0:-3:2])
        self.assertEquals([0, 1, 2, 3, "one", "two"], list1[::])
        self.assertEquals([2, 3, "one", "two"], list1[2::])
        self.assertEquals([0, 1, 2, 3], list1[:4:])
        self.assertEquals([2, 3], list1[2:4:])
        self.assertEquals([0, 2, 4, 6, 8], list2[::2])
        self.assertEquals([2, 5, 8], list2[2::3])
        self.assertEquals([0, 3], list2[:6:3])
        self.assertEquals([2, 5, 8], list2[-8:9:3])
        self.assertEquals([], list2[100000:1000:-100])

        list1[3] = 100
        self.assertEquals(100, list1[3])
        list1[-3] = 101
        self.assertEquals([0, 1, 2, 101, "one", "two"], list1)
        list1[5:] = [6, 7, 8]
        self.assertEquals([6, 7, 8], list1[5:])
        self.assertEquals([0, 1, 2, 101, "one", 6, 7, 8], list1)
        list1[2:4] = [-1, -2, -3, -4, -5]
        self.assertEquals([0, 1, -1, -2, -3, -4, -5, "one", 6, 7, 8], list1)
        list1[0:-3] = [99]
        self.assertEquals([99, 6, 7, 8], list1)
        list2[0:6:2] = [100, 102, 104]
        self.assertEquals([100, 1, 102, 3, 104, 5, 6, 7, 8, 9], list2)
        list2[::3] = [200, 203, 206, 209]
        self.assertEquals([200, 1, 102, 203, 104, 5, 206, 7, 8, 209], list2)
        list2[::] = range(7)
        self.assertEquals([0, 1, 2, 3, 4, 5, 6], list2)
        self.assertRaises(ValueError, assign, list2, 0, 5, 2,
                          [100, 102, 104, 106])

        del list2[2]
        self.assertEquals([0, 1, 3, 4, 5, 6], list2)
        del list2[-3]
        self.assertEquals([0, 1, 3, 5, 6], list2)
        self.assertRaises(IndexError, delete, list2, 100)
        self.assertRaises(IndexError, delete, list2, -6)
        list2[:] = range(10)
        del list2[3:6]
        self.assertEquals([0, 1, 2, 6, 7, 8, 9], list2)
        del list2[-2:]
        self.assertEquals([0, 1, 2, 6, 7], list2)
        del list2[:2]
        self.assertEquals([2, 6, 7], list2)
        list2[:] = range(10)
        del list2[2:8:2]
        self.assertEquals([0, 1, 3, 5, 7, 8, 9], list2)

    def _test_add_radd_iadd(self, builder):
        """Run tests on __r/i/add__ of a list built with *builder*."""
        list1 = builder(range(5))
        list2 = builder(range(5, 10))
        self.assertEquals([0, 1, 2, 3, 4, 5, 6], list1 + [5, 6])
        self.assertEquals([0, 1, 2, 3, 4], list1)
        self.assertEquals(list(range(10)), list1 + list2)
        self.assertEquals([-2, -1, 0, 1, 2, 3, 4], [-2, -1] + list1)
        self.assertEquals([0, 1, 2, 3, 4], list1)
        list1 += ["foo", "bar", "baz"]
        self.assertEquals([0, 1, 2, 3, 4, "foo", "bar", "baz"], list1)

    def _test_other_magic_methods(self, builder):
        """Run tests on other magic methods of a list built with *builder*."""
        list1 = builder([0, 1, 2, 3, "one", "two"])
        list2 = builder([])
        list3 = builder([0, 2, 3, 4])
        list4 = builder([0, 1, 2])

        if py3k:
            self.assertEquals("[0, 1, 2, 3, 'one', 'two']", str(list1))
            self.assertEquals(b"[0, 1, 2, 3, 'one', 'two']", bytes(list1))
            self.assertEquals("[0, 1, 2, 3, 'one', 'two']", repr(list1))
        else:
            self.assertEquals("[0, 1, 2, 3, u'one', u'two']", unicode(list1))
            self.assertEquals(b"[0, 1, 2, 3, u'one', u'two']", str(list1))
            self.assertEquals(b"[0, 1, 2, 3, u'one', u'two']", repr(list1))

        self.assertTrue(list1 < list3)
        self.assertTrue(list1 <= list3)
        self.assertFalse(list1 == list3)
        self.assertTrue(list1 != list3)
        self.assertFalse(list1 > list3)
        self.assertFalse(list1 >= list3)

        other1 = [0, 2, 3, 4]
        self.assertTrue(list1 < other1)
        self.assertTrue(list1 <= other1)
        self.assertFalse(list1 == other1)
        self.assertTrue(list1 != other1)
        self.assertFalse(list1 > other1)
        self.assertFalse(list1 >= other1)

        other2 = [0, 0, 1, 2]
        self.assertFalse(list1 < other2)
        self.assertFalse(list1 <= other2)
        self.assertFalse(list1 == other2)
        self.assertTrue(list1 != other2)
        self.assertTrue(list1 > other2)
        self.assertTrue(list1 >= other2)

        other3 = [0, 1, 2, 3, "one", "two"]
        self.assertFalse(list1 < other3)
        self.assertTrue(list1 <= other3)
        self.assertTrue(list1 == other3)
        self.assertFalse(list1 != other3)
        self.assertFalse(list1 > other3)
        self.assertTrue(list1 >= other3)

        self.assertTrue(bool(list1))
        self.assertFalse(bool(list2))

        self.assertEquals(6, len(list1))
        self.assertEquals(0, len(list2))

        out = []
        for obj in list1:
            out.append(obj)
        self.assertEquals([0, 1, 2, 3, "one", "two"], out)

        out = []
        for ch in list2:
            out.append(ch)
        self.assertEquals([], out)

        gen1 = iter(list1)
        out = []
        for i in range(len(list1)):
            out.append(gen1.next())
        self.assertRaises(StopIteration, gen1.next)
        self.assertEquals([0, 1, 2, 3, "one", "two"], out)
        gen2 = iter(list2)
        self.assertRaises(StopIteration, gen2.next)

        self.assertEquals(["two", "one", 3, 2, 1, 0], list(reversed(list1)))
        self.assertEquals([], list(reversed(list2)))

        self.assertTrue("one" in list1)
        self.assertTrue(3 in list1)
        self.assertFalse(10 in list1)
        self.assertFalse(0 in list2)

        self.assertEquals([], list2 * 5)
        self.assertEquals([], 5 * list2)
        self.assertEquals([0, 1, 2, 0, 1, 2, 0, 1, 2], list4 * 3)
        self.assertEquals([0, 1, 2, 0, 1, 2, 0, 1, 2], 3 * list4)
        list4 *= 2
        self.assertEquals([0, 1, 2, 0, 1, 2], list4)

    def _test_list_methods(self, builder):
        """Run tests on the public methods of a list built with *builder*."""
        list1 = builder(range(5))
        list2 = builder(["foo"])
        list3 = builder([("a", 5), ("d", 2), ("b", 8), ("c", 3)])

        list1.append(5)
        list1.append(1)
        list1.append(2)
        self.assertEquals([0, 1, 2, 3, 4, 5, 1, 2], list1)

        self.assertEquals(0, list1.count(6))
        self.assertEquals(2, list1.count(1))

        list1.extend(range(5, 8))
        self.assertEquals([0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 7], list1)

        self.assertEquals(1, list1.index(1))
        self.assertEquals(6, list1.index(1, 3))
        self.assertEquals(6, list1.index(1, 3, 7))
        self.assertRaises(ValueError, list1.index, 1, 3, 5)

        list1.insert(0, -1)
        self.assertEquals([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 7], list1)
        list1.insert(-1, 6.5)
        self.assertEquals([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5, 7], list1)
        list1.insert(13, 8)
        self.assertEquals([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5, 7, 8], list1)

        self.assertEquals(8, list1.pop())
        self.assertEquals(7, list1.pop())
        self.assertEquals([-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5], list1)
        self.assertEquals(-1, list1.pop(0))
        self.assertEquals(5, list1.pop(5))
        self.assertEquals(6.5, list1.pop(-1))
        self.assertEquals([0, 1, 2, 3, 4, 1, 2, 5, 6], list1)
        self.assertEquals("foo", list2.pop())
        self.assertRaises(IndexError, list2.pop)
        self.assertEquals([], list2)

        list1.remove(6)
        self.assertEquals([0, 1, 2, 3, 4, 1, 2, 5], list1)
        list1.remove(1)
        self.assertEquals([0, 2, 3, 4, 1, 2, 5], list1)
        list1.remove(1)
        self.assertEquals([0, 2, 3, 4, 2, 5], list1)
        self.assertRaises(ValueError, list1.remove, 1)

        list1.reverse()
        self.assertEquals([5, 2, 4, 3, 2, 0], list1)

        list1.sort()
        self.assertEquals([0, 2, 2, 3, 4, 5], list1)
        list1.sort(reverse=True)
        self.assertEquals([5, 4, 3, 2, 2, 0], list1)
        list1.sort(cmp=lambda x, y: abs(3 - x) - abs(3 - y))  # Distance from 3
        self.assertEquals([3, 4, 2, 2, 5, 0], list1)
        list1.sort(cmp=lambda x, y: abs(3 - x) - abs(3 - y), reverse=True)
        self.assertEquals([0, 5, 4, 2, 2, 3], list1)
        list3.sort(key=lambda i: i[1])
        self.assertEquals([("d", 2), ("c", 3), ("a", 5), ("b", 8)], list3)
        list3.sort(key=lambda i: i[1], reverse=True)
        self.assertEquals([("b", 8), ("a", 5), ("c", 3), ("d", 2)], list3)

    def test_docs(self):
        """make sure the methods of SmartList/_ListProxy have docstrings"""
        methods = ["append", "count", "extend", "index", "insert", "pop",
                   "remove", "reverse", "sort"]
        for meth in methods:
            expected = getattr(list, meth).__doc__
            smartlist_doc = getattr(SmartList, meth).__doc__
            listproxy_doc = getattr(_ListProxy, meth).__doc__
            self.assertEquals(expected, smartlist_doc)
            self.assertEquals(expected, listproxy_doc)

    def test_doctest(self):
        """make sure the test embedded in SmartList's docstring passes"""
        parent = SmartList([0, 1, 2, 3])
        self.assertEquals([0, 1, 2, 3], parent)
        child = parent[2:]
        self.assertEquals([2, 3], child)
        child.append(4)
        self.assertEquals([2, 3, 4], child)
        self.assertEquals([0, 1, 2, 3, 4], parent)

    def test_parent_get_set_del(self):
        """make sure SmartList's getitem/setitem/delitem work"""
        self._test_get_set_del_item(lambda L: SmartList(L))

    def test_parent_add(self):
        """make sure SmartList's add/radd/iadd work"""
        self._test_add_radd_iadd(lambda L: SmartList(L))

    def test_parent_unaffected_magics(self):
        """sanity checks against SmartList features that were not modified"""
        self._test_other_magic_methods(lambda L: SmartList(L))

    def test_parent_methods(self):
        """make sure SmartList's non-magic methods work, like append()"""
        self._test_list_methods(lambda L: SmartList(L))

    def test_child_get_set_del(self):
        """make sure _ListProxy's getitem/setitem/delitem work"""
        self._test_get_set_del_item(lambda L: SmartList(list(L))[:])
        self._test_get_set_del_item(lambda L: SmartList([999] + list(L))[1:])
        self._test_get_set_del_item(lambda L: SmartList(list(L) + [999])[:-1])
        builder = lambda L: SmartList([101, 102] + list(L) + [201, 202])[2:-2]
        self._test_get_set_del_item(builder)

    def test_child_add(self):
        """make sure _ListProxy's add/radd/iadd work"""
        self._test_add_radd_iadd(lambda L: SmartList(list(L))[:])
        self._test_add_radd_iadd(lambda L: SmartList([999] + list(L))[1:])
        self._test_add_radd_iadd(lambda L: SmartList(list(L) + [999])[:-1])
        builder = lambda L: SmartList([101, 102] + list(L) + [201, 202])[2:-2]
        self._test_add_radd_iadd(builder)

    def test_child_other_magics(self):
        """make sure _ListProxy's other magically implemented features work"""
        self._test_other_magic_methods(lambda L: SmartList(list(L))[:])
        self._test_other_magic_methods(lambda L: SmartList([999] + list(L))[1:])
        self._test_other_magic_methods(lambda L: SmartList(list(L) + [999])[:-1])
        builder = lambda L: SmartList([101, 102] + list(L) + [201, 202])[2:-2]
        self._test_other_magic_methods(builder)

    def test_child_methods(self):
        """make sure _ListProxy's non-magic methods work, like append()"""
        self._test_list_methods(lambda L: SmartList(list(L))[:])
        self._test_list_methods(lambda L: SmartList([999] + list(L))[1:])
        self._test_list_methods(lambda L: SmartList(list(L) + [999])[:-1])
        builder = lambda L: SmartList([101, 102] + list(L) + [201, 202])[2:-2]
        self._test_list_methods(builder)

    def test_influence(self):
        """make sure changes are propagated from parents to children"""
        pass
        # also test whether children that exit scope are removed from parent's map

if __name__ == "__main__":
    unittest.main(verbosity=2)

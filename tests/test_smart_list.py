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
        def assign(L, s1, s2, s3, val):
            L[s1:s2:s3] = val
        def delete(L, s1):
            del L[s1]

        list1 = SmartList([0, 1, 2, 3, "one", "two"])
        list2 = SmartList(list(range(10)))

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
        list1[5:] = [6, 7, 8]
        self.assertEquals([6, 7, 8], list1[5:])
        self.assertEquals([0, 1, 2, 100, "one", 6, 7, 8], list1)
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
        self.assertRaises(ValueError,
                          lambda: assign(list2, 0, 5, 2, [100, 102, 104, 106]))

        del list2[2]
        self.assertEquals([0, 1, 3, 4, 5, 6], list2)
        del list2[-3]
        self.assertEquals([0, 1, 3, 5, 6], list2)
        self.assertRaises(IndexError, lambda: delete(list2, 100))
        self.assertRaises(IndexError, lambda: delete(list2, -6))
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

    def test_parent_add(self):
        """make sure SmartList's add/radd/iadd work"""
        list1 = SmartList(range(5))
        list2 = SmartList(range(5, 10))
        self.assertEquals([0, 1, 2, 3, 4, 5, 6], list1 + [5, 6])
        self.assertEquals([0, 1, 2, 3, 4], list1)
        self.assertEquals(list(range(10)), list1 + list2)
        self.assertEquals([-2, -1, 0, 1, 2, 3, 4], [-2, -1] + list1)
        self.assertEquals([0, 1, 2, 3, 4], list1)
        list1 += ["foo", "bar", "baz"]
        self.assertEquals([0, 1, 2, 3, 4, "foo", "bar", "baz"], list1)

    def test_parent_unaffected_magics(self):
        """sanity checks against SmartList features that were not modified"""
        list1 = SmartList([0, 1, 2, 3, "one", "two"])
        list2 = SmartList([])
        list3 = SmartList([0, 2, 3, 4])
        list4 = SmartList([0, 1, 2])

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

    def test_parent_methods(self):
        pass
        # append
        # count
        # extend
        # index
        # insert
        # pop
        # remove
        # reverse
        # sort

    def test_child_magics(self):
        pass
        # if py3k:
        #     __str__
        #     __bytes__
        # else:
        #     __unicode__
        #     __str__
        # __repr__
        # __lt__
        # __le__
        # __eq__
        # __ne__
        # __gt__
        # __ge__
        # if py3k:
        #     __bool__
        # else:
        #     __nonzero__
        # __len__
        # __getitem__
        # __setitem__
        # __delitem__
        # __iter__
        # __reversed__
        # __contains__
        # if not py3k:
        #     __getslice__
        #     __setslice__
        #     __delslice__
        # __add__
        # __radd__
        # __iadd__
        # __mul__
        # __rmul__
        # __imul__

    def test_child_methods(self):
        pass
        # append
        # count
        # extend
        # index
        # insert
        # pop
        # remove
        # reverse
        # sort

    def test_influence(self):
        pass
        # test whether changes are propogated correctly
        # also test whether children that exit scope are removed from parent's map

if __name__ == "__main__":
    unittest.main(verbosity=2)

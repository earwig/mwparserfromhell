# Copyright (C) 2012-2023 Ben Kurtovic <ben.kurtovic@gmail.com>
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
Test cases for the SmartList class and its child, ListProxy.
"""

import pickle

import pytest

from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.smart_list.list_proxy import ListProxy


def _test_get_set_del_item(builder):
    """Run tests on __get/set/delitem__ of a list built with *builder*."""
    list1 = builder([0, 1, 2, 3, "one", "two"])
    list2 = builder(list(range(10)))

    assert 1 == list1[1]
    assert "one" == list1[-2]
    assert [2, 3] == list1[2:4]
    with pytest.raises(IndexError):
        list1[6]
    with pytest.raises(IndexError):
        list1[-7]

    assert [0, 1, 2] == list1[:3]
    assert [0, 1, 2, 3, "one", "two"] == list1[:]
    assert [3, "one", "two"] == list1[3:]
    assert [3, "one", "two"] == list1[3:100]
    assert ["one", "two"] == list1[-2:]
    assert [0, 1] == list1[:-4]
    assert [] == list1[6:]
    assert [] == list1[4:2]

    assert [0, 2, "one"] == list1[0:5:2]
    assert [0, 2] == list1[0:-3:2]
    assert [0, 1, 2, 3, "one", "two"] == list1[::]
    assert [2, 3, "one", "two"] == list1[2::]
    assert [0, 1, 2, 3] == list1[:4:]
    assert [2, 3] == list1[2:4:]
    assert [0, 2, 4, 6, 8] == list2[::2]
    assert [2, 5, 8] == list2[2::3]
    assert [0, 3] == list2[:6:3]
    assert [2, 5, 8] == list2[-8:9:3]
    assert [] == list2[100000:1000:-100]

    list1[3] = 100
    assert 100 == list1[3]
    list1[-3] = 101
    assert [0, 1, 2, 101, "one", "two"] == list1
    list1[5:] = [6, 7, 8]
    assert [6, 7, 8] == list1[5:]
    assert [0, 1, 2, 101, "one", 6, 7, 8] == list1
    list1[2:4] = [-1, -2, -3, -4, -5]
    assert [0, 1, -1, -2, -3, -4, -5, "one", 6, 7, 8] == list1
    list1[0:-3] = [99]
    assert [99, 6, 7, 8] == list1
    list2[0:6:2] = [100, 102, 104]
    assert [100, 1, 102, 3, 104, 5, 6, 7, 8, 9] == list2
    list2[::3] = [200, 203, 206, 209]
    assert [200, 1, 102, 203, 104, 5, 206, 7, 8, 209] == list2
    list2[::] = range(7)
    assert [0, 1, 2, 3, 4, 5, 6] == list2
    with pytest.raises(ValueError):
        list2[0:5:2] = [100, 102, 104, 106]
    with pytest.raises(IndexError):
        list2[7] = "foo"
    with pytest.raises(IndexError):
        list2[-8] = "foo"

    del list2[2]
    assert [0, 1, 3, 4, 5, 6] == list2
    del list2[-3]
    assert [0, 1, 3, 5, 6] == list2
    with pytest.raises(IndexError):
        del list2[100]
    with pytest.raises(IndexError):
        del list2[-6]
    list2[:] = range(10)
    del list2[3:6]
    assert [0, 1, 2, 6, 7, 8, 9] == list2
    del list2[-2:]
    assert [0, 1, 2, 6, 7] == list2
    del list2[:2]
    assert [2, 6, 7] == list2
    list2[:] = range(10)
    del list2[2:8:2]
    assert [0, 1, 3, 5, 7, 8, 9] == list2


def _test_add_radd_iadd(builder):
    """Run tests on __r/i/add__ of a list built with *builder*."""
    list1 = builder(range(5))
    list2 = builder(range(5, 10))
    assert [0, 1, 2, 3, 4, 5, 6] == list1 + [5, 6]
    assert [0, 1, 2, 3, 4] == list1
    assert list(range(10)) == list1 + list2
    assert [-2, -1, 0, 1, 2, 3, 4], [-2, -1] + list1
    assert [0, 1, 2, 3, 4] == list1
    list1 += ["foo", "bar", "baz"]
    assert [0, 1, 2, 3, 4, "foo", "bar", "baz"] == list1


def _test_other_magic_methods(builder):
    """Run tests on other magic methods of a list built with *builder*."""
    list1 = builder([0, 1, 2, 3, "one", "two"])
    list2 = builder([])
    list3 = builder([0, 2, 3, 4])
    list4 = builder([0, 1, 2])

    assert "[0, 1, 2, 3, 'one', 'two']" == str(list1)
    assert b"\x00\x01\x02" == bytes(list4)
    assert "[0, 1, 2, 3, 'one', 'two']" == repr(list1)

    assert list1 < list3
    assert list1 <= list3
    assert list1 != list3
    assert list1 != list3
    assert list1 <= list3
    assert list1 < list3

    other1 = [0, 2, 3, 4]
    assert list1 < other1
    assert list1 <= other1
    assert list1 != other1
    assert list1 != other1
    assert list1 <= other1
    assert list1 < other1

    other2 = [0, 0, 1, 2]
    assert list1 >= other2
    assert list1 > other2
    assert list1 != other2
    assert list1 != other2
    assert list1 > other2
    assert list1 >= other2

    other3 = [0, 1, 2, 3, "one", "two"]
    assert list1 >= other3
    assert list1 <= other3
    assert list1 == other3
    assert list1 == other3
    assert list1 <= other3
    assert list1 >= other3

    assert bool(list1) is True
    assert bool(list2) is False

    assert 6 == len(list1)
    assert 0 == len(list2)

    out = []
    for obj in list1:
        out.append(obj)
    assert [0, 1, 2, 3, "one", "two"] == out

    out = []
    for ch in list2:
        out.append(ch)
    assert [] == out

    gen1 = iter(list1)
    out = []
    for _ in range(len(list1)):
        out.append(next(gen1))
    with pytest.raises(StopIteration):
        next(gen1)
    assert [0, 1, 2, 3, "one", "two"] == out
    gen2 = iter(list2)
    with pytest.raises(StopIteration):
        next(gen2)

    assert ["two", "one", 3, 2, 1, 0] == list(reversed(list1))
    assert [] == list(reversed(list2))

    assert "one" in list1
    assert 3 in list1
    assert 10 not in list1
    assert 0 not in list2

    assert [] == list2 * 5
    assert [] == 5 * list2
    assert [0, 1, 2, 0, 1, 2, 0, 1, 2] == list4 * 3
    assert [0, 1, 2, 0, 1, 2, 0, 1, 2] == 3 * list4
    list4 *= 2
    assert [0, 1, 2, 0, 1, 2] == list4


def _test_list_methods(builder):
    """Run tests on the public methods of a list built with *builder*."""
    list1 = builder(range(5))
    list2 = builder(["foo"])
    list3 = builder([("a", 5), ("d", 2), ("b", 8), ("c", 3)])

    list1.append(5)
    list1.append(1)
    list1.append(2)
    assert [0, 1, 2, 3, 4, 5, 1, 2] == list1

    assert 0 == list1.count(6)
    assert 2 == list1.count(1)

    list1.extend(range(5, 8))
    assert [0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 7] == list1

    assert 1 == list1.index(1)
    assert 6 == list1.index(1, 3)
    assert 6 == list1.index(1, 3, 7)
    with pytest.raises(ValueError):
        list1.index(1, 3, 5)

    list1.insert(0, -1)
    assert [-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 7] == list1
    list1.insert(-1, 6.5)
    assert [-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5, 7] == list1
    list1.insert(13, 8)
    assert [-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5, 7, 8] == list1

    assert 8 == list1.pop()
    assert 7 == list1.pop()
    assert [-1, 0, 1, 2, 3, 4, 5, 1, 2, 5, 6, 6.5] == list1
    assert -1 == list1.pop(0)
    assert 5 == list1.pop(5)
    assert 6.5 == list1.pop(-1)
    assert [0, 1, 2, 3, 4, 1, 2, 5, 6] == list1
    assert "foo" == list2.pop()
    with pytest.raises(IndexError):
        list2.pop()
    assert [] == list2

    list1.remove(6)
    assert [0, 1, 2, 3, 4, 1, 2, 5] == list1
    list1.remove(1)
    assert [0, 2, 3, 4, 1, 2, 5] == list1
    list1.remove(1)
    assert [0, 2, 3, 4, 2, 5] == list1
    with pytest.raises(ValueError):
        list1.remove(1)

    list1.reverse()
    assert [5, 2, 4, 3, 2, 0] == list1

    list1.sort()
    assert [0, 2, 2, 3, 4, 5] == list1
    list1.sort(reverse=True)
    assert [5, 4, 3, 2, 2, 0] == list1
    list3.sort(key=lambda i: i[1])
    assert [("d", 2), ("c", 3), ("a", 5), ("b", 8)] == list3
    list3.sort(key=lambda i: i[1], reverse=True)
    assert [("b", 8), ("a", 5), ("c", 3), ("d", 2)] == list3


def _dispatch_test_for_children(meth):
    """Run a test method on various different types of children."""
    meth(lambda L: SmartList(list(L))[:])
    meth(lambda L: SmartList([999] + list(L))[1:])
    meth(lambda L: SmartList(list(L) + [999])[:-1])
    meth(lambda L: SmartList([101, 102] + list(L) + [201, 202])[2:-2])


def test_docs():
    """make sure the methods of SmartList/ListProxy have docstrings"""
    methods = [
        "append",
        "count",
        "extend",
        "index",
        "insert",
        "pop",
        "remove",
        "reverse",
        "sort",
    ]
    for meth in methods:
        expected = getattr(list, meth).__doc__
        smartlist_doc = getattr(SmartList, meth).__doc__
        listproxy_doc = getattr(ListProxy, meth).__doc__
        assert expected == smartlist_doc
        assert expected == listproxy_doc


def test_doctest():
    """make sure the test embedded in SmartList's docstring passes"""
    parent = SmartList([0, 1, 2, 3])
    assert [0, 1, 2, 3] == parent
    child = parent[2:]
    assert [2, 3] == child
    child.append(4)
    assert [2, 3, 4] == child
    assert [0, 1, 2, 3, 4] == parent


def test_parent_get_set_del():
    """make sure SmartList's getitem/setitem/delitem work"""
    _test_get_set_del_item(SmartList)


def test_parent_add():
    """make sure SmartList's add/radd/iadd work"""
    _test_add_radd_iadd(SmartList)


def test_parent_other_magics():
    """make sure SmartList's other magically implemented features work"""
    _test_other_magic_methods(SmartList)


def test_parent_methods():
    """make sure SmartList's non-magic methods work, like append()"""
    _test_list_methods(SmartList)


def test_child_get_set_del():
    """make sure ListProxy's getitem/setitem/delitem work"""
    _dispatch_test_for_children(_test_get_set_del_item)


def test_child_add():
    """make sure ListProxy's add/radd/iadd work"""
    _dispatch_test_for_children(_test_add_radd_iadd)


def test_child_other_magics():
    """make sure ListProxy's other magically implemented features work"""
    _dispatch_test_for_children(_test_other_magic_methods)


def test_child_methods():
    """make sure ListProxy's non-magic methods work, like append()"""
    _dispatch_test_for_children(_test_list_methods)


def test_influence():
    """make sure changes are propagated from parents to children"""
    parent = SmartList([0, 1, 2, 3, 4, 5])
    child1 = parent[2:]
    child2 = parent[2:5]
    assert [0, 1, 2, 3, 4, 5] == parent
    assert [2, 3, 4, 5] == child1
    assert [2, 3, 4] == child2
    assert 2 == len(parent._children)

    parent.append(6)
    child1.append(7)
    child2.append(4.5)
    assert [0, 1, 2, 3, 4, 4.5, 5, 6, 7] == parent
    assert [2, 3, 4, 4.5, 5, 6, 7] == child1
    assert [2, 3, 4, 4.5] == child2

    parent.insert(0, -1)
    parent.insert(4, 2.5)
    parent.insert(10, 6.5)
    assert [-1, 0, 1, 2, 2.5, 3, 4, 4.5, 5, 6, 6.5, 7] == parent
    assert [2, 2.5, 3, 4, 4.5, 5, 6, 6.5, 7] == child1
    assert [2, 2.5, 3, 4, 4.5] == child2

    assert 7 == parent.pop()
    assert 6.5 == child1.pop()
    assert 4.5 == child2.pop()
    assert [-1, 0, 1, 2, 2.5, 3, 4, 5, 6] == parent
    assert [2, 2.5, 3, 4, 5, 6] == child1
    assert [2, 2.5, 3, 4] == child2

    parent.remove(-1)
    child1.remove(2.5)
    assert [0, 1, 2, 3, 4, 5, 6] == parent
    assert [2, 3, 4, 5, 6] == child1
    assert [2, 3, 4] == child2

    assert 0 == parent.pop(0)
    assert [1, 2, 3, 4, 5, 6] == parent
    assert [2, 3, 4, 5, 6] == child1
    assert [2, 3, 4] == child2

    child2.reverse()
    assert [1, 4, 3, 2, 5, 6] == parent
    assert [4, 3, 2, 5, 6] == child1
    assert [4, 3, 2] == child2

    parent.extend([7, 8])
    child1.extend([8.1, 8.2])
    child2.extend([1.9, 1.8])
    assert [1, 4, 3, 2, 1.9, 1.8, 5, 6, 7, 8, 8.1, 8.2] == parent
    assert [4, 3, 2, 1.9, 1.8, 5, 6, 7, 8, 8.1, 8.2] == child1
    assert [4, 3, 2, 1.9, 1.8] == child2

    child3 = parent[9:]
    assert [8, 8.1, 8.2] == child3

    del parent[8:]
    assert [1, 4, 3, 2, 1.9, 1.8, 5, 6] == parent
    assert [4, 3, 2, 1.9, 1.8, 5, 6] == child1
    assert [4, 3, 2, 1.9, 1.8] == child2
    assert [] == child3
    assert 0 == len(child3)

    del child1
    assert [1, 4, 3, 2, 1.9, 1.8, 5, 6] == parent
    assert [4, 3, 2, 1.9, 1.8] == child2
    assert [] == child3
    assert 2 == len(parent._children)

    del child3
    assert [1, 4, 3, 2, 1.9, 1.8, 5, 6] == parent
    assert [4, 3, 2, 1.9, 1.8] == child2
    assert 1 == len(parent._children)

    parent.remove(1.9)
    parent.remove(1.8)
    assert [1, 4, 3, 2, 5, 6] == parent
    assert [4, 3, 2] == child2

    parent.reverse()
    assert [6, 5, 2, 3, 4, 1] == parent
    assert [4, 3, 2] == child2
    assert 0 == len(parent._children)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickling(protocol: int):
    """test SmartList objects behave properly when pickling"""
    parent = SmartList([0, 1, 2, 3, 4, 5])
    enc = pickle.dumps(parent, protocol=protocol)
    assert pickle.loads(enc) == parent

    child = parent[1:3]
    assert len(parent._children) == 1
    assert list(parent._children.values())[0][0]() is child
    enc = pickle.dumps(parent, protocol=protocol)
    parent2 = pickle.loads(enc)
    assert parent2 == parent
    assert parent2._children == {}

    enc = pickle.dumps(child, protocol=protocol)
    child2 = pickle.loads(enc)
    assert child2 == child
    assert child2._parent == parent
    assert child2._parent is not parent
    assert len(child2._parent._children) == 1
    assert list(child2._parent._children.values())[0][0]() is child2

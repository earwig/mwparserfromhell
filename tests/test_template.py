# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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
Test cases for the Template node.
"""

from difflib import unified_diff

import pytest

from mwparserfromhell.nodes import HTMLEntity, Template, Text
from mwparserfromhell.nodes.extras import Parameter
from mwparserfromhell import parse
from .conftest import assert_wikicode_equal, wrap, wraptext

pgens = lambda k, v: Parameter(wraptext(k), wraptext(v), showkey=True)
pgenh = lambda k, v: Parameter(wraptext(k), wraptext(v), showkey=False)


def test_str():
    """test Template.__str__()"""
    node = Template(wraptext("foobar"))
    assert "{{foobar}}" == str(node)
    node2 = Template(wraptext("foo"), [pgenh("1", "bar"), pgens("abc", "def")])
    assert "{{foo|bar|abc=def}}" == str(node2)


def test_children():
    """test Template.__children__()"""
    node2p1 = Parameter(wraptext("1"), wraptext("bar"), showkey=False)
    node2p2 = Parameter(wraptext("abc"), wrap([Text("def"), Text("ghi")]), showkey=True)
    node1 = Template(wraptext("foobar"))
    node2 = Template(wraptext("foo"), [node2p1, node2p2])

    gen1 = node1.__children__()
    gen2 = node2.__children__()
    assert node1.name == next(gen1)
    assert node2.name == next(gen2)
    assert node2.params[0].value == next(gen2)
    assert node2.params[1].name == next(gen2)
    assert node2.params[1].value == next(gen2)
    with pytest.raises(StopIteration):
        next(gen1)
    with pytest.raises(StopIteration):
        next(gen2)


def test_strip():
    """test Template.__strip__()"""
    node1 = Template(wraptext("foobar"))
    node2 = Template(
        wraptext("foo"), [pgenh("1", "bar"), pgens("foo", ""), pgens("abc", "def")]
    )
    node3 = Template(
        wraptext("foo"),
        [
            pgenh("1", "foo"),
            Parameter(
                wraptext("2"), wrap([Template(wraptext("hello"))]), showkey=False
            ),
            pgenh("3", "bar"),
        ],
    )

    assert node1.__strip__(keep_template_params=False) is None
    assert node2.__strip__(keep_template_params=False) is None
    assert "" == node1.__strip__(keep_template_params=True)
    assert "bar def" == node2.__strip__(keep_template_params=True)
    assert "foo bar" == node3.__strip__(keep_template_params=True)


def test_showtree():
    """test Template.__showtree__()"""
    output = []
    getter, marker = object(), object()
    get = lambda code: output.append((getter, code))
    mark = lambda: output.append(marker)
    node1 = Template(wraptext("foobar"))
    node2 = Template(wraptext("foo"), [pgenh("1", "bar"), pgens("abc", "def")])
    node1.__showtree__(output.append, get, mark)
    node2.__showtree__(output.append, get, mark)
    valid = [
        "{{",
        (getter, node1.name),
        "}}",
        "{{",
        (getter, node2.name),
        "    | ",
        marker,
        (getter, node2.params[0].name),
        "    = ",
        marker,
        (getter, node2.params[0].value),
        "    | ",
        marker,
        (getter, node2.params[1].name),
        "    = ",
        marker,
        (getter, node2.params[1].value),
        "}}",
    ]
    assert valid == output


def test_name():
    """test getter/setter for the name attribute"""
    name = wraptext("foobar")
    node1 = Template(name)
    node2 = Template(name, [pgenh("1", "bar")])
    assert name is node1.name
    assert name is node2.name
    node1.name = "asdf"
    node2.name = "téstïng"
    assert_wikicode_equal(wraptext("asdf"), node1.name)
    assert_wikicode_equal(wraptext("téstïng"), node2.name)


def test_params():
    """test getter for the params attribute"""
    node1 = Template(wraptext("foobar"))
    plist = [pgenh("1", "bar"), pgens("abc", "def")]
    node2 = Template(wraptext("foo"), plist)
    assert [] == node1.params
    assert plist is node2.params


def test_has():
    """test Template.has()"""
    node1 = Template(wraptext("foobar"))
    node2 = Template(wraptext("foo"), [pgenh("1", "bar"), pgens("\nabc ", "def")])
    node3 = Template(
        wraptext("foo"), [pgenh("1", "a"), pgens("b", "c"), pgens("1", "d")]
    )
    node4 = Template(wraptext("foo"), [pgenh("1", "a"), pgens("b", " ")])
    assert node1.has("foobar", False) is False
    assert node2.has(1, False) is True
    assert node2.has("abc", False) is True
    assert node2.has("def", False) is False
    assert node3.has("1", False) is True
    assert node3.has(" b ", False) is True
    assert node4.has("b", False) is True
    assert node3.has("b", True) is True
    assert node4.has("b", True) is False
    assert node1.has_param("foobar", False) is False
    assert node2.has_param(1, False) is True


def test_get():
    """test Template.get()"""
    node1 = Template(wraptext("foobar"))
    node2p1 = pgenh("1", "bar")
    node2p2 = pgens("abc", "def")
    node2 = Template(wraptext("foo"), [node2p1, node2p2])
    node3p1 = pgens("b", "c")
    node3p2 = pgens("1", "d")
    node3 = Template(wraptext("foo"), [pgenh("1", "a"), node3p1, node3p2])
    node4p1 = pgens(" b", " ")
    node4 = Template(wraptext("foo"), [pgenh("1", "a"), node4p1])
    with pytest.raises(ValueError):
        node1.get("foobar")
    assert node2p1 is node2.get(1)
    assert node2p2 is node2.get("abc")
    with pytest.raises(ValueError):
        node2.get("def")
    assert node3p1 is node3.get("b")
    assert node3p2 is node3.get("1")
    assert node4p1 is node4.get("b ")


def test_add():
    """test Template.add()"""
    node1 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
    node2 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
    node3 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
    node4 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
    node5 = Template(wraptext("a"), [pgens("b", "c"), pgens("    d ", "e")])
    node6 = Template(wraptext("a"), [pgens("b", "c"), pgens("b", "d"), pgens("b", "e")])
    node7 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
    node8p = pgenh("1", "d")
    node8 = Template(wraptext("a"), [pgens("b", "c"), node8p])
    node9 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "d")])
    node10 = Template(wraptext("a"), [pgens("b", "c"), pgenh("1", "e")])
    node11 = Template(wraptext("a"), [pgens("b", "c")])
    node12 = Template(wraptext("a"), [pgens("b", "c")])
    node13 = Template(
        wraptext("a"), [pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")]
    )
    node14 = Template(
        wraptext("a\n"),
        [
            pgens("b ", "c\n"),
            pgens("d ", " e"),
            pgens("f ", "g\n"),
            pgens("h ", " i\n"),
        ],
    )
    node15 = Template(
        wraptext("a"),
        [pgens("b  ", " c\n"), pgens("\nd  ", " e"), pgens("\nf  ", "g ")],
    )
    node16 = Template(
        wraptext("a"), [pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")]
    )
    node17 = Template(wraptext("a"), [pgenh("1", "b")])
    node18 = Template(wraptext("a"), [pgenh("1", "b")])
    node19 = Template(wraptext("a"), [pgenh("1", "b")])
    node20 = Template(
        wraptext("a"),
        [pgenh("1", "b"), pgenh("2", "c"), pgenh("3", "d"), pgenh("4", "e")],
    )
    node21 = Template(
        wraptext("a"),
        [pgenh("1", "b"), pgenh("2", "c"), pgens("4", "d"), pgens("5", "e")],
    )
    node22 = Template(
        wraptext("a"),
        [pgenh("1", "b"), pgenh("2", "c"), pgens("4", "d"), pgens("5", "e")],
    )
    node23 = Template(wraptext("a"), [pgenh("1", "b")])
    node24 = Template(wraptext("a"), [pgenh("1", "b")])
    node25 = Template(wraptext("a"), [pgens("b", "c")])
    node26 = Template(wraptext("a"), [pgenh("1", "b")])
    node27 = Template(wraptext("a"), [pgenh("1", "b")])
    node28 = Template(wraptext("a"), [pgens("1", "b")])
    node29 = Template(
        wraptext("a"), [pgens("\nb ", " c"), pgens("\nd ", " e"), pgens("\nf ", " g")]
    )
    node30 = Template(
        wraptext("a\n"),
        [
            pgens("b ", "c\n"),
            pgens("d ", " e"),
            pgens("f ", "g\n"),
            pgens("h ", " i\n"),
        ],
    )
    node31 = Template(
        wraptext("a"),
        [pgens("b  ", " c\n"), pgens("\nd  ", " e"), pgens("\nf  ", "g ")],
    )
    node32 = Template(
        wraptext("a"),
        [pgens("\nb ", " c "), pgens("\nd ", " e "), pgens("\nf ", " g ")],
    )
    node33 = Template(
        wraptext("a"),
        [
            pgens("b", "c"),
            pgens("d", "e"),
            pgens("b", "f"),
            pgens("b", "h"),
            pgens("i", "j"),
        ],
    )
    node34 = Template(
        wraptext("a"),
        [pgens("1", "b"), pgens("x", "y"), pgens("1", "c"), pgens("2", "d")],
    )
    node35 = Template(
        wraptext("a"),
        [pgens("1", "b"), pgens("x", "y"), pgenh("1", "c"), pgenh("2", "d")],
    )
    node36 = Template(
        wraptext("a"), [pgens("b", "c"), pgens("d", "e"), pgens("f", "g")]
    )
    node37 = Template(wraptext("a"), [pgenh("1", "")])
    node38 = Template(wraptext("abc"))
    node39 = Template(wraptext("a"), [pgenh("1", " b ")])
    node40 = Template(wraptext("a"), [pgenh("1", " b"), pgenh("2", " c")])
    node41 = Template(wraptext("a"), [pgens("1", " b"), pgens("2", " c")])
    node42 = Template(wraptext("a"), [pgens("b", "  \n")])

    node1.add("e", "f", showkey=True)
    node2.add(2, "g", showkey=False)
    node3.add("e", "foo|bar", showkey=True)
    node4.add("e", "f", showkey=True, before="b")
    node5.add("f", "g", showkey=True, before=" d     ")
    node6.add("f", "g", showkey=True, before="b")
    with pytest.raises(ValueError):
        node7.add("e", "f", showkey=True, before="q")
    node8.add("e", "f", showkey=True, before=node8p)
    node9.add("e", "f", showkey=True, before=pgenh("1", "d"))
    with pytest.raises(ValueError):
        node10.add("e", "f", showkey=True, before=pgenh("1", "d"))
    node11.add("d", "foo=bar", showkey=True)
    node12.add("1", "foo=bar", showkey=False)
    node13.add("h", "i", showkey=True)
    node14.add("j", "k", showkey=True)
    node15.add("h", "i", showkey=True)
    node16.add("h", "i", showkey=True, preserve_spacing=False)
    node17.add("2", "c")
    node18.add("3", "c")
    node19.add("c", "d")
    node20.add("5", "f")
    node21.add("3", "f")
    node22.add("6", "f")
    node23.add("c", "foo=bar")
    node24.add("2", "foo=bar")
    node25.add("b", "d")
    node26.add("1", "foo=bar")
    node27.add("1", "foo=bar", showkey=True)
    node28.add("1", "foo=bar", showkey=False)
    node29.add("d", "foo")
    node30.add("f", "foo")
    node31.add("f", "foo")
    node32.add("d", "foo", preserve_spacing=False)
    node33.add("b", "k")
    node34.add("1", "e")
    node35.add("1", "e")
    node36.add("d", "h", before="b")
    node37.add(1, "b")
    node38.add("1", "foo")
    with pytest.raises(ValueError):
        node38.add("z", "bar", showkey=False)
    node39.add("1", "c")
    node40.add("3", "d")
    node41.add("3", "d")
    node42.add("b", "hello")

    assert "{{a|b=c|d|e=f}}" == node1
    assert "{{a|b=c|d|g}}" == node2
    assert "{{a|b=c|d|e=foo&#124;bar}}" == node3
    assert isinstance(node3.params[2].value.get(1), HTMLEntity)
    assert "{{a|e=f|b=c|d}}" == node4
    assert "{{a|b=c|f=g|    d =e}}" == node5
    assert "{{a|b=c|b=d|f=g|b=e}}" == node6
    assert "{{a|b=c|d}}" == node7
    assert "{{a|b=c|e=f|d}}" == node8
    assert "{{a|b=c|e=f|d}}" == node9
    assert "{{a|b=c|e}}" == node10
    assert "{{a|b=c|d=foo=bar}}" == node11
    assert "{{a|b=c|foo&#61;bar}}" == node12
    assert isinstance(node12.params[1].value.get(1), HTMLEntity)
    assert "{{a|\nb = c|\nd = e|\nf = g|\nh = i}}" == node13
    assert "{{a\n|b =c\n|d = e|f =g\n|h = i\n|j =k\n}}" == node14
    assert "{{a|b  = c\n|\nd  = e|\nf  =g |\nh  = i}}" == node15
    assert "{{a|\nb = c|\nd = e|\nf = g|h=i}}" == node16
    assert "{{a|b|c}}" == node17
    assert "{{a|b|3=c}}" == node18
    assert "{{a|b|c=d}}" == node19
    assert "{{a|b|c|d|e|f}}" == node20
    assert "{{a|b|c|4=d|5=e|f}}" == node21
    assert "{{a|b|c|4=d|5=e|6=f}}" == node22
    assert "{{a|b|c=foo=bar}}" == node23
    assert "{{a|b|foo&#61;bar}}" == node24
    assert isinstance(node24.params[1].value.get(1), HTMLEntity)
    assert "{{a|b=d}}" == node25
    assert "{{a|foo&#61;bar}}" == node26
    assert isinstance(node26.params[0].value.get(1), HTMLEntity)
    assert "{{a|1=foo=bar}}" == node27
    assert "{{a|foo&#61;bar}}" == node28
    assert isinstance(node28.params[0].value.get(1), HTMLEntity)
    assert "{{a|\nb = c|\nd = foo|\nf = g}}" == node29
    assert "{{a\n|b =c\n|d = e|f =foo\n|h = i\n}}" == node30
    assert "{{a|b  = c\n|\nd  = e|\nf  =foo }}" == node31
    assert "{{a|\nb = c |\nd =foo|\nf = g }}" == node32
    assert "{{a|b=k|d=e|i=j}}" == node33
    assert "{{a|1=e|x=y|2=d}}" == node34
    assert "{{a|x=y|e|d}}" == node35
    assert "{{a|b=c|d=h|f=g}}" == node36
    assert "{{a|b}}" == node37
    assert "{{abc|foo}}" == node38
    assert "{{a|c}}" == node39
    assert "{{a| b| c|d}}" == node40
    assert "{{a|1= b|2= c|3= d}}" == node41
    assert "{{a|b=hello  \n}}" == node42


def test_remove():
    """test Template.remove()"""
    node1 = Template(wraptext("foobar"))
    node2 = Template(wraptext("foo"), [pgenh("1", "bar"), pgens("abc", "def")])
    node3 = Template(wraptext("foo"), [pgenh("1", "bar"), pgens("abc", "def")])
    node4 = Template(wraptext("foo"), [pgenh("1", "bar"), pgenh("2", "baz")])
    node5 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node6 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node7 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgens("  1", "b"), pgens("2", "c")]
    )
    node8 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgens("  1", "b"), pgens("2", "c")]
    )
    node9 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")]
    )
    node10 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")]
    )
    node11 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node12 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node13 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node14 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node15 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node16 = Template(
        wraptext("foo"), [pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")]
    )
    node17 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")]
    )
    node18 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")]
    )
    node19 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")]
    )
    node20 = Template(
        wraptext("foo"), [pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")]
    )
    node21 = Template(
        wraptext("foo"),
        [
            pgens("a", "b"),
            pgens("c", "d"),
            pgens("e", "f"),
            pgens("a", "b"),
            pgens("a", "b"),
        ],
    )
    node22 = Template(
        wraptext("foo"),
        [
            pgens("a", "b"),
            pgens("c", "d"),
            pgens("e", "f"),
            pgens("a", "b"),
            pgens("a", "b"),
        ],
    )
    node23 = Template(
        wraptext("foo"),
        [
            pgens("a", "b"),
            pgens("c", "d"),
            pgens("e", "f"),
            pgens("a", "b"),
            pgens("a", "b"),
        ],
    )
    node24 = Template(
        wraptext("foo"),
        [
            pgens("a", "b"),
            pgens("c", "d"),
            pgens("e", "f"),
            pgens("a", "b"),
            pgens("a", "b"),
        ],
    )
    node25 = Template(
        wraptext("foo"),
        [
            pgens("a", "b"),
            pgens("c", "d"),
            pgens("e", "f"),
            pgens("a", "b"),
            pgens("a", "b"),
        ],
    )
    node26 = Template(
        wraptext("foo"),
        [
            pgens("a", "b"),
            pgens("c", "d"),
            pgens("e", "f"),
            pgens("a", "b"),
            pgens("a", "b"),
        ],
    )
    node27 = Template(wraptext("foo"), [pgenh("1", "bar")])
    node28 = Template(wraptext("foo"), [pgenh("1", "bar")])

    node2.remove("1")
    node2.remove("abc")
    node3.remove(1, keep_field=True)
    node3.remove("abc", keep_field=True)
    node4.remove("1", keep_field=False)
    node5.remove("a", keep_field=False)
    node6.remove("a", keep_field=True)
    node7.remove(1, keep_field=True)
    node8.remove(1, keep_field=False)
    node9.remove(1, keep_field=True)
    node10.remove(1, keep_field=False)
    node11.remove(node11.params[0], keep_field=False)
    node12.remove(node12.params[0], keep_field=True)
    node13.remove(node13.params[1], keep_field=False)
    node14.remove(node14.params[1], keep_field=True)
    node15.remove(node15.params[2], keep_field=False)
    node16.remove(node16.params[2], keep_field=True)
    node17.remove(node17.params[0], keep_field=False)
    node18.remove(node18.params[0], keep_field=True)
    node19.remove(node19.params[1], keep_field=False)
    node20.remove(node20.params[1], keep_field=True)
    node21.remove("a", keep_field=False)
    node22.remove("a", keep_field=True)
    node23.remove(node23.params[0], keep_field=False)
    node24.remove(node24.params[0], keep_field=True)
    node25.remove(node25.params[3], keep_field=False)
    node26.remove(node26.params[3], keep_field=True)

    with pytest.raises(ValueError):
        node1.remove(1)
    with pytest.raises(ValueError):
        node1.remove("a")
    with pytest.raises(ValueError):
        node2.remove("1")
    assert "{{foo}}" == node2
    assert "{{foo||abc=}}" == node3
    assert "{{foo|2=baz}}" == node4
    assert "{{foo|b=c}}" == node5
    assert "{{foo| a=|b=c}}" == node6
    assert "{{foo|1  =|2=c}}" == node7
    assert "{{foo|2=c}}" == node8
    assert "{{foo||c}}" == node9
    assert "{{foo|2=c}}" == node10
    assert "{{foo|b=c|a =d}}" == node11
    assert "{{foo| a=|b=c|a =d}}" == node12
    assert "{{foo| a=b|a =d}}" == node13
    assert "{{foo| a=b|b=|a =d}}" == node14
    assert "{{foo| a=b|b=c}}" == node15
    assert "{{foo| a=b|b=c|a =}}" == node16
    assert "{{foo|b|c}}" == node17
    assert "{{foo|1  =|b|c}}" == node18
    assert "{{foo|1  =a|2=c}}" == node19
    assert "{{foo|1  =a||c}}" == node20
    assert "{{foo|c=d|e=f}}" == node21
    assert "{{foo|a=|c=d|e=f}}" == node22
    assert "{{foo|c=d|e=f|a=b|a=b}}" == node23
    assert "{{foo|a=|c=d|e=f|a=b|a=b}}" == node24
    assert "{{foo|a=b|c=d|e=f|a=b}}" == node25
    assert "{{foo|a=b|c=d|e=f|a=|a=b}}" == node26
    with pytest.raises(ValueError):
        node27.remove(node28.get(1))


def test_formatting():
    """test realistic param manipulation with complex whitespace formatting
    (assumes that parsing works correctly)"""
    tests = [
        # https://en.wikipedia.org/w/index.php?title=Lamar_County,_Georgia&oldid=792356004
        (
            """{{Infobox U.S. county
| county = Lamar County
| state = Georgia
| seal =
| founded = 1920
| seat wl = Barnesville
| largest city wl = Barnesville
| area_total_sq_mi = 186
| area_land_sq_mi = 184
| area_water_sq_mi = 2.3
| area percentage = 1.3%
| census yr = 2010
| pop = 18317
| density_sq_mi = 100
| time zone = Eastern
| footnotes =
| web = www.lamarcountyga.com
| ex image = Lamar County Georgia Courthouse.jpg
| ex image cap = Lamar County courthouse in Barnesville
| district = 3rd
| named for = [[Lucius Quintus Cincinnatus Lamar II]]
}}""",
            """@@ -11,4 +11,4 @@
 | area percentage = 1.3%
-| census yr = 2010
-| pop = 18317
+| census estimate yr = 2016
+| pop = 12345<ref>example ref</ref>
 | density_sq_mi = 100""",
        ),
        # https://en.wikipedia.org/w/index.php?title=Rockdale_County,_Georgia&oldid=792359760
        (
            """{{Infobox U.S. County|
 county = Rockdale County |
 state = Georgia |
 seal =  |
 founded = October 18, 1870 |
 seat wl = Conyers |
 largest city wl = Conyers |
 area_total_sq_mi = 132 |
 area_land_sq_mi = 130 |
 area_water_sq_mi = 2.3 |
 area percentage = 1.7% |
 census yr = 2010|
 pop = 85215 |
 density_sq_mi = 657 |
 web = www.rockdalecounty.org
| ex image = Rockdale-county-courthouse.jpg
| ex image cap = Rockdale County Courthouse in Conyers
| district = 4th
| time zone= Eastern
}}""",
            """@@ -11,4 +11,4 @@
  area percentage = 1.7% |
- census yr = 2010|
- pop = 85215 |
+ census estimate yr = 2016 |
+ pop = 12345<ref>example ref</ref> |
  density_sq_mi = 657 |""",
        ),
        # https://en.wikipedia.org/w/index.php?title=Spalding_County,_Georgia&oldid=792360413
        (
            """{{Infobox U.S. County|
| county = Spalding County |
| state = Georgia |
| seal =  |
| founded = 1851 |
| seat wl = Griffin |
| largest city wl = Griffin |
| area_total_sq_mi = 200 |
| area_land_sq_mi = 196 |
| area_water_sq_mi = 3.1 |
| area percentage = 1.6% |
| census yr = 2010|
| pop = 64073 |
| density_sq_mi = 326 |
| web = www.spaldingcounty.com |
| named for = [[Thomas Spalding]]
| ex image = Spalding County Courthouse (NE corner).JPG
| ex image cap = Spalding County Courthouse in Griffin
| district = 3rd
| time zone = Eastern
}}""",
            """@@ -11,4 +11,4 @@
 | area percentage = 1.6% |
-| census yr = 2010|
-| pop = 64073 |
+|
+| census estimate yr = 2016 | pop = 12345<ref>example ref</ref> |
 | density_sq_mi = 326 |""",
        ),
        # https://en.wikipedia.org/w/index.php?title=Clinton_County,_Illinois&oldid=794694648
        (
            """{{Infobox U.S. county
 |county  = Clinton County
 |state = Illinois
| ex image           = File:Clinton County Courthouse, Carlyle.jpg
| ex image cap       = [[Clinton County Courthouse (Illinois)|Clinton County Courthouse]]
 |seal =
 |founded = 1824
 |named for = [[DeWitt Clinton]]
 |seat wl= Carlyle
| largest city wl = Breese
 |time zone=Central
 |area_total_sq_mi = 503
 |area_land_sq_mi = 474
 |area_water_sq_mi = 29
 |area percentage = 5.8%
 |census yr = 2010
 |pop = 37762
 |density_sq_mi = 80
 |web = www.clintonco.illinois.gov
| district = 15th
}}""",
            """@@ -15,4 +15,4 @@
  |area percentage = 5.8%
- |census yr = 2010
- |pop = 37762
+ |census estimate yr = 2016
+ |pop = 12345<ref>example ref</ref>
  |density_sq_mi = 80""",
        ),
        # https://en.wikipedia.org/w/index.php?title=Winnebago_County,_Illinois&oldid=789193800
        (
            """{{Infobox U.S. county |
 county  = Winnebago County |
 state = Illinois |
 seal = Winnebago County il seal.png |
 named for = [[Winnebago (tribe)|Winnebago Tribe]] |
 seat wl= Rockford |
 largest city wl = Rockford|
 area_total_sq_mi = 519 |
 area_land_sq_mi = 513|
 area_water_sq_mi = 5.9 |
 area percentage = 1.1% |
 census yr = 2010|
 pop = 295266 |
 density_sq_mi = 575
| web = www.wincoil.us
| founded year = 1836
| founded date = January 16
| time zone = Central
| district = 16th
| district2 = 17th
}}""",
            """@@ -11,4 +11,4 @@
  area percentage = 1.1% |
- census yr = 2010|
- pop = 295266 |
+ census estimate yr = 2016|
+ pop = 12345<ref>example ref</ref> |
  density_sq_mi = 575""",
        ),
    ]

    for original, expected in tests:
        code = parse(original)
        template = code.filter_templates()[0]
        template.add("pop", "12345<ref>example ref</ref>")
        template.add("census estimate yr", "2016", before="pop")
        template.remove("census yr")

        oldlines = original.splitlines(True)
        newlines = str(code).splitlines(True)
        difflines = unified_diff(oldlines, newlines, n=1)
        diff = "".join(list(difflines)[2:]).strip()
        assert expected == diff

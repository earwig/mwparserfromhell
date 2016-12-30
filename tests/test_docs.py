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

from __future__ import print_function, unicode_literals
import json
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mwparserfromhell
from mwparserfromhell.compat import py3k, str

from .compat import StringIO, urlencode, urlopen

class TestDocs(unittest.TestCase):
    """Integration test cases for mwparserfromhell's documentation."""

    def assertPrint(self, input, output):
        """Assertion check that *input*, when printed, produces *output*."""
        buff = StringIO()
        print(input, end="", file=buff)
        buff.seek(0)
        self.assertEqual(output, buff.read())

    def test_readme_1(self):
        """test a block of example code in the README"""
        text = "I has a template! {{foo|bar|baz|eggs=spam}} See it?"
        wikicode = mwparserfromhell.parse(text)
        self.assertPrint(wikicode,
                         "I has a template! {{foo|bar|baz|eggs=spam}} See it?")
        templates = wikicode.filter_templates()
        if py3k:
            self.assertPrint(templates, "['{{foo|bar|baz|eggs=spam}}']")
        else:
            self.assertPrint(templates, "[u'{{foo|bar|baz|eggs=spam}}']")
        template = templates[0]
        self.assertPrint(template.name, "foo")
        if py3k:
            self.assertPrint(template.params, "['bar', 'baz', 'eggs=spam']")
        else:
            self.assertPrint(template.params, "[u'bar', u'baz', u'eggs=spam']")
        self.assertPrint(template.get(1).value, "bar")
        self.assertPrint(template.get("eggs").value, "spam")

    def test_readme_2(self):
        """test a block of example code in the README"""
        text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
        temps = mwparserfromhell.parse(text).filter_templates()
        if py3k:
            res = "['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']"
        else:
            res = "[u'{{foo|{{bar}}={{baz|{{spam}}}}}}', u'{{bar}}', u'{{baz|{{spam}}}}', u'{{spam}}']"
        self.assertPrint(temps, res)

    def test_readme_3(self):
        """test a block of example code in the README"""
        code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
        if py3k:
            self.assertPrint(code.filter_templates(recursive=False),
                             "['{{foo|this {{includes a|template}}}}']")
        else:
            self.assertPrint(code.filter_templates(recursive=False),
                             "[u'{{foo|this {{includes a|template}}}}']")
        foo = code.filter_templates(recursive=False)[0]
        self.assertPrint(foo.get(1).value, "this {{includes a|template}}")
        self.assertPrint(foo.get(1).value.filter_templates()[0],
                         "{{includes a|template}}")
        self.assertPrint(foo.get(1).value.filter_templates()[0].get(1).value,
                         "template")

    def test_readme_4(self):
        """test a block of example code in the README"""
        text = "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}"
        code = mwparserfromhell.parse(text)
        for template in code.filter_templates():
            if template.name.matches("Cleanup") and not template.has("date"):
                template.add("date", "July 2012")
        res = "{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{uncategorized}}"
        self.assertPrint(code, res)
        code.replace("{{uncategorized}}", "{{bar-stub}}")
        res = "{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}"
        self.assertPrint(code, res)
        if py3k:
            res = "['{{cleanup|date=July 2012}}', '{{bar-stub}}']"
        else:
            res = "[u'{{cleanup|date=July 2012}}', u'{{bar-stub}}']"
        self.assertPrint(code.filter_templates(), res)
        text = str(code)
        res = "{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}"
        self.assertPrint(text, res)
        self.assertEqual(text, code)

    @unittest.skipIf("NOWEB" in os.environ, "web test disabled by environ var")
    def test_readme_5(self):
        """test a block of example code in the README; includes a web call"""
        url1 = "https://en.wikipedia.org/w/api.php"
        url2 = "https://en.wikipedia.org/w/index.php?title={0}&action=raw"
        title = "Test"
        data = {"action": "query", "prop": "revisions", "rvlimit": 1,
                "rvprop": "content", "format": "json", "titles": title}
        try:
            raw = urlopen(url1, urlencode(data).encode("utf8")).read()
        except IOError:
            self.skipTest("cannot continue because of unsuccessful web call")
        res = json.loads(raw.decode("utf8"))
        text = list(res["query"]["pages"].values())[0]["revisions"][0]["*"]
        try:
            expected = urlopen(url2.format(title)).read().decode("utf8")
        except IOError:
            self.skipTest("cannot continue because of unsuccessful web call")
        actual = mwparserfromhell.parse(text)
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main(verbosity=2)

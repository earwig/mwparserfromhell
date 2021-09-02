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

import codecs
from os import listdir, path
import warnings

import pytest

from mwparserfromhell.parser import contexts, tokens
from mwparserfromhell.parser.builder import Builder
from mwparserfromhell.parser.tokenizer import Tokenizer as PyTokenizer

try:
    from mwparserfromhell.parser._tokenizer import CTokenizer
except ImportError:
    CTokenizer = None


class _TestParseError(Exception):
    """Raised internally when a test could not be parsed."""


def _parse_test(test, data):
    """Parse an individual *test*, storing its info in *data*."""
    for line in test.strip().splitlines():
        if line.startswith("name:"):
            data["name"] = line[len("name:") :].strip()
        elif line.startswith("label:"):
            data["label"] = line[len("label:") :].strip()
        elif line.startswith("input:"):
            raw = line[len("input:") :].strip()
            if raw[0] == '"' and raw[-1] == '"':
                raw = raw[1:-1]
            raw = raw.encode("raw_unicode_escape")
            data["input"] = raw.decode("unicode_escape")
        elif line.startswith("output:"):
            raw = line[len("output:") :].strip()
            try:
                data["output"] = eval(raw, vars(tokens))
            except Exception as err:
                raise _TestParseError(err) from err


def _load_tests(filename, name, text):
    """Load all tests in *text* from the file *filename*."""
    tests = text.split("\n---\n")
    for test in tests:
        data = {"name": None, "label": None, "input": None, "output": None}
        try:
            _parse_test(test, data)
        except _TestParseError as err:
            if data["name"]:
                error = "Could not parse test '{0}' in '{1}':\n\t{2}"
                warnings.warn(error.format(data["name"], filename, err))
            else:
                error = "Could not parse a test in '{0}':\n\t{1}"
                warnings.warn(error.format(filename, err))
            continue

        if not data["name"]:
            error = "A test in '{0}' was ignored because it lacked a name"
            warnings.warn(error.format(filename))
            continue
        if data["input"] is None or data["output"] is None:
            error = (
                "Test '{}' in '{}' was ignored because it lacked an input or an output"
            )
            warnings.warn(error.format(data["name"], filename))
            continue

        # Include test filename in name
        data["name"] = "{}:{}".format(name, data["name"])

        yield data


def build():
    """Load and install all tests from the 'tokenizer' directory."""
    directory = path.join(path.dirname(__file__), "tokenizer")
    extension = ".mwtest"
    for filename in listdir(directory):
        if not filename.endswith(extension):
            continue
        fullname = path.join(directory, filename)
        with codecs.open(fullname, "r", encoding="utf8") as fp:
            text = fp.read()
            name = path.split(fullname)[1][: -len(extension)]
            yield from _load_tests(fullname, name, text)


@pytest.mark.parametrize(
    "tokenizer",
    filter(None, (CTokenizer, PyTokenizer)),
    ids=lambda t: "CTokenizer" if t.USES_C else "PyTokenizer",
)
@pytest.mark.parametrize("data", build(), ids=lambda data: data["name"])
def test_tokenizer(tokenizer, data):
    expected = data["output"]
    actual = tokenizer().tokenize(data["input"])
    assert expected == actual


@pytest.mark.parametrize("data", build(), ids=lambda data: data["name"])
def test_roundtrip(data):
    expected = data["input"]
    actual = str(Builder().build(data["output"][:]))
    assert expected == actual


@pytest.mark.skipif(CTokenizer is None, reason="CTokenizer not available")
def test_c_tokenizer_uses_c():
    """make sure the C tokenizer identifies as using a C extension"""
    assert CTokenizer.USES_C is True
    assert CTokenizer().USES_C is True


def test_describe_context():
    assert "" == contexts.describe(0)
    ctx = contexts.describe(contexts.TEMPLATE_PARAM_KEY | contexts.HAS_TEXT)
    assert "TEMPLATE_PARAM_KEY|HAS_TEXT" == ctx

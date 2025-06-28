# Copyright (C) 2012-2025 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from __future__ import annotations

import os
from collections.abc import Generator
from dataclasses import dataclass

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


@dataclass
class _TestCase:
    name: str
    label: str | None
    input: str
    output: list[tokens.Token]


def _load_tests(file_path, filename, text) -> Generator[_TestCase]:
    tests = text.split("\n---\n")
    for test in tests:
        name = None
        label = None
        input = None
        output = None

        for line in test.strip().splitlines():
            if line.startswith("name:"):
                name = line[len("name:") :].strip()
            elif line.startswith("label:"):
                label = line[len("label:") :].strip()
            elif line.startswith("input:"):
                raw = line[len("input:") :].strip()
                if raw[0] == '"' and raw[-1] == '"':
                    raw = raw[1:-1]
                raw = raw.encode("raw_unicode_escape")
                input = raw.decode("unicode_escape")
            elif line.startswith("output:"):
                raw = line[len("output:") :].strip()
                try:
                    output = eval(raw, dict(vars(tokens)))
                except Exception as err:
                    raise _TestParseError(
                        f"Could not parse a test in {file_path!r}:\n\t{err}\n\n"
                        f"Raw test:\n{test}"
                    )

        if not name:
            raise _TestParseError(
                f"Test in {filename!r} lacks a name\nRaw test:\n{test}"
            )
            continue
        if input is None or output is None:
            raise _TestParseError(
                f"Test {name!r} in {file_path!r} lacks an input or an output"
            )
            continue
        if not isinstance(output, list) or not all(
            isinstance(tok, tokens.Token) for tok in output
        ):
            raise _TestParseError(
                f"Test {name!r} in {file_path!r} should have a list of tokens as its output"
            )

        yield _TestCase(
            name=f"{filename}:{name}",
            label=label,
            input=input,
            output=output,
        )


def build():
    """Load and install all tests from the 'tokenizer' directory."""
    directory = os.path.join(os.path.dirname(__file__), "tokenizer")
    extension = ".mwtest"
    for filename in os.listdir(directory):
        if not filename.endswith(extension):
            continue
        fullname = os.path.join(directory, filename)
        with open(fullname, encoding="utf8") as fp:
            text = fp.read()
            name = os.path.split(fullname)[1][: -len(extension)]
            yield from _load_tests(fullname, name, text)


@pytest.mark.parametrize(
    "tokenizer",
    filter(None, (CTokenizer, PyTokenizer)),
    ids=lambda t: "CTokenizer" if t.USES_C else "PyTokenizer",
)
@pytest.mark.parametrize("test_case", build(), ids=lambda test_case: test_case.name)
def test_tokenizer(tokenizer, test_case: _TestCase):
    actual = tokenizer().tokenize(test_case.input)
    assert test_case.output == actual


@pytest.mark.parametrize("test_case", build(), ids=lambda test_case: test_case.name)
def test_roundtrip(test_case: _TestCase):
    actual = str(Builder().build(test_case.output[:]))
    assert test_case.input == actual


@pytest.mark.skipif(CTokenizer is None, reason="CTokenizer not available")
def test_c_tokenizer_uses_c():
    """make sure the C tokenizer identifies as using a C extension"""
    assert CTokenizer is not None
    assert CTokenizer.USES_C is True
    assert CTokenizer().USES_C is True


def test_describe_context():
    assert "" == contexts.describe(0)
    ctx = contexts.describe(contexts.TEMPLATE_PARAM_KEY | contexts.HAS_TEXT)
    assert "TEMPLATE_PARAM_KEY|HAS_TEXT" == ctx

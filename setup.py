#! /usr/bin/env python
#
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

import glob
import os
import platform
import sys
from enum import Enum

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class UseExtension(Enum):
    REQUIRED = 1
    OPTIONAL = 2
    IGNORED = 3


if "WITH_EXTENSION" in os.environ:
    if "WITHOUT_EXTENSION" in os.environ:
        raise RuntimeError("Cannot set both $WITH_EXTENSION and $WITHOUT_EXTENSION")
    value = os.environ["WITH_EXTENSION"].lower()
    if value in ("1", "true", "yes", "required"):
        use_extension = UseExtension.REQUIRED
    elif value == "optional":
        use_extension = UseExtension.OPTIONAL
    elif value in ("0", "false", "no"):
        use_extension = UseExtension.IGNORED
    else:
        raise RuntimeError(
            f"Unknown value for $WITH_EXTENSION; should be '1', '0', or 'optional', "
            f"but found {value!r}"
        )
elif "WITHOUT_EXTENSION" in os.environ:
    value = os.environ["WITHOUT_EXTENSION"].lower()
    if value in ("1", "true", "yes"):
        use_extension = UseExtension.IGNORED
    elif value in ("0", "false", "no"):
        use_extension = UseExtension.REQUIRED
    else:
        raise RuntimeError(
            f"Unknown value for $WITHOUT_EXTENSION; should be '1', or '0', "
            f"but found {value!r}"
        )
elif platform.python_implementation() == "CPython":
    use_extension = UseExtension.REQUIRED
else:
    use_extension = UseExtension.IGNORED

if use_extension == UseExtension.IGNORED:
    ext_modules = []
else:
    tokenizer = Extension(
        "mwparserfromhell.parser._tokenizer",
        sources=sorted(glob.glob("src/mwparserfromhell/parser/ctokenizer/*.c")),
        depends=sorted(glob.glob("src/mwparserfromhell/parser/ctokenizer/*.h")),
        optional=use_extension == UseExtension.OPTIONAL,
    )
    ext_modules = [tokenizer]


def build_ext_patched(self):
    try:
        build_ext_original(self)
    except Exception:
        print(
            """
**********
Note: To avoid building the C tokenizer extension, set the environment variable \
`WITH_EXTENSION=0`.
This will fall back to a pure-Python tokenizer.
**********
""",
            file=sys.stderr,
        )
        raise


build_ext.run, build_ext_original = build_ext_patched, build_ext.run

setup(ext_modules=ext_modules)

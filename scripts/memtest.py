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
Tests for memory leaks in the CTokenizer.

This appears to work mostly fine under Linux, but gives an absurd number of
false positives on macOS. I'm not sure why. Running the tests multiple times
yields different results (tests don't always leak, and the amount they leak by
varies). Increasing the number of loops results in a smaller bytes/loop value,
too, indicating the increase in memory usage might be due to something else.
Actual memory leaks typically leak very large amounts of memory (megabytes)
and scale with the number of loops.
"""

from locale import LC_ALL, setlocale
from multiprocessing import Process, Pipe
from os import listdir, path
import sys

import psutil

from mwparserfromhell.parser._tokenizer import CTokenizer

LOOPS = 10000


class Color:
    GRAY = "\x1b[30;1m"
    GREEN = "\x1b[92m"
    YELLOW = "\x1b[93m"
    RESET = "\x1b[0m"


class MemoryTest:
    """Manages a memory test."""

    def __init__(self):
        self._tests = []
        self._load()

    def _parse_file(self, name, text):
        tests = text.split("\n---\n")
        counter = 1
        digits = len(str(len(tests)))
        for test in tests:
            data = {"name": None, "label": None, "input": None, "output": None}
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
            number = str(counter).zfill(digits)
            fname = "test_{}{}_{}".format(name, number, data["name"])
            self._tests.append((fname, data["input"]))
            counter += 1

    def _load(self):
        def load_file(filename):
            with open(filename, "rU") as fp:
                text = fp.read()
                name = path.split(filename)[1][: 0 - len(extension)]
                self._parse_file(name, text)

        root = path.split(path.dirname(path.abspath(__file__)))[0]
        directory = path.join(root, "tests", "tokenizer")
        extension = ".mwtest"
        if len(sys.argv) > 2 and sys.argv[1] == "--use":
            for name in sys.argv[2:]:
                load_file(path.join(directory, name + extension))
            sys.argv = [sys.argv[0]]  # So unittest doesn't try to load these
        else:
            for filename in listdir(directory):
                if not filename.endswith(extension):
                    continue
                load_file(path.join(directory, filename))

    @staticmethod
    def _print_results(info1, info2):
        r1, r2 = info1.rss, info2.rss
        buff = 8192
        if r2 - buff > r1:
            d = r2 - r1
            p = float(d) / r1
            bpt = d // LOOPS
            tmpl = "{0}LEAKING{1}: {2:n} bytes, {3:.2%} inc ({4:n} bytes/loop)"
            sys.stdout.write(tmpl.format(Color.YELLOW, Color.RESET, d, p, bpt))
        else:
            sys.stdout.write("{}OK{}".format(Color.GREEN, Color.RESET))

    def run(self):
        """Run the memory test suite."""
        width = 1
        for (name, _) in self._tests:
            if len(name) > width:
                width = len(name)

        tmpl = "{0}[{1:03}/{2}]{3} {4}: "
        for i, (name, text) in enumerate(self._tests, 1):
            sys.stdout.write(
                tmpl.format(
                    Color.GRAY, i, len(self._tests), Color.RESET, name.ljust(width)
                )
            )
            sys.stdout.flush()
            parent, child = Pipe()
            p = Process(target=_runner, args=(text, child))
            p.start()
            try:
                proc = psutil.Process(p.pid)
                parent.recv()
                parent.send("OK")
                parent.recv()
                info1 = proc.get_memory_info()
                sys.stdout.flush()
                parent.send("OK")
                parent.recv()
                info2 = proc.get_memory_info()
                self._print_results(info1, info2)
                sys.stdout.flush()
                parent.send("OK")
            finally:
                proc.kill()
                print()


def _runner(text, child):
    r1, r2 = range(250), range(LOOPS)
    for _ in r1:
        CTokenizer().tokenize(text)
    child.send("OK")
    child.recv()
    child.send("OK")
    child.recv()
    for _ in r2:
        CTokenizer().tokenize(text)
    child.send("OK")
    child.recv()


if __name__ == "__main__":
    setlocale(LC_ALL, "")
    MemoryTest().run()

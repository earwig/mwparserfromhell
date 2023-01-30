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


from ._base import Node
from ..utils import parse_anything

__all__ = ["Wikilink"]


class Wikilink(Node):
    """Represents an internal wikilink, like ``[[Foo|Bar]]``."""

    def __init__(self, title, args=None):
        super().__init__()
        self.title = title
        self.args = args
        if args is not None:
            if not '|' in args:
                self.text = args
            else:
                self.text = parse_anything(args).nodes[len(self.args)-1:]
        else:
            self.text = None

    def __str__(self):
        if self.text is not None:
            return "[[" + str(self.title) + "|" + str(self.text) + "]]"
        return "[[" + str(self.title) + "]]"

    def __children__(self):
        yield self.title
        if self.text is not None:
            yield self.text

    def __strip__(self, **kwargs):
        if self.text is not None:
            return self.text.strip_code(**kwargs)
        return self.title.strip_code(**kwargs)

    def __showtree__(self, write, get, mark):
        write("[[")
        get(self.title)
        if self.args is not None:
            write("    | ")
            mark()
            get(self.args)
        if self.text is not None:
            write("    | ")
            mark()
            get(self.text)
        write("]]")

    @property
    def title(self):
        """The title of the linked page, as a :class:`.Wikicode` object."""
        return self._title

    @property
    def args(self):
        """The args (if any), as a :class:`.list` object."""
        return self._args

    @property
    def text(self):
        """The text to display (if any), as a :class:`.Wikicode` object."""
        return self._text

    @args.setter
    def args(self, value):
        if arg := parse_anything(value):
            self._args = [node for node in str(arg.nodes[0]).split('|')]
            if len(self._args) > 0:
                self._text = str(arg)[len('|'.join(str(a) for a in self._args)):]
                self._args.pop()
            if len(self._text) == 0:
                self._text = None
            if len(self._args) == 0:
                self._args = None
        elif not hasattr(arg, 'nodes'):
            self._args = None
        else:
            self._args = None

    @title.setter
    def title(self, value):
        if value is not None:
            self._title = parse_anything(value)
        else:
            self._title = None

    @text.setter
    def text(self, value):
        if value is not None:
            self._text = parse_anything(value)
        else:
            self._text = None

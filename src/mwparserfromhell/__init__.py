# Copyright (C) 2012-2021 Ben Kurtovic <ben.kurtovic@gmail.com>
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
`mwparserfromhell <https://github.com/earwig/mwparserfromhell>`_ (the MediaWiki
Parser from Hell) is a Python package that provides an easy-to-use and
outrageously powerful parser for `MediaWiki <https://www.mediawiki.org>`_ wikicode.
"""

__author__ = "Ben Kurtovic"
__copyright__ = "Copyright (C) 2012-2021 Ben Kurtovic"
__license__ = "MIT License"
__version__ = "0.6.3"
__email__ = "ben.kurtovic@gmail.com"

from . import definitions, nodes, parser, smart_list, string_mixin, utils, wikicode

parse = utils.parse_anything

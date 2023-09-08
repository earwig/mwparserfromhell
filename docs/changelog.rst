Changelog
=========

v0.7
----

Unreleased
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.6.5...main>`__):

- Dropped support for end-of-life Python 3.7.

v0.6.5
------

`Released September 5, 2023 <https://github.com/earwig/mwparserfromhell/tree/v0.6.5>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.6.4...v0.6.5>`__):

- Dropped support for end-of-life Python 3.6.
- Added support for Python 3.11.
- Fixed parsing of leading zeros in named HTML entities.
  (`#288 <https://github.com/earwig/mwparserfromhell/issues/288>`_)
- Fixed memory leak parsing tags.
  (`#303 <https://github.com/earwig/mwparserfromhell/issues/303>`_)
- Fixed pickling SmartList objects.
  (`#289 <https://github.com/earwig/mwparserfromhell/issues/289>`_)

v0.6.4
------

`Released February 14, 2022 <https://github.com/earwig/mwparserfromhell/tree/v0.6.4>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.6.3...v0.6.4>`__):

- Dropped support for end-of-life Python 3.5.
- Added support for Python 3.10.
  (`#278 <https://github.com/earwig/mwparserfromhell/issues/278>`_)
- Fixed a regression in v0.6.2 that broke parsing of nested wikilinks in file
  captions. For now, the parser will handle interpret wikilinks in normal links
  as well, even though this differs from MediaWiki.
  (`#270 <https://github.com/earwig/mwparserfromhell/issues/270>`_)

v0.6.3
------

`Released September 2, 2021 <https://github.com/earwig/mwparserfromhell/tree/v0.6.3>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.6.2...v0.6.3>`__):

- Added Linux AArch64 wheels.
  (`#276 <https://github.com/earwig/mwparserfromhell/issues/276>`_)
- Fixed C integer conversion, manifesting as parsing errors on big-endian
  platforms.
  (`#277 <https://github.com/earwig/mwparserfromhell/issues/277>`_)

v0.6.2
------

`Released May 16, 2021 <https://github.com/earwig/mwparserfromhell/tree/v0.6.2>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.6...v0.6.2>`__):

- Improved parsing of external links.
  (`#232 <https://github.com/earwig/mwparserfromhell/issues/232>`_)
- Fixed parsing of nested wikilinks.
- Ported tests to pytest.
  (`#237 <https://github.com/earwig/mwparserfromhell/issues/237>`_)
- Moved mwparserfromhell package to src/ dir.
- There was no 0.6.1 release due to a packaging error.

v0.6
----

`Released December 21, 2020 <https://github.com/earwig/mwparserfromhell/tree/v0.6>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.5.4...v0.6>`__):

Thanks to everyone for their patience with this release!

- Breaking change: dropped support for end-of-life Python 2.7 and 3.4.
- Added support for Python 3.8 and 3.9.
- Added binary wheels for Linux and macOS.
- Updated :meth:`.Wikicode.matches` to recognize underscores as being
  equivalent to spaces.
  (`#216 <https://github.com/earwig/mwparserfromhell/issues/216>`_)
- Added a `default` parameter to :meth:`.Template.get`, and implement dict-style
  item access for template parameters.
  (`#252 <https://github.com/earwig/mwparserfromhell/issues/252>`_)
- Fixed a rare parsing bug involving deeply nested style tags.
  (`#224 <https://github.com/earwig/mwparserfromhell/issues/224>`_)
- Fixed parsing of section headings inside templates.
  (`#233 <https://github.com/earwig/mwparserfromhell/issues/233>`_)
- Updated HTML tag definitions.
- Internal refactoring and cleanup.

v0.5.4
------

`Released May 15, 2019 <https://github.com/earwig/mwparserfromhell/tree/v0.5.4>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.5.3...v0.5.4>`__):

- Fixed an unlikely crash in the C tokenizer when interrupted while parsing
  a heading.

v0.5.3
------

`Released March 30, 2019 <https://github.com/earwig/mwparserfromhell/tree/v0.5.3>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.5.2...v0.5.3>`__):

- Fixed manual construction of Node objects, previously unsupported.
  (`#214 <https://github.com/earwig/mwparserfromhell/issues/214>`_)
- Fixed :class:`.Wikicode` transformation methods (:meth:`.Wikicode.replace`,
  :meth:`.Wikicode.remove`, etc.) when passed an empty section as an argument.
  (`#212 <https://github.com/earwig/mwparserfromhell/issues/212>`_)
- Fixed the parser getting stuck inside malformed tables.
  (`#206 <https://github.com/earwig/mwparserfromhell/issues/206>`_)

v0.5.2
------

`Released November 1, 2018 <https://github.com/earwig/mwparserfromhell/tree/v0.5.2>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.5.1...v0.5.2>`__):

- Dropped support for end-of-life Python versions 2.6, 3.2, 3.3.
  (`#199 <https://github.com/earwig/mwparserfromhell/issues/199>`_,
  `#204 <https://github.com/earwig/mwparserfromhell/pull/204>`_)
- Fixed signals getting stuck inside the C tokenizer until parsing finishes,
  in pathological cases.
  (`#206 <https://github.com/earwig/mwparserfromhell/issues/206>`_)
- Fixed `<wbr>` not being considered a single-only tag.
  (`#200 <https://github.com/earwig/mwparserfromhell/pull/200>`_)
- Fixed a C tokenizer crash on Python 3.7 when compiled with assertions.
  (`#208 <https://github.com/earwig/mwparserfromhell/issues/208>`_)
- Cleaned up some minor documentation issues.
  (`#207 <https://github.com/earwig/mwparserfromhell/pull/207>`_)

v0.5.1
------

`Released March 3, 2018 <https://github.com/earwig/mwparserfromhell/tree/v0.5.1>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.5...v0.5.1>`__):

- Improved behavior when adding parameters to templates (via
  :meth:`.Template.add`) with poorly formatted whitespace conventions.
  (`#185 <https://github.com/earwig/mwparserfromhell/issues/185>`_)
- Fixed the parser getting stuck in deeply nested HTML tags with unclosed,
  quoted attributes.
  (`#190 <https://github.com/earwig/mwparserfromhell/issues/190>`_)

v0.5
----

`Released June 23, 2017 <https://github.com/earwig/mwparserfromhell/tree/v0.5>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.4.4...v0.5>`__):

- Added :meth:`.Wikicode.contains` to determine whether a :class:`.Node` or
  :class:`.Wikicode` object is contained within another :class:`.Wikicode`
  object.
- Added :meth:`.Wikicode.get_ancestors` and :meth:`.Wikicode.get_parent` to
  find all ancestors and the direct parent of a :class:`.Node`, respectively.
- Fixed a long-standing performance issue with deeply nested, invalid syntax
  (`issue #42 <https://github.com/earwig/mwparserfromhell/issues/42>`_). The
  parser should be much faster on certain complex pages. The "max cycle"
  restriction has also been removed, so some situations where templates at the
  end of a page were being skipped are now resolved.
- Made :meth:`Template.remove(keep_field=True) <.Template.remove>` behave more
  reasonably when the parameter is already empty.
- Added the *keep_template_params* argument to :meth:`.Wikicode.strip_code`.
  If *True*, then template parameters will be preserved in the output.
- :class:`.Wikicode` objects can now be pickled properly (fixed infinite
  recursion error on incompletely-constructed :class:`.StringMixIn`
  subclasses).
- Fixed :meth:`.Wikicode.matches`\ 's behavior on iterables besides lists and
  tuples.
- Fixed ``len()`` sometimes raising ``ValueError`` on empty node lists.
- Fixed a rare parsing bug involving self-closing tags inside the attributes of
  unpaired tags.
- Fixed release script after changes to PyPI.

v0.4.4
------

`Released December 30, 2016 <https://github.com/earwig/mwparserfromhell/tree/v0.4.4>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.4.3...v0.4.4>`__):

- Added support for Python 3.6.
- Fixed parsing bugs involving:

  - wikitables nested in templates;
  - wikitable error recovery when unable to recurse;
  - templates nested in template parameters before other parameters.

- Fixed parsing file-like objects.
- Made builds deterministic.
- Documented caveats.

v0.4.3
------

`Released October 29, 2015 <https://github.com/earwig/mwparserfromhell/tree/v0.4.3>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.4.2...v0.4.3>`__):

- Added Windows binaries for Python 3.5.
- Fixed edge cases involving wikilinks inside of external links and vice versa.
- Fixed a C tokenizer crash when a keyboard interrupt happens while parsing.

v0.4.2
------

`Released July 30, 2015 <https://github.com/earwig/mwparserfromhell/tree/v0.4.2>`__
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.4.1...v0.4.2>`__):

- Fixed setup script not including header files in releases.
- Fixed Windows binary uploads.

v0.4.1
------

`Released July 30, 2015 <https://github.com/earwig/mwparserfromhell/tree/v0.4.1>`__
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.4...v0.4.1>`__):

- The process for building Windows binaries has been fixed, and these should be
  distributed along with new releases. Windows users can now take advantage of
  C speedups without having a compiler of their own.
- Added support for Python 3.5.
- ``<`` and ``>`` are now disallowed in wikilink titles and template names.
  This includes when denoting tags, but not comments.
- Fixed the behavior of *preserve_spacing* in :meth:`.Template.add` and
  *keep_field* in :meth:`.Template.remove` on parameters with hidden keys.
- Removed :meth:`._ListProxy.detach`. :class:`.SmartList`\ s now use weak
  references and their children are garbage-collected properly.
- Fixed parser bugs involving:

  - templates with completely blank names;
  - templates with newlines and comments.

- Heavy refactoring and fixes to the C tokenizer, including:

  - corrected a design flaw in text handling, allowing for substantial speed
    improvements when parsing long strings of plain text;
  - implemented new Python 3.3
    `PEP 393 <https://www.python.org/dev/peps/pep-0393/>`_ Unicode APIs.

- Fixed various bugs in :class:`.SmartList`, including one that was causing
  memory issues on 64-bit builds of Python 2 on Windows.
- Fixed some bugs in the release scripts.

v0.4
----

`Released May 23, 2015 <https://github.com/earwig/mwparserfromhell/tree/v0.4>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3.3...v0.4>`__):

- The parser now falls back on pure Python mode if C extensions cannot be
  built. This fixes an issue that prevented some Windows users from installing
  the parser.
- Added support for parsing wikicode tables (patches by David Winegar).
- Added a script to test for memory leaks in :file:`scripts/memtest.py`.
- Added a script to do releases in :file:`scripts/release.sh`.
- *skip_style_tags* can now be passed to :func:`mwparserfromhell.parse()
  <.parse_anything>` (previously, only :meth:`.Parser.parse` allowed it).
- The *recursive* argument to :class:`Wikicode's <.Wikicode>` :meth:`.filter`
  methods now accepts a third option, ``RECURSE_OTHERS``, which recurses over
  all children except instances of *forcetype* (for example,
  ``code.filter_templates(code.RECURSE_OTHERS)`` returns all un-nested
  templates).
- The parser now understands HTML tag attributes quoted with single quotes.
  When setting a tag attribute's value, quotes will be added if necessary. As
  part of this, :class:`.Attribute`\ 's :attr:`~.Attribute.quoted` attribute
  has been changed to :attr:`~.Attribute.quotes`, and is now either a string or
  ``None``.
- Calling :meth:`.Template.remove` with a :class:`.Parameter` object that is
  not part of the template now raises :exc:`ValueError` instead of doing
  nothing.
- :class:`.Parameter`\ s with non-integer keys can no longer be created with
  *showkey=False*, nor have the value of this attribute be set to *False*
  later.
- :meth:`._ListProxy.destroy` has been changed to :meth:`._ListProxy.detach`,
  and now works in a more useful way.
- If something goes wrong while parsing, :exc:`.ParserError` will now be
  raised. Previously, the parser would produce an unclear :exc:`.BadRoute`
  exception or allow an incorrect node tree to be build.
- Fixed parser bugs involving:

  - nested tags;
  - comments in template names;
  - tags inside of ``<nowiki>`` tags.

- Added tests to ensure that parsed trees convert back to wikicode without
  unintentional modifications.
- Added support for a :envvar:`NOWEB` environment variable, which disables a
  unit test that makes a web call.
- Test coverage has been improved, and some minor related bugs have been fixed.
- Updated and fixed some documentation.

v0.3.3
------

`Released April 22, 2014 <https://github.com/earwig/mwparserfromhell/tree/v0.3.3>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3.2...v0.3.3>`__):

- Added support for Python 2.6 and 3.4.
- :meth:`.Template.has` is now passed *ignore_empty=False* by default
  instead of *True*. This fixes a bug when adding parameters to templates with
  empty fields, **and is a breaking change if you rely on the default
  behavior.**
- The *matches* argument of :class:`Wikicode's <.Wikicode>` :meth:`.filter`
  methods now accepts a function (taking one argument, a :class:`.Node`, and
  returning a bool) in addition to a regex.
- Re-added *flat* argument to :meth:`.Wikicode.get_sections`, fixed the order
  in which it returns sections, and made it faster.
- :meth:`.Wikicode.matches` now accepts a tuple or list of
  strings/:class:`.Wikicode` objects instead of just a single string or
  :class:`.Wikicode`.
- Given the frequency of issues with the (admittedly insufficient) tag parser,
  there's a temporary *skip_style_tags* argument to :meth:`~.Parser.parse` that
  ignores ``''`` and ``'''`` until these issues are corrected.
- Fixed a parser bug involving nested wikilinks and external links.
- C code cleanup and speed improvements.

v0.3.2
------

`Released September 1, 2013 <https://github.com/earwig/mwparserfromhell/tree/v0.3.2>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3.1...v0.3.2>`__):

- Added support for Python 3.2 (along with current support for 3.3 and 2.7).
- Renamed :meth:`.Template.remove`\ 's first argument from *name* to *param*,
  which now accepts :class:`.Parameter` objects in addition to parameter name
  strings.

v0.3.1
------

`Released August 29, 2013 <https://github.com/earwig/mwparserfromhell/tree/v0.3.1>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3...v0.3.1>`__):

- Fixed a parser bug involving URLs nested inside other markup.
- Fixed some typos.

v0.3
----

`Released August 24, 2013 <https://github.com/earwig/mwparserfromhell/tree/v0.3>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.2...v0.3>`__):

- Added complete support for HTML :class:`Tags <.Tag>`, including forms like
  ``<ref>foo</ref>``, ``<ref name="bar"/>``, and wiki-markup tags like bold
  (``'''``), italics (``''``), and lists (``*``, ``#``, ``;`` and ``:``).
- Added support for :class:`.ExternalLink`\ s (``http://example.com/`` and
  ``[http://example.com/ Example]``).
- :class:`Wikicode's <.Wikicode>` :meth:`.filter` methods are now passed
  *recursive=True* by default instead of *False*. **This is a breaking change
  if you rely on any filter() methods being non-recursive by default.**
- Added a :meth:`.matches` method to :class:`.Wikicode` for page/template name
  comparisons.
- The *obj* param of :meth:`.Wikicode.insert_before`, :meth:`.insert_after`,
  :meth:`~.Wikicode.replace`, and :meth:`~.Wikicode.remove` now accepts
  :class:`.Wikicode` objects and strings representing parts of wikitext,
  instead of just nodes. These methods also make all possible substitutions
  instead of just one.
- Renamed :meth:`.Template.has_param` to :meth:`~.Template.has` for consistency
  with :class:`.Template`\ 's other methods; :meth:`.has_param` is now an
  alias.
- The C tokenizer extension now works on Python 3 in addition to Python 2.7.
- Various bugfixes, internal changes, and cleanup.

v0.2
----

`Released June 20, 2013 <https://github.com/earwig/mwparserfromhell/tree/v0.2>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.1.1...v0.2>`__):

- The parser now fully supports Python 3 in addition to Python 2.7.
- Added a C tokenizer extension that is significantly faster than its Python
  equivalent. It is enabled by default (if available) and can be toggled by
  setting :attr:`mwparserfromhell.parser.use_c` to a boolean value.
- Added a complete set of unit tests covering parsing and wikicode
  manipulation.
- Renamed :meth:`.filter_links` to :meth:`.filter_wikilinks` (applies to
  :meth:`.ifilter` as well).
- Added filter methods for :class:`Arguments <.Argument>`,
  :class:`Comments <.Comment>`, :class:`Headings <.Heading>`, and
  :class:`HTMLEntities <.HTMLEntity>`.
- Added *before* param to :meth:`.Template.add`; renamed *force_nonconformity*
  to *preserve_spacing*.
- Added *include_lead* param to :meth:`.Wikicode.get_sections`.
- Removed *flat* param from :meth:`.get_sections`.
- Removed *force_no_field* param from :meth:`.Template.remove`.
- Added support for Travis CI.
- Added note about Windows build issue in the README.
- The tokenizer will limit itself to a realistic recursion depth to prevent
  errors and unreasonably long parse times.
- Fixed how some nodes' attribute setters handle input.
- Fixed multiple bugs in the tokenizer's handling of invalid markup.
- Fixed bugs in the implementation of :class:`.SmartList` and
  :class:`.StringMixIn`.
- Fixed some broken example code in the README; other copyedits.
- Other bugfixes and code cleanup.

v0.1.1
------

`Released September 21, 2012 <https://github.com/earwig/mwparserfromhell/tree/v0.1.1>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.1...v0.1.1>`__):

- Added support for :class:`Comments <.Comment>` (``<!-- foo -->``) and
  :class:`Wikilinks <.Wikilink>` (``[[foo]]``).
- Added corresponding :meth:`.ifilter_links` and :meth:`.filter_links` methods
  to :class:`.Wikicode`.
- Fixed a bug when parsing incomplete templates.
- Fixed :meth:`.strip_code` to affect the contents of headings.
- Various copyedits in documentation and comments.

v0.1
----

`Released August 23, 2012 <https://github.com/earwig/mwparserfromhell/tree/v0.1>`_:

- Initial release.

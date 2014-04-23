Changelog
=========

v0.4
----

Unreleased
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3.3...develop>`__):

- Added a script to test for memory leaks in :file:`scripts/memtest.py`.
- Added a script to do releases in :file:`scripts/release.sh`.

v0.3.3
------

`Released April 22, 2014 <https://github.com/earwig/mwparserfromhell/tree/v0.3.3>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3.2...v0.3.3>`__):

- Added support for Python 2.6 and 3.4.
- :py:meth:`.Template.has` is now passed *ignore_empty=False* by default
  instead of *True*. This fixes a bug when adding parameters to templates with
  empty fields, **and is a breaking change if you rely on the default
  behavior.**
- The *matches* argument of :py:class:`Wikicode's <.Wikicode>`
  :py:meth:`.filter` methods now accepts a function (taking one argument, a
  :py:class:`.Node`, and returning a bool) in addition to a regex.
- Re-added *flat* argument to :py:meth:`.Wikicode.get_sections`, fixed the
  order in which it returns sections, and made it faster.
- :py:meth:`.Wikicode.matches` now accepts a tuple or list of
  strings/:py:class:`.Wikicode` objects instead of just a single string or
  :py:class:`.Wikicode`.
- Given the frequency of issues with the (admittedly insufficient) tag parser,
  there's a temporary *skip_style_tags* argument to
  :py:meth:`~.Parser.parse` that ignores ``''`` and ``'''`` until these issues
  are corrected.
- Fixed a parser bug involving nested wikilinks and external links.
- C code cleanup and speed improvements.

v0.3.2
------

`Released September 1, 2013 <https://github.com/earwig/mwparserfromhell/tree/v0.3.2>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.3.1...v0.3.2>`__):

- Added support for Python 3.2 (along with current support for 3.3 and 2.7).
- Renamed :py:meth:`.Template.remove`\ 's first argument from *name* to
  *param*, which now accepts :py:class:`.Parameter` objects in addition to
  parameter name strings.

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

- Added complete support for HTML :py:class:`Tags <.Tag>`, including forms like
  ``<ref>foo</ref>``, ``<ref name="bar"/>``, and wiki-markup tags like bold
  (``'''``), italics (``''``), and lists (``*``, ``#``, ``;`` and ``:``).
- Added support for :py:class:`.ExternalLink`\ s (``http://example.com/`` and
  ``[http://example.com/ Example]``).
- :py:class:`Wikicode's <.Wikicode>` :py:meth:`.filter` methods are now passed
  *recursive=True* by default instead of *False*. **This is a breaking change
  if you rely on any filter() methods being non-recursive by default.**
- Added a :py:meth:`.matches` method to :py:class:`~.Wikicode` for
  page/template name comparisons.
- The *obj* param of :py:meth:`Wikicode.insert_before() <.insert_before>`,
  :py:meth:`~.insert_after`, :py:meth:`~.Wikicode.replace`, and
  :py:meth:`~.Wikicode.remove` now accepts :py:class:`~.Wikicode` objects and
  strings representing parts of wikitext, instead of just nodes. These methods
  also make all possible substitutions instead of just one.
- Renamed :py:meth:`Template.has_param() <.has_param>` to
  :py:meth:`~.Template.has` for consistency with :py:class:`~.Template`\ 's
  other methods; :py:meth:`~.has_param` is now an alias.
- The C tokenizer extension now works on Python 3 in addition to Python 2.7.
- Various bugfixes, internal changes, and cleanup.

v0.2
----

`Released June 20, 2013 <https://github.com/earwig/mwparserfromhell/tree/v0.2>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.1.1...v0.2>`__):

- The parser now fully supports Python 3 in addition to Python 2.7.
- Added a C tokenizer extension that is significantly faster than its Python
  equivalent. It is enabled by default (if available) and can be toggled by
  setting :py:attr:`mwparserfromhell.parser.use_c` to a boolean value.
- Added a complete set of unit tests covering parsing and wikicode
  manipulation.
- Renamed :py:meth:`.filter_links` to :py:meth:`.filter_wikilinks` (applies to
  :py:meth:`.ifilter` as well).
- Added filter methods for :py:class:`Arguments <.Argument>`,
  :py:class:`Comments <.Comment>`, :py:class:`Headings <.Heading>`, and
  :py:class:`HTMLEntities <.HTMLEntity>`.
- Added *before* param to :py:meth:`Template.add() <.Template.add>`; renamed
  *force_nonconformity* to *preserve_spacing*.
- Added *include_lead* param to :py:meth:`Wikicode.get_sections()
  <.get_sections>`.
- Removed *flat* param from :py:meth:`.get_sections`.
- Removed *force_no_field* param from :py:meth:`Template.remove()
  <.Template.remove>`.
- Added support for Travis CI.
- Added note about Windows build issue in the README.
- The tokenizer will limit itself to a realistic recursion depth to prevent
  errors and unreasonably long parse times.
- Fixed how some nodes' attribute setters handle input.
- Fixed multiple bugs in the tokenizer's handling of invalid markup.
- Fixed bugs in the implementation of :py:class:`.SmartList` and
  :py:class:`.StringMixIn`.
- Fixed some broken example code in the README; other copyedits.
- Other bugfixes and code cleanup.

v0.1.1
------

`Released September 21, 2012 <https://github.com/earwig/mwparserfromhell/tree/v0.1.1>`_
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.1...v0.1.1>`__):

- Added support for :py:class:`Comments <.Comment>` (``<!-- foo -->``) and
  :py:class:`Wikilinks <.Wikilink>` (``[[foo]]``).
- Added corresponding :py:meth:`.ifilter_links` and :py:meth:`.filter_links`
  methods to :py:class:`.Wikicode`.
- Fixed a bug when parsing incomplete templates.
- Fixed :py:meth:`.strip_code` to affect the contents of headings.
- Various copyedits in documentation and comments.

v0.1
----

`Released August 23, 2012 <https://github.com/earwig/mwparserfromhell/tree/v0.1>`_:

- Initial release.

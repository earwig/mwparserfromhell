Changelog
=========

v0.3
----

Unreleased
(`changes <https://github.com/earwig/mwparserfromhell/compare/v0.2...develop>`__):

- Added complete support for HTML :py:class:`Tags <.Tag>`, along with
  appropriate unit tests. This includes forms like ``<ref>foo</ref>``,
  ``<ref name="bar"/>``, and wiki-markup tags like bold (``'''``), italics
  (``''``), and lists (``*``, ``#``, ``;`` and ``:``).
- :py:class:`Wikicode's <.Wikicode>` :py:meth:`.filter` methods are now passed
  *recursive=True* by default instead of *False*. **This is a breaking change
  if you rely on any filter() methods being non-recursive by default.**
- Added a :py:meth:`.matches` method to :py:class:`~.Wikicode` for
  page/template name comparisons.
- The *obj* param of :py:meth:`Wikicode.insert_before <.insert_before>`,
  :py:meth:`~.insert_after`, :py:meth:`~.replace`, and :py:meth:`~.remove` now
  accepts :py:class:`~.Wikicode` objects and strings representing parts of
  wikitext, instead of just nodes. These methods also make all possible
  substitutions instead of just one.
- The C tokenizer extension now works on Python 3 in addition to Python 2.7.
- Various fixes and cleanup.

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

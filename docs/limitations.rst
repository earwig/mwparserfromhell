Limitations
===========

While the MediaWiki parser generates HTML and has access to the contents of
templates, among other things, mwparserfromhell acts as a direct interface to
the source code only. This has several implications:

* Syntax elements produced by a template transclusion cannot be detected. For
  example, imagine a hypothetical page ``"Template:End-bold"`` that contained
  the text ``</b>``. While MediaWiki would correctly understand that
  ``<b>foobar{{end-bold}}`` translates to ``<b>foobar</b>``, mwparserfromhell
  has no way of examining the contents of ``{{end-bold}}``. Instead, it would
  treat the bold tag as unfinished, possibly extending further down the page.

* Templates adjacent to external links, as in ``http://example.com{{foo}}``,
  are considered part of the link. In reality, this would depend on the
  contents of the template.

* When different syntax elements cross over each other, as in
  ``{{echo|''Hello}}, world!''``, the parser gets confused because this cannot
  be represented by an ordinary syntax tree. Instead, the parser will treat the
  first syntax construct as plain text. In this case, only the italic tag would
  be properly parsed.

  **Workaround:** Since this commonly occurs with text formatting and text
  formatting is often not of interest to users, you may pass
  *skip_style_tags=True* to ``mwparserfromhell.parse()``. This treats ``''``
  and ``'''`` as plain text.

  A future version of mwparserfromhell may include multiple parsing modes to
  get around this restriction more sensibly.

Additionally, the parser lacks awareness of certain wiki-specific settings:

* `Word-ending links`_ are not supported, since the linktrail rules are
  language-specific.

* Localized namespace names aren't recognized, so file links (such as
  ``[[File:...]]``) are treated as regular wikilinks.

* Anything that looks like an XML tag is treated as a tag, even if it is not a
  recognized tag name, since the list of valid tags depends on loaded MediaWiki
  extensions.

.. _Word-ending links:      https://www.mediawiki.org/wiki/Help:Links#linktrail

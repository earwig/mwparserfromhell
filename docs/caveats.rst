Caveats
=======

An inherent limitation in wikicode prevents us from generating complete parse
trees in certain cases. For example, the string ``{{echo|''Hello}}, world!''``
produces the valid output ``<i>Hello, world!</i>`` in MediaWiki, assuming
``{{echo}}`` is a template that returns its first parameter. But since
representing this in mwparserfromhell's node tree would be impossible, we
compromise by treating the first node (i.e., the template) as plain text,
parsing only the italics.

The current workaround for cases where you are not interested in text
formatting is to pass *skip_style_tags=True* to :func:`mwparserfromhell.parse`.
This treats ``''`` and ``'''`` like plain text.

A future version of mwparserfromhell will include multiple parsing modes to get
around this restriction.

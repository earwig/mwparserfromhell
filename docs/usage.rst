Usage
=====

Normal usage is rather straightforward (where ``text`` is page text)::

    >>> import mwparserfromhell
    >>> wikicode = mwparserfromhell.parse(text)

``wikicode`` is a :py:class:`mwparserfromhell.Wikicode <.Wikicode>` object,
which acts like an ordinary ``unicode`` object (or ``str`` in Python 3) with
some extra methods. For example::

    >>> text = "I has a template! {{foo|bar|baz|eggs=spam}} See it?"
    >>> wikicode = mwparserfromhell.parse(text)
    >>> print wikicode
    I has a template! {{foo|bar|baz|eggs=spam}} See it?
    >>> templates = wikicode.filter_templates()
    >>> print templates
    ['{{foo|bar|baz|eggs=spam}}']
    >>> template = templates[0]
    >>> print template.name
    foo
    >>> print template.params
    ['bar', 'baz', 'eggs=spam']
    >>> print template.get(1).value
    bar
    >>> print template.get("eggs").value
    spam

Since every node you reach is also a :py:class:`~.Wikicode` object, it's
trivial to get nested templates::

    >>> code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
    >>> print code.filter_templates()
    ['{{foo|this {{includes a|template}}}}']
    >>> foo = code.filter_templates()[0]
    >>> print foo.get(1).value
    this {{includes a|template}}
    >>> print foo.get(1).value.filter_templates()[0]
    {{includes a|template}}
    >>> print foo.get(1).value.filter_templates()[0].get(1).value
    template

Additionally, you can include nested templates in :py:meth:`~.filter_templates`
by passing *recursive=True*::

    >>> text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
    >>> mwparserfromhell.parse(text).filter_templates(recursive=True)
    ['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']

Templates can be easily modified to add, remove, or alter params.
:py:class:`~.Wikicode` can also be treated like a list with
:py:meth:`~.Wikicode.append`, :py:meth:`~.Wikicode.insert`,
:py:meth:`~.Wikicode.remove`, :py:meth:`~.Wikicode.replace`, and more::

    >>> text = "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}"
    >>> code = mwparserfromhell.parse(text)
    >>> for template in code.filter_templates():
    ...     if template.name == "cleanup" and not template.has_param("date"):
    ...         template.add("date", "July 2012")
    ...
    >>> print code
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{uncategorized}}
    >>> code.replace("{{uncategorized}}", "{{bar-stub}}")
    >>> print code
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> print code.filter_templates()
    ['{{cleanup|date=July 2012}}', '{{bar-stub}}']

You can then convert ``code`` back into a regular :py:class:`unicode` object
(for saving the page!) by calling :py:func:`unicode` on it::

    >>> text = unicode(code)
    >>> print text
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> text == code
    True

(Likewise, use :py:func:`str(code) <str>` in Python 3.)

For more tips, check out :py:class:`Wikicode's full method list <.Wikicode>`
and the :py:mod:`list of Nodes <.nodes>`.

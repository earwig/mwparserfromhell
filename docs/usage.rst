Usage
=====

Normal usage is rather straightforward (where ``text`` is page text)::

    >>> import mwparserfromhell
    >>> wikicode = mwparserfromhell.parse(text)

``wikicode`` is a :class:`mwparserfromhell.Wikicode <.Wikicode>` object, which
acts like an ordinary ``str`` object with some extra methods. For example::

    >>> text = "I has a template! {{foo|bar|baz|eggs=spam}} See it?"
    >>> wikicode = mwparserfromhell.parse(text)
    >>> print(wikicode)
    I has a template! {{foo|bar|baz|eggs=spam}} See it?
    >>> templates = wikicode.filter_templates()
    >>> print(templates)
    ['{{foo|bar|baz|eggs=spam}}']
    >>> template = templates[0]
    >>> print(template.name)
    foo
    >>> print(template.params)
    ['bar', 'baz', 'eggs=spam']
    >>> print(template.get(1).value)
    bar
    >>> print(template.get("eggs").value)
    spam

Since nodes can contain other nodes, getting nested templates is trivial::

    >>> text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
    >>> mwparserfromhell.parse(text).filter_templates()
    ['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']

You can also pass *recursive=False* to :meth:`.filter_templates` and explore
templates manually. This is possible because nodes can contain additional
:class:`.Wikicode` objects::

    >>> code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
    >>> print(code.filter_templates(recursive=False))
    ['{{foo|this {{includes a|template}}}}']
    >>> foo = code.filter_templates(recursive=False)[0]
    >>> print(foo.get(1).value)
    this {{includes a|template}}
    >>> print(foo.get(1).value.filter_templates()[0])
    {{includes a|template}}
    >>> print(foo.get(1).value.filter_templates()[0].get(1).value)
    template

Templates can be easily modified to add, remove, or alter params.
:class:`.Wikicode` objects can be treated like lists, with
:meth:`~.Wikicode.append`, :meth:`~.Wikicode.insert`,
:meth:`~.Wikicode.remove`, :meth:`~.Wikicode.replace`, and more. They also have
a :meth:`~.Wikicode.matches` method for comparing page or template names, which
takes care of capitalization and whitespace::

    >>> text = "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}"
    >>> code = mwparserfromhell.parse(text)
    >>> for template in code.filter_templates():
    ...     if template.name.matches("Cleanup") and not template.has("date"):
    ...         template.add("date", "July 2012")
    ...
    >>> print(code)
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{uncategorized}}
    >>> code.replace("{{uncategorized}}", "{{bar-stub}}")
    >>> print(code)
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> print(code.filter_templates())
    ['{{cleanup|date=July 2012}}', '{{bar-stub}}']

You can then convert ``code`` back into a regular :class:`str` object (for
saving the page!) by calling :func:`str` on it::

    >>> text = str(code)
    >>> print(text)
    {{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}
    >>> text == code
    True


For more tips, check out :class:`Wikicode's full method list <.Wikicode>` and
the :mod:`list of Nodes <.nodes>`.

import mwparserfromhell
text = "foo {{spam|eggs}} bar"
code = mwparserfromhell.parse(text)
template = code.filter_templates()[0]
template.name
template.params
template.params[0].value
template.params[0].name
template.params[0].showkey
template.params[0].showkey = True
template.params[0].name = "apples"
code
template.add("pears", "{{plums}}")
code.filter_templates(recursive=True)

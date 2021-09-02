/*
Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include "tokens.h"

/* Globals */

PyObject *Text;

PyObject *TemplateOpen;
PyObject *TemplateParamSeparator;
PyObject *TemplateParamEquals;
PyObject *TemplateClose;

PyObject *ArgumentOpen;
PyObject *ArgumentSeparator;
PyObject *ArgumentClose;

PyObject *WikilinkOpen;
PyObject *WikilinkSeparator;
PyObject *WikilinkClose;

PyObject *ExternalLinkOpen;
PyObject *ExternalLinkSeparator;
PyObject *ExternalLinkClose;

PyObject *HTMLEntityStart;
PyObject *HTMLEntityNumeric;
PyObject *HTMLEntityHex;
PyObject *HTMLEntityEnd;
PyObject *HeadingStart;
PyObject *HeadingEnd;

PyObject *CommentStart;
PyObject *CommentEnd;

PyObject *TagOpenOpen;
PyObject *TagAttrStart;
PyObject *TagAttrEquals;
PyObject *TagAttrQuote;
PyObject *TagCloseOpen;
PyObject *TagCloseSelfclose;
PyObject *TagOpenClose;
PyObject *TagCloseClose;

/*
    Load individual tokens into globals from the given Python module object.
*/
void
load_tokens_from_module(PyObject *module)
{
    Text = PyObject_GetAttrString(module, "Text");

    TemplateOpen = PyObject_GetAttrString(module, "TemplateOpen");
    TemplateParamSeparator = PyObject_GetAttrString(module, "TemplateParamSeparator");
    TemplateParamEquals = PyObject_GetAttrString(module, "TemplateParamEquals");
    TemplateClose = PyObject_GetAttrString(module, "TemplateClose");

    ArgumentOpen = PyObject_GetAttrString(module, "ArgumentOpen");
    ArgumentSeparator = PyObject_GetAttrString(module, "ArgumentSeparator");
    ArgumentClose = PyObject_GetAttrString(module, "ArgumentClose");

    WikilinkOpen = PyObject_GetAttrString(module, "WikilinkOpen");
    WikilinkSeparator = PyObject_GetAttrString(module, "WikilinkSeparator");
    WikilinkClose = PyObject_GetAttrString(module, "WikilinkClose");

    ExternalLinkOpen = PyObject_GetAttrString(module, "ExternalLinkOpen");
    ExternalLinkSeparator = PyObject_GetAttrString(module, "ExternalLinkSeparator");
    ExternalLinkClose = PyObject_GetAttrString(module, "ExternalLinkClose");

    HTMLEntityStart = PyObject_GetAttrString(module, "HTMLEntityStart");
    HTMLEntityNumeric = PyObject_GetAttrString(module, "HTMLEntityNumeric");
    HTMLEntityHex = PyObject_GetAttrString(module, "HTMLEntityHex");
    HTMLEntityEnd = PyObject_GetAttrString(module, "HTMLEntityEnd");

    HeadingStart = PyObject_GetAttrString(module, "HeadingStart");
    HeadingEnd = PyObject_GetAttrString(module, "HeadingEnd");

    CommentStart = PyObject_GetAttrString(module, "CommentStart");
    CommentEnd = PyObject_GetAttrString(module, "CommentEnd");

    TagOpenOpen = PyObject_GetAttrString(module, "TagOpenOpen");
    TagAttrStart = PyObject_GetAttrString(module, "TagAttrStart");
    TagAttrEquals = PyObject_GetAttrString(module, "TagAttrEquals");
    TagAttrQuote = PyObject_GetAttrString(module, "TagAttrQuote");
    TagCloseOpen = PyObject_GetAttrString(module, "TagCloseOpen");
    TagCloseSelfclose = PyObject_GetAttrString(module, "TagCloseSelfclose");
    TagOpenClose = PyObject_GetAttrString(module, "TagOpenClose");
    TagCloseClose = PyObject_GetAttrString(module, "TagCloseClose");
}

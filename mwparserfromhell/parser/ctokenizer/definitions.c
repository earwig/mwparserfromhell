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

#include "definitions.h"

/*
    This file should be kept up to date with mwparserfromhell/definitions.py.
    See the Python version for data sources.
*/

static const char* URI_SCHEMES[] = {
    "http", "https", "ftp", "ftps", "ssh", "sftp", "irc", "ircs", "xmpp",
    "sip", "sips", "gopher", "telnet", "nntp", "worldwind", "mailto", "tel",
    "sms", "news", "svn", "git", "mms", "bitcoin", "magnet", "urn", "geo", NULL
};

static const char* URI_SCHEMES_AUTHORITY_OPTIONAL[] = {
    "xmpp", "sip", "sips", "mailto", "tel", "sms", "news", "bitcoin", "magnet",
    "urn", "geo", NULL
};

static const char* PARSER_BLACKLIST[] = {
    "categorytree", "gallery", "hiero", "imagemap", "inputbox", "math",
    "nowiki", "pre", "score", "section", "source", "syntaxhighlight",
    "templatedata", "timeline", NULL
};

static const char* SINGLE[] = {
    "br", "hr", "meta", "link", "img", "li", "dt", "dd", "th", "td", "tr", NULL
};

static const char* SINGLE_ONLY[] = {
    "br", "hr", "meta", "link", "img", NULL
};

/*
    Convert a PyUnicodeObject to a lowercase ASCII char* array and store it in
    the second argument. The caller must free the return value when finished.
    If the return value is NULL, the conversion failed and *string is not set.
*/
static PyObject* unicode_to_lcase_ascii(PyObject *input, const char **string)
{
    PyObject *lower = PyObject_CallMethod(input, "lower", NULL), *bytes;

    if (!lower)
        return NULL;
    bytes = PyUnicode_AsASCIIString(lower);
    Py_DECREF(lower);
    if (!bytes) {
        if (PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_UnicodeEncodeError))
            PyErr_Clear();
        return NULL;
    }
    *string = PyBytes_AS_STRING(bytes);
    return bytes;
}

/*
    Return whether a PyUnicodeObject is in a list of lowercase ASCII strings.
*/
static int unicode_in_string_list(PyObject *input, const char **list)
{
    const char *string;
    PyObject *temp = unicode_to_lcase_ascii(input, &string);
    int retval = 0;

    if (!temp)
        return 0;

    while (*list) {
        if (!strcmp(*(list++), string)) {
            retval = 1;
            goto end;
        }
    }

    end:
    Py_DECREF(temp);
    return retval;
}

/*
    Return if the given tag's contents should be passed to the parser.
*/
int is_parsable(PyObject *tag)
{
    return !unicode_in_string_list(tag, PARSER_BLACKLIST);
}

/*
    Return whether or not the given tag can exist without a close tag.
*/
int is_single(PyObject *tag)
{
    return unicode_in_string_list(tag, SINGLE);
}

/*
    Return whether or not the given tag must exist without a close tag.
*/
int is_single_only(PyObject *tag)
{
    return unicode_in_string_list(tag, SINGLE_ONLY);
}

/*
    Return whether the given scheme is valid for external links.
*/
int is_scheme(PyObject *scheme, int slashes)
{
    if (slashes)
        return unicode_in_string_list(scheme, URI_SCHEMES);
    else
        return unicode_in_string_list(scheme, URI_SCHEMES_AUTHORITY_OPTIONAL);
}

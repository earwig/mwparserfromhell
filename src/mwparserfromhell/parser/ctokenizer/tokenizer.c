/*
Copyright (C) 2012-2017 Ben Kurtovic <ben.kurtovic@gmail.com>

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

#include "tokenizer.h"
#include "tok_parse.h"
#include "tok_support.h"
#include "tokens.h"

/* Globals */

int route_state;
uint64_t route_context;

char **entitydefs;

PyObject *NOARGS;
PyObject *definitions;

static PyObject *ParserError;

/* Forward declarations */

static int load_exceptions(void);

/*
    Create a new tokenizer object.
*/
static PyObject *
Tokenizer_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    Tokenizer *self = (Tokenizer *) type->tp_alloc(type, 0);
    return (PyObject *) self;
}

/*
    Deallocate the given tokenizer's text field.
*/
static void
dealloc_tokenizer_text(TokenizerInput *text)
{
    Py_XDECREF(text->object);
}

/*
    Deallocate the given tokenizer object.
*/
static void
Tokenizer_dealloc(Tokenizer *self)
{
    Stack *this = self->topstack, *next;
    dealloc_tokenizer_text(&self->text);

    while (this) {
        Py_DECREF(this->stack);
        Textbuffer_dealloc(this->textbuffer);
        next = this->next;
        free(this);
        this = next;
    }
    Py_TYPE(self)->tp_free((PyObject *) self);
}

/*
    Initialize a new tokenizer instance's text field.
*/
static void
init_tokenizer_text(TokenizerInput *text)
{
    text->object = Py_None;
    Py_INCREF(Py_None);
    text->length = 0;
    text->kind = PyUnicode_WCHAR_KIND;
    text->data = NULL;
}

/*
    Initialize a new tokenizer instance by setting instance attributes.
*/
static int
Tokenizer_init(Tokenizer *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) {
        return -1;
    }
    init_tokenizer_text(&self->text);
    self->topstack = NULL;
    self->head = self->global = self->depth = 0;
    self->route_context = self->route_state = 0;
    self->bad_routes = NULL;
    self->skip_style_tags = 0;
    return 0;
}

/*
    Load input text into the tokenizer.
*/
static int
load_tokenizer_text(TokenizerInput *text, PyObject *input)
{
    dealloc_tokenizer_text(text);
    text->object = input;

    if (PyUnicode_READY(input) < 0) {
        return -1;
    }
    text->kind = PyUnicode_KIND(input);
    text->data = PyUnicode_DATA(input);
    text->length = PyUnicode_GET_LENGTH(input);
    return 0;
}

/*
    Build a list of tokens from a string of wikicode and return it.
*/
static PyObject *
Tokenizer_tokenize(Tokenizer *self, PyObject *args)
{
    PyObject *input, *tokens;
    unsigned long long context = 0;
    int skip_style_tags = 0;

    if (PyArg_ParseTuple(args, "U|Kp", &input, &context, &skip_style_tags)) {
        Py_INCREF(input);
        if (load_tokenizer_text(&self->text, input)) {
            return NULL;
        }
    } else {
        const char *encoded;
        Py_ssize_t size;

        /* Failed to parse a Unicode object; try a string instead. */
        PyErr_Clear();
        if (!PyArg_ParseTuple(
                args, "s#|Kp", &encoded, &size, &context, &skip_style_tags)) {
            return NULL;
        }
        if (!(input = PyUnicode_FromStringAndSize(encoded, size))) {
            return NULL;
        }
        if (load_tokenizer_text(&self->text, input)) {
            return NULL;
        }
    }

    self->head = self->global = self->depth = 0;
    self->skip_style_tags = skip_style_tags;
    self->bad_routes = NULL;

    tokens = Tokenizer_parse(self, context, 1);

    Tokenizer_free_bad_route_tree(self);

    if (!tokens || self->topstack) {
        Py_XDECREF(tokens);
        if (PyErr_Occurred()) {
            return NULL;
        }
        if (!ParserError && load_exceptions() < 0) {
            return NULL;
        }
        if (BAD_ROUTE) {
            RESET_ROUTE();
            PyErr_SetString(ParserError, "C tokenizer exited with BAD_ROUTE");
        } else if (self->topstack) {
            PyErr_SetString(ParserError,
                            "C tokenizer exited with non-empty token stack");
        } else {
            PyErr_SetString(ParserError, "C tokenizer exited unexpectedly");
        }
        return NULL;
    }
    return tokens;
}

static int
load_entities(void)
{
    PyObject *tempmod, *defmap, *deflist;
    unsigned numdefs, i;
    PyObject *string;

    tempmod = PyImport_ImportModule("html.entities");
    if (!tempmod) {
        return -1;
    }
    defmap = PyObject_GetAttrString(tempmod, "entitydefs");
    if (!defmap) {
        return -1;
    }
    Py_DECREF(tempmod);
    deflist = PyDict_Keys(defmap);
    if (!deflist) {
        return -1;
    }
    Py_DECREF(defmap);
    numdefs = (unsigned) PyList_GET_SIZE(deflist);
    entitydefs = calloc(numdefs + 1, sizeof(char *));
    if (!entitydefs) {
        return -1;
    }
    for (i = 0; i < numdefs; i++) {
        string = PyUnicode_AsASCIIString(PyList_GET_ITEM(deflist, i));
        if (!string) {
            return -1;
        }
        entitydefs[i] = PyBytes_AsString(string);
        if (!entitydefs[i]) {
            return -1;
        }
    }
    Py_DECREF(deflist);
    return 0;
}

static int
load_tokens(void)
{
    PyObject *tempmod, *tokens;
    PyObject *globals = PyEval_GetGlobals(), *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1), *modname = PyUnicode_FromString("tokens");
    char *name = "mwparserfromhell.parser";

    if (!fromlist || !modname) {
        return -1;
    }
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod) {
        return -1;
    }
    tokens = PyObject_GetAttrString(tempmod, "tokens");
    Py_DECREF(tempmod);
    load_tokens_from_module(tokens);
    Py_DECREF(tokens);
    return 0;
}

static int
load_defs(void)
{
    PyObject *tempmod;
    PyObject *globals = PyEval_GetGlobals(), *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1), *modname = PyUnicode_FromString("definitions");
    char *name = "mwparserfromhell";

    if (!fromlist || !modname) {
        return -1;
    }
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod) {
        return -1;
    }
    definitions = PyObject_GetAttrString(tempmod, "definitions");
    Py_DECREF(tempmod);
    return 0;
}

static int
load_exceptions(void)
{
    PyObject *tempmod, *parsermod;
    PyObject *globals = PyEval_GetGlobals(), *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1), *modname = PyUnicode_FromString("parser");
    char *name = "mwparserfromhell";

    if (!fromlist || !modname) {
        return -1;
    }
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod) {
        return -1;
    }
    parsermod = PyObject_GetAttrString(tempmod, "parser");
    Py_DECREF(tempmod);
    ParserError = PyObject_GetAttrString(parsermod, "ParserError");
    Py_DECREF(parsermod);
    return 0;
}

PyMODINIT_FUNC
PyInit__tokenizer(void)
{
    PyObject *module;

    TokenizerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TokenizerType) < 0) {
        return NULL;
    }
    module = PyModule_Create(&module_def);
    if (!module) {
        return NULL;
    }
    Py_INCREF(&TokenizerType);
    PyModule_AddObject(module, "CTokenizer", (PyObject *) &TokenizerType);
    Py_INCREF(Py_True);
    PyDict_SetItemString(TokenizerType.tp_dict, "USES_C", Py_True);
    NOARGS = PyTuple_New(0);
    if (!NOARGS || load_entities() || load_tokens() || load_defs()) {
        return NULL;
    }
    return module;
}

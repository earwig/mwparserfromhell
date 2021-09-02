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

#pragma once

#include "common.h"
#include "textbuffer.h"

/* Functions */

static PyObject *Tokenizer_new(PyTypeObject *, PyObject *, PyObject *);
static void Tokenizer_dealloc(Tokenizer *);
static int Tokenizer_init(Tokenizer *, PyObject *, PyObject *);
static PyObject *Tokenizer_tokenize(Tokenizer *, PyObject *);

/* Structs */

static PyMethodDef Tokenizer_methods[] = {
    {
        "tokenize",
        (PyCFunction) Tokenizer_tokenize,
        METH_VARARGS,
        "Build a list of tokens from a string of wikicode and return it.",
    },
    {NULL},
};

static PyMemberDef Tokenizer_members[] = {
    {NULL},
};

static PyTypeObject TokenizerType = {
    PyVarObject_HEAD_INIT(NULL, 0)                         /* header */
    "_tokenizer.CTokenizer",                               /* tp_name */
    sizeof(Tokenizer),                                     /* tp_basicsize */
    0,                                                     /* tp_itemsize */
    (destructor) Tokenizer_dealloc,                        /* tp_dealloc */
    0,                                                     /* tp_print */
    0,                                                     /* tp_getattr */
    0,                                                     /* tp_setattr */
    0,                                                     /* tp_compare */
    0,                                                     /* tp_repr */
    0,                                                     /* tp_as_number */
    0,                                                     /* tp_as_sequence */
    0,                                                     /* tp_as_mapping */
    0,                                                     /* tp_hash  */
    0,                                                     /* tp_call */
    0,                                                     /* tp_str */
    0,                                                     /* tp_getattro */
    0,                                                     /* tp_setattro */
    0,                                                     /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                                    /* tp_flags */
    "Creates a list of tokens from a string of wikicode.", /* tp_doc */
    0,                                                     /* tp_traverse */
    0,                                                     /* tp_clear */
    0,                                                     /* tp_richcompare */
    0,                                                     /* tp_weaklistoffset */
    0,                                                     /* tp_iter */
    0,                                                     /* tp_iternext */
    Tokenizer_methods,                                     /* tp_methods */
    Tokenizer_members,                                     /* tp_members */
    0,                                                     /* tp_getset */
    0,                                                     /* tp_base */
    0,                                                     /* tp_dict */
    0,                                                     /* tp_descr_get */
    0,                                                     /* tp_descr_set */
    0,                                                     /* tp_dictoffset */
    (initproc) Tokenizer_init,                             /* tp_init */
    0,                                                     /* tp_alloc */
    Tokenizer_new,                                         /* tp_new */
};

static PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "_tokenizer",
    "Creates a list of tokens from a string of wikicode.",
    -1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
};

/*
Tokenizer Header File for MWParserFromHell
Copyright (C) 2012 Ben Kurtovic <ben.kurtovic@verizon.net>

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

#ifndef PY_SSIZE_T_CLEAN
#define PY_SSIZE_T_CLEAN
#endif

#include <Python.h>
#include <math.h>
#include <structmember.h>

static const char* MARKERS[] = {
    "{",  "}", "[", "]", "<", ">", "|", "=", "&", "#", "*", ";", ":", "/", "-",
    "!", "\n", ""};
static const int NUM_MARKERS = 18;

static int route_state = 0;
#define BAD_ROUTE     (route_state)
#define FAIL_ROUTE()  (route_state = 1)
#define RESET_ROUTE() (route_state = 0)

static PyObject* EMPTY;
static PyObject* NOARGS;
static PyObject* tokens;


/* Local contexts: */

static const Py_ssize_t LC_TEMPLATE =             0x0007;
static const Py_ssize_t LC_TEMPLATE_NAME =        0x0001;
static const Py_ssize_t LC_TEMPLATE_PARAM_KEY =   0x0002;
static const Py_ssize_t LC_TEMPLATE_PARAM_VALUE = 0x0004;

static const Py_ssize_t LC_ARGUMENT =             0x0018;
static const Py_ssize_t LC_ARGUMENT_NAME =        0x0008;
static const Py_ssize_t LC_ARGUMENT_DEFAULT =     0x0010;

static const Py_ssize_t LC_WIKILINK =             0x0060;
static const Py_ssize_t LC_WIKILINK_TITLE =       0x0020;
static const Py_ssize_t LC_WIKILINK_TEXT =        0x0040;

static const Py_ssize_t LC_HEADING =              0x1f80;
static const Py_ssize_t LC_HEADING_LEVEL_1 =      0x0080;
static const Py_ssize_t LC_HEADING_LEVEL_2 =      0x0100;
static const Py_ssize_t LC_HEADING_LEVEL_3 =      0x0200;
static const Py_ssize_t LC_HEADING_LEVEL_4 =      0x0400;
static const Py_ssize_t LC_HEADING_LEVEL_5 =      0x0800;
static const Py_ssize_t LC_HEADING_LEVEL_6 =      0x1000;

static const Py_ssize_t LC_COMMENT =              0x2000;


/* Global contexts: */

static const Py_ssize_t GL_HEADING = 0x1;


/* Miscellaneous structs: */

typedef struct {
    PyObject* title;
    Py_ssize_t level;
} HeadingData;


/* Tokenizer object definition: */

typedef struct {
    PyObject_HEAD
    PyObject* text;        /* text to tokenize */
    PyObject* stacks;      /* token stacks */
    PyObject* topstack;    /* topmost stack */
    Py_ssize_t head;       /* current position in text */
    Py_ssize_t length;     /* length of text */
    Py_ssize_t global;     /* global context */
} Tokenizer;


/* Macros for accessing Tokenizer data: */

#define Tokenizer_STACK(self) PySequence_Fast_GET_ITEM(self->topstack, 0)
#define Tokenizer_CONTEXT(self) PySequence_Fast_GET_ITEM(self->topstack, 1)
#define Tokenizer_CONTEXT_VAL(self) PyInt_AsSsize_t(Tokenizer_CONTEXT(self))
#define Tokenizer_TEXTBUFFER(self) PySequence_Fast_GET_ITEM(self->topstack, 2)
#define Tokenizer_READ(self, num) PyUnicode_AS_UNICODE(Tokenizer_read(self, num))


/* Tokenizer function prototypes: */

static PyObject* Tokenizer_new(PyTypeObject*, PyObject*, PyObject*);
static void Tokenizer_dealloc(Tokenizer*);
static int Tokenizer_init(Tokenizer*, PyObject*, PyObject*);
static int Tokenizer_set_context(Tokenizer*, Py_ssize_t);
static int Tokenizer_set_textbuffer(Tokenizer*, PyObject*);
static int Tokenizer_push(Tokenizer*, Py_ssize_t);
static int Tokenizer_push_textbuffer(Tokenizer*);
static int Tokenizer_delete_top_of_stack(Tokenizer*);
static PyObject* Tokenizer_pop(Tokenizer*);
static PyObject* Tokenizer_pop_keeping_context(Tokenizer*);
static void* Tokenizer_fail_route(Tokenizer*);
static int Tokenizer_write(Tokenizer*, PyObject*);
static int Tokenizer_write_first(Tokenizer*, PyObject*);
static int Tokenizer_write_text(Tokenizer*, PyObject*);
static int Tokenizer_write_all(Tokenizer*, PyObject*);
static int Tokenizer_write_text_then_stack(Tokenizer*, PyObject*);
static PyObject* Tokenizer_read(Tokenizer*, Py_ssize_t);
static PyObject* Tokenizer_read_backwards(Tokenizer*, Py_ssize_t);
static int Tokenizer_parse_template_or_argument(Tokenizer*);
static int Tokenizer_parse_template(Tokenizer*);
static int Tokenizer_parse_argument(Tokenizer*);
static int Tokenizer_verify_safe(Tokenizer*, const char* []);
static int Tokenizer_handle_template_param(Tokenizer*);
static int Tokenizer_handle_template_param_value(Tokenizer*);
static PyObject* Tokenizer_handle_template_end(Tokenizer*);
static int Tokenizer_handle_argument_separator(Tokenizer*);
static PyObject* Tokenizer_handle_argument_end(Tokenizer*);
static int Tokenizer_parse_wikilink(Tokenizer*);
static int Tokenizer_handle_wikilink_separator(Tokenizer*);
static PyObject* Tokenizer_handle_wikilink_end(Tokenizer*);
static int Tokenizer_parse_heading(Tokenizer*);
static HeadingData* Tokenizer_handle_heading_end(Tokenizer*);
static int Tokenizer_really_parse_entity(Tokenizer*);
static int Tokenizer_parse_entity(Tokenizer*);
static int Tokenizer_parse_comment(Tokenizer*);
static PyObject* Tokenizer_parse(Tokenizer*, Py_ssize_t);
static PyObject* Tokenizer_tokenize(Tokenizer*, PyObject*);


/* More structs for creating the Tokenizer type: */

static PyMethodDef
Tokenizer_methods[] = {
    {"tokenize", (PyCFunction) Tokenizer_tokenize, METH_VARARGS,
    "Build a list of tokens from a string of wikicode and return it."},
    {NULL}
};

static PyMemberDef
Tokenizer_members[] = {
    {NULL}
};

static PyMethodDef
module_methods[] = {
    {NULL}
};

static PyTypeObject
TokenizerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                      /* ob_size */
    "_tokenizer.CTokenizer",                                /* tp_name */
    sizeof(Tokenizer),                                      /* tp_basicsize */
    0,                                                      /* tp_itemsize */
    (destructor) Tokenizer_dealloc,                         /* tp_dealloc */
    0,                                                      /* tp_print */
    0,                                                      /* tp_getattr */
    0,                                                      /* tp_setattr */
    0,                                                      /* tp_compare */
    0,                                                      /* tp_repr */
    0,                                                      /* tp_as_number */
    0,                                                      /* tp_as_sequence */
    0,                                                      /* tp_as_mapping */
    0,                                                      /* tp_hash  */
    0,                                                      /* tp_call */
    0,                                                      /* tp_str */
    0,                                                      /* tp_getattro */
    0,                                                      /* tp_setattro */
    0,                                                      /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                                     /* tp_flags */
    "Creates a list of tokens from a string of wikicode.",  /* tp_doc */
    0,                                                      /* tp_traverse */
    0,                                                      /* tp_clear */
    0,                                                      /* tp_richcompare */
    0,                                                      /* tp_weaklistoffset */
    0,                                                      /* tp_iter */
    0,                                                      /* tp_iternext */
    Tokenizer_methods,                                      /* tp_methods */
    Tokenizer_members,                                      /* tp_members */
    0,                                                      /* tp_getset */
    0,                                                      /* tp_base */
    0,                                                      /* tp_dict */
    0,                                                      /* tp_descr_get */
    0,                                                      /* tp_descr_set */
    0,                                                      /* tp_dictoffset */
    (initproc) Tokenizer_init,                              /* tp_init */
    0,                                                      /* tp_alloc */
    Tokenizer_new,                                          /* tp_new */
};

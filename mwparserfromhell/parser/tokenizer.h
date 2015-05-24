/*
Tokenizer Header File for MWParserFromHell
Copyright (C) 2012-2015 Ben Kurtovic <ben.kurtovic@gmail.com>

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
#include <bytesobject.h>
#include <stdint.h>

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif

#define malloc PyObject_Malloc
#define free   PyObject_Free

#define DIGITS    "0123456789"
#define HEXDIGITS "0123456789abcdefABCDEF"
#define ALPHANUM  "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

static const char MARKERS[] = {
    '{', '}', '[', ']', '<', '>', '|', '=', '&', '\'', '#', '*', ';', ':', '/',
    '-', '!', '\n', '\0'};

#define NUM_MARKERS 19
#define TEXTBUFFER_BLOCKSIZE 1024
#define MAX_DEPTH 40
#define MAX_CYCLES 100000
#define MAX_BRACES 255
#define MAX_ENTITY_SIZE 8

static int route_state = 0;
static uint64_t route_context = 0;
#define BAD_ROUTE            route_state
#define BAD_ROUTE_CONTEXT    route_context
#define FAIL_ROUTE(context)  route_state = 1; route_context = context
#define RESET_ROUTE()        route_state = 0

static char** entitydefs;

static PyObject* EMPTY;
static PyObject* NOARGS;
static PyObject* ParserError;
static PyObject* definitions;


/* Tokens: */

static PyObject* Text;

static PyObject* TemplateOpen;
static PyObject* TemplateParamSeparator;
static PyObject* TemplateParamEquals;
static PyObject* TemplateClose;

static PyObject* ArgumentOpen;
static PyObject* ArgumentSeparator;
static PyObject* ArgumentClose;

static PyObject* WikilinkOpen;
static PyObject* WikilinkSeparator;
static PyObject* WikilinkClose;

static PyObject* ExternalLinkOpen;
static PyObject* ExternalLinkSeparator;
static PyObject* ExternalLinkClose;

static PyObject* HTMLEntityStart;
static PyObject* HTMLEntityNumeric;
static PyObject* HTMLEntityHex;
static PyObject* HTMLEntityEnd;
static PyObject* HeadingStart;
static PyObject* HeadingEnd;

static PyObject* CommentStart;
static PyObject* CommentEnd;

static PyObject* TagOpenOpen;
static PyObject* TagAttrStart;
static PyObject* TagAttrEquals;
static PyObject* TagAttrQuote;
static PyObject* TagCloseOpen;
static PyObject* TagCloseSelfclose;
static PyObject* TagOpenClose;
static PyObject* TagCloseClose;


/* Local contexts: */

#define LC_TEMPLATE                 0x0000000000000007
#define LC_TEMPLATE_NAME            0x0000000000000001
#define LC_TEMPLATE_PARAM_KEY       0x0000000000000002
#define LC_TEMPLATE_PARAM_VALUE     0x0000000000000004

#define LC_ARGUMENT                 0x0000000000000018
#define LC_ARGUMENT_NAME            0x0000000000000008
#define LC_ARGUMENT_DEFAULT         0x0000000000000010

#define LC_WIKILINK                 0x0000000000000060
#define LC_WIKILINK_TITLE           0x0000000000000020
#define LC_WIKILINK_TEXT            0x0000000000000040

#define LC_EXT_LINK                 0x0000000000000180
#define LC_EXT_LINK_URI             0x0000000000000080
#define LC_EXT_LINK_TITLE           0x0000000000000100

#define LC_HEADING                  0x0000000000007E00
#define LC_HEADING_LEVEL_1          0x0000000000000200
#define LC_HEADING_LEVEL_2          0x0000000000000400
#define LC_HEADING_LEVEL_3          0x0000000000000800
#define LC_HEADING_LEVEL_4          0x0000000000001000
#define LC_HEADING_LEVEL_5          0x0000000000002000
#define LC_HEADING_LEVEL_6          0x0000000000004000

#define LC_TAG                      0x0000000000078000
#define LC_TAG_OPEN                 0x0000000000008000
#define LC_TAG_ATTR                 0x0000000000010000
#define LC_TAG_BODY                 0x0000000000020000
#define LC_TAG_CLOSE                0x0000000000040000

#define LC_STYLE                    0x0000000000780000
#define LC_STYLE_ITALICS            0x0000000000080000
#define LC_STYLE_BOLD               0x0000000000100000
#define LC_STYLE_PASS_AGAIN         0x0000000000200000
#define LC_STYLE_SECOND_PASS        0x0000000000400000

#define LC_DLTERM                   0x0000000000800000

#define LC_SAFETY_CHECK             0x000000003F000000
#define LC_HAS_TEXT                 0x0000000001000000
#define LC_FAIL_ON_TEXT             0x0000000002000000
#define LC_FAIL_NEXT                0x0000000004000000
#define LC_FAIL_ON_LBRACE           0x0000000008000000
#define LC_FAIL_ON_RBRACE           0x0000000010000000
#define LC_FAIL_ON_EQUALS           0x0000000020000000

#define LC_TABLE                    0x0000000FC0000000
#define LC_TABLE_CELL_LINE_CONTEXTS 0x0000000D00000000
#define LC_TABLE_OPEN               0x0000000040000000
#define LC_TABLE_CELL_OPEN          0x0000000080000000
#define LC_TABLE_CELL_STYLE         0x0000000100000000
#define LC_TABLE_ROW_OPEN           0x0000000200000000
#define LC_TABLE_TD_LINE            0x0000000400000000
#define LC_TABLE_TH_LINE            0x0000000800000000

/* Global contexts: */

#define GL_HEADING 0x1

/* Aggregate contexts: */

#define AGG_FAIL         (LC_TEMPLATE | LC_ARGUMENT | LC_WIKILINK | LC_EXT_LINK_TITLE | LC_HEADING | LC_TAG | LC_STYLE | LC_TABLE_OPEN)
#define AGG_UNSAFE       (LC_TEMPLATE_NAME | LC_WIKILINK_TITLE | LC_EXT_LINK_TITLE | LC_TEMPLATE_PARAM_KEY | LC_ARGUMENT_NAME)
#define AGG_DOUBLE       (LC_TEMPLATE_PARAM_KEY | LC_TAG_CLOSE | LC_TABLE_ROW_OPEN)
#define AGG_NO_WIKILINKS (LC_TEMPLATE_NAME | LC_ARGUMENT_NAME | LC_WIKILINK_TITLE | LC_EXT_LINK_URI)
#define AGG_NO_EXT_LINKS (LC_TEMPLATE_NAME | LC_ARGUMENT_NAME | LC_WIKILINK_TITLE | LC_EXT_LINK)

/* Tag contexts: */

#define TAG_NAME        0x01
#define TAG_ATTR_READY  0x02
#define TAG_ATTR_NAME   0x04
#define TAG_ATTR_VALUE  0x08
#define TAG_QUOTED      0x10
#define TAG_NOTE_SPACE  0x20
#define TAG_NOTE_EQUALS 0x40
#define TAG_NOTE_QUOTE  0x80


/* Miscellaneous structs: */

struct Textbuffer {
    Py_ssize_t size;
    Py_UNICODE* data;
    struct Textbuffer* prev;
    struct Textbuffer* next;
};

struct Stack {
    PyObject* stack;
    uint64_t context;
    struct Textbuffer* textbuffer;
    struct Stack* next;
};

typedef struct {
    PyObject* title;
    int level;
} HeadingData;

typedef struct {
    uint64_t context;
    struct Textbuffer* pad_first;
    struct Textbuffer* pad_before_eq;
    struct Textbuffer* pad_after_eq;
    Py_UNICODE quoter;
    Py_ssize_t reset;
} TagData;

typedef struct Textbuffer Textbuffer;
typedef struct Stack Stack;


/* Tokenizer object definition: */

typedef struct {
    PyObject_HEAD
    PyObject* text;         /* text to tokenize */
    Stack* topstack;        /* topmost stack */
    Py_ssize_t head;        /* current position in text */
    Py_ssize_t length;      /* length of text */
    int global;             /* global context */
    int depth;              /* stack recursion depth */
    int cycles;             /* total number of stack recursions */
    int skip_style_tags;    /* temporary fix for the sometimes broken tag parser */
} Tokenizer;


/* Macros related to Tokenizer functions: */

#define Tokenizer_READ(self, delta) (*PyUnicode_AS_UNICODE(Tokenizer_read(self, delta)))
#define Tokenizer_READ_BACKWARDS(self, delta) \
                (*PyUnicode_AS_UNICODE(Tokenizer_read_backwards(self, delta)))
#define Tokenizer_CAN_RECURSE(self) (self->depth < MAX_DEPTH && self->cycles < MAX_CYCLES)

#define Tokenizer_emit(self, token) Tokenizer_emit_token(self, token, 0)
#define Tokenizer_emit_first(self, token) Tokenizer_emit_token(self, token, 1)
#define Tokenizer_emit_kwargs(self, token, kwargs) Tokenizer_emit_token_kwargs(self, token, kwargs, 0)
#define Tokenizer_emit_first_kwargs(self, token, kwargs) Tokenizer_emit_token_kwargs(self, token, kwargs, 1)


/* Macros for accessing definitions: */

#define GET_HTML_TAG(markup) (markup == ':' ? "dd" : markup == ';' ? "dt" : "li")
#define IS_PARSABLE(tag) (call_def_func("is_parsable", tag, NULL, NULL))
#define IS_SINGLE(tag) (call_def_func("is_single", tag, NULL, NULL))
#define IS_SINGLE_ONLY(tag) (call_def_func("is_single_only", tag, NULL, NULL))
#define IS_SCHEME(scheme, slashes, reverse) \
    (call_def_func("is_scheme", scheme, slashes ? Py_True : Py_False, reverse ? Py_True : Py_False))


/* Function prototypes: */

static Textbuffer* Textbuffer_new(void);
static void Textbuffer_dealloc(Textbuffer*);

static TagData* TagData_new(void);
static void TagData_dealloc(TagData*);

static PyObject* Tokenizer_new(PyTypeObject*, PyObject*, PyObject*);
static void Tokenizer_dealloc(Tokenizer*);
static int Tokenizer_init(Tokenizer*, PyObject*, PyObject*);
static int Tokenizer_parse_entity(Tokenizer*);
static int Tokenizer_parse_comment(Tokenizer*);
static int Tokenizer_handle_dl_term(Tokenizer*);
static int Tokenizer_parse_tag(Tokenizer*);
static PyObject* Tokenizer_parse(Tokenizer*, uint64_t, int);
static PyObject* Tokenizer_tokenize(Tokenizer*, PyObject*);

static int load_exceptions(void);


/* Macros for Python 2/3 compatibility: */

#ifdef IS_PY3K
    #define NEW_INT_FUNC      PyLong_FromSsize_t
    #define IMPORT_NAME_FUNC  PyUnicode_FromString
    #define CREATE_MODULE     PyModule_Create(&module_def);
    #define ENTITYDEFS_MODULE "html.entities"
    #define INIT_FUNC_NAME    PyInit__tokenizer
    #define INIT_ERROR        return NULL
#else
    #define NEW_INT_FUNC      PyInt_FromSsize_t
    #define IMPORT_NAME_FUNC  PyBytes_FromString
    #define CREATE_MODULE     Py_InitModule("_tokenizer", NULL);
    #define ENTITYDEFS_MODULE "htmlentitydefs"
    #define INIT_FUNC_NAME    init_tokenizer
    #define INIT_ERROR        return
#endif


/* More structs for creating the Tokenizer type: */

static PyMethodDef Tokenizer_methods[] = {
    {"tokenize", (PyCFunction) Tokenizer_tokenize, METH_VARARGS,
    "Build a list of tokens from a string of wikicode and return it."},
    {NULL}
};

static PyMemberDef Tokenizer_members[] = {
    {NULL}
};

static PyTypeObject TokenizerType = {
    PyVarObject_HEAD_INIT(NULL, 0)
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

#ifdef IS_PY3K
static PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "_tokenizer",
    "Creates a list of tokens from a string of wikicode.",
    -1, NULL, NULL, NULL, NULL, NULL
};
#endif

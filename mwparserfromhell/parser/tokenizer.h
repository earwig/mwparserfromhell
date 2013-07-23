/*
Tokenizer Header File for MWParserFromHell
Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>

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

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif

#define malloc PyObject_Malloc
#define free   PyObject_Free

#define DIGITS    "0123456789"
#define HEXDIGITS "0123456789abcdefABCDEF"
#define ALPHANUM  "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

static const char* MARKERS[] = {
    "{",  "}", "[", "]", "<", ">", "|", "=", "&", "#", "*", ";", ":", "/",
    "\\", "\"", "-", "!", "\n", ""};

#define NUM_MARKERS 20
#define TEXTBUFFER_BLOCKSIZE 1024
#define MAX_DEPTH 40
#define MAX_CYCLES 100000
#define MAX_BRACES 255
#define MAX_ENTITY_SIZE 8

static int route_state = 0;
#define BAD_ROUTE     (route_state)
#define FAIL_ROUTE()  (route_state = 1)
#define RESET_ROUTE() (route_state = 0)

static char** entitydefs;

static PyObject* EMPTY;
static PyObject* NOARGS;
static PyObject* tag_defs;


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

#define LC_TEMPLATE             0x000007
#define LC_TEMPLATE_NAME        0x000001
#define LC_TEMPLATE_PARAM_KEY   0x000002
#define LC_TEMPLATE_PARAM_VALUE 0x000004

#define LC_ARGUMENT             0x000018
#define LC_ARGUMENT_NAME        0x000008
#define LC_ARGUMENT_DEFAULT     0x000010

#define LC_WIKILINK             0x000060
#define LC_WIKILINK_TITLE       0x000020
#define LC_WIKILINK_TEXT        0x000040

#define LC_HEADING              0x001F80
#define LC_HEADING_LEVEL_1      0x000080
#define LC_HEADING_LEVEL_2      0x000100
#define LC_HEADING_LEVEL_3      0x000200
#define LC_HEADING_LEVEL_4      0x000400
#define LC_HEADING_LEVEL_5      0x000800
#define LC_HEADING_LEVEL_6      0x001000

#define LC_COMMENT              0x002000

#define LC_TAG                  0x03C000
#define LC_TAG_OPEN             0x004000
#define LC_TAG_ATTR             0x008000
#define LC_TAG_BODY             0x010000
#define LC_TAG_CLOSE            0x020000

#define LC_SAFETY_CHECK         0xFC0000
#define LC_HAS_TEXT             0x040000
#define LC_FAIL_ON_TEXT         0x080000
#define LC_FAIL_NEXT            0x100000
#define LC_FAIL_ON_LBRACE       0x200000
#define LC_FAIL_ON_RBRACE       0x400000
#define LC_FAIL_ON_EQUALS       0x800000

/* Global contexts: */

#define GL_HEADING 0x1

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
    struct Textbuffer* next;
};

struct Stack {
    PyObject* stack;
    int context;
    struct Textbuffer* textbuffer;
    struct Stack* next;
};

typedef struct {
    PyObject* title;
    int level;
} HeadingData;

typedef struct {
    int context;
    struct Textbuffer* pad_first;
    struct Textbuffer* pad_before_eq;
    struct Textbuffer* pad_after_eq;
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
} Tokenizer;


/* Macros for accessing Tokenizer data: */

#define Tokenizer_READ(self, delta) (*PyUnicode_AS_UNICODE(Tokenizer_read(self, delta)))
#define Tokenizer_READ_BACKWARDS(self, delta) \
                (*PyUnicode_AS_UNICODE(Tokenizer_read_backwards(self, delta)))
#define Tokenizer_CAN_RECURSE(self) (self->depth < MAX_DEPTH && self->cycles < MAX_CYCLES)


/* Macros for accessing HTML tag definitions: */

#define IS_PARSABLE(tag) (call_tag_def_func("is_parsable", tag))
#define IS_SINGLE(tag) (call_tag_def_func("is_single", tag))
#define IS_SINGLE_ONLY(tag) (call_tag_def_func("is_single_only", tag))


/* Function prototypes: */

static Textbuffer* Textbuffer_new(void);
static void Textbuffer_dealloc(Textbuffer*);
static int Textbuffer_write(Textbuffer**, Py_UNICODE);
static PyObject* Textbuffer_render(Textbuffer*);

static TagData* TagData_new(void);
static void TagData_dealloc(TagData*);
static int TagData_reset_buffers(TagData*);

static PyObject* Tokenizer_new(PyTypeObject*, PyObject*, PyObject*);
static void Tokenizer_dealloc(Tokenizer*);
static int Tokenizer_init(Tokenizer*, PyObject*, PyObject*);
static int Tokenizer_push(Tokenizer*, int);
static int Tokenizer_push_textbuffer(Tokenizer*);
static void Tokenizer_delete_top_of_stack(Tokenizer*);
static PyObject* Tokenizer_pop(Tokenizer*);
static PyObject* Tokenizer_pop_keeping_context(Tokenizer*);
static void* Tokenizer_fail_route(Tokenizer*);
static int Tokenizer_emit(Tokenizer*, PyObject*);
static int Tokenizer_emit_first(Tokenizer*, PyObject*);
static int Tokenizer_emit_text(Tokenizer*, Py_UNICODE);
static int Tokenizer_emit_all(Tokenizer*, PyObject*);
static int Tokenizer_emit_text_then_stack(Tokenizer*, const char*);
static PyObject* Tokenizer_read(Tokenizer*, Py_ssize_t);
static PyObject* Tokenizer_read_backwards(Tokenizer*, Py_ssize_t);
static int Tokenizer_parse_template_or_argument(Tokenizer*);
static int Tokenizer_parse_template(Tokenizer*);
static int Tokenizer_parse_argument(Tokenizer*);
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
static int Tokenizer_parse_tag(Tokenizer*);
static PyObject* Tokenizer_really_parse_tag(Tokenizer*);
static int Tokenizer_push_tag_buffer(Tokenizer*, TagData*);
static int Tokenizer_handle_tag_data(Tokenizer*, TagData*, Py_UNICODE);
static int Tokenizer_handle_tag_space(Tokenizer*, TagData*, Py_UNICODE);
static int Tokenizer_handle_tag_text(Tokenizer*, Py_UNICODE);
static PyObject* Tokenizer_handle_blacklisted_tag(Tokenizer*);
static int Tokenizer_handle_tag_close_open(Tokenizer*, TagData*, PyObject*);
static int Tokenizer_handle_tag_open_close(Tokenizer*);
static PyObject* Tokenizer_handle_tag_close_close(Tokenizer*);
static int Tokenizer_handle_invalid_tag_start(Tokenizer*);
static PyObject* Tokenizer_handle_single_only_tag_end(Tokenizer*);
static PyObject* Tokenizer_handle_single_tag_end(Tokenizer*);
static PyObject* Tokenizer_handle_end(Tokenizer*, int);
static int Tokenizer_verify_safe(Tokenizer*, int, Py_UNICODE);
static PyObject* Tokenizer_parse(Tokenizer*, int, int);
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

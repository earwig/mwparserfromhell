/*
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

#pragma once

#ifndef PY_SSIZE_T_CLEAN
#define PY_SSIZE_T_CLEAN  // See: https://docs.python.org/2/c-api/arg.html
#endif

#include <Python.h>
#include <structmember.h>
#include <bytesobject.h>

/* Compatibility macros */

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif

#ifndef uint64_t
#define uint64_t unsigned PY_LONG_LONG
#endif

#define malloc PyObject_Malloc  // XXX: yuck
#define free   PyObject_Free

/* Error handling globals/macros */

extern int route_state;  // TODO: this is NOT thread-safe!
extern uint64_t route_context;

#define BAD_ROUTE            route_state
#define BAD_ROUTE_CONTEXT    route_context
#define FAIL_ROUTE(context)  { route_state = 1; route_context = context; }
#define RESET_ROUTE()        route_state = 0

/* Shared globals */

extern char** entitydefs;

extern PyObject* EMPTY;
extern PyObject* NOARGS;
extern PyObject* definitions;

/* Structs */

struct Textbuffer {
    Py_ssize_t size;
    Py_UNICODE* data;
    struct Textbuffer* prev;
    struct Textbuffer* next;
};
typedef struct Textbuffer Textbuffer;

struct Stack {
    PyObject* stack;
    uint64_t context;
    struct Textbuffer* textbuffer;
    struct Stack* next;
};
typedef struct Stack Stack;

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

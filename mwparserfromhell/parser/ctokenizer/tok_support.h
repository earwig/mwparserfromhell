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

/* Functions */

int Tokenizer_push(Tokenizer*, uint64_t);
int Tokenizer_push_textbuffer(Tokenizer*);
void Tokenizer_delete_top_of_stack(Tokenizer*);
PyObject* Tokenizer_pop(Tokenizer*);
PyObject* Tokenizer_pop_keeping_context(Tokenizer*);
void* Tokenizer_fail_route(Tokenizer*);

int Tokenizer_emit_token(Tokenizer*, PyObject*, int);
int Tokenizer_emit_token_kwargs(Tokenizer*, PyObject*, PyObject*, int);
int Tokenizer_emit_char(Tokenizer*, Unicode);
int Tokenizer_emit_text(Tokenizer*, const char*);
int Tokenizer_emit_textbuffer(Tokenizer*, Textbuffer*);
int Tokenizer_emit_all(Tokenizer*, PyObject*);
int Tokenizer_emit_text_then_stack(Tokenizer*, const char*);

Unicode Tokenizer_read(Tokenizer*, Py_ssize_t);
Unicode Tokenizer_read_backwards(Tokenizer*, Py_ssize_t);

/* Macros */

#define MAX_DEPTH 40
#define MAX_CYCLES 100000

#define Tokenizer_CAN_RECURSE(self)                                           \
    (self->depth < MAX_DEPTH && self->cycles < MAX_CYCLES)

#define Tokenizer_emit(self, token)                                           \
    Tokenizer_emit_token(self, token, 0)
#define Tokenizer_emit_first(self, token)                                     \
    Tokenizer_emit_token(self, token, 1)
#define Tokenizer_emit_kwargs(self, token, kwargs)                            \
    Tokenizer_emit_token_kwargs(self, token, kwargs, 0)
#define Tokenizer_emit_first_kwargs(self, token, kwargs)                      \
    Tokenizer_emit_token_kwargs(self, token, kwargs, 1)

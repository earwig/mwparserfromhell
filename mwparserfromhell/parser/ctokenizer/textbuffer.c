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

#include "textbuffer.h"

#define TEXTBUFFER_BLOCKSIZE 1024

/*
    Create a new textbuffer object.
*/
Textbuffer* Textbuffer_new(void)
{
    Textbuffer* buffer = malloc(sizeof(Textbuffer));

    if (!buffer) {
        PyErr_NoMemory();
        return NULL;
    }
    buffer->size = 0;
    buffer->data = malloc(sizeof(Py_UNICODE) * TEXTBUFFER_BLOCKSIZE);
    if (!buffer->data) {
        free(buffer);
        PyErr_NoMemory();
        return NULL;
    }
    buffer->prev = buffer->next = NULL;
    return buffer;
}

/*
    Deallocate the given textbuffer.
*/
void Textbuffer_dealloc(Textbuffer* self)
{
    Textbuffer* next;

    while (self) {
        free(self->data);
        next = self->next;
        free(self);
        self = next;
    }
}

/*
    Write a Unicode codepoint to the given textbuffer.
*/
int Textbuffer_write(Textbuffer** this, Py_UNICODE code)
{
    Textbuffer* self = *this;

    if (self->size == TEXTBUFFER_BLOCKSIZE) {
        Textbuffer* new = Textbuffer_new();
        if (!new)
            return -1;
        new->next = self;
        self->prev = new;
        *this = self = new;
    }
    self->data[self->size++] = code;
    return 0;
}

/*
    Return the contents of the textbuffer as a Python Unicode object.
*/
PyObject* Textbuffer_render(Textbuffer* self)
{
    PyObject *result = PyUnicode_FromUnicode(self->data, self->size);
    PyObject *left, *concat;

    while (self->next) {
        self = self->next;
        left = PyUnicode_FromUnicode(self->data, self->size);
        concat = PyUnicode_Concat(left, result);
        Py_DECREF(left);
        Py_DECREF(result);
        result = concat;
    }
    return result;
}

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

#include "textbuffer.h"

#define INITIAL_CAPACITY 32
#define RESIZE_FACTOR 2
#define CONCAT_EXTRA 32

/*
    Internal allocation function for textbuffers.
*/
static int internal_alloc(Textbuffer* self, Unicode maxchar)
{
    self->capacity = INITIAL_CAPACITY;
    self->length = 0;

#ifdef PEP_393
    self->object = PyUnicode_New(self->capacity, maxchar);
    if (!self->object)
        return -1;
    self->kind = PyUnicode_KIND(self->object);
    self->data = PyUnicode_DATA(self->object);
#else
    (void) maxchar;  // Unused
    self->data = malloc(sizeof(Unicode) * self->capacity);
    if (!self->data)
        return -1;
#endif

    return 0;
}

/*
    Internal deallocation function for textbuffers.
*/
static void internal_dealloc(Textbuffer* self)
{
#ifdef PEP_393
    Py_DECREF(self->object);
#else
    free(self->data);
#endif
}

/*
    Internal resize function.
*/
static int internal_resize(Textbuffer* self, Py_ssize_t new_cap)
{
#ifdef PEP_393
    PyObject *newobj;
    void *newdata;

    newobj = PyUnicode_New(new_cap, PyUnicode_MAX_CHAR_VALUE(self->object));
    if (!newobj)
        return -1;
    newdata = PyUnicode_DATA(newobj);
    memcpy(newdata, self->data, self->length * self->kind);
    Py_DECREF(self->object);
    self->object = newobj;
    self->data = newdata;
#else
    if (!(self->data = realloc(self->data, sizeof(Unicode) * new_cap)))
        return -1;
#endif

    self->capacity = new_cap;
    return 0;
}

/*
    Create a new textbuffer object.
*/
Textbuffer* Textbuffer_new(TokenizerInput* text)
{
    Textbuffer* self = malloc(sizeof(Textbuffer));
    Unicode maxchar = 0;

#ifdef PEP_393
    maxchar = PyUnicode_MAX_CHAR_VALUE(text->object);
#endif

    if (!self)
        goto fail_nomem;
    if (internal_alloc(self, maxchar) < 0)
        goto fail_dealloc;
    return self;

    fail_dealloc:
    free(self);
    fail_nomem:
    PyErr_NoMemory();
    return NULL;
}

/*
    Deallocate the given textbuffer.
*/
void Textbuffer_dealloc(Textbuffer* self)
{
    internal_dealloc(self);
    free(self);
}

/*
    Reset a textbuffer to its initial, empty state.
*/
int Textbuffer_reset(Textbuffer* self)
{
    Unicode maxchar = 0;

#ifdef PEP_393
    maxchar = PyUnicode_MAX_CHAR_VALUE(self->object);
#endif

    internal_dealloc(self);
    if (internal_alloc(self, maxchar))
        return -1;
    return 0;
}

/*
    Write a Unicode codepoint to the given textbuffer.
*/
int Textbuffer_write(Textbuffer* self, Unicode code)
{
    if (self->length >= self->capacity) {
        if (internal_resize(self, self->capacity * RESIZE_FACTOR) < 0)
            return -1;
    }

#ifdef PEP_393
    PyUnicode_WRITE(self->kind, self->data, self->length++, code);
#else
    self->data[self->length++] = code;
#endif

    return 0;
}

/*
    Read a Unicode codepoint from the given index of the given textbuffer.

    This function does not check for bounds.
*/
Unicode Textbuffer_read(Textbuffer* self, Py_ssize_t index)
{
#ifdef PEP_393
    return PyUnicode_READ(self->kind, self->data, index);
#else
    return self->data[index];
#endif
}

/*
    Return the contents of the textbuffer as a Python Unicode object.
*/
PyObject* Textbuffer_render(Textbuffer* self)
{
#ifdef PEP_393
    return PyUnicode_FromKindAndData(self->kind, self->data, self->length);
#else
    return PyUnicode_FromUnicode(self->data, self->length);
#endif
}

/*
    Concatenate the 'other' textbuffer onto the end of the given textbuffer.
*/
int Textbuffer_concat(Textbuffer* self, Textbuffer* other)
{
    Py_ssize_t newlen = self->length + other->length;

    if (newlen > self->capacity) {
        if (internal_resize(self, newlen + CONCAT_EXTRA) < 0)
            return -1;
    }

#ifdef PEP_393
    assert(self->kind == other->kind);
    memcpy(((Py_UCS1*) self->data) + self->kind * self->length, other->data,
           other->length * other->kind);
#else
    memcpy(self->data + self->length, other->data,
           other->length * sizeof(Unicode));
#endif

    self->length = newlen;
    return 0;
}

/*
    Reverse the contents of the given textbuffer.
*/
void Textbuffer_reverse(Textbuffer* self)
{
    Py_ssize_t i, end = self->length - 1;
    Unicode tmp;

    for (i = 0; i < self->length / 2; i++) {
#ifdef PEP_393
        tmp = PyUnicode_READ(self->kind, self->data, i);
        PyUnicode_WRITE(self->kind, self->data, i,
                        PyUnicode_READ(self->kind, self->data, end - i));
        PyUnicode_WRITE(self->kind, self->data, end - i, tmp);
#else
        tmp = self->data[i];
        self->data[i] = self->data[end - i];
        self->data[end - i] = tmp;
#endif
    }
}

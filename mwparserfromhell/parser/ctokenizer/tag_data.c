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

#include "tag_data.h"
#include "contexts.h"

/*
    Initialize a new TagData object.
*/
TagData* TagData_new(void)
{
#define ALLOC_BUFFER(name)     \
    name = Textbuffer_new();   \
    if (!name) {               \
        TagData_dealloc(self); \
        return NULL;           \
    }

    TagData *self = malloc(sizeof(TagData));
    if (!self) {
        PyErr_NoMemory();
        return NULL;
    }
    self->context = TAG_NAME;
    ALLOC_BUFFER(self->pad_first)
    ALLOC_BUFFER(self->pad_before_eq)
    ALLOC_BUFFER(self->pad_after_eq)
    self->quoter = 0;
    self->reset = 0;
    return self;

#undef ALLOC_BUFFER
}

/*
    Deallocate the given TagData object.
*/
void TagData_dealloc(TagData* self)
{
#define DEALLOC_BUFFER(name)      \
    if (name)                     \
        Textbuffer_dealloc(name);

    DEALLOC_BUFFER(self->pad_first);
    DEALLOC_BUFFER(self->pad_before_eq);
    DEALLOC_BUFFER(self->pad_after_eq);
    free(self);

#undef DEALLOC_BUFFER
}

/*
    Clear the internal buffers of the given TagData object.
*/
int TagData_reset_buffers(TagData* self)
{
#define RESET_BUFFER(name)    \
    Textbuffer_dealloc(name); \
    name = Textbuffer_new();  \
    if (!name)                \
        return -1;

    RESET_BUFFER(self->pad_first)
    RESET_BUFFER(self->pad_before_eq)
    RESET_BUFFER(self->pad_after_eq)
    return 0;

#undef RESET_BUFFER
}

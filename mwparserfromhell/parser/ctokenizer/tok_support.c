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

#include "tok_support.h"
#include "textbuffer.h"
#include "tokens.h"

/*
    Add a new token stack, context, and textbuffer to the list.
*/
int Tokenizer_push(Tokenizer* self, uint64_t context)
{
    Stack* top = malloc(sizeof(Stack));

    if (!top) {
        PyErr_NoMemory();
        return -1;
    }
    top->stack = PyList_New(0);
    top->context = context;
    top->textbuffer = Textbuffer_new(&self->text);
    if (!top->textbuffer)
        return -1;
    top->next = self->topstack;
    self->topstack = top;
    self->depth++;
    self->cycles++;
    return 0;
}

/*
    Push the textbuffer onto the stack as a Text node and clear it.
*/
int Tokenizer_push_textbuffer(Tokenizer* self)
{
    PyObject *text, *kwargs, *token;
    Textbuffer* buffer = self->topstack->textbuffer;

    if (buffer->length == 0)
        return 0;
    text = Textbuffer_render(buffer);
    if (!text)
        return -1;
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(text);
        return -1;
    }
    PyDict_SetItemString(kwargs, "text", text);
    Py_DECREF(text);
    token = PyObject_Call(Text, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!token)
        return -1;
    if (PyList_Append(self->topstack->stack, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    if (Textbuffer_reset(buffer))
        return -1;
    return 0;
}

/*
    Pop and deallocate the top token stack/context/textbuffer.
*/
void Tokenizer_delete_top_of_stack(Tokenizer* self)
{
    Stack* top = self->topstack;

    Py_DECREF(top->stack);
    Textbuffer_dealloc(top->textbuffer);
    self->topstack = top->next;
    free(top);
    self->depth--;
}

/*
    Pop the current stack/context/textbuffer, returing the stack.
*/
PyObject* Tokenizer_pop(Tokenizer* self)
{
    PyObject* stack;

    if (Tokenizer_push_textbuffer(self))
        return NULL;
    stack = self->topstack->stack;
    Py_INCREF(stack);
    Tokenizer_delete_top_of_stack(self);
    return stack;
}

/*
    Pop the current stack/context/textbuffer, returing the stack. We will also
    replace the underlying stack's context with the current stack's.
*/
PyObject* Tokenizer_pop_keeping_context(Tokenizer* self)
{
    PyObject* stack;
    uint64_t context;

    if (Tokenizer_push_textbuffer(self))
        return NULL;
    stack = self->topstack->stack;
    Py_INCREF(stack);
    context = self->topstack->context;
    Tokenizer_delete_top_of_stack(self);
    self->topstack->context = context;
    return stack;
}

/*
    Fail the current tokenization route. Discards the current
    stack/context/textbuffer and sets the BAD_ROUTE flag.
*/
void* Tokenizer_fail_route(Tokenizer* self)
{
    uint64_t context = self->topstack->context;
    PyObject* stack = Tokenizer_pop(self);

    Py_XDECREF(stack);
    FAIL_ROUTE(context);
    return NULL;
}

/*
    Write a token to the current token stack.
*/
int Tokenizer_emit_token(Tokenizer* self, PyObject* token, int first)
{
    PyObject* instance;

    if (Tokenizer_push_textbuffer(self))
        return -1;
    instance = PyObject_CallObject(token, NULL);
    if (!instance)
        return -1;
    if (first ? PyList_Insert(self->topstack->stack, 0, instance) :
                PyList_Append(self->topstack->stack, instance)) {
        Py_DECREF(instance);
        return -1;
    }
    Py_DECREF(instance);
    return 0;
}

/*
    Write a token to the current token stack, with kwargs. Steals a reference
    to kwargs.
*/
int Tokenizer_emit_token_kwargs(Tokenizer* self, PyObject* token,
                                       PyObject* kwargs, int first)
{
    PyObject* instance;

    if (Tokenizer_push_textbuffer(self)) {
        Py_DECREF(kwargs);
        return -1;
    }
    instance = PyObject_Call(token, NOARGS, kwargs);
    if (!instance) {
        Py_DECREF(kwargs);
        return -1;
    }
    if (first ? PyList_Insert(self->topstack->stack, 0, instance):
                PyList_Append(self->topstack->stack, instance)) {
        Py_DECREF(instance);
        Py_DECREF(kwargs);
        return -1;
    }
    Py_DECREF(instance);
    Py_DECREF(kwargs);
    return 0;
}

/*
    Write a Unicode codepoint to the current textbuffer.
*/
int Tokenizer_emit_char(Tokenizer* self, Unicode code)
{
    return Textbuffer_write(self->topstack->textbuffer, code);
}

/*
    Write a string of text to the current textbuffer.
*/
int Tokenizer_emit_text(Tokenizer* self, const char* text)
{
    int i = 0;

    while (text[i]) {
        if (Tokenizer_emit_char(self, text[i]))
            return -1;
        i++;
    }
    return 0;
}

/*
    Write the contents of another textbuffer to the current textbuffer,
    deallocating it in the process.
*/
int Tokenizer_emit_textbuffer(Tokenizer* self, Textbuffer* buffer)
{
    int retval = Textbuffer_concat(self->topstack->textbuffer, buffer);
    Textbuffer_dealloc(buffer);
    return retval;
}

/*
    Write a series of tokens to the current stack at once.
*/
int Tokenizer_emit_all(Tokenizer* self, PyObject* tokenlist)
{
    int pushed = 0;
    PyObject *stack, *token, *left, *right, *text;
    Textbuffer* buffer;
    Py_ssize_t size;

    if (PyList_GET_SIZE(tokenlist) > 0) {
        token = PyList_GET_ITEM(tokenlist, 0);
        switch (PyObject_IsInstance(token, Text)) {
            case 0:
                break;
            case 1: {
                pushed = 1;
                buffer = self->topstack->textbuffer;
                if (buffer->length == 0)
                    break;
                left = Textbuffer_render(buffer);
                if (!left)
                    return -1;
                right = PyObject_GetAttrString(token, "text");
                if (!right)
                    return -1;
                text = PyUnicode_Concat(left, right);
                Py_DECREF(left);
                Py_DECREF(right);
                if (!text)
                    return -1;
                if (PyObject_SetAttrString(token, "text", text)) {
                    Py_DECREF(text);
                    return -1;
                }
                Py_DECREF(text);
                if (Textbuffer_reset(buffer))
                    return -1;
                break;
            }
            case -1:
                return -1;
        }
    }
    if (!pushed) {
        if (Tokenizer_push_textbuffer(self))
            return -1;
    }
    stack = self->topstack->stack;
    size = PyList_GET_SIZE(stack);
    if (PyList_SetSlice(stack, size, size, tokenlist))
        return -1;
    return 0;
}

/*
    Pop the current stack, write text, and then write the stack. 'text' is a
    NULL-terminated array of chars.
*/
int Tokenizer_emit_text_then_stack(Tokenizer* self, const char* text)
{
    PyObject* stack = Tokenizer_pop(self);

    if (Tokenizer_emit_text(self, text)) {
        Py_DECREF(stack);
        return -1;
    }
    if (stack) {
        if (PyList_GET_SIZE(stack) > 0) {
            if (Tokenizer_emit_all(self, stack)) {
                Py_DECREF(stack);
                return -1;
            }
        }
        Py_DECREF(stack);
    }
    self->head--;
    return 0;
}

/*
    Internal function to read the codepoint at the given index from the input.
*/
static Unicode read_codepoint(TokenizerInput* text, Py_ssize_t index)
{
#ifdef PEP_393
    return PyUnicode_READ(text->kind, text->data, index);
#else
    return text->buf[index];
#endif
}

/*
    Read the value at a relative point in the wikicode, forwards.
*/
Unicode Tokenizer_read(Tokenizer* self, Py_ssize_t delta)
{
    Py_ssize_t index = self->head + delta;

    if (index >= self->text.length)
        return '\0';
    return read_codepoint(&self->text, index);
}

/*
    Read the value at a relative point in the wikicode, backwards.
*/
Unicode Tokenizer_read_backwards(Tokenizer* self, Py_ssize_t delta)
{
    Py_ssize_t index;

    if (delta > self->head)
        return '\0';
    index = self->head - delta;
    return read_codepoint(&self->text, index);
}

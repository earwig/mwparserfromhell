/*
Tokenizer for MWParserFromHell
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

#include "tokenizer.h"

/*
    Given a context, return the heading level encoded within it.
*/
static int heading_level_from_context(int n)
{
    int level;
    n /= LC_HEADING_LEVEL_1;
    for (level = 1; n > 1; n >>= 1)
        level++;
    return level;
}

/*
    Call the given function in tag_defs, using 'tag' as a parameter, and return
    its output as a bool.
*/
static int
call_tag_def_func(const char* funcname, PyObject* tag)
{
    PyObject* func = PyObject_GetAttrString(tag_defs, funcname);
    PyObject* result = PyObject_CallFunctionObjArgs(func, tag, NULL);
    int ans = (result == Py_True) ? 1 : 0;

    Py_DECREF(func);
    Py_DECREF(result);
    return ans;
}

/*
    Sanitize the name of a tag so it can be compared with others for equality.
*/
static PyObject*
strip_tag_name(PyObject* token)
{
    PyObject *text, *rstripped, *lowered;

    text = PyObject_GetAttrString(token, "text");
    if (!text)
        return NULL;
    rstripped = PyObject_CallMethod(text, "rstrip", NULL);
    Py_DECREF(text);
    if (!rstripped)
        return NULL;
    lowered = PyObject_CallMethod(rstripped, "rstrip", NULL);
    Py_DECREF(rstripped);
    return lowered;
}

static Textbuffer*
Textbuffer_new(void)
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
    buffer->next = NULL;
    return buffer;
}

static void
Textbuffer_dealloc(Textbuffer* self)
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
    Write text to the given textbuffer.
*/
static int
Textbuffer_write(Textbuffer** this, Py_UNICODE text)
{
    Textbuffer* self = *this;
    if (self->size == TEXTBUFFER_BLOCKSIZE) {
        Textbuffer* new = Textbuffer_new();
        if (!new)
            return -1;
        new->next = self;
        *this = self = new;
    }
    self->data[self->size] = text;
    self->size++;
    return 0;
}

/*
    Return the contents of the textbuffer as a Python Unicode object.
*/
static PyObject*
Textbuffer_render(Textbuffer* self)
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

static PyObject*
Tokenizer_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    Tokenizer* self = (Tokenizer*) type->tp_alloc(type, 0);
    return (PyObject*) self;
}

static void
Tokenizer_dealloc(Tokenizer* self)
{
    Stack *this = self->topstack, *next;
    Py_XDECREF(self->text);

    while (this) {
        Py_DECREF(this->stack);
        Textbuffer_dealloc(this->textbuffer);
        next = this->next;
        free(this);
        this = next;
    }
    self->ob_type->tp_free((PyObject*) self);
}

static int
Tokenizer_init(Tokenizer* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = {NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist))
        return -1;
    self->text = Py_None;
    Py_INCREF(Py_None);
    self->topstack = NULL;
    self->head = 0;
    self->length = 0;
    self->global = 0;
    return 0;
}

/*
    Add a new token stack, context, and textbuffer to the list.
*/
static int
Tokenizer_push(Tokenizer* self, int context)
{
    Stack* top = malloc(sizeof(Stack));
    if (!top) {
        PyErr_NoMemory();
        return -1;
    }
    top->stack = PyList_New(0);
    top->context = context;
    top->textbuffer = Textbuffer_new();
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
static int
Tokenizer_push_textbuffer(Tokenizer* self)
{
    PyObject *text, *kwargs, *token;
    Textbuffer* buffer = self->topstack->textbuffer;
    if (buffer->size == 0 && !buffer->next)
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
    Textbuffer_dealloc(buffer);
    self->topstack->textbuffer = Textbuffer_new();
    if (!self->topstack->textbuffer)
        return -1;
    return 0;
}

/*
    Pop and deallocate the top token stack/context/textbuffer.
*/
static void
Tokenizer_delete_top_of_stack(Tokenizer* self)
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
static PyObject*
Tokenizer_pop(Tokenizer* self)
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
static PyObject*
Tokenizer_pop_keeping_context(Tokenizer* self)
{
    PyObject* stack;
    int context;
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
    stack/context/textbuffer and raises a BadRoute exception.
*/
static void*
Tokenizer_fail_route(Tokenizer* self)
{
    PyObject* stack = Tokenizer_pop(self);
    Py_XDECREF(stack);
    FAIL_ROUTE();
    return NULL;
}

/*
    Write a token to the end of the current token stack.
*/
static int
Tokenizer_emit(Tokenizer* self, PyObject* token)
{
    if (Tokenizer_push_textbuffer(self))
        return -1;
    if (PyList_Append(self->topstack->stack, token))
        return -1;
    return 0;
}

/*
    Write a token to the beginning of the current token stack.
*/
static int
Tokenizer_emit_first(Tokenizer* self, PyObject* token)
{
    if (Tokenizer_push_textbuffer(self))
        return -1;
    if (PyList_Insert(self->topstack->stack, 0, token))
        return -1;
    return 0;
}

/*
    Write text to the current textbuffer.
*/
static int
Tokenizer_emit_text(Tokenizer* self, Py_UNICODE text)
{
    return Textbuffer_write(&(self->topstack->textbuffer), text);
}

/*
    Write a series of tokens to the current stack at once.
*/
static int
Tokenizer_emit_all(Tokenizer* self, PyObject* tokenlist)
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
                if (buffer->size == 0 && !buffer->next)
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
                Textbuffer_dealloc(buffer);
                self->topstack->textbuffer = Textbuffer_new();
                if (!self->topstack->textbuffer)
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
static int
Tokenizer_emit_text_then_stack(Tokenizer* self, const char* text)
{
    PyObject* stack = Tokenizer_pop(self);
    int i = 0;
    while (1) {
        if (!text[i])
            break;
        if (Tokenizer_emit_text(self, (Py_UNICODE) text[i])) {
            Py_XDECREF(stack);
            return -1;
        }
        i++;
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
    Read the value at a relative point in the wikicode, forwards.
*/
static PyObject*
Tokenizer_read(Tokenizer* self, Py_ssize_t delta)
{
    Py_ssize_t index = self->head + delta;
    if (index >= self->length)
        return EMPTY;
    return PyList_GET_ITEM(self->text, index);
}

/*
    Read the value at a relative point in the wikicode, backwards.
*/
static PyObject*
Tokenizer_read_backwards(Tokenizer* self, Py_ssize_t delta)
{
    Py_ssize_t index;
    if (delta > self->head)
        return EMPTY;
    index = self->head - delta;
    return PyList_GET_ITEM(self->text, index);
}

/*
    Parse a template or argument at the head of the wikicode string.
*/
static int
Tokenizer_parse_template_or_argument(Tokenizer* self)
{
    unsigned int braces = 2, i;
    PyObject *tokenlist;

    self->head += 2;
    while (Tokenizer_READ(self, 0) == *"{" && braces < MAX_BRACES) {
        self->head++;
        braces++;
    }
    if (Tokenizer_push(self, 0))
        return -1;
    while (braces) {
        if (braces == 1) {
            if (Tokenizer_emit_text_then_stack(self, "{"))
                return -1;
            return 0;
        }
        if (braces == 2) {
            if (Tokenizer_parse_template(self))
                return -1;
            if (BAD_ROUTE) {
                RESET_ROUTE();
                if (Tokenizer_emit_text_then_stack(self, "{{"))
                    return -1;
                return 0;
            }
            break;
        }
        if (Tokenizer_parse_argument(self))
            return -1;
        if (BAD_ROUTE) {
            RESET_ROUTE();
            if (Tokenizer_parse_template(self))
                return -1;
            if (BAD_ROUTE) {
                char text[MAX_BRACES + 1];
                RESET_ROUTE();
                for (i = 0; i < braces; i++) text[i] = *"{";
                text[braces] = *"";
                if (Tokenizer_emit_text_then_stack(self, text)) {
                    Py_XDECREF(text);
                    return -1;
                }
                Py_XDECREF(text);
                return 0;
            }
            else
                braces -= 2;
        }
        else
            braces -= 3;
        if (braces)
            self->head++;
    }
    tokenlist = Tokenizer_pop(self);
    if (!tokenlist)
        return -1;
    if (Tokenizer_emit_all(self, tokenlist)) {
        Py_DECREF(tokenlist);
        return -1;
    }
    Py_DECREF(tokenlist);
    if (self->topstack->context & LC_FAIL_NEXT)
        self->topstack->context ^= LC_FAIL_NEXT;
    return 0;
}

/*
    Parse a template at the head of the wikicode string.
*/
static int
Tokenizer_parse_template(Tokenizer* self)
{
    PyObject *template, *token;
    Py_ssize_t reset = self->head;

    template = Tokenizer_parse(self, LC_TEMPLATE_NAME, 1);
    if (BAD_ROUTE) {
        self->head = reset;
        return 0;
    }
    if (!template)
        return -1;
    token = PyObject_CallObject(TemplateOpen, NULL);
    if (!token) {
        Py_DECREF(template);
        return -1;
    }
    if (Tokenizer_emit_first(self, token)) {
        Py_DECREF(token);
        Py_DECREF(template);
        return -1;
    }
    Py_DECREF(token);
    if (Tokenizer_emit_all(self, template)) {
        Py_DECREF(template);
        return -1;
    }
    Py_DECREF(template);
    token = PyObject_CallObject(TemplateClose, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    return 0;
}

/*
    Parse an argument at the head of the wikicode string.
*/
static int
Tokenizer_parse_argument(Tokenizer* self)
{
    PyObject *argument, *token;
    Py_ssize_t reset = self->head;

    argument = Tokenizer_parse(self, LC_ARGUMENT_NAME, 1);
    if (BAD_ROUTE) {
        self->head = reset;
        return 0;
    }
    if (!argument)
        return -1;
    token = PyObject_CallObject(ArgumentOpen, NULL);
    if (!token) {
        Py_DECREF(argument);
        return -1;
    }
    if (Tokenizer_emit_first(self, token)) {
        Py_DECREF(token);
        Py_DECREF(argument);
        return -1;
    }
    Py_DECREF(token);
    if (Tokenizer_emit_all(self, argument)) {
        Py_DECREF(argument);
        return -1;
    }
    Py_DECREF(argument);
    token = PyObject_CallObject(ArgumentClose, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    return 0;
}

/*
    Handle a template parameter at the head of the string.
*/
static int
Tokenizer_handle_template_param(Tokenizer* self)
{
    PyObject *stack, *token;

    if (self->topstack->context & LC_TEMPLATE_NAME)
        self->topstack->context ^= LC_TEMPLATE_NAME;
    else if (self->topstack->context & LC_TEMPLATE_PARAM_VALUE)
        self->topstack->context ^= LC_TEMPLATE_PARAM_VALUE;
    if (self->topstack->context & LC_TEMPLATE_PARAM_KEY) {
        stack = Tokenizer_pop_keeping_context(self);
        if (!stack)
            return -1;
        if (Tokenizer_emit_all(self, stack)) {
            Py_DECREF(stack);
            return -1;
        }
        Py_DECREF(stack);
    }
    else
        self->topstack->context |= LC_TEMPLATE_PARAM_KEY;

    token = PyObject_CallObject(TemplateParamSeparator, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    if (Tokenizer_push(self, self->topstack->context))
        return -1;
    return 0;
}

/*
    Handle a template parameter's value at the head of the string.
*/
static int
Tokenizer_handle_template_param_value(Tokenizer* self)
{
    PyObject *stack, *token;

    stack = Tokenizer_pop_keeping_context(self);
    if (!stack)
        return -1;
    if (Tokenizer_emit_all(self, stack)) {
        Py_DECREF(stack);
        return -1;
    }
    Py_DECREF(stack);
    self->topstack->context ^= LC_TEMPLATE_PARAM_KEY;
    self->topstack->context |= LC_TEMPLATE_PARAM_VALUE;
    token = PyObject_CallObject(TemplateParamEquals, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    return 0;
}

/*
    Handle the end of a template at the head of the string.
*/
static PyObject*
Tokenizer_handle_template_end(Tokenizer* self)
{
    PyObject* stack;

    if (self->topstack->context & LC_TEMPLATE_PARAM_KEY) {
        stack = Tokenizer_pop_keeping_context(self);
        if (!stack)
            return NULL;
        if (Tokenizer_emit_all(self, stack)) {
            Py_DECREF(stack);
            return NULL;
        }
        Py_DECREF(stack);
    }
    self->head++;
    stack = Tokenizer_pop(self);
    return stack;
}

/*
    Handle the separator between an argument's name and default.
*/
static int
Tokenizer_handle_argument_separator(Tokenizer* self)
{
    PyObject* token;
    self->topstack->context ^= LC_ARGUMENT_NAME;
    self->topstack->context |= LC_ARGUMENT_DEFAULT;
    token = PyObject_CallObject(ArgumentSeparator, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    return 0;
}

/*
    Handle the end of an argument at the head of the string.
*/
static PyObject*
Tokenizer_handle_argument_end(Tokenizer* self)
{
    PyObject* stack = Tokenizer_pop(self);
    self->head += 2;
    return stack;
}

/*
    Parse an internal wikilink at the head of the wikicode string.
*/
static int
Tokenizer_parse_wikilink(Tokenizer* self)
{
    Py_ssize_t reset;
    PyObject *wikilink, *token;
    int i;

    self->head += 2;
    reset = self->head - 1;
    wikilink = Tokenizer_parse(self, LC_WIKILINK_TITLE, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        for (i = 0; i < 2; i++) {
            if (Tokenizer_emit_text(self, *"["))
                return -1;
        }
        return 0;
    }
    if (!wikilink)
        return -1;
    token = PyObject_CallObject(WikilinkOpen, NULL);
    if (!token) {
        Py_DECREF(wikilink);
        return -1;
    }
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        Py_DECREF(wikilink);
        return -1;
    }
    Py_DECREF(token);
    if (Tokenizer_emit_all(self, wikilink)) {
        Py_DECREF(wikilink);
        return -1;
    }
    Py_DECREF(wikilink);
    token = PyObject_CallObject(WikilinkClose, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    if (self->topstack->context & LC_FAIL_NEXT)
        self->topstack->context ^= LC_FAIL_NEXT;
    return 0;
}

/*
    Handle the separator between a wikilink's title and its text.
*/
static int
Tokenizer_handle_wikilink_separator(Tokenizer* self)
{
    PyObject* token;
    self->topstack->context ^= LC_WIKILINK_TITLE;
    self->topstack->context |= LC_WIKILINK_TEXT;
    token = PyObject_CallObject(WikilinkSeparator, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    return 0;
}

/*
    Handle the end of a wikilink at the head of the string.
*/
static PyObject*
Tokenizer_handle_wikilink_end(Tokenizer* self)
{
    PyObject* stack = Tokenizer_pop(self);
    self->head += 1;
    return stack;
}

/*
    Parse a section heading at the head of the wikicode string.
*/
static int
Tokenizer_parse_heading(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    int best = 1, i, context, diff;
    HeadingData *heading;
    PyObject *level, *kwargs, *token;

    self->global |= GL_HEADING;
    self->head += 1;
    while (Tokenizer_READ(self, 0) == *"=") {
        best++;
        self->head++;
    }
    context = LC_HEADING_LEVEL_1 << (best > 5 ? 5 : best - 1);
    heading = (HeadingData*) Tokenizer_parse(self, context, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset + best - 1;
        for (i = 0; i < best; i++) {
            if (Tokenizer_emit_text(self, *"="))
                return -1;
        }
        self->global ^= GL_HEADING;
        return 0;
    }
    level = PyInt_FromSsize_t(heading->level);
    if (!level) {
        Py_DECREF(heading->title);
        free(heading);
        return -1;
    }
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(level);
        Py_DECREF(heading->title);
        free(heading);
        return -1;
    }
    PyDict_SetItemString(kwargs, "level", level);
    Py_DECREF(level);
    token = PyObject_Call(HeadingStart, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!token) {
        Py_DECREF(heading->title);
        free(heading);
        return -1;
    }
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        Py_DECREF(heading->title);
        free(heading);
        return -1;
    }
    Py_DECREF(token);
    if (heading->level < best) {
        diff = best - heading->level;
        for (i = 0; i < diff; i++) {
            if (Tokenizer_emit_text(self, *"=")) {
                Py_DECREF(heading->title);
                free(heading);
                return -1;
            }
        }
    }
    if (Tokenizer_emit_all(self, heading->title)) {
        Py_DECREF(heading->title);
        free(heading);
        return -1;
    }
    Py_DECREF(heading->title);
    free(heading);
    token = PyObject_CallObject(HeadingEnd, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    self->global ^= GL_HEADING;
    return 0;
}

/*
    Handle the end of a section heading at the head of the string.
*/
static HeadingData*
Tokenizer_handle_heading_end(Tokenizer* self)
{
    Py_ssize_t reset = self->head, best;
    int i, current, level, diff;
    HeadingData *after, *heading;
    PyObject *stack;

    self->head += 1;
    best = 1;
    while (Tokenizer_READ(self, 0) == *"=") {
        best++;
        self->head++;
    }
    current = heading_level_from_context(self->topstack->context);
    level = current > best ? (best > 6 ? 6 : best) :
                             (current > 6 ? 6 : current);
    after = (HeadingData*) Tokenizer_parse(self, self->topstack->context, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        if (level < best) {
            diff = best - level;
            for (i = 0; i < diff; i++) {
                if (Tokenizer_emit_text(self, *"="))
                    return NULL;
            }
        }
        self->head = reset + best - 1;
    }
    else {
        for (i = 0; i < best; i++) {
            if (Tokenizer_emit_text(self, *"=")) {
                Py_DECREF(after->title);
                free(after);
                return NULL;
            }
        }
        if (Tokenizer_emit_all(self, after->title)) {
            Py_DECREF(after->title);
            free(after);
            return NULL;
        }
        Py_DECREF(after->title);
        level = after->level;
        free(after);
    }
    stack = Tokenizer_pop(self);
    if (!stack)
        return NULL;
    heading = malloc(sizeof(HeadingData));
    if (!heading) {
        PyErr_NoMemory();
        return NULL;
    }
    heading->title = stack;
    heading->level = level;
    return heading;
}

/*
    Actually parse an HTML entity and ensure that it is valid.
*/
static int
Tokenizer_really_parse_entity(Tokenizer* self)
{
    PyObject *token, *kwargs, *textobj;
    Py_UNICODE this;
    int numeric, hexadecimal, i, j, zeroes, test;
    char *valid, *text, *buffer, *def;

    #define FAIL_ROUTE_AND_EXIT() { \
        Tokenizer_fail_route(self); \
        free(text);                 \
        return 0;                   \
    }

    token = PyObject_CallObject(HTMLEntityStart, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    self->head++;
    this = Tokenizer_READ(self, 0);
    if (this == *"") {
        Tokenizer_fail_route(self);
        return 0;
    }
    if (this == *"#") {
        numeric = 1;
        token = PyObject_CallObject(HTMLEntityNumeric, NULL);
        if (!token)
            return -1;
        if (Tokenizer_emit(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);
        self->head++;
        this = Tokenizer_READ(self, 0);
        if (this == *"") {
            Tokenizer_fail_route(self);
            return 0;
        }
        if (this == *"x" || this == *"X") {
            hexadecimal = 1;
            kwargs = PyDict_New();
            if (!kwargs)
                return -1;
            PyDict_SetItemString(kwargs, "char", Tokenizer_read(self, 0));
            token = PyObject_Call(HTMLEntityHex, NOARGS, kwargs);
            Py_DECREF(kwargs);
            if (!token)
                return -1;
            if (Tokenizer_emit(self, token)) {
                Py_DECREF(token);
                return -1;
            }
            Py_DECREF(token);
            self->head++;
        }
        else
            hexadecimal = 0;
    }
    else
        numeric = hexadecimal = 0;
    if (hexadecimal)
        valid = HEXDIGITS;
    else if (numeric)
        valid = DIGITS;
    else
        valid = ALPHANUM;
    text = calloc(MAX_ENTITY_SIZE, sizeof(char));
    if (!text) {
        PyErr_NoMemory();
        return -1;
    }
    i = 0;
    zeroes = 0;
    while (1) {
        this = Tokenizer_READ(self, 0);
        if (this == *";") {
            if (i == 0)
                FAIL_ROUTE_AND_EXIT()
            break;
        }
        if (i == 0 && this == *"0") {
            zeroes++;
            self->head++;
            continue;
        }
        if (i >= 8)
            FAIL_ROUTE_AND_EXIT()
        for (j = 0; j < NUM_MARKERS; j++) {
            if (this == *MARKERS[j])
                FAIL_ROUTE_AND_EXIT()
        }
        j = 0;
        while (1) {
            if (!valid[j])
                FAIL_ROUTE_AND_EXIT()
            if (this == valid[j])
                break;
            j++;
        }
        text[i] = this;
        self->head++;
        i++;
    }
    if (numeric) {
        sscanf(text, (hexadecimal ? "%x" : "%d"), &test);
        if (test < 1 || test > 0x10FFFF)
            FAIL_ROUTE_AND_EXIT()
    }
    else {
        i = 0;
        while (1) {
            def = entitydefs[i];
            if (!def)  // We've reached the end of the defs without finding it
                FAIL_ROUTE_AND_EXIT()
            if (strcmp(text, def) == 0)
                break;
            i++;
        }
    }
    if (zeroes) {
        buffer = calloc(strlen(text) + zeroes + 1, sizeof(char));
        if (!buffer) {
            free(text);
            PyErr_NoMemory();
            return -1;
        }
        for (i = 0; i < zeroes; i++)
            strcat(buffer, "0");
        strcat(buffer, text);
        free(text);
        text = buffer;
    }
    textobj = PyUnicode_FromString(text);
    if (!textobj) {
        free(text);
        return -1;
    }
    free(text);
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(textobj);
        return -1;
    }
    PyDict_SetItemString(kwargs, "text", textobj);
    Py_DECREF(textobj);
    token = PyObject_Call(Text, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    token = PyObject_CallObject(HTMLEntityEnd, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    return 0;
}

/*
    Parse an HTML entity at the head of the wikicode string.
*/
static int
Tokenizer_parse_entity(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    PyObject *tokenlist;

    if (Tokenizer_push(self, 0))
        return -1;
    if (Tokenizer_really_parse_entity(self))
        return -1;
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        if (Tokenizer_emit_text(self, *"&"))
            return -1;
        return 0;
    }
    tokenlist = Tokenizer_pop(self);
    if (!tokenlist)
        return -1;
    if (Tokenizer_emit_all(self, tokenlist)) {
        Py_DECREF(tokenlist);
        return -1;
    }
    Py_DECREF(tokenlist);
    return 0;
}

/*
    Parse an HTML comment at the head of the wikicode string.
*/
static int
Tokenizer_parse_comment(Tokenizer* self)
{
    Py_ssize_t reset = self->head + 3;
    PyObject *token, *comment;
    int i;

    self->head += 4;
    comment = Tokenizer_parse(self, LC_COMMENT, 1);
    if (BAD_ROUTE) {
        const char* text = "<!--";
        RESET_ROUTE();
        self->head = reset;
        i = 0;
        while (1) {
            if (!text[i])
                return 0;
            if (Tokenizer_emit_text(self, (Py_UNICODE) text[i])) {
                Py_XDECREF(text);
                return -1;
            }
            i++;
        }
        return 0;
    }
    if (!comment)
        return -1;
    token = PyObject_CallObject(CommentStart, NULL);
    if (!token) {
        Py_DECREF(comment);
        return -1;
    }
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        Py_DECREF(comment);
        return -1;
    }
    Py_DECREF(token);
    if (Tokenizer_emit_all(self, comment)) {
        Py_DECREF(comment);
        return -1;
    }
    Py_DECREF(comment);
    token = PyObject_CallObject(CommentEnd, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    self->head += 2;
    return 0;
}

/*
    Parse an HTML tag at the head of the wikicode string.
*/
static int
Tokenizer_parse_tag(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    PyObject* tag;

    self->head++;
    tag = Tokenizer_really_parse_tag(self);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        return Tokenizer_emit_text(self, *"<");
    }
    if (!tag) {
        return -1;
    }
    Tokenizer_emit_all(self, tag);
    Py_DECREF(tag);
    return 0;
}

/*
    Actually parse an HTML tag, starting with the open (<foo>).
*/
static PyObject*
Tokenizer_really_parse_tag(Tokenizer* self)
{
    TagOpenData *data = malloc(sizeof(TagOpenData));
    PyObject *token, *text, *trash;
    Py_UNICODE this, next;
    int can_exit;

    if (!data) {
        PyErr_NoMemory();
        return NULL;
    }
    data->pad_first = Textbuffer_new();
    data->pad_before_eq = Textbuffer_new();
    data->pad_after_eq = Textbuffer_new();
    if (!data->pad_first || !data->pad_before_eq || !data->pad_after_eq) {
        free(data);
        return NULL;
    }
    if (Tokenizer_push(self, LC_TAG_OPEN)) {
        free(data);
        return NULL;
    }
    token = PyObject_CallObject(TagOpenOpen, NULL);
    if (!token) {
        free(data);
        return NULL;
    }
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        free(data);
        return NULL;
    }
    Py_DECREF(token);
    while (1) {
        this = Tokenizer_READ(self, 0);
        next = Tokenizer_READ(self, 1);
        can_exit = (!(data->context & (TAG_QUOTED | TAG_NAME)) ||
                    data->context & TAG_NOTE_SPACE);
        if (this == *"") {
            if (self->topstack->context & LC_TAG_ATTR) {
                if (data->context & TAG_QUOTED) {
                    // Unclosed attribute quote: reset, don't die
                    data->context = TAG_ATTR_VALUE;
                    trash = Tokenizer_pop(self);
                    Py_XDECREF(trash);
                    self->head = data->reset;
                    continue;
                }
                trash = Tokenizer_pop(self);
                Py_XDECREF(trash);
            }
            free(data);
            return Tokenizer_fail_route(self);
        }
        else if (this == *">" && can_exit) {
            if (Tokenizer_handle_tag_close_open(self, data, TagCloseOpen)) {
                free(data);
                return NULL;
            }
            free(data);
            self->topstack->context = LC_TAG_BODY;
            token = PyList_GET_ITEM(self->topstack->stack, 1);
            text = PyObject_GetAttrString(token, "text");
            if (!text)
                return NULL;
            if (IS_SINGLE_ONLY(text)) {
                Py_DECREF(text);
                return Tokenizer_handle_single_only_tag_end(self);
            }
            if (IS_PARSABLE(text)) {
                Py_DECREF(text);
                return Tokenizer_parse(self, 0, 0);
            }
            Py_DECREF(text);
            return Tokenizer_handle_blacklisted_tag(self);
        }
        else if (this == *"/" && next == *">" && can_exit) {
            if (Tokenizer_handle_tag_close_open(self, data, TagCloseSelfclose)) {
                free(data);
                return NULL;
            }
            free(data);
            return Tokenizer_pop(self);
        }
        else {
            if (Tokenizer_handle_tag_data(self, data, this) || BAD_ROUTE) {
                RESET_ROUTE();
                free(data);
                return NULL;
            }
        }
        self->head++;
    }
}

/*
    Write a pending tag attribute from data to the stack.
*/
static int
Tokenizer_push_tag_buffer(Tokenizer* self, TagOpenData* data)
{
    PyObject *token, *tokens, *kwargs, *pad_first, *pad_before_eq,
             *pad_after_eq;

    if (data->context & TAG_QUOTED) {
        token = PyObject_CallObject(TagAttrQuote, NULL);
        if (!token)
            return -1;
        if (Tokenizer_emit_first(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);
        tokens = Tokenizer_pop(self);
        if (!tokens)
            return -1;
        if (Tokenizer_emit_all(self, tokens)) {
            Py_DECREF(tokens);
            return -1;
        }
        Py_DECREF(tokens);
    }
    pad_first = Textbuffer_render(data->pad_first);
    pad_before_eq = Textbuffer_render(data->pad_before_eq);
    pad_after_eq = Textbuffer_render(data->pad_after_eq);
    if (!pad_first || !pad_before_eq || !pad_after_eq)
        return -1;
    kwargs = PyDict_New();
    if (!kwargs)
        return -1;
    PyDict_SetItemString(kwargs, "pad_first", pad_first);
    PyDict_SetItemString(kwargs, "pad_before_eq", pad_before_eq);
    PyDict_SetItemString(kwargs, "pad_after_eq", pad_after_eq);
    Py_DECREF(pad_first);
    Py_DECREF(pad_before_eq);
    Py_DECREF(pad_after_eq);
    token = PyObject_Call(TagAttrStart, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!token)
        return -1;
    if (Tokenizer_emit_first(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    tokens = Tokenizer_pop(self);
    if (!tokens)
        return -1;
    if (Tokenizer_emit_all(self, tokens)) {
        Py_DECREF(tokens);
        return -1;
    }
    Py_DECREF(tokens);
    Textbuffer_dealloc(data->pad_first);
    Textbuffer_dealloc(data->pad_before_eq);
    Textbuffer_dealloc(data->pad_after_eq);
    data->pad_first = Textbuffer_new();
    data->pad_before_eq = Textbuffer_new();
    data->pad_after_eq = Textbuffer_new();
    if (!data->pad_first || !data->pad_before_eq || !data->pad_after_eq)
        return -1;
    return 0;
}

/*
    Handle all sorts of text data inside of an HTML open tag.
*/
static int
Tokenizer_handle_tag_data(Tokenizer* self, TagOpenData* data, Py_UNICODE chunk)
{
    PyObject *trash, *token;
    int first_time, i, is_marker = 0, escaped;

    if (data->context & TAG_NAME) {
        first_time = !(data->context & TAG_NOTE_SPACE);
        for (i = 0; i < NUM_MARKERS; i++) {
            if (*MARKERS[i] == chunk) {
                is_marker = 1;
                break;
            }
        }
        if (is_marker || (Py_UNICODE_ISSPACE(chunk) && first_time)) {
            // Tags must start with text, not spaces
            Tokenizer_fail_route(self);
            return 0;
        }
        else if (first_time)
            data->context |= TAG_NOTE_SPACE;
        else if (Py_UNICODE_ISSPACE(chunk))
            data->context = TAG_ATTR_READY;
    }
    else if (Py_UNICODE_ISSPACE(chunk))
        return Tokenizer_handle_tag_space(self, data, chunk);
    else if (data->context & TAG_NOTE_SPACE) {
        if (data->context & TAG_QUOTED) {
            data->context = TAG_ATTR_VALUE;
            trash = Tokenizer_pop(self);
            Py_XDECREF(trash);
            self->head = data->reset - 1;  // Will be auto-incremented
        }
        else
            Tokenizer_fail_route(self);
        return 0;
    }
    else if (data->context & TAG_ATTR_READY) {
        data->context = TAG_ATTR_NAME;
        if (Tokenizer_push(self, LC_TAG_ATTR))
            return -1;
    }
    else if (data->context & TAG_ATTR_NAME) {
        if (chunk == *"=") {
            data->context = TAG_ATTR_VALUE | TAG_NOTE_QUOTE;
            token = PyObject_CallObject(TagAttrEquals, NULL);
            if (!token)
                return -1;
            if (Tokenizer_emit(self, token)) {
                Py_DECREF(token);
                return -1;
            }
            Py_DECREF(token);
            return 0;
        }
        if (data->context & TAG_NOTE_EQUALS) {
            if (Tokenizer_push_tag_buffer(self, data))
                return -1;
            data->context = TAG_ATTR_NAME;
            if (Tokenizer_push(self, LC_TAG_ATTR))
                return -1;
        }
    }
    else if (data->context & TAG_ATTR_VALUE) {
        escaped = (Tokenizer_READ_BACKWARDS(self, 1) == *"\\" &&
                   Tokenizer_READ_BACKWARDS(self, 2) != *"\\");
        if (data->context & TAG_NOTE_QUOTE) {
            data->context ^= TAG_NOTE_QUOTE;
            if (chunk == *"\"" && !escaped) {
                data->context |= TAG_QUOTED;
                if (Tokenizer_push(self, self->topstack->context))
                    return -1;
                data->reset = self->head;
                return 0;
            }
        }
        else if (data->context & TAG_QUOTED) {
            if (chunk == *"\"" && !escaped) {
                data->context |= TAG_NOTE_SPACE;
                return 0;
            }
        }
    }
    return Tokenizer_handle_tag_text(self, chunk);
}

/*
    Handle whitespace inside of an HTML open tag.
*/
static int
Tokenizer_handle_tag_space(Tokenizer* self, TagOpenData* data, Py_UNICODE text)
{
    int ctx = data->context;
    int end_of_value = (ctx & TAG_ATTR_VALUE &&
                        !(ctx & (TAG_QUOTED | TAG_NOTE_QUOTE)));

    if (end_of_value || (ctx & TAG_QUOTED && ctx & TAG_NOTE_SPACE)) {
        if (Tokenizer_push_tag_buffer(self, data))
            return -1;
        data->context = TAG_ATTR_READY;
    }
    else if (ctx & TAG_NOTE_SPACE)
        data->context = TAG_ATTR_READY;
    else if (ctx & TAG_ATTR_NAME) {
        data->context |= TAG_NOTE_EQUALS;
        if (Textbuffer_write(&(data->pad_before_eq), text))
            return -1;
    }
    if (ctx & TAG_QUOTED && !(ctx & TAG_NOTE_SPACE)) {
        if (Tokenizer_emit_text(self, text))
            return -1;
    }
    else if (data->context & TAG_ATTR_READY)
        return Textbuffer_write(&(data->pad_first), text);
    else if (data->context & TAG_ATTR_VALUE)
        return Textbuffer_write(&(data->pad_after_eq), text);
    return 0;
}

/*
    Handle regular text inside of an HTML open tag.
*/
static int
Tokenizer_handle_tag_text(Tokenizer* self, Py_UNICODE text)
{
    Py_UNICODE next = Tokenizer_READ(self, 1);
    int i, is_marker = 0;

    for (i = 0; i < NUM_MARKERS; i++) {
        if (*MARKERS[i] == text) {
            is_marker = 1;
            break;
        }
    }
    if (!is_marker || !Tokenizer_CAN_RECURSE(self))
        return Tokenizer_emit_text(self, text);
    else if (text == next && next == *"{")
        return Tokenizer_parse_template_or_argument(self);
    else if (text == next && next == *"[")
        return Tokenizer_parse_wikilink(self);
    else if (text == *"<")
        return Tokenizer_parse_tag(self);
    return Tokenizer_emit_text(self, text);
}

/*
    Handle the body of an HTML tag that is parser-blacklisted.
*/
static PyObject*
Tokenizer_handle_blacklisted_tag(Tokenizer* self)
{
    Py_UNICODE this, next;

    while (1) {
        this = Tokenizer_READ(self, 0);
        next = Tokenizer_READ(self, 1);
        self->head++;
        if (this == *"")
            return Tokenizer_fail_route(self);
        else if (this == *"<" && next == *"/") {
            if (Tokenizer_handle_tag_open_close(self))
                return NULL;
            return Tokenizer_parse(self, 0, 0);
        }
        if (Tokenizer_emit_text(self, this))
            return NULL;
    }
}

/*
    Handle the closing of a open tag (<foo>).
*/
static int
Tokenizer_handle_tag_close_open(Tokenizer* self, TagOpenData* data,
                                PyObject* token)
{
    PyObject *padding, *kwargs, *tok;

    if (data->context & (TAG_ATTR_NAME | TAG_ATTR_VALUE)) {
        if (Tokenizer_push_tag_buffer(self, data))
            return -1;
    }
    padding = Textbuffer_render(data->pad_first);
    if (!padding)
        return -1;
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(padding);
        return -1;
    }
    PyDict_SetItemString(kwargs, "padding", padding);
    Py_DECREF(padding);
    tok = PyObject_Call(token, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!tok)
        return -1;
    if (Tokenizer_emit(self, tok)) {
        Py_DECREF(tok);
        return -1;
    }
    Py_DECREF(tok);
    self->head++;
    return 0;
}

/*
    Handle the opening of a closing tag (</foo>).
*/
static int
Tokenizer_handle_tag_open_close(Tokenizer* self)
{
    PyObject* token;

    token = PyObject_CallObject(TagOpenClose, NULL);
    if (!token)
        return -1;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);
    if (Tokenizer_push(self, LC_TAG_CLOSE))
        return -1;
    self->head++;
    return 0;
}

/*
    Handle the ending of a closing tag (</foo>).
*/
static PyObject*
Tokenizer_handle_tag_close_close(Tokenizer* self)
{
    PyObject *closing, *first, *so, *sc, *token;
    int valid = 1;

    closing = Tokenizer_pop(self);
    if (!closing)
        return NULL;
    if (PyList_GET_SIZE(closing) != 1)
        valid = 0;
    else {
        first = PyList_GET_ITEM(closing, 0);
        switch (PyObject_IsInstance(first, Text)) {
            case 0:
                valid = 0;
                break;
            case 1: {
                so = strip_tag_name(first);
                sc = strip_tag_name(PyList_GET_ITEM(self->topstack->stack, 1));
                if (so && sc) {
                    if (PyUnicode_Compare(so, sc))
                        valid = 0;
                    Py_DECREF(so);
                    Py_DECREF(sc);
                    break;
                }
                Py_XDECREF(so);
                Py_XDECREF(sc);
            }
            case -1:
                Py_DECREF(closing);
                return NULL;
        }
    }
    if (!valid) {
        Py_DECREF(closing);
        return Tokenizer_fail_route(self);
    }
    if (Tokenizer_emit_all(self, closing)) {
        Py_DECREF(closing);
        return NULL;
    }
    Py_DECREF(closing);
    token = PyObject_CallObject(TagCloseClose, NULL);
    if (!token)
        return NULL;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return NULL;
    }
    Py_DECREF(token);
    return Tokenizer_pop(self);
}

/*
    Handle the (possible) start of an implicitly closing single tag.
*/
static int
Tokenizer_handle_invalid_tag_start(Tokenizer* self)
{
    Py_ssize_t reset = self->head + 1, pos = 0;
    Textbuffer* buf;
    PyObject *name, *tag;
    Py_UNICODE this;
    int is_marker, i;

    self->head += 2;
    buf = Textbuffer_new();
    if (!buf)
        return -1;
    while (1) {
        this = Tokenizer_READ(self, pos);
        is_marker = 0;
        for (i = 0; i < NUM_MARKERS; i++) {
            if (*MARKERS[i] == this) {
                is_marker = 1;
                break;
            }
        }
        if (is_marker) {
            name = Textbuffer_render(buf);
            if (!name) {
                Textbuffer_dealloc(buf);
                return -1;
            }
            if (!IS_SINGLE_ONLY(name))
                FAIL_ROUTE();
            break;
        }
        pos++;
    }
    if (!BAD_ROUTE) {
        tag = Tokenizer_really_parse_tag(self);
        if (!tag)
            return -1;
    }
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        return (Tokenizer_emit_text(self, *"<") ||
                Tokenizer_emit_text(self, *"/"));
    }
    // Set invalid=True flag of TagOpenOpen
    if (PyObject_SetAttrString(PyList_GET_ITEM(tag, 0), "invalid", Py_True))
        return -1;
    return Tokenizer_emit_all(self, tag);
}

/*
    Handle the end of an implicitly closing single-only HTML tag.
*/
static PyObject*
Tokenizer_handle_single_only_tag_end(Tokenizer* self)
{
    PyObject *top, *padding, *kwargs, *token;

    top = PyObject_CallMethod(self->topstack->stack, "pop", NULL);
    if (!top)
        return NULL;
    padding = PyObject_GetAttrString(top, "padding");
    Py_DECREF(top);
    if (!padding)
        return NULL;
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(padding);
        return NULL;
    }
    PyDict_SetItemString(kwargs, "padding", padding);
    PyDict_SetItemString(kwargs, "implicit", Py_True);
    Py_DECREF(padding);
    token = PyObject_Call(TagCloseSelfclose, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!token)
        return NULL;
    if (Tokenizer_emit(self, token)) {
        Py_DECREF(token);
        return NULL;
    }
    Py_DECREF(token);
    self->head--;  // Offset displacement done by handle_tag_close_open
    return Tokenizer_pop(self);
}

/*
    Handle the stream end when inside a single-supporting HTML tag.
*/
static PyObject*
Tokenizer_handle_single_tag_end(Tokenizer* self)
{
    PyObject *token = 0, *padding, *kwargs;
    Py_ssize_t len, index;
    int is_instance;

    len = PyList_GET_SIZE(self->topstack->stack);
    for (index = 0; index < len; index++) {
        token = PyList_GET_ITEM(self->topstack->stack, index);
        is_instance = PyObject_IsInstance(token, TagCloseOpen);
        if (is_instance == -1)
            return NULL;
        else if (is_instance == 1)
            break;
    }
    if (!token)
        return NULL;
    padding = PyObject_GetAttrString(token, "padding");
    if (!padding)
        return NULL;
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(padding);
        return NULL;
    }
    PyDict_SetItemString(kwargs, "padding", padding);
    PyDict_SetItemString(kwargs, "implicit", Py_True);
    Py_DECREF(padding);
    token = PyObject_Call(TagCloseSelfclose, NOARGS, kwargs);
    Py_DECREF(kwargs);
    if (!token)
        return NULL;
    if (PyList_SetItem(self->topstack->stack, index, token)) {
        Py_DECREF(token);
        return NULL;
    }
    Py_DECREF(token);
    return Tokenizer_pop(self);
}

/*
    Handle the end of the stream of wikitext.
*/
static PyObject*
Tokenizer_handle_end(Tokenizer* self, int context)
{
    static int fail_contexts = (LC_TEMPLATE | LC_ARGUMENT | LC_WIKILINK |
                                LC_HEADING | LC_COMMENT);
    static int double_fail = (LC_TEMPLATE_PARAM_KEY | LC_TAG_CLOSE);
    PyObject *token, *text, *trash;
    int single;

    if (context & fail_contexts) {
        if (context & LC_TAG_BODY) {
            token = PyList_GET_ITEM(self->topstack->stack, 1);
            text = PyObject_GetAttrString(token, "text");
            if (!text)
                return NULL;
            single = IS_SINGLE(text);
            Py_DECREF(text);
            if (single)
                return Tokenizer_handle_single_tag_end(self);
        }
        else if (context & double_fail) {
            trash = Tokenizer_pop(self);
            Py_XDECREF(trash);
        }
        return Tokenizer_fail_route(self);
    }
    return Tokenizer_pop(self);
}

/*
    Make sure we are not trying to write an invalid character. Return 0 if
    everything is safe, or -1 if the route must be failed.
*/
static int
Tokenizer_verify_safe(Tokenizer* self, int context, Py_UNICODE data)
{
    if (context & LC_FAIL_NEXT) {
        return -1;
    }
    if (context & LC_WIKILINK_TITLE) {
        if (data == *"]" || data == *"{")
            self->topstack->context |= LC_FAIL_NEXT;
        else if (data == *"\n" || data == *"[" || data == *"}")
            return -1;
        return 0;
    }
    if (context & LC_TAG_CLOSE) {
        if (data == *"<")
            return -1;
        return 0;
    }
    if (context & LC_TEMPLATE_NAME) {
        if (data == *"{" || data == *"}" || data == *"[") {
            self->topstack->context |= LC_FAIL_NEXT;
            return 0;
        }
        if (data == *"]") {
            return -1;
        }
        if (data == *"|")
            return 0;
        if (context & LC_HAS_TEXT) {
            if (context & LC_FAIL_ON_TEXT) {
                if (!Py_UNICODE_ISSPACE(data))
                    return -1;
            }
            else {
                if (data == *"\n")
                    self->topstack->context |= LC_FAIL_ON_TEXT;
            }
        }
        else if (!Py_UNICODE_ISSPACE(data))
            self->topstack->context |= LC_HAS_TEXT;
    }
    else {
        if (context & LC_FAIL_ON_EQUALS) {
            if (data == *"=") {
                return -1;
            }
        }
        else if (context & LC_FAIL_ON_LBRACE) {
            if (data == *"{" || (Tokenizer_READ(self, -1) == *"{" &&
                                 Tokenizer_READ(self, -2) == *"{")) {
                if (context & LC_TEMPLATE)
                    self->topstack->context |= LC_FAIL_ON_EQUALS;
                else
                    self->topstack->context |= LC_FAIL_NEXT;
                return 0;
            }
            self->topstack->context ^= LC_FAIL_ON_LBRACE;
        }
        else if (context & LC_FAIL_ON_RBRACE) {
            if (data == *"}") {
                if (context & LC_TEMPLATE)
                    self->topstack->context |= LC_FAIL_ON_EQUALS;
                else
                    self->topstack->context |= LC_FAIL_NEXT;
                return 0;
            }
            self->topstack->context ^= LC_FAIL_ON_RBRACE;
        }
        else if (data == *"{")
            self->topstack->context |= LC_FAIL_ON_LBRACE;
        else if (data == *"}")
            self->topstack->context |= LC_FAIL_ON_RBRACE;
    }
    return 0;
}

/*
    Parse the wikicode string, using context for when to stop. If push is true,
    we will push a new context, otherwise we won't and context will be ignored.
*/
static PyObject*
Tokenizer_parse(Tokenizer* self, int context, int push)
{
    static int unsafe_contexts = (LC_TEMPLATE_NAME | LC_WIKILINK_TITLE |
                                  LC_TEMPLATE_PARAM_KEY | LC_ARGUMENT_NAME);
    static int double_unsafe = (LC_TEMPLATE_PARAM_KEY | LC_TAG_CLOSE);
    int this_context, is_marker, i;
    Py_UNICODE this, next, next_next, last;
    PyObject* trash;

    if (push) {
        if (Tokenizer_push(self, context))
            return NULL;
    }
    while (1) {
        this = Tokenizer_READ(self, 0);
        this_context = self->topstack->context;
        if (this_context & unsafe_contexts) {
            if (Tokenizer_verify_safe(self, this_context, this) < 0) {
                if (this_context & double_unsafe) {
                    trash = Tokenizer_pop(self);
                    Py_XDECREF(trash);
                }
                return Tokenizer_fail_route(self);
            }
        }
        is_marker = 0;
        for (i = 0; i < NUM_MARKERS; i++) {
            if (*MARKERS[i] == this) {
                is_marker = 1;
                break;
            }
        }
        if (!is_marker) {
            if (Tokenizer_emit_text(self, this))
                return NULL;
            self->head++;
            continue;
        }
        if (this == *"")
            return Tokenizer_handle_end(self, this_context);
        next = Tokenizer_READ(self, 1);
        if (this_context & LC_COMMENT) {
            if (this == next && next == *"-") {
                if (Tokenizer_READ(self, 2) == *">")
                    return Tokenizer_pop(self);
            }
            if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == next && next == *"{") {
            if (Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_template_or_argument(self))
                    return NULL;
            }
            else if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == *"|" && this_context & LC_TEMPLATE) {
            if (Tokenizer_handle_template_param(self))
                return NULL;
        }
        else if (this == *"=" && this_context & LC_TEMPLATE_PARAM_KEY) {
            if (Tokenizer_handle_template_param_value(self))
                return NULL;
        }
        else if (this == next && next == *"}" && this_context & LC_TEMPLATE)
            return Tokenizer_handle_template_end(self);
        else if (this == *"|" && this_context & LC_ARGUMENT_NAME) {
            if (Tokenizer_handle_argument_separator(self))
                return NULL;
        }
        else if (this == next && next == *"}" && this_context & LC_ARGUMENT) {
            if (Tokenizer_READ(self, 2) == *"}") {
                return Tokenizer_handle_argument_end(self);
            }
            if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == next && next == *"[") {
            if (!(this_context & LC_WIKILINK_TITLE) &&
                                                Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_wikilink(self))
                    return NULL;
            }
            else if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == *"|" && this_context & LC_WIKILINK_TITLE) {
            if (Tokenizer_handle_wikilink_separator(self))
                return NULL;
        }
        else if (this == next && next == *"]" && this_context & LC_WIKILINK)
            return Tokenizer_handle_wikilink_end(self);
        else if (this == *"=" && !(self->global & GL_HEADING)) {
            last = Tokenizer_READ_BACKWARDS(self, 1);
            if (last == *"\n" || last == *"") {
                if (Tokenizer_parse_heading(self))
                    return NULL;
            }
            else if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == *"=" && this_context & LC_HEADING)
            return (PyObject*) Tokenizer_handle_heading_end(self);
        else if (this == *"\n" && this_context & LC_HEADING)
            return Tokenizer_fail_route(self);
        else if (this == *"&") {
            if (Tokenizer_parse_entity(self))
                return NULL;
        }
        else if (this == *"<" && next == *"!") {
            next_next = Tokenizer_READ(self, 2);
            if (next_next == Tokenizer_READ(self, 3) && next_next == *"-") {
                if (Tokenizer_parse_comment(self))
                    return NULL;
            }
            else if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == *"<" && next == *"/" &&
                                            Tokenizer_READ(self, 2) != *"") {
            if (this_context & LC_TAG_BODY) {
                if (Tokenizer_handle_tag_open_close(self))
                    return NULL;
            }
            else {
                if (Tokenizer_handle_invalid_tag_start(self))
                    return NULL;
            }
        }
        else if (this == *"<") {
            if (!(this_context & LC_TAG_CLOSE) &&
                                                Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_tag(self))
                    return NULL;
            }
            else if (Tokenizer_emit_text(self, this))
                return NULL;
        }
        else if (this == *">" && this_context & LC_TAG_CLOSE)
            return Tokenizer_handle_tag_close_close(self);
        else if (Tokenizer_emit_text(self, this))
            return NULL;
        self->head++;
    }
}

/*
    Build a list of tokens from a string of wikicode and return it.
*/
static PyObject*
Tokenizer_tokenize(Tokenizer* self, PyObject* args)
{
    PyObject *text, *temp;

    if (!PyArg_ParseTuple(args, "U", &text)) {
        const char* encoded;
        Py_ssize_t size;
        /* Failed to parse a Unicode object; try a string instead. */
        PyErr_Clear();
        if (!PyArg_ParseTuple(args, "s#", &encoded, &size))
            return NULL;
        temp = PyUnicode_FromStringAndSize(encoded, size);
        if (!text)
            return NULL;
        Py_XDECREF(self->text);
        text = PySequence_Fast(temp, "expected a sequence");
        Py_XDECREF(temp);
        self->text = text;
    }
    else {
        Py_XDECREF(self->text);
        self->text = PySequence_Fast(text, "expected a sequence");
    }
    self->length = PyList_GET_SIZE(self->text);
    return Tokenizer_parse(self, 0, 1);
}

static void
load_entitydefs(void)
{
    PyObject *tempmod, *defmap, *deflist;
    unsigned numdefs, i;

    tempmod = PyImport_ImportModule("htmlentitydefs");
    if (!tempmod)
        return;
    defmap = PyObject_GetAttrString(tempmod, "entitydefs");
    if (!defmap)
        return;
    Py_DECREF(tempmod);
    deflist = PyDict_Keys(defmap);
    if (!deflist)
        return;
    Py_DECREF(defmap);
    numdefs = (unsigned) PyList_GET_SIZE(defmap);
    entitydefs = calloc(numdefs + 1, sizeof(char*));
    for (i = 0; i < numdefs; i++)
        entitydefs[i] = PyBytes_AsString(PyList_GET_ITEM(deflist, i));
    Py_DECREF(deflist);
}

static void
load_tokens(void)
{
    PyObject *tempmod, *tokens,
             *globals = PyEval_GetGlobals(),
             *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1),
             *modname = PyBytes_FromString("tokens");
    char *name = "mwparserfromhell.parser";

    if (!fromlist || !modname)
        return;
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod)
        return;
    tokens = PyObject_GetAttrString(tempmod, "tokens");
    Py_DECREF(tempmod);

    Text = PyObject_GetAttrString(tokens, "Text");

    TemplateOpen = PyObject_GetAttrString(tokens, "TemplateOpen");
    TemplateParamSeparator = PyObject_GetAttrString(tokens,
                                                    "TemplateParamSeparator");
    TemplateParamEquals = PyObject_GetAttrString(tokens,
                                                 "TemplateParamEquals");
    TemplateClose = PyObject_GetAttrString(tokens, "TemplateClose");

    ArgumentOpen = PyObject_GetAttrString(tokens, "ArgumentOpen");
    ArgumentSeparator = PyObject_GetAttrString(tokens, "ArgumentSeparator");
    ArgumentClose = PyObject_GetAttrString(tokens, "ArgumentClose");

    WikilinkOpen = PyObject_GetAttrString(tokens, "WikilinkOpen");
    WikilinkSeparator = PyObject_GetAttrString(tokens, "WikilinkSeparator");
    WikilinkClose = PyObject_GetAttrString(tokens, "WikilinkClose");

    HTMLEntityStart = PyObject_GetAttrString(tokens, "HTMLEntityStart");
    HTMLEntityNumeric = PyObject_GetAttrString(tokens, "HTMLEntityNumeric");
    HTMLEntityHex = PyObject_GetAttrString(tokens, "HTMLEntityHex");
    HTMLEntityEnd = PyObject_GetAttrString(tokens, "HTMLEntityEnd");

    HeadingStart = PyObject_GetAttrString(tokens, "HeadingStart");
    HeadingEnd = PyObject_GetAttrString(tokens, "HeadingEnd");

    CommentStart = PyObject_GetAttrString(tokens, "CommentStart");
    CommentEnd = PyObject_GetAttrString(tokens, "CommentEnd");

    TagOpenOpen = PyObject_GetAttrString(tokens, "TagOpenOpen");
    TagAttrStart = PyObject_GetAttrString(tokens, "TagAttrStart");
    TagAttrEquals = PyObject_GetAttrString(tokens, "TagAttrEquals");
    TagAttrQuote = PyObject_GetAttrString(tokens, "TagAttrQuote");
    TagCloseOpen = PyObject_GetAttrString(tokens, "TagCloseOpen");
    TagCloseSelfclose = PyObject_GetAttrString(tokens, "TagCloseSelfclose");
    TagOpenClose = PyObject_GetAttrString(tokens, "TagOpenClose");
    TagCloseClose = PyObject_GetAttrString(tokens, "TagCloseClose");

    Py_DECREF(tokens);
}

static void
load_tag_defs(void)
{
    PyObject *tempmod,
             *globals = PyEval_GetGlobals(),
             *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1),
             *modname = PyBytes_FromString("tag_defs");
    char *name = "mwparserfromhell";

    if (!fromlist || !modname)
        return;
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod)
        return;
    tag_defs = PyObject_GetAttrString(tempmod, "tag_defs");
    Py_DECREF(tempmod);
}

PyMODINIT_FUNC
init_tokenizer(void)
{
    PyObject *module;

    TokenizerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TokenizerType) < 0)
        return;
    module = Py_InitModule("_tokenizer", module_methods);
    Py_INCREF(&TokenizerType);
    PyModule_AddObject(module, "CTokenizer", (PyObject*) &TokenizerType);
    Py_INCREF(Py_True);
    PyDict_SetItemString(TokenizerType.tp_dict, "USES_C", Py_True);

    EMPTY = PyUnicode_FromString("");
    NOARGS = PyTuple_New(0);

    load_entitydefs();
    load_tokens();
    load_tag_defs();
}

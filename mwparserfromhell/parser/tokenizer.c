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
    Determine whether the given Py_UNICODE is a marker.
*/
static int is_marker(Py_UNICODE this)
{
    int i;

    for (i = 0; i < NUM_MARKERS; i++) {
        if (*MARKERS[i] == this)
            return 1;
    }
    return 0;
}

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
    Call the given function in definitions.py, using 'in1', 'in2', and 'in3' as
    parameters, and return its output as a bool.
*/
static int call_def_func(const char* funcname, PyObject* in1, PyObject* in2,
                         PyObject* in3)
{
    PyObject* func = PyObject_GetAttrString(definitions, funcname);
    PyObject* result = PyObject_CallFunctionObjArgs(func, in1, in2, in3, NULL);
    int ans = (result == Py_True) ? 1 : 0;

    Py_DECREF(func);
    Py_DECREF(result);
    return ans;
}

/*
    Sanitize the name of a tag so it can be compared with others for equality.
*/
static PyObject* strip_tag_name(PyObject* token)
{
    PyObject *text, *rstripped, *lowered;

    text = PyObject_GetAttrString(token, "text");
    if (!text)
        return NULL;
    rstripped = PyObject_CallMethod(text, "rstrip", NULL);
    Py_DECREF(text);
    if (!rstripped)
        return NULL;
    lowered = PyObject_CallMethod(rstripped, "lower", NULL);
    Py_DECREF(rstripped);
    return lowered;
}

static Textbuffer* Textbuffer_new(void)
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

static void Textbuffer_dealloc(Textbuffer* self)
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
static int Textbuffer_write(Textbuffer** this, Py_UNICODE code)
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
static PyObject* Textbuffer_render(Textbuffer* self)
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

static TagData* TagData_new(void)
{
    TagData *self = malloc(sizeof(TagData));

    #define ALLOC_BUFFER(name)     \
        name = Textbuffer_new();   \
        if (!name) {               \
            TagData_dealloc(self); \
            return NULL;           \
        }

    if (!self) {
        PyErr_NoMemory();
        return NULL;
    }
    self->context = TAG_NAME;
    ALLOC_BUFFER(self->pad_first)
    ALLOC_BUFFER(self->pad_before_eq)
    ALLOC_BUFFER(self->pad_after_eq)
    self->reset = 0;
    return self;
}

static void TagData_dealloc(TagData* self)
{
    #define DEALLOC_BUFFER(name) \
        if (name)                \
            Textbuffer_dealloc(name);

    DEALLOC_BUFFER(self->pad_first);
    DEALLOC_BUFFER(self->pad_before_eq);
    DEALLOC_BUFFER(self->pad_after_eq);
    free(self);
}

static int TagData_reset_buffers(TagData* self)
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
}

static PyObject*
Tokenizer_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    Tokenizer* self = (Tokenizer*) type->tp_alloc(type, 0);
    return (PyObject*) self;
}

static void Tokenizer_dealloc(Tokenizer* self)
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
    Py_TYPE(self)->tp_free((PyObject*) self);
}

static int Tokenizer_init(Tokenizer* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = {NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist))
        return -1;
    self->text = Py_None;
    Py_INCREF(Py_None);
    self->topstack = NULL;
    self->head = self->length = self->global = self->depth = self->cycles = 0;
    return 0;
}

/*
    Add a new token stack, context, and textbuffer to the list.
*/
static int Tokenizer_push(Tokenizer* self, int context)
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
static int Tokenizer_push_textbuffer(Tokenizer* self)
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
static void Tokenizer_delete_top_of_stack(Tokenizer* self)
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
static PyObject* Tokenizer_pop(Tokenizer* self)
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
static PyObject* Tokenizer_pop_keeping_context(Tokenizer* self)
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
static void* Tokenizer_fail_route(Tokenizer* self)
{
    int context = self->topstack->context;
    PyObject* stack = Tokenizer_pop(self);

    Py_XDECREF(stack);
    FAIL_ROUTE(context);
    return NULL;
}

/*
    Write a token to the current token stack.
*/
static int Tokenizer_emit_token(Tokenizer* self, PyObject* token, int first)
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
static int Tokenizer_emit_token_kwargs(Tokenizer* self, PyObject* token,
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
static int Tokenizer_emit_char(Tokenizer* self, Py_UNICODE code)
{
    return Textbuffer_write(&(self->topstack->textbuffer), code);
}

/*
    Write a string of text to the current textbuffer.
*/
static int Tokenizer_emit_text(Tokenizer* self, const char* text)
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
static int
Tokenizer_emit_textbuffer(Tokenizer* self, Textbuffer* buffer, int reverse)
{
    Textbuffer *original = buffer;
    int i;

    if (reverse) {
        do {
            for (i = buffer->size - 1; i >= 0; i--) {
                if (Tokenizer_emit_char(self, buffer->data[i])) {
                    Textbuffer_dealloc(original);
                    return -1;
                }
            }
        } while ((buffer = buffer->next));
    }
    else {
        while (buffer->next)
            buffer = buffer->next;
        do {
            for (i = 0; i < buffer->size; i++) {
                if (Tokenizer_emit_char(self, buffer->data[i])) {
                    Textbuffer_dealloc(original);
                    return -1;
                }
            }
        } while ((buffer = buffer->prev));
    }
    Textbuffer_dealloc(original);
    return 0;
}

/*
    Write a series of tokens to the current stack at once.
*/
static int Tokenizer_emit_all(Tokenizer* self, PyObject* tokenlist)
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
static int Tokenizer_emit_text_then_stack(Tokenizer* self, const char* text)
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
    Read the value at a relative point in the wikicode, forwards.
*/
static PyObject* Tokenizer_read(Tokenizer* self, Py_ssize_t delta)
{
    Py_ssize_t index = self->head + delta;

    if (index >= self->length)
        return EMPTY;
    return PyList_GET_ITEM(self->text, index);
}

/*
    Read the value at a relative point in the wikicode, backwards.
*/
static PyObject* Tokenizer_read_backwards(Tokenizer* self, Py_ssize_t delta)
{
    Py_ssize_t index;

    if (delta > self->head)
        return EMPTY;
    index = self->head - delta;
    return PyList_GET_ITEM(self->text, index);
}

/*
    Parse a template at the head of the wikicode string.
*/
static int Tokenizer_parse_template(Tokenizer* self)
{
    PyObject *template;
    Py_ssize_t reset = self->head;

    template = Tokenizer_parse(self, LC_TEMPLATE_NAME, 1);
    if (BAD_ROUTE) {
        self->head = reset;
        return 0;
    }
    if (!template)
        return -1;
    if (Tokenizer_emit_first(self, TemplateOpen)) {
        Py_DECREF(template);
        return -1;
    }
    if (Tokenizer_emit_all(self, template)) {
        Py_DECREF(template);
        return -1;
    }
    Py_DECREF(template);
    if (Tokenizer_emit(self, TemplateClose))
        return -1;
    return 0;
}

/*
    Parse an argument at the head of the wikicode string.
*/
static int Tokenizer_parse_argument(Tokenizer* self)
{
    PyObject *argument;
    Py_ssize_t reset = self->head;

    argument = Tokenizer_parse(self, LC_ARGUMENT_NAME, 1);
    if (BAD_ROUTE) {
        self->head = reset;
        return 0;
    }
    if (!argument)
        return -1;
    if (Tokenizer_emit_first(self, ArgumentOpen)) {
        Py_DECREF(argument);
        return -1;
    }
    if (Tokenizer_emit_all(self, argument)) {
        Py_DECREF(argument);
        return -1;
    }
    Py_DECREF(argument);
    if (Tokenizer_emit(self, ArgumentClose))
        return -1;
    return 0;
}

/*
    Parse a template or argument at the head of the wikicode string.
*/
static int Tokenizer_parse_template_or_argument(Tokenizer* self)
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
    Handle a template parameter at the head of the string.
*/
static int Tokenizer_handle_template_param(Tokenizer* self)
{
    PyObject *stack;

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
    if (Tokenizer_emit(self, TemplateParamSeparator))
        return -1;
    if (Tokenizer_push(self, self->topstack->context))
        return -1;
    return 0;
}

/*
    Handle a template parameter's value at the head of the string.
*/
static int Tokenizer_handle_template_param_value(Tokenizer* self)
{
    PyObject *stack;

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
    if (Tokenizer_emit(self, TemplateParamEquals))
        return -1;
    return 0;
}

/*
    Handle the end of a template at the head of the string.
*/
static PyObject* Tokenizer_handle_template_end(Tokenizer* self)
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
static int Tokenizer_handle_argument_separator(Tokenizer* self)
{
    self->topstack->context ^= LC_ARGUMENT_NAME;
    self->topstack->context |= LC_ARGUMENT_DEFAULT;
    if (Tokenizer_emit(self, ArgumentSeparator))
        return -1;
    return 0;
}

/*
    Handle the end of an argument at the head of the string.
*/
static PyObject* Tokenizer_handle_argument_end(Tokenizer* self)
{
    PyObject* stack = Tokenizer_pop(self);

    self->head += 2;
    return stack;
}

/*
    Parse an internal wikilink at the head of the wikicode string.
*/
static int Tokenizer_parse_wikilink(Tokenizer* self)
{
    Py_ssize_t reset;
    PyObject *wikilink;

    self->head += 2;
    reset = self->head - 1;
    wikilink = Tokenizer_parse(self, LC_WIKILINK_TITLE, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        if (Tokenizer_emit_text(self, "[["))
            return -1;
        return 0;
    }
    if (!wikilink)
        return -1;
    if (Tokenizer_emit(self, WikilinkOpen)) {
        Py_DECREF(wikilink);
        return -1;
    }
    if (Tokenizer_emit_all(self, wikilink)) {
        Py_DECREF(wikilink);
        return -1;
    }
    Py_DECREF(wikilink);
    if (Tokenizer_emit(self, WikilinkClose))
        return -1;
    if (self->topstack->context & LC_FAIL_NEXT)
        self->topstack->context ^= LC_FAIL_NEXT;
    return 0;
}

/*
    Handle the separator between a wikilink's title and its text.
*/
static int Tokenizer_handle_wikilink_separator(Tokenizer* self)
{
    self->topstack->context ^= LC_WIKILINK_TITLE;
    self->topstack->context |= LC_WIKILINK_TEXT;
    if (Tokenizer_emit(self, WikilinkSeparator))
        return -1;
    return 0;
}

/*
    Handle the end of a wikilink at the head of the string.
*/
static PyObject* Tokenizer_handle_wikilink_end(Tokenizer* self)
{
    PyObject* stack = Tokenizer_pop(self);
    self->head += 1;
    return stack;
}

/*
    Parse the URI scheme of a bracket-enclosed external link.
*/
static int Tokenizer_parse_bracketed_uri_scheme(Tokenizer* self)
{
    static const char* valid = "abcdefghijklmnopqrstuvwxyz0123456789+.-";
    Textbuffer* buffer;
    PyObject* scheme;
    Py_UNICODE this;
    int slashes, i;

    if (Tokenizer_push(self, LC_EXT_LINK_URI))
        return -1;
    if (Tokenizer_READ(self, 0) == *"/" && Tokenizer_READ(self, 1) == *"/") {
        if (Tokenizer_emit_text(self, "//"))
            return -1;
        self->head += 2;
    }
    else {
        buffer = Textbuffer_new();
        if (!buffer)
            return -1;
        while ((this = Tokenizer_READ(self, 0)) != *"") {
            i = 0;
            while (1) {
                if (!valid[i])
                    goto end_of_loop;
                if (this == valid[i])
                    break;
                i++;
            }
            Textbuffer_write(&buffer, this);
            if (Tokenizer_emit_char(self, this)) {
                Textbuffer_dealloc(buffer);
                return -1;
            }
            self->head++;
        }
        end_of_loop:
        if (this != *":") {
            Textbuffer_dealloc(buffer);
            Tokenizer_fail_route(self);
            return 0;
        }
        if (Tokenizer_emit_char(self, *":")) {
            Textbuffer_dealloc(buffer);
            return -1;
        }
        self->head++;
        slashes = (Tokenizer_READ(self, 0) == *"/" &&
                   Tokenizer_READ(self, 1) == *"/");
        if (slashes) {
            if (Tokenizer_emit_text(self, "//")) {
                Textbuffer_dealloc(buffer);
                return -1;
            }
            self->head += 2;
        }
        scheme = Textbuffer_render(buffer);
        Textbuffer_dealloc(buffer);
        if (!scheme)
            return -1;
        if (!IS_SCHEME(scheme, slashes, 0)) {
            Py_DECREF(scheme);
            Tokenizer_fail_route(self);
            return 0;
        }
        Py_DECREF(scheme);
    }
    return 0;
}

/*
    Parse the URI scheme of a free (no brackets) external link.
*/
static int Tokenizer_parse_free_uri_scheme(Tokenizer* self)
{
    static const char* valid = "abcdefghijklmnopqrstuvwxyz0123456789+.-";
    Textbuffer *scheme_buffer = Textbuffer_new(), *temp_buffer;
    PyObject *scheme;
    Py_UNICODE chunk;
    int slashes, i, j;

    if (!scheme_buffer)
        return -1;
    // We have to backtrack through the textbuffer looking for our scheme since
    // it was just parsed as text:
    temp_buffer = self->topstack->textbuffer;
    while (temp_buffer) {
        for (i = temp_buffer->size - 1; i >= 0; i--) {
            chunk = temp_buffer->data[i];
            if (Py_UNICODE_ISSPACE(chunk) || is_marker(chunk))
                goto end_of_loop;
            j = 0;
            while (1) {
                if (!valid[j]) {
                    Textbuffer_dealloc(scheme_buffer);
                    FAIL_ROUTE(0);
                    return 0;
                }
                if (chunk == valid[j])
                    break;
                j++;
            }
            Textbuffer_write(&scheme_buffer, chunk);
        }
        temp_buffer = temp_buffer->next;
    }
    end_of_loop:
    scheme = Textbuffer_render(scheme_buffer);
    if (!scheme) {
        Textbuffer_dealloc(scheme_buffer);
        return -1;
    }
    slashes = (Tokenizer_READ(self, 0) == *"/" &&
               Tokenizer_READ(self, 1) == *"/");
    if (!IS_SCHEME(scheme, slashes, 1)) {
        Py_DECREF(scheme);
        Textbuffer_dealloc(scheme_buffer);
        FAIL_ROUTE(0);
        return 0;
    }
    Py_DECREF(scheme);
    if (Tokenizer_push(self, self->topstack->context | LC_EXT_LINK_URI)) {
        Textbuffer_dealloc(scheme_buffer);
        return -1;
    }
    if (Tokenizer_emit_textbuffer(self, scheme_buffer, 1))
        return -1;
    if (Tokenizer_emit_char(self, *":"))
        return -1;
    if (slashes) {
        if (Tokenizer_emit_text(self, "//"))
            return -1;
        self->head += 2;
    }
    return 0;
}

/*
    Handle text in a free external link, including trailing punctuation.
*/
static int
Tokenizer_handle_free_link_text(Tokenizer* self, int* parens,
                                Textbuffer** tail, Py_UNICODE this)
{
    #define PUSH_TAIL_BUFFER(tail, error)                 \
        if ((tail)->size || (tail)->next) {               \
            if (Tokenizer_emit_textbuffer(self, tail, 0)) \
                return error;                             \
            tail = Textbuffer_new();                      \
            if (!(tail))                                  \
                return error;                             \
        }

    if (this == *"(" && !(*parens)) {
        *parens = 1;
        PUSH_TAIL_BUFFER(*tail, -1)
    }
    else if (this == *"," || this == *";" || this == *"\\" || this == *"." ||
             this == *":" || this == *"!" || this == *"?" ||
             (!(*parens) && this == *")"))
        return Textbuffer_write(tail, this);
    else
        PUSH_TAIL_BUFFER(*tail, -1)
    return Tokenizer_emit_char(self, this);
}

/*
    Return whether the current head is the end of a free link.
*/
static int
Tokenizer_is_free_link(Tokenizer* self, Py_UNICODE this, Py_UNICODE next)
{
    // Built from Tokenizer_parse()'s end sentinels:
    Py_UNICODE after = Tokenizer_READ(self, 2);
    int ctx = self->topstack->context;

    return (this == *"" || this == *"\n" || this == *"[" || this == *"]" ||
        this == *"<" || this == *">"  || (this == *"'" && next == *"'") ||
        (this == *"|" && ctx & LC_TEMPLATE) ||
        (this == *"=" && ctx & (LC_TEMPLATE_PARAM_KEY | LC_HEADING)) ||
        (this == *"}" && next == *"}" &&
            (ctx & LC_TEMPLATE || (after == *"}" && ctx & LC_ARGUMENT))));
}

/*
    Really parse an external link.
*/
static PyObject*
Tokenizer_really_parse_external_link(Tokenizer* self, int brackets,
                                     Textbuffer** extra)
{
    Py_UNICODE this, next;
    int parens = 0;

    if (brackets ? Tokenizer_parse_bracketed_uri_scheme(self) :
                   Tokenizer_parse_free_uri_scheme(self))
        return NULL;
    if (BAD_ROUTE)
        return NULL;
    this = Tokenizer_READ(self, 0);
    if (this == *"" || this == *"\n" || this == *" " || this == *"]")
        return Tokenizer_fail_route(self);
    if (!brackets && this == *"[")
        return Tokenizer_fail_route(self);
    while (1) {
        this = Tokenizer_READ(self, 0);
        next = Tokenizer_READ(self, 1);
        if (this == *"&") {
            PUSH_TAIL_BUFFER(*extra, NULL)
            if (Tokenizer_parse_entity(self))
                return NULL;
        }
        else if (this == *"<" && next == *"!"
                 && Tokenizer_READ(self, 2) == *"-"
                 && Tokenizer_READ(self, 3) == *"-") {
            PUSH_TAIL_BUFFER(*extra, NULL)
            if (Tokenizer_parse_comment(self))
                return NULL;
        }
        else if (!brackets && Tokenizer_is_free_link(self, this, next)) {
            self->head--;
            return Tokenizer_pop(self);
        }
        else if (this == *"" || this == *"\n")
            return Tokenizer_fail_route(self);
        else if (this == *"{" && next == *"{" && Tokenizer_CAN_RECURSE(self)) {
            PUSH_TAIL_BUFFER(*extra, NULL)
            if (Tokenizer_parse_template_or_argument(self))
                return NULL;
        }
        else if (this == *"]")
            return Tokenizer_pop(self);
        else if (this == *" ") {
            if (brackets) {
                if (Tokenizer_emit(self, ExternalLinkSeparator))
                    return NULL;
                self->topstack->context ^= LC_EXT_LINK_URI;
                self->topstack->context |= LC_EXT_LINK_TITLE;
                self->head++;
                return Tokenizer_parse(self, 0, 0);
            }
            if (Textbuffer_write(extra, *" "))
                return NULL;
            return Tokenizer_pop(self);
        }
        else if (!brackets) {
            if (Tokenizer_handle_free_link_text(self, &parens, extra, this))
                return NULL;
        }
        else {
            if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        self->head++;
    }
}

/*
    Remove the URI scheme of a new external link from the textbuffer.
*/
static int
Tokenizer_remove_uri_scheme_from_textbuffer(Tokenizer* self, PyObject* link)
{
    PyObject *text = PyObject_GetAttrString(PyList_GET_ITEM(link, 0), "text"),
             *split, *scheme;
    Py_ssize_t length;
    Textbuffer* temp;

    if (!text)
        return -1;
    split = PyObject_CallMethod(text, "split", "si", ":", 1);
    Py_DECREF(text);
    if (!split)
        return -1;
    scheme = PyList_GET_ITEM(split, 0);
    length = PyUnicode_GET_SIZE(scheme);
    while (length) {
        temp = self->topstack->textbuffer;
        if (length <= temp->size) {
            temp->size -= length;
            break;
        }
        length -= temp->size;
        self->topstack->textbuffer = temp->next;
        free(temp->data);
        free(temp);
    }
    Py_DECREF(split);
    return 0;
}

/*
    Parse an external link at the head of the wikicode string.
*/
static int Tokenizer_parse_external_link(Tokenizer* self, int brackets)
{
    #define INVALID_CONTEXT self->topstack->context & AGG_INVALID_LINK
    #define NOT_A_LINK                                        \
        if (!brackets && self->topstack->context & LC_DLTERM) \
            return Tokenizer_handle_dl_term(self);            \
        return Tokenizer_emit_char(self, Tokenizer_READ(self, 0))

    Py_ssize_t reset = self->head;
    PyObject *link, *kwargs;
    Textbuffer *extra = 0;

    if (INVALID_CONTEXT || !(Tokenizer_CAN_RECURSE(self))) {
        NOT_A_LINK;
    }
    extra = Textbuffer_new();
    if (!extra)
        return -1;
    self->head++;
    link = Tokenizer_really_parse_external_link(self, brackets, &extra);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        Textbuffer_dealloc(extra);
        NOT_A_LINK;
    }
    if (!link) {
        Textbuffer_dealloc(extra);
        return -1;
    }
    if (!brackets) {
        if (Tokenizer_remove_uri_scheme_from_textbuffer(self, link)) {
            Textbuffer_dealloc(extra);
            Py_DECREF(link);
            return -1;
        }
    }
    kwargs = PyDict_New();
    if (!kwargs) {
        Textbuffer_dealloc(extra);
        Py_DECREF(link);
        return -1;
    }
    PyDict_SetItemString(kwargs, "brackets", brackets ? Py_True : Py_False);
    if (Tokenizer_emit_kwargs(self, ExternalLinkOpen, kwargs)) {
        Textbuffer_dealloc(extra);
        Py_DECREF(link);
        return -1;
    }
    if (Tokenizer_emit_all(self, link)) {
        Textbuffer_dealloc(extra);
        Py_DECREF(link);
        return -1;
    }
    Py_DECREF(link);
    if (Tokenizer_emit(self, ExternalLinkClose)) {
        Textbuffer_dealloc(extra);
        return -1;
    }
    if (extra->size || extra->next)
        return Tokenizer_emit_textbuffer(self, extra, 0);
    Textbuffer_dealloc(extra);
    return 0;
}

/*
    Parse a section heading at the head of the wikicode string.
*/
static int Tokenizer_parse_heading(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    int best = 1, i, context, diff;
    HeadingData *heading;
    PyObject *level, *kwargs;

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
            if (Tokenizer_emit_char(self, *"="))
                return -1;
        }
        self->global ^= GL_HEADING;
        return 0;
    }
    level = NEW_INT_FUNC(heading->level);
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
    if (Tokenizer_emit_kwargs(self, HeadingStart, kwargs)) {
        Py_DECREF(heading->title);
        free(heading);
        return -1;
    }
    if (heading->level < best) {
        diff = best - heading->level;
        for (i = 0; i < diff; i++) {
            if (Tokenizer_emit_char(self, *"=")) {
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
    if (Tokenizer_emit(self, HeadingEnd))
        return -1;
    self->global ^= GL_HEADING;
    return 0;
}

/*
    Handle the end of a section heading at the head of the string.
*/
static HeadingData* Tokenizer_handle_heading_end(Tokenizer* self)
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
                if (Tokenizer_emit_char(self, *"="))
                    return NULL;
            }
        }
        self->head = reset + best - 1;
    }
    else {
        for (i = 0; i < best; i++) {
            if (Tokenizer_emit_char(self, *"=")) {
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
static int Tokenizer_really_parse_entity(Tokenizer* self)
{
    PyObject *kwargs, *textobj;
    Py_UNICODE this;
    int numeric, hexadecimal, i, j, zeroes, test;
    char *valid, *text, *buffer, *def;

    #define FAIL_ROUTE_AND_EXIT() { \
        Tokenizer_fail_route(self); \
        free(text);                 \
        return 0;                   \
    }

    if (Tokenizer_emit(self, HTMLEntityStart))
        return -1;
    self->head++;
    this = Tokenizer_READ(self, 0);
    if (this == *"") {
        Tokenizer_fail_route(self);
        return 0;
    }
    if (this == *"#") {
        numeric = 1;
        if (Tokenizer_emit(self, HTMLEntityNumeric))
            return -1;
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
            if (Tokenizer_emit_kwargs(self, HTMLEntityHex, kwargs))
                return -1;
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
        if (i >= MAX_ENTITY_SIZE)
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
        text[i] = (char) this;
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
    if (Tokenizer_emit_kwargs(self, Text, kwargs))
        return -1;
    if (Tokenizer_emit(self, HTMLEntityEnd))
        return -1;
    return 0;
}

/*
    Parse an HTML entity at the head of the wikicode string.
*/
static int Tokenizer_parse_entity(Tokenizer* self)
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
        if (Tokenizer_emit_char(self, *"&"))
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
static int Tokenizer_parse_comment(Tokenizer* self)
{
    Py_ssize_t reset = self->head + 3;
    PyObject *comment;
    Py_UNICODE this;

    self->head += 4;
    if (Tokenizer_push(self, 0))
        return -1;
    while (1) {
        this = Tokenizer_READ(self, 0);
        if (this == *"") {
            comment = Tokenizer_pop(self);
            Py_XDECREF(comment);
            self->head = reset;
            return Tokenizer_emit_text(self, "<!--");
        }
        if (this == *"-" && Tokenizer_READ(self, 1) == this &&
                            Tokenizer_READ(self, 2) == *">") {
            if (Tokenizer_emit_first(self, CommentStart))
                return -1;
            if (Tokenizer_emit(self, CommentEnd))
                return -1;
            comment = Tokenizer_pop(self);
            if (!comment)
                return -1;
            if (Tokenizer_emit_all(self, comment))
                return -1;
            Py_DECREF(comment);
            self->head += 2;
            return 0;
        }
        if (Tokenizer_emit_char(self, this))
            return -1;
        self->head++;
    }
}

/*
    Write a pending tag attribute from data to the stack.
*/
static int Tokenizer_push_tag_buffer(Tokenizer* self, TagData* data)
{
    PyObject *tokens, *kwargs, *pad_first, *pad_before_eq, *pad_after_eq;

    if (data->context & TAG_QUOTED) {
        if (Tokenizer_emit_first(self, TagAttrQuote))
            return -1;
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
    if (Tokenizer_emit_first_kwargs(self, TagAttrStart, kwargs))
        return -1;
    tokens = Tokenizer_pop(self);
    if (!tokens)
        return -1;
    if (Tokenizer_emit_all(self, tokens)) {
        Py_DECREF(tokens);
        return -1;
    }
    Py_DECREF(tokens);
    if (TagData_reset_buffers(data))
        return -1;
    return 0;
}

/*
    Handle whitespace inside of an HTML open tag.
*/
static int
Tokenizer_handle_tag_space(Tokenizer* self, TagData* data, Py_UNICODE text)
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
        if (Tokenizer_emit_char(self, text))
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
static int Tokenizer_handle_tag_text(Tokenizer* self, Py_UNICODE text)
{
    Py_UNICODE next = Tokenizer_READ(self, 1);

    if (!is_marker(text) || !Tokenizer_CAN_RECURSE(self))
        return Tokenizer_emit_char(self, text);
    else if (text == next && next == *"{")
        return Tokenizer_parse_template_or_argument(self);
    else if (text == next && next == *"[")
        return Tokenizer_parse_wikilink(self);
    else if (text == *"<")
        return Tokenizer_parse_tag(self);
    return Tokenizer_emit_char(self, text);
}

/*
    Handle all sorts of text data inside of an HTML open tag.
*/
static int
Tokenizer_handle_tag_data(Tokenizer* self, TagData* data, Py_UNICODE chunk)
{
    PyObject *trash;
    int first_time, escaped;

    if (data->context & TAG_NAME) {
        first_time = !(data->context & TAG_NOTE_SPACE);
        if (is_marker(chunk) || (Py_UNICODE_ISSPACE(chunk) && first_time)) {
            // Tags must start with text, not spaces
            Tokenizer_fail_route(self);
            return 0;
        }
        else if (first_time)
            data->context |= TAG_NOTE_SPACE;
        else if (Py_UNICODE_ISSPACE(chunk)) {
            data->context = TAG_ATTR_READY;
            return Tokenizer_handle_tag_space(self, data, chunk);
        }
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
            if (Tokenizer_emit(self, TagAttrEquals))
                return -1;
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
    Handle the closing of a open tag (<foo>).
*/
static int
Tokenizer_handle_tag_close_open(Tokenizer* self, TagData* data, PyObject* cls)
{
    PyObject *padding, *kwargs;

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
    if (Tokenizer_emit_kwargs(self, cls, kwargs))
        return -1;
    self->head++;
    return 0;
}

/*
    Handle the opening of a closing tag (</foo>).
*/
static int Tokenizer_handle_tag_open_close(Tokenizer* self)
{
    if (Tokenizer_emit(self, TagOpenClose))
        return -1;
    if (Tokenizer_push(self, LC_TAG_CLOSE))
        return -1;
    self->head++;
    return 0;
}

/*
    Handle the ending of a closing tag (</foo>).
*/
static PyObject* Tokenizer_handle_tag_close_close(Tokenizer* self)
{
    PyObject *closing, *first, *so, *sc;
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
    if (Tokenizer_emit(self, TagCloseClose))
        return NULL;
    return Tokenizer_pop(self);
}

/*
    Handle the body of an HTML tag that is parser-blacklisted.
*/
static PyObject* Tokenizer_handle_blacklisted_tag(Tokenizer* self)
{
    Py_UNICODE this, next;

    while (1) {
        this = Tokenizer_READ(self, 0);
        next = Tokenizer_READ(self, 1);
        if (this == *"")
            return Tokenizer_fail_route(self);
        else if (this == *"<" && next == *"/") {
            if (Tokenizer_handle_tag_open_close(self))
                return NULL;
            self->head++;
            return Tokenizer_parse(self, 0, 0);
        }
        else if (this == *"&") {
            if (Tokenizer_parse_entity(self))
                return NULL;
        }
        else if (Tokenizer_emit_char(self, this))
            return NULL;
        self->head++;
    }
}

/*
    Handle the end of an implicitly closing single-only HTML tag.
*/
static PyObject* Tokenizer_handle_single_only_tag_end(Tokenizer* self)
{
    PyObject *top, *padding, *kwargs;

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
    if (Tokenizer_emit_kwargs(self, TagCloseSelfclose, kwargs))
        return NULL;
    self->head--;  // Offset displacement done by handle_tag_close_open
    return Tokenizer_pop(self);
}

/*
    Handle the stream end when inside a single-supporting HTML tag.
*/
static PyObject* Tokenizer_handle_single_tag_end(Tokenizer* self)
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
    return Tokenizer_pop(self);
}

/*
    Actually parse an HTML tag, starting with the open (<foo>).
*/
static PyObject* Tokenizer_really_parse_tag(Tokenizer* self)
{
    TagData *data = TagData_new();
    PyObject *token, *text, *trash;
    Py_UNICODE this, next;
    int can_exit;

    if (!data)
        return NULL;
    if (Tokenizer_push(self, LC_TAG_OPEN)) {
        TagData_dealloc(data);
        return NULL;
    }
    if (Tokenizer_emit(self, TagOpenOpen)) {
        TagData_dealloc(data);
        return NULL;
    }
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
            TagData_dealloc(data);
            return Tokenizer_fail_route(self);
        }
        else if (this == *">" && can_exit) {
            if (Tokenizer_handle_tag_close_open(self, data, TagCloseOpen)) {
                TagData_dealloc(data);
                return NULL;
            }
            TagData_dealloc(data);
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
            if (Tokenizer_handle_tag_close_open(self, data,
                                                TagCloseSelfclose)) {
                TagData_dealloc(data);
                return NULL;
            }
            TagData_dealloc(data);
            return Tokenizer_pop(self);
        }
        else {
            if (Tokenizer_handle_tag_data(self, data, this) || BAD_ROUTE) {
                TagData_dealloc(data);
                return NULL;
            }
        }
        self->head++;
    }
}

/*
    Handle the (possible) start of an implicitly closing single tag.
*/
static int Tokenizer_handle_invalid_tag_start(Tokenizer* self)
{
    Py_ssize_t reset = self->head + 1, pos = 0;
    Textbuffer* buf;
    PyObject *name, *tag;
    Py_UNICODE this;

    self->head += 2;
    buf = Textbuffer_new();
    if (!buf)
        return -1;
    while (1) {
        this = Tokenizer_READ(self, pos);
        if (Py_UNICODE_ISSPACE(this) || is_marker(this)) {
            name = Textbuffer_render(buf);
            if (!name) {
                Textbuffer_dealloc(buf);
                return -1;
            }
            if (!IS_SINGLE_ONLY(name))
                FAIL_ROUTE(0);
            Py_DECREF(name);
            break;
        }
        Textbuffer_write(&buf, this);
        pos++;
    }
    Textbuffer_dealloc(buf);
    if (!BAD_ROUTE)
        tag = Tokenizer_really_parse_tag(self);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        return Tokenizer_emit_text(self, "</");
    }
    if (!tag)
        return -1;
    // Set invalid=True flag of TagOpenOpen
    if (PyObject_SetAttrString(PyList_GET_ITEM(tag, 0), "invalid", Py_True))
        return -1;
    if (Tokenizer_emit_all(self, tag)) {
        Py_DECREF(tag);
        return -1;
    }
    Py_DECREF(tag);
    return 0;
}

/*
    Parse an HTML tag at the head of the wikicode string.
*/
static int Tokenizer_parse_tag(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    PyObject* tag;

    self->head++;
    tag = Tokenizer_really_parse_tag(self);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        return Tokenizer_emit_char(self, *"<");
    }
    if (!tag) {
        return -1;
    }
    if (Tokenizer_emit_all(self, tag)) {
        Py_DECREF(tag);
        return -1;
    }
    Py_DECREF(tag);
    return 0;
}

/*
    Write the body of a tag and the tokens that should surround it.
*/
static int Tokenizer_emit_style_tag(Tokenizer* self, const char* tag,
                                    const char* ticks, PyObject* body)
{
    PyObject *markup, *kwargs;

    markup = PyUnicode_FromString(ticks);
    if (!markup)
        return -1;
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(markup);
        return -1;
    }
    PyDict_SetItemString(kwargs, "wiki_markup", markup);
    Py_DECREF(markup);
    if (Tokenizer_emit_kwargs(self, TagOpenOpen, kwargs))
        return -1;
    if (Tokenizer_emit_text(self, tag))
        return -1;
    if (Tokenizer_emit(self, TagCloseOpen))
        return -1;
    if (Tokenizer_emit_all(self, body))
        return -1;
    Py_DECREF(body);
    if (Tokenizer_emit(self, TagOpenClose))
        return -1;
    if (Tokenizer_emit_text(self, tag))
        return -1;
    if (Tokenizer_emit(self, TagCloseClose))
        return -1;
    return 0;
}

/*
    Parse wiki-style italics.
*/
static int Tokenizer_parse_italics(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    int context;
    PyObject *stack;

    stack = Tokenizer_parse(self, LC_STYLE_ITALICS, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        if (BAD_ROUTE_CONTEXT & LC_STYLE_PASS_AGAIN) {
            context = LC_STYLE_ITALICS | LC_STYLE_SECOND_PASS;
            stack = Tokenizer_parse(self, context, 1);
        }
        else
            return Tokenizer_emit_text(self, "''");
    }
    if (!stack)
        return -1;
    return Tokenizer_emit_style_tag(self, "i", "''", stack);
}

/*
    Parse wiki-style bold.
*/
static int Tokenizer_parse_bold(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    PyObject *stack;

    stack = Tokenizer_parse(self, LC_STYLE_BOLD, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        if (self->topstack->context & LC_STYLE_SECOND_PASS)
            return Tokenizer_emit_char(self, *"'") ? -1 : 1;
        if (self->topstack->context & LC_STYLE_ITALICS) {
            self->topstack->context |= LC_STYLE_PASS_AGAIN;
            return Tokenizer_emit_text(self, "'''");
        }
        if (Tokenizer_emit_char(self, *"'"))
            return -1;
        return Tokenizer_parse_italics(self);
    }
    if (!stack)
        return -1;
    return Tokenizer_emit_style_tag(self, "b", "'''", stack);
}

/*
    Parse wiki-style italics and bold together (i.e., five ticks).
*/
static int Tokenizer_parse_italics_and_bold(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    PyObject *stack, *stack2;

    stack = Tokenizer_parse(self, LC_STYLE_BOLD, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        stack = Tokenizer_parse(self, LC_STYLE_ITALICS, 1);
        if (BAD_ROUTE) {
            RESET_ROUTE();
            self->head = reset;
            return Tokenizer_emit_text(self, "'''''");
        }
        if (!stack)
            return -1;
        reset = self->head;
        stack2 = Tokenizer_parse(self, LC_STYLE_BOLD, 1);
        if (BAD_ROUTE) {
            RESET_ROUTE();
            self->head = reset;
            if (Tokenizer_emit_text(self, "'''"))
                return -1;
            return Tokenizer_emit_style_tag(self, "i", "''", stack);
        }
        if (!stack2)
            return -1;
        if (Tokenizer_push(self, 0))
            return -1;
        if (Tokenizer_emit_style_tag(self, "i", "''", stack))
            return -1;
        if (Tokenizer_emit_all(self, stack2))
            return -1;
        Py_DECREF(stack2);
        stack2 = Tokenizer_pop(self);
        if (!stack2)
            return -1;
        return Tokenizer_emit_style_tag(self, "b", "'''", stack2);
    }
    if (!stack)
        return -1;
    reset = self->head;
    stack2 = Tokenizer_parse(self, LC_STYLE_ITALICS, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        if (Tokenizer_emit_text(self, "''"))
            return -1;
        return Tokenizer_emit_style_tag(self, "b", "'''", stack);
    }
    if (!stack2)
        return -1;
    if (Tokenizer_push(self, 0))
        return -1;
    if (Tokenizer_emit_style_tag(self, "b", "'''", stack))
        return -1;
    if (Tokenizer_emit_all(self, stack2))
        return -1;
    Py_DECREF(stack2);
    stack2 = Tokenizer_pop(self);
    if (!stack2)
        return -1;
    return Tokenizer_emit_style_tag(self, "i", "''", stack2);
}

/*
    Parse wiki-style formatting (''/''' for italics/bold).
*/
static PyObject* Tokenizer_parse_style(Tokenizer* self)
{
    int context = self->topstack->context, ticks = 2, i;

    self->head += 2;
    while (Tokenizer_READ(self, 0) == *"'") {
        self->head++;
        ticks++;
    }
    if (ticks > 5) {
        for (i = 0; i < ticks - 5; i++) {
            if (Tokenizer_emit_char(self, *"'"))
                return NULL;
        }
        ticks = 5;
    }
    else if (ticks == 4) {
        if (Tokenizer_emit_char(self, *"'"))
            return NULL;
        ticks = 3;
    }
    if ((context & LC_STYLE_ITALICS && (ticks == 2 || ticks == 5)) ||
           (context & LC_STYLE_BOLD && (ticks == 3 || ticks == 5))) {
        if (ticks == 5)
            self->head -= context & LC_STYLE_ITALICS ? 3 : 2;
        return Tokenizer_pop(self);
    }
    if (!Tokenizer_CAN_RECURSE(self)) {
        if (ticks == 3) {
            if (context & LC_STYLE_SECOND_PASS) {
                if (Tokenizer_emit_char(self, *"'"))
                    return NULL;
                return Tokenizer_pop(self);
            }
            if (context & LC_STYLE_ITALICS)
                self->topstack->context |= LC_STYLE_PASS_AGAIN;
        }
        for (i = 0; i < ticks; i++) {
            if (Tokenizer_emit_char(self, *"'"))
                return NULL;
        }
    }
    else if (ticks == 2) {
        if (Tokenizer_parse_italics(self))
            return NULL;
    }
    else if (ticks == 3) {
        switch (Tokenizer_parse_bold(self)) {
            case 1:
                return Tokenizer_pop(self);
            case -1:
                return NULL;
        }
    }
    else {
        if (Tokenizer_parse_italics_and_bold(self))
            return NULL;
    }
    self->head--;
    return Py_None;
}

/*
    Handle a list marker at the head (#, *, ;, :).
*/
static int Tokenizer_handle_list_marker(Tokenizer* self)
{
    PyObject *markup = Tokenizer_read(self, 0), *kwargs;
    Py_UNICODE code = *PyUnicode_AS_UNICODE(markup);

    if (code == *";")
        self->topstack->context |= LC_DLTERM;
    kwargs = PyDict_New();
    if (!kwargs)
        return -1;
    PyDict_SetItemString(kwargs, "wiki_markup", markup);
    if (Tokenizer_emit_kwargs(self, TagOpenOpen, kwargs))
        return -1;
    if (Tokenizer_emit_text(self, GET_HTML_TAG(code)))
        return -1;
    if (Tokenizer_emit(self, TagCloseSelfclose))
        return -1;
    return 0;
}

/*
    Handle a wiki-style list (#, *, ;, :).
*/
static int Tokenizer_handle_list(Tokenizer* self)
{
    Py_UNICODE marker = Tokenizer_READ(self, 1);

    if (Tokenizer_handle_list_marker(self))
        return -1;
    while (marker == *"#" || marker == *"*" || marker == *";" ||
           marker == *":") {
        self->head++;
        if (Tokenizer_handle_list_marker(self))
            return -1;
        marker = Tokenizer_READ(self, 1);
    }
    return 0;
}

/*
    Handle a wiki-style horizontal rule (----) in the string.
*/
static int Tokenizer_handle_hr(Tokenizer* self)
{
    PyObject *markup, *kwargs;
    Textbuffer *buffer = Textbuffer_new();
    int i;

    if (!buffer)
        return -1;
    self->head += 3;
    for (i = 0; i < 4; i++) {
        if (Textbuffer_write(&buffer, *"-"))
            return -1;
    }
    while (Tokenizer_READ(self, 1) == *"-") {
        if (Textbuffer_write(&buffer, *"-"))
            return -1;
        self->head++;
    }
    markup = Textbuffer_render(buffer);
    Textbuffer_dealloc(buffer);
    if (!markup)
        return -1;
    kwargs = PyDict_New();
    if (!kwargs)
        return -1;
    PyDict_SetItemString(kwargs, "wiki_markup", markup);
    Py_DECREF(markup);
    if (Tokenizer_emit_kwargs(self, TagOpenOpen, kwargs))
        return -1;
    if (Tokenizer_emit_text(self, "hr"))
        return -1;
    if (Tokenizer_emit(self, TagCloseSelfclose))
        return -1;
    return 0;
}

/*
    Handle the term in a description list ('foo' in ';foo:bar').
*/
static int Tokenizer_handle_dl_term(Tokenizer* self)
{
    self->topstack->context ^= LC_DLTERM;
    if (Tokenizer_READ(self, 0) == *":")
        return Tokenizer_handle_list_marker(self);
    return Tokenizer_emit_char(self, *"\n");
}

/*
    Handle the end of the stream of wikitext.
*/
static PyObject* Tokenizer_handle_end(Tokenizer* self, int context)
{
    PyObject *token, *text, *trash;
    int single;

    if (context & AGG_FAIL) {
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
        else if (context & AGG_DOUBLE) {
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
static int Tokenizer_verify_safe(Tokenizer* self, int context, Py_UNICODE data)
{
    if (context & LC_FAIL_NEXT)
        return -1;
    if (context & LC_WIKILINK) {
        if (context & LC_WIKILINK_TEXT)
            return (data == *"[" && Tokenizer_READ(self, 1) == *"[") ? -1 : 0;
        else if (data == *"]" || data == *"{")
            self->topstack->context |= LC_FAIL_NEXT;
        else if (data == *"\n" || data == *"[" || data == *"}")
            return -1;
        return 0;
    }
    if (context & LC_EXT_LINK_TITLE)
        return (data == *"\n") ? -1 : 0;
    if (context & LC_TAG_CLOSE)
        return (data == *"<") ? -1 : 0;
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
static PyObject* Tokenizer_parse(Tokenizer* self, int context, int push)
{
    int this_context;
    Py_UNICODE this, next, next_next, last;
    PyObject* temp;

    if (push) {
        if (Tokenizer_push(self, context))
            return NULL;
    }
    while (1) {
        this = Tokenizer_READ(self, 0);
        this_context = self->topstack->context;
        if (this_context & AGG_UNSAFE) {
            if (Tokenizer_verify_safe(self, this_context, this) < 0) {
                if (this_context & AGG_DOUBLE) {
                    temp = Tokenizer_pop(self);
                    Py_XDECREF(temp);
                }
                return Tokenizer_fail_route(self);
            }
        }
        if (!is_marker(this)) {
            if (Tokenizer_emit_char(self, this))
                return NULL;
            self->head++;
            continue;
        }
        if (this == *"")
            return Tokenizer_handle_end(self, this_context);
        next = Tokenizer_READ(self, 1);
        last = Tokenizer_READ_BACKWARDS(self, 1);
        if (this == next && next == *"{") {
            if (Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_template_or_argument(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
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
            if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == next && next == *"[" && Tokenizer_CAN_RECURSE(self)) {
            if (!(this_context & AGG_INVALID_LINK)) {
                if (Tokenizer_parse_wikilink(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == *"|" && this_context & LC_WIKILINK_TITLE) {
            if (Tokenizer_handle_wikilink_separator(self))
                return NULL;
        }
        else if (this == next && next == *"]" && this_context & LC_WIKILINK)
            return Tokenizer_handle_wikilink_end(self);
        else if (this == *"[") {
            if (Tokenizer_parse_external_link(self, 1))
                return NULL;
        }
        else if (this == *":" && !is_marker(last)) {
            if (Tokenizer_parse_external_link(self, 0))
                return NULL;
        }
        else if (this == *"]" && this_context & LC_EXT_LINK_TITLE)
            return Tokenizer_pop(self);
        else if (this == *"=" && !(self->global & GL_HEADING)) {
            if (last == *"\n" || last == *"") {
                if (Tokenizer_parse_heading(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
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
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == *"<" && next == *"/" &&
                                            Tokenizer_READ(self, 2) != *"") {
            if (this_context & LC_TAG_BODY ?
                Tokenizer_handle_tag_open_close(self) :
                Tokenizer_handle_invalid_tag_start(self))
                return NULL;
        }
        else if (this == *"<" && !(this_context & LC_TAG_CLOSE)) {
            if (Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_tag(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == *">" && this_context & LC_TAG_CLOSE)
            return Tokenizer_handle_tag_close_close(self);
        else if (this == next && next == *"'") {
            temp = Tokenizer_parse_style(self);
            if (temp != Py_None)
                return temp;
        }
        else if (last == *"\n" || last == *"") {
            if (this == *"#" || this == *"*" || this == *";" || this == *":") {
                if (Tokenizer_handle_list(self))
                    return NULL;
            }
            else if (this == *"-" && this == next &&
                     this == Tokenizer_READ(self, 2) &&
                     this == Tokenizer_READ(self, 3)) {
                if (Tokenizer_handle_hr(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if ((this == *"\n" || this == *":") && this_context & LC_DLTERM) {
            if (Tokenizer_handle_dl_term(self))
                return NULL;
        }
        else if (Tokenizer_emit_char(self, this))
            return NULL;
        self->head++;
    }
}

/*
    Build a list of tokens from a string of wikicode and return it.
*/
static PyObject* Tokenizer_tokenize(Tokenizer* self, PyObject* args)
{
    PyObject *text, *temp;
    int context = 0;

    if (PyArg_ParseTuple(args, "U|i", &text, &context)) {
        Py_XDECREF(self->text);
        self->text = PySequence_Fast(text, "expected a sequence");
    }
    else {
        const char* encoded;
        Py_ssize_t size;
        /* Failed to parse a Unicode object; try a string instead. */
        PyErr_Clear();
        if (!PyArg_ParseTuple(args, "s#|i", &encoded, &size, &context))
            return NULL;
        temp = PyUnicode_FromStringAndSize(encoded, size);
        if (!text)
            return NULL;
        Py_XDECREF(self->text);
        text = PySequence_Fast(temp, "expected a sequence");
        Py_XDECREF(temp);
        self->text = text;
    }
    self->head = self->global = self->depth = self->cycles = 0;
    self->length = PyList_GET_SIZE(self->text);
    return Tokenizer_parse(self, context, 1);
}

static int load_entitydefs(void)
{
    PyObject *tempmod, *defmap, *deflist;
    unsigned numdefs, i;
#ifdef IS_PY3K
    PyObject *string;
#endif

    tempmod = PyImport_ImportModule(ENTITYDEFS_MODULE);
    if (!tempmod)
        return -1;
    defmap = PyObject_GetAttrString(tempmod, "entitydefs");
    if (!defmap)
        return -1;
    Py_DECREF(tempmod);
    deflist = PyDict_Keys(defmap);
    if (!deflist)
        return -1;
    Py_DECREF(defmap);
    numdefs = (unsigned) PyList_GET_SIZE(defmap);
    entitydefs = calloc(numdefs + 1, sizeof(char*));
    if (!entitydefs)
        return -1;
    for (i = 0; i < numdefs; i++) {
#ifdef IS_PY3K
        string = PyUnicode_AsASCIIString(PyList_GET_ITEM(deflist, i));
        if (!string)
            return -1;
        entitydefs[i] = PyBytes_AsString(string);
#else
        entitydefs[i] = PyBytes_AsString(PyList_GET_ITEM(deflist, i));
#endif
        if (!entitydefs[i])
            return -1;
    }
    Py_DECREF(deflist);
    return 0;
}

static int load_tokens(void)
{
    PyObject *tempmod, *tokens,
             *globals = PyEval_GetGlobals(),
             *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1),
             *modname = IMPORT_NAME_FUNC("tokens");
    char *name = "mwparserfromhell.parser";

    if (!fromlist || !modname)
        return -1;
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod)
        return -1;
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

    ExternalLinkOpen = PyObject_GetAttrString(tokens, "ExternalLinkOpen");
    ExternalLinkSeparator = PyObject_GetAttrString(tokens,
                                                   "ExternalLinkSeparator");
    ExternalLinkClose = PyObject_GetAttrString(tokens, "ExternalLinkClose");

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
    return 0;
}

static int load_definitions(void)
{
    PyObject *tempmod,
             *globals = PyEval_GetGlobals(),
             *locals = PyEval_GetLocals(),
             *fromlist = PyList_New(1),
             *modname = IMPORT_NAME_FUNC("definitions");
    char *name = "mwparserfromhell";

    if (!fromlist || !modname)
        return -1;
    PyList_SET_ITEM(fromlist, 0, modname);
    tempmod = PyImport_ImportModuleLevel(name, globals, locals, fromlist, 0);
    Py_DECREF(fromlist);
    if (!tempmod)
        return -1;
    definitions = PyObject_GetAttrString(tempmod, "definitions");
    Py_DECREF(tempmod);
    return 0;
}

PyMODINIT_FUNC INIT_FUNC_NAME(void)
{
    PyObject *module;

    TokenizerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TokenizerType) < 0)
        INIT_ERROR;
    module = CREATE_MODULE;
    if (!module)
        INIT_ERROR;
    Py_INCREF(&TokenizerType);
    PyModule_AddObject(module, "CTokenizer", (PyObject*) &TokenizerType);
    Py_INCREF(Py_True);
    PyDict_SetItemString(TokenizerType.tp_dict, "USES_C", Py_True);
    EMPTY = PyUnicode_FromString("");
    NOARGS = PyTuple_New(0);
    if (!EMPTY || !NOARGS)
        INIT_ERROR;
    if (load_entitydefs() || load_tokens() || load_definitions())
        INIT_ERROR;
#ifdef IS_PY3K
    return module;
#endif
}

/*
Tokenizer for MWParserFromHell
Copyright (C) 2012 Ben Kurtovic <ben.kurtovic@verizon.net>

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

static PyObject*
Tokenizer_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    Tokenizer *self;

    self = (Tokenizer*) type->tp_alloc(type, 0);
    if (self != NULL) {

        self->text = Py_None;
        Py_INCREF(Py_None);

        self->stacks = PyList_New(0);
        if (!self->stacks) {
            Py_DECREF(self);
            return NULL;
        }

        self->head = 0;
        self->length = 0;
        self->global = 0;
    }

    return (PyObject*) self;
}

static void
Tokenizer_dealloc(Tokenizer* self)
{
    Py_XDECREF(self->text);
    Py_XDECREF(self->stacks);
    Py_XDECREF(self->topstack);
    self->ob_type->tp_free((PyObject*) self);
}

static int
Tokenizer_init(Tokenizer* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = {NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist))
        return -1;
    return 0;
}

static int
Tokenizer_set_context(Tokenizer* self, Py_ssize_t value)
{
    if (PyList_SetItem(self->topstack, 1, PyInt_FromSsize_t(value)))
        return -1;
    return 0;
}

static int
Tokenizer_set_textbuffer(Tokenizer* self, PyObject* value)
{
    if (PyList_SetItem(self->topstack, 2, value))
        return -1;
    return 0;
}

/*
    Add a new token stack, context, and textbuffer to the list.
*/
static int
Tokenizer_push(Tokenizer* self, Py_ssize_t context)
{
    PyObject* top = PyList_New(3);
    PyList_SET_ITEM(top, 0, PyList_New(0));
    PyList_SET_ITEM(top, 1, PyInt_FromSsize_t(context));
    PyList_SET_ITEM(top, 2, PyList_New(0));

    Py_XDECREF(self->topstack);
    self->topstack = top;

    if (PyList_Append(self->stacks, top))
        return -1;
    return 0;
}

/*
    Push the textbuffer onto the stack as a Text node and clear it.
*/
static int
Tokenizer_push_textbuffer(Tokenizer* self)
{
    if (PySequence_Fast_GET_SIZE(Tokenizer_TEXTBUFFER(self)) > 0) {
        PyObject* text = PyUnicode_Join(EMPTY, Tokenizer_TEXTBUFFER(self));
        if (!text) return -1;

        PyObject* class = PyObject_GetAttrString(tokens, "Text");
        if (!class) {
            Py_DECREF(text);
            return -1;
        }
        PyObject* kwargs = PyDict_New();
        if (!kwargs) {
            Py_DECREF(class);
            Py_DECREF(text);
            return -1;
        }
        PyDict_SetItemString(kwargs, "text", text);
        Py_DECREF(text);

        PyObject* token = PyInstance_New(class, NOARGS, kwargs);
        Py_DECREF(class);
        Py_DECREF(kwargs);
        if (!token) return -1;

        if (PyList_Append(Tokenizer_STACK(self), token)) {
            Py_DECREF(token);
            return -1;
        }

        Py_DECREF(token);

        if (Tokenizer_set_textbuffer(self, PyList_New(0)))
            return -1;
    }
    return 0;
}

static int
Tokenizer_delete_top_of_stack(Tokenizer* self)
{
    if (PySequence_DelItem(self->stacks, -1))
        return -1;
    Py_DECREF(self->topstack);

    Py_ssize_t size = PySequence_Fast_GET_SIZE(self->stacks);
    if (size > 0) {
        PyObject* top = PySequence_Fast_GET_ITEM(self->stacks, size - 1);
        self->topstack = top;
        Py_INCREF(top);
    }
    else {
        self->topstack = NULL;
    }

    return 0;
}

/*
    Pop the current stack/context/textbuffer, returing the stack.
*/
static PyObject*
Tokenizer_pop(Tokenizer* self)
{
    if (Tokenizer_push_textbuffer(self))
        return NULL;

    PyObject* stack = Tokenizer_STACK(self);
    Py_INCREF(stack);

    if (Tokenizer_delete_top_of_stack(self))
        return NULL;

    return stack;
}

/*
    Pop the current stack/context/textbuffer, returing the stack. We will also
    replace the underlying stack's context with the current stack's.
*/
static PyObject*
Tokenizer_pop_keeping_context(Tokenizer* self)
{
    if (Tokenizer_push_textbuffer(self))
        return NULL;

    PyObject* stack = Tokenizer_STACK(self);
    PyObject* context = Tokenizer_CONTEXT(self);
    Py_INCREF(stack);
    Py_INCREF(context);

    if (Tokenizer_delete_top_of_stack(self))
        return NULL;

    if (PyList_SetItem(self->topstack, 1, context))
        return NULL;

    return stack;
}

/*
    Fail the current tokenization route. Discards the current
    stack/context/textbuffer and "raises a BAD_ROUTE exception", which is
    implemented using longjmp().
*/
static void
Tokenizer_fail_route(Tokenizer* self)
{
    PyObject* stack = Tokenizer_pop(self);
    Py_XDECREF(stack);
    longjmp(exception_env, BAD_ROUTE);
}

/*
    Write a token to the end of the current token stack.
*/
static int
Tokenizer_write(Tokenizer* self, PyObject* token)
{
    if (Tokenizer_push_textbuffer(self))
        return -1;

    if (PyList_Append(Tokenizer_STACK(self), token))
        return -1;

    return 0;
}

/*
    Write a token to the beginning of the current token stack.
*/
static int
Tokenizer_write_first(Tokenizer* self, PyObject* token)
{
    if (Tokenizer_push_textbuffer(self))
        return -1;

    if (PyList_Insert(Tokenizer_STACK(self), 0, token))
        return -1;

    return 0;
}

/*
    Write text to the current textbuffer.
*/
static int
Tokenizer_write_text(Tokenizer* self, PyObject* text)
{
    if (PyList_Append(Tokenizer_TEXTBUFFER(self), text))
        return -1;

    return 0;
}

/*
    Write a series of tokens to the current stack at once.
*/
static int
Tokenizer_write_all(Tokenizer* self, PyObject* tokenlist)
{
    if (PySequence_Fast_GET_SIZE(tokenlist) > 0) {
        PyObject* token = PySequence_Fast_GET_ITEM(tokenlist, 0);
        PyObject* class = PyObject_GetAttrString(tokens, "Text");
        if (!class) return -1;

        PyObject* text;
        switch (PyObject_IsInstance(token, class)) {
            case 0:
                break;
            case 1:
                text = PyObject_GetAttrString(token, "text");
                if (!text) {
                    Py_DECREF(class);
                    return -1;
                }
                if (PySequence_DelItem(tokenlist, 0)) {
                    Py_DECREF(text);
                    Py_DECREF(class);
                    return -1;
                }
                if (Tokenizer_write_text(self, text)) {
                    Py_DECREF(text);
                    Py_DECREF(class);
                    return -1;
                }
                Py_DECREF(text);
                break;
            case -1:
                Py_DECREF(class);
                return -1;
        }
        Py_DECREF(class);
    }

    if (Tokenizer_push_textbuffer(self))
        return -1;

    PyObject* stack = Tokenizer_STACK(self);
    Py_ssize_t size = PySequence_Fast_GET_SIZE(stack);

    if (PyList_SetSlice(stack, size, size, tokenlist))
        return -1;

    return 0;
}

/*
    Pop the current stack, write text, and then write the stack.
*/
static int
Tokenizer_write_text_then_stack(Tokenizer* self, PyObject* text)
{
    PyObject* stack = Tokenizer_pop(self);
    if (Tokenizer_write_text(self, text)) {
        Py_XDECREF(stack);
        return -1;
    }

    if (stack) {
        if (PySequence_Fast_GET_SIZE(stack) > 0) {
            if (Tokenizer_write_all(self, stack)) {
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

    return PySequence_Fast_GET_ITEM(self->text, index);
}

/*
    Read the value at a relative point in the wikicode, backwards.
*/
static PyObject*
Tokenizer_read_backwards(Tokenizer* self, Py_ssize_t delta)
{
    if (delta > self->head)
        return EMPTY;

    Py_ssize_t index = self->head - delta;
    return PySequence_Fast_GET_ITEM(self->text, index);
}

/*
    Parse a template or argument at the head of the wikicode string.
*/
static int
Tokenizer_parse_template_or_argument(Tokenizer* self)
{
    self->head += 2;
    unsigned int braces = 2, i;

    while (Tokenizer_READ(self, 0) == PU "{") {
        self->head++;
        braces++;
    }
    Tokenizer_push(self, 0);

    while (braces) {
        if (braces == 1) {
            PyObject* text = PyUnicode_FromString("{");

            if (Tokenizer_write_text_then_stack(self, text)) {
                Py_XDECREF(text);
                return -1;
            }

            Py_XDECREF(text);
            return 0;
        }

        if (braces == 2) {
            if (setjmp(exception_env) == BAD_ROUTE) {
                PyObject* text = PyUnicode_FromString("{{");

                if (Tokenizer_write_text_then_stack(self, text)) {
                    Py_XDECREF(text);
                    return -1;
                }

                Py_XDECREF(text);
                return 0;
            } else {
                Tokenizer_parse_template(self);
            }
            break;
        }

        if (setjmp(exception_env) == BAD_ROUTE) {
            if (setjmp(exception_env) == BAD_ROUTE) {
                char bracestr[braces];
                for (i = 0; i < braces; i++) bracestr[i] = *"{";
                PyObject* text = PyUnicode_FromString(bracestr);

                if (Tokenizer_write_text_then_stack(self, text)) {
                    Py_XDECREF(text);
                    return -1;
                }

                Py_XDECREF(text);
                return 0;
            }
            else {
                Tokenizer_parse_template(self);
                braces -= 2;
            }
        }
        else {
            Tokenizer_parse_argument(self);
            braces -= 3;
        }

        if (braces) {
            self->head++;
        }
    }

    PyObject* tokenlist = Tokenizer_pop(self);
    if (!tokenlist) return -1;
    if (Tokenizer_write_all(self, tokenlist)) {
        Py_DECREF(tokenlist);
        return -1;
    }

    Py_DECREF(tokenlist);
    return 0;
}

/*
    Parse a template at the head of the wikicode string.
*/
static int
Tokenizer_parse_template(Tokenizer* self)
{
    PyObject *template, *class, *token;
    Py_ssize_t reset = self->head;

    if (setjmp(exception_env) == BAD_ROUTE) {
        self->head = reset;
        longjmp(exception_env, BAD_ROUTE);
    }

    else {
        template = Tokenizer_parse(self, LC_TEMPLATE_NAME);
        if (!template) return -1;

        class = PyObject_GetAttrString(tokens, "TemplateOpen");
        if (!class) {
            Py_DECREF(template);
            return -1;
        }
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) {
            Py_DECREF(template);
            return -1;
        }

        if (Tokenizer_write_first(self, token)) {
            Py_DECREF(token);
            Py_DECREF(template);
            return -1;
        }
        Py_DECREF(token);

        if (Tokenizer_write_all(self, template)) {
            Py_DECREF(template);
            return -1;
        }
        Py_DECREF(template);

        class = PyObject_GetAttrString(tokens, "TemplateClose");
        if (!class) return -1;
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) return -1;

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);
    }

    return 0;
}

/*
    Parse an argument at the head of the wikicode string.
*/
static int
Tokenizer_parse_argument(Tokenizer* self)
{
    PyObject *argument, *class, *token;
    Py_ssize_t reset = self->head;

    if (setjmp(exception_env) == BAD_ROUTE) {
        self->head = reset;
        longjmp(exception_env, BAD_ROUTE);
    }

    else {
        argument = Tokenizer_parse(self, LC_ARGUMENT_NAME);
        if (!argument) return -1;

        class = PyObject_GetAttrString(tokens, "ArgumentOpen");
        if (!class) {
            Py_DECREF(argument);
            return -1;
        }
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) {
            Py_DECREF(argument);
            return -1;
        }

        if (Tokenizer_write_first(self, token)) {
            Py_DECREF(token);
            Py_DECREF(argument);
            return -1;
        }
        Py_DECREF(token);

        if (Tokenizer_write_all(self, argument)) {
            Py_DECREF(argument);
            return -1;
        }
        Py_DECREF(argument);

        class = PyObject_GetAttrString(tokens, "ArgumentClose");
        if (!class) return -1;
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) return -1;

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);
    }

    return 0;
}

/*
    Verify that there are no unsafe characters in the current stack. The route
    will be failed if the name contains any element of unsafes in it (not
    merely at the beginning or end). This is used when parsing a template name
    or parameter key, which cannot contain newlines.
*/
static int
Tokenizer_verify_safe(Tokenizer* self, const char* unsafes[])
{
    if (Tokenizer_push_textbuffer(self))
        return -1;

    PyObject* stack = Tokenizer_STACK(self);
    if (stack) {
        PyObject* textlist = PyList_New(0);
        if (!textlist) return -1;

        PyObject* class = PyObject_GetAttrString(tokens, "Text");
        if (!class) {
            Py_DECREF(textlist);
            return -1;
        }

        int i;
        Py_ssize_t length = PySequence_Fast_GET_SIZE(stack);
        PyObject *token, *textdata;

        for (i = 0; i < length; i++) {
            token = PySequence_Fast_GET_ITEM(stack, i);
            switch (PyObject_IsInstance(token, class)) {
                case 0:
                    break;
                case 1:
                    textdata = PyObject_GetAttrString(token, "text");
                    if (!textdata) {
                        Py_DECREF(textlist);
                        Py_DECREF(class);
                        return -1;
                    }
                    if (PyList_Append(textlist, textdata)) {
                        Py_DECREF(textlist);
                        Py_DECREF(class);
                        Py_DECREF(textdata);
                        return -1;
                    }
                    Py_DECREF(textdata);
                    break;
                case -1:
                    Py_DECREF(textlist);
                    Py_DECREF(class);
                    return -1;
            }
        }
        Py_DECREF(class);

        PyObject* text = PyUnicode_Join(EMPTY, textlist);
        if (!text) {
            Py_DECREF(textlist);
            return -1;
        }
        Py_DECREF(textlist);

        PyObject* stripped = PyObject_CallMethod(text, "strip", NULL);
        if (!stripped) {
            Py_DECREF(text);
            return -1;
        }
        Py_DECREF(text);

        const char* unsafe_char;
        PyObject* unsafe;
        i = 0;
        while (1) {
            unsafe_char = unsafes[i];
            if (!unsafe_char) break;

            unsafe = PyUnicode_FromString(unsafe_char);

            if (!unsafe) {
                Py_DECREF(stripped);
                return -1;
            }

            switch (PyUnicode_Contains(stripped, unsafe)) {
                case 0:
                    break;
                case 1:
                    Py_DECREF(stripped);
                    Py_DECREF(unsafe);
                    Tokenizer_fail_route(self);
                    break;
                case -1:
                    Py_DECREF(stripped);
                    Py_DECREF(unsafe);
                    return -1;
            }
            i++;
        }
    }

    return 0;
}

/*
    Handle a template parameter at the head of the string.
*/
static int
Tokenizer_handle_template_param(Tokenizer* self)
{
    Py_ssize_t context = Tokenizer_CONTEXT_VAL(self);

    if (context & LC_TEMPLATE_NAME) {
        const char* unsafes[] = {"\n", "{", "}", "[", "]"};
        if (Tokenizer_verify_safe(self, unsafes))
            return -1;
        if (Tokenizer_set_context(self, context ^ LC_TEMPLATE_NAME))
            return -1;
    }
    else if (context & LC_TEMPLATE_PARAM_VALUE) {
        if (Tokenizer_set_context(self, context ^ LC_TEMPLATE_PARAM_VALUE))
            return -1;
    }

    if (context & LC_TEMPLATE_PARAM_KEY) {
        PyObject* stack = Tokenizer_pop_keeping_context(self);
        if (!stack) return -1;
        if (Tokenizer_write_all(self, stack)) {
            Py_DECREF(stack);
            return -1;
        }
        Py_DECREF(stack);
    }
    else {
        if (Tokenizer_set_context(self, context | LC_TEMPLATE_PARAM_KEY))
            return -1;
    }

    PyObject* class = PyObject_GetAttrString(tokens, "TemplateParamSeparator");
    if (!class) return -1;
    PyObject* token = PyInstance_New(class, NOARGS, NOKWARGS);
    Py_DECREF(class);
    if (!token) return -1;

    if (Tokenizer_write(self, token)) {
        Py_DECREF(token);
        return -1;
    }
    Py_DECREF(token);

    Tokenizer_push(self, Tokenizer_CONTEXT_VAL(self));
    return 0;
}

/*
    Handle a template parameter's value at the head of the string.
*/
static int
Tokenizer_handle_template_param_value(Tokenizer* self)
{
    if (setjmp(exception_env) == BAD_ROUTE) {
        PyObject* stack = Tokenizer_pop(self);
        Py_XDECREF(stack);
        longjmp(exception_env, BAD_ROUTE);
    }

    else {
        const char* unsafes[] = {"\n", "{{", "}}"};
        if (Tokenizer_verify_safe(self, unsafes))
            return -1;
    }

    PyObject* stack = Tokenizer_pop_keeping_context(self);
    if (!stack) return -1;
    if (Tokenizer_write_all(self, stack)) {
        Py_DECREF(stack);
        return -1;
    }
    Py_DECREF(stack);

    Py_ssize_t context = Tokenizer_CONTEXT_VAL(self);
    context ^= LC_TEMPLATE_PARAM_KEY;
    context |= LC_TEMPLATE_PARAM_VALUE;
    if (Tokenizer_set_context(self, context))
        return -1;

    PyObject* class = PyObject_GetAttrString(tokens, "TemplateParamEquals");
    if (!class) return -1;
    PyObject* token = PyInstance_New(class, NOARGS, NOKWARGS);
    Py_DECREF(class);
    if (!token) return -1;

    if (Tokenizer_write(self, token)) {
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
    Py_ssize_t context = Tokenizer_CONTEXT_VAL(self);

    if (context & LC_TEMPLATE_NAME) {
        const char* unsafes[] = {"\n", "{", "}", "[", "]"};
        if (Tokenizer_verify_safe(self, unsafes))
            return NULL;
    }
    else if (context & LC_TEMPLATE_PARAM_KEY) {
        stack = Tokenizer_pop_keeping_context(self);
        if (!stack) return NULL;
        if (Tokenizer_write_all(self, stack)) {
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
    const char* unsafes[] = {"\n", "{{", "}}"};
    if (Tokenizer_verify_safe(self, unsafes))
        return -1;

    Py_ssize_t context = Tokenizer_CONTEXT_VAL(self);
    context ^= LC_ARGUMENT_NAME;
    context |= LC_ARGUMENT_DEFAULT;
    if (Tokenizer_set_context(self, context))
        return -1;

    PyObject* class = PyObject_GetAttrString(tokens, "ArgumentSeparator");
    if (!class) return -1;
    PyObject* token = PyInstance_New(class, NOARGS, NOKWARGS);
    Py_DECREF(class);
    if (!token) return -1;

    if (Tokenizer_write(self, token)) {
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
    if (Tokenizer_CONTEXT_VAL(self) & LC_ARGUMENT_NAME) {
        const char* unsafes[] = {"\n", "{{", "}}"};
        if (Tokenizer_verify_safe(self, unsafes))
            return NULL;
    }

    self->head += 2;
    PyObject* stack = Tokenizer_pop(self);
    return stack;
}

/*
    Parse an internal wikilink at the head of the wikicode string.
*/
static int
Tokenizer_parse_wikilink(Tokenizer* self)
{
    self->head += 2;
    Py_ssize_t reset = self->head - 1;

    if (setjmp(exception_env) == BAD_ROUTE) {
        self->head = reset;
        PyObject* text = PyUnicode_FromString("[[");
        if (!text) return -1;
        if (Tokenizer_write_text(self, text)) {
            Py_XDECREF(text);
            return -1;
        }
    }
    else {
        PyObject *class, *token;
        PyObject *wikilink = Tokenizer_parse(self, LC_WIKILINK_TITLE);
        if (!wikilink) return -1;

        class = PyObject_GetAttrString(tokens, "WikilinkOpen");
        if (!class) {
            Py_DECREF(wikilink);
            return -1;
        }
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) {
            Py_DECREF(wikilink);
            return -1;
        }

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            Py_DECREF(wikilink);
            return -1;
        }
        Py_DECREF(token);

        if (Tokenizer_write_all(self, wikilink)) {
            Py_DECREF(wikilink);
            return -1;
        }
        Py_DECREF(wikilink);

        class = PyObject_GetAttrString(tokens, "WikilinkClose");
        if (!class) return -1;
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) return -1;

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);
    }
    return 0;
}

/*
    Handle the separator between a wikilink's title and its text.
*/
static int
Tokenizer_handle_wikilink_separator(Tokenizer* self)
{
    const char* unsafes[] = {"\n", "{", "}", "[", "]"};
    if (Tokenizer_verify_safe(self, unsafes))
        return -1;

    Py_ssize_t context = Tokenizer_CONTEXT_VAL(self);
    context ^= LC_WIKILINK_TITLE;
    context |= LC_WIKILINK_TEXT;
    if (Tokenizer_set_context(self, context))
        return -1;

    PyObject* class = PyObject_GetAttrString(tokens, "WikilinkSeparator");
    if (!class) return -1;
    PyObject* token = PyInstance_New(class, NOARGS, NOKWARGS);
    Py_DECREF(class);
    if (!token) return -1;

    if (Tokenizer_write(self, token)) {
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
    if (Tokenizer_CONTEXT_VAL(self) & LC_WIKILINK_TITLE) {
        const char* unsafes[] = {"\n", "{", "}", "[", "]"};
        if (Tokenizer_verify_safe(self, unsafes))
            return NULL;
    }

    self->head += 1;
    PyObject* stack = Tokenizer_pop(self);
    return stack;
}

/*
    Parse a section heading at the head of the wikicode string.
*/
static int
Tokenizer_parse_heading(Tokenizer* self)
{
    self->global |= GL_HEADING;
    Py_ssize_t reset = self->head;
    self->head += 1;
    Py_ssize_t best = 1;
    PyObject* text;
    int i;

    while (Tokenizer_READ(self, 0) == PU "=") {
        best++;
        self->head++;
    }

    Py_ssize_t context = LC_HEADING_LEVEL_1 << (best > 5 ? 5 : best - 1);

    if (setjmp(exception_env) == BAD_ROUTE) {
        self->head = reset + best - 1;
        char blocks[best];
        for (i = 0; i < best; i++) blocks[i] = *"{";
        text = PyUnicode_FromString(blocks);
        if (!text) return -1;

        if (Tokenizer_write_text_then_stack(self, text)) {
            Py_DECREF(text);
            return -1;
        }
        Py_DECREF(text);
        self->global ^= GL_HEADING;
    }
    else {
        HeadingData* heading = (HeadingData*) Tokenizer_parse(self, context);

        PyObject* level = PyInt_FromSsize_t(heading->level);
        if (!level) {
            Py_DECREF(heading->title);
            free(heading);
            return -1;
        }

        PyObject* class = PyObject_GetAttrString(tokens, "HeadingStart");
        if (!class) {
            Py_DECREF(level);
            Py_DECREF(heading->title);
            free(heading);
            return -1;
        }
        PyObject* kwargs = PyDict_New();
        if (!kwargs) {
            Py_DECREF(class);
            Py_DECREF(level);
            Py_DECREF(heading->title);
            free(heading);
            return -1;
        }
        PyDict_SetItemString(kwargs, "level", level);
        Py_DECREF(level);

        PyObject* token = PyInstance_New(class, NOARGS, kwargs);
        Py_DECREF(class);
        Py_DECREF(kwargs);
        if (!token) {
            Py_DECREF(heading->title);
            free(heading);
            return -1;
        }

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            Py_DECREF(heading->title);
            free(heading);
            return -1;
        }
        Py_DECREF(token);

        if (heading->level < best) {
            Py_ssize_t diff = best - heading->level;
            char diffblocks[diff];
            for (i = 0; i < diff; i++) diffblocks[i] = *"=";
            PyObject* text = PyUnicode_FromString(diffblocks);
            if (!text) {
                Py_DECREF(heading->title);
                free(heading);
                return -1;
            }

            if (Tokenizer_write_text_then_stack(self, text)) {
                Py_DECREF(text);
                Py_DECREF(heading->title);
                free(heading);
                return -1;
            }
            Py_DECREF(text);
        }

        if (Tokenizer_write_all(self, heading->title)) {
            Py_DECREF(heading->title);
            free(heading);
            return -1;
        }
        Py_DECREF(heading->title);
        free(heading);

        class = PyObject_GetAttrString(tokens, "HeadingEnd");
        if (!class) return -1;
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) return -1;

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);

        self->global ^= GL_HEADING;
    }
    return 0;
}

/*
    Handle the end of a section heading at the head of the string.
*/
static HeadingData*
Tokenizer_handle_heading_end(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    self->head += 1;
    Py_ssize_t best = 1;
    PyObject* text;
    int i;

    while (Tokenizer_READ(self, 0) == PU "=") {
        best++;
        self->head++;
    }

    Py_ssize_t current = LC_HEADING_LEVEL_1 << (best > 5 ? 5 : best - 1);       // FIXME
    Py_ssize_t level = current > best ? (best > 6 ? 6 : best) : (current > 6 ? 6 : current);

    if (setjmp(exception_env) == BAD_ROUTE) {
        if (level < best) {
            Py_ssize_t diff = best - level;
            char diffblocks[diff];
            for (i = 0; i < diff; i++) diffblocks[i] = *"=";
            text = PyUnicode_FromString(diffblocks);
            if (!text) return NULL;

            if (Tokenizer_write_text_then_stack(self, text)) {
                Py_DECREF(text);
                return NULL;
            }
            Py_DECREF(text);
        }

        self->head = reset + best - 1;
    }
    else {
        Py_ssize_t context = Tokenizer_CONTEXT_VAL(self);
        HeadingData* after = (HeadingData*) Tokenizer_parse(self, context);

        char blocks[best];
        for (i = 0; i < best; i++) blocks[i] = *"=";
        text = PyUnicode_FromString(blocks);
        if (!text) {
            Py_DECREF(after->title);
            free(after);
            return NULL;
        }

        if (Tokenizer_write_text_then_stack(self, text)) {
            Py_DECREF(text);
            Py_DECREF(after->title);
            free(after);
            return NULL;
        }
        Py_DECREF(text);

        if (Tokenizer_write_all(self, after->title)) {
            Py_DECREF(after->title);
            free(after);
            return NULL;
        }
        Py_DECREF(after->title);
        level = after->level;
        free(after);
    }

    PyObject* stack = Tokenizer_pop(self);
    if (!stack) return NULL;

    HeadingData* heading = malloc(sizeof(HeadingData));
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

}

/*
    Parse an HTML entity at the head of the wikicode string.
*/
static int
Tokenizer_parse_entity(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    if (Tokenizer_push(self, 0))
        return -1;

    if (setjmp(exception_env) == BAD_ROUTE) {
        self->head = reset;
        if (Tokenizer_write_text(self, Tokenizer_read(self, 0)))
            return -1;
    }
    else {
        if (Tokenizer_really_parse_entity(self))
            return -1;

        PyObject* tokenlist = Tokenizer_pop(self);
        if (!tokenlist) return -1;
        if (Tokenizer_write_all(self, tokenlist)) {
            Py_DECREF(tokenlist);
            return -1;
        }

        Py_DECREF(tokenlist);
    }
    return 0;
}

/*
    Parse an HTML comment at the head of the wikicode string.
*/
static int
Tokenizer_parse_comment(Tokenizer* self)
{
    self->head += 4;
    Py_ssize_t reset = self->head - 1;

    if (setjmp(exception_env) == BAD_ROUTE) {
        self->head = reset;
        PyObject* text = PyUnicode_FromString("<!--");
        if (!text) return -1;
        if (Tokenizer_write_text(self, text)) {
            Py_XDECREF(text);
            return -1;
        }
    }
    else {
        PyObject *class, *token;
        PyObject *comment = Tokenizer_parse(self, LC_WIKILINK_TITLE);
        if (!comment) return -1;

        class = PyObject_GetAttrString(tokens, "CommentStart");
        if (!class) {
            Py_DECREF(comment);
            return -1;
        }
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) {
            Py_DECREF(comment);
            return -1;
        }

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            Py_DECREF(comment);
            return -1;
        }
        Py_DECREF(token);

        if (Tokenizer_write_all(self, comment)) {
            Py_DECREF(comment);
            return -1;
        }
        Py_DECREF(comment);

        class = PyObject_GetAttrString(tokens, "CommentEnd");
        if (!class) return -1;
        token = PyInstance_New(class, NOARGS, NOKWARGS);
        Py_DECREF(class);
        if (!token) return -1;

        if (Tokenizer_write(self, token)) {
            Py_DECREF(token);
            return -1;
        }
        Py_DECREF(token);
        self->head += 2;
    }
    return 0;
}

/*
    Parse the wikicode string, using context for when to stop.
*/
static PyObject*
Tokenizer_parse(Tokenizer* self, Py_ssize_t context)
{
    PyObject *this;
    Py_UNICODE *this_data, *next, *next_next, *last;
    Py_ssize_t this_context;
    Py_ssize_t fail_contexts = LC_TEMPLATE | LC_ARGUMENT | LC_HEADING | LC_COMMENT;
    int is_marker, i;

    Tokenizer_push(self, context);

    while (1) {
        this = Tokenizer_read(self, 0);
        this_data = PyUnicode_AS_UNICODE(this);

        is_marker = 0;
        for (i = 0; i < NUM_MARKERS; i++) {
            if (MARKERS[i] == this_data) {
                is_marker = 1;
                break;
            }
        }

        if (!is_marker) {
            Tokenizer_write_text(self, this);
            self->head++;
            continue;
        }

        this_context = Tokenizer_CONTEXT_VAL(self);

        if (this == EMPTY) {
            if (this_context & fail_contexts) {
                Tokenizer_fail_route(self);
            }
            return Tokenizer_pop(self);
        }

        next = Tokenizer_READ(self, 1);

        if (this_context & LC_COMMENT) {
            if (this_data == next && next == PU "-") {
                if (Tokenizer_READ(self, 2) == PU ">") {
                    return Tokenizer_pop(self);
                }
            }
            Tokenizer_write_text(self, this);
        }
        else if (this_data == next && next == PU "{") {
            Tokenizer_parse_template_or_argument(self);
        }
        else if (this_data == PU "|" && this_context & LC_TEMPLATE) {
            Tokenizer_handle_template_param(self);
        }
        else if (this_data == PU "=" && this_context & LC_TEMPLATE_PARAM_KEY) {
            Tokenizer_handle_template_param_value(self);
        }
        else if (this_data == next && next == PU "}" && this_context & LC_TEMPLATE) {
            Tokenizer_handle_template_end(self);
        }
        else if (this_data == PU "|" && this_context & LC_ARGUMENT_NAME) {
            Tokenizer_handle_argument_separator(self);
        }
        else if (this_data == next && next == PU "}" && this_context & LC_ARGUMENT) {
            if (Tokenizer_READ(self, 2) == PU "}") {
                return Tokenizer_handle_argument_end(self);
            }
            Tokenizer_write_text(self, this);
        }
        else if (this_data == next && next == PU "[") {
            if (!(this_context & LC_WIKILINK_TITLE)) {
                Tokenizer_parse_wikilink(self);
            }
            else {
                Tokenizer_write_text(self, this);
            }
        }
        else if (this_data == PU "|" && this_context & LC_WIKILINK_TITLE) {
            Tokenizer_handle_wikilink_separator(self);
        }
        else if (this_data == next && next == PU "]" && this_context & LC_WIKILINK) {
            return Tokenizer_handle_wikilink_end(self);
        }
        else if (this_data == PU "=" && !(self->global & GL_HEADING)) {
            last = PyUnicode_AS_UNICODE(Tokenizer_read_backwards(self, 1));
            if (last == PU "\n" || last == PU "") {
                Tokenizer_parse_heading(self);
            }
            else {
                Tokenizer_write_text(self, this);
            }
        }
        else if (this_data == PU "=" && this_context & LC_HEADING) {
            return (PyObject*) Tokenizer_handle_heading_end(self);
        }
        else if (this_data == PU "\n" && this_context & LC_HEADING) {
            Tokenizer_fail_route(self);
        }
        else if (this_data == PU "&") {
            Tokenizer_parse_entity(self);
        }
        else if (this_data == PU "<" && next == PU "!") {
            next_next = Tokenizer_READ(self, 2);
            if (next_next == Tokenizer_READ(self, 3) && next_next == PU "-") {
                Tokenizer_parse_comment(self);
            }
            else {
                Tokenizer_write_text(self, this);
            }
        }
        else {
            Tokenizer_write_text(self, this);
        }

        self->head++;
    }
}

/*
    Build a list of tokens from a string of wikicode and return it.
*/
static PyObject*
Tokenizer_tokenize(Tokenizer* self, PyObject *args)
{
    PyObject* text;

    if (!PyArg_ParseTuple(args, "U", &text)) {
        /* Failed to parse a Unicode object; try a string instead. */
        PyErr_Clear();
        const char* encoded;
        Py_ssize_t size;

        if (!PyArg_ParseTuple(args, "s#", &encoded, &size)) {
            return NULL;
        }

        PyObject* temp;
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

    self->length = PySequence_Length(self->text);

    return Tokenizer_parse(self, 0);
}

PyMODINIT_FUNC
init_tokenizer(void)
{
    PyObject* module;

    TokenizerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TokenizerType) < 0)
        return;

    module = Py_InitModule("_tokenizer", module_methods);

    Py_INCREF(&TokenizerType);
    PyModule_AddObject(module, "CTokenizer", (PyObject*) &TokenizerType);

    EMPTY = PyUnicode_FromString("");
    NOARGS = PyTuple_New(0);
    NOKWARGS = PyDict_New();

    PyObject* globals = PyEval_GetGlobals();
    PyObject* locals = PyEval_GetLocals();
    PyObject* fromlist = PyList_New(0);

    tokens = PyImport_ImportModuleLevel("tokens", globals, locals, fromlist, 1);
    Py_DECREF(fromlist);
}

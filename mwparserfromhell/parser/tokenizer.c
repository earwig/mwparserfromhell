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

        PyObject* klass = PyObject_GetAttrString(tokens, "Text");
        if (!klass) return -1;
        PyObject* args = PyTuple_New(0);
        if (!args) return -1;
        PyObject* kwargs = PyDict_New();
        if (!kwargs) return -1;
        PyDict_SetItemString(kwargs, "text", text);
        Py_DECREF(text);

        PyObject* token = PyInstance_New(klass, args, kwargs);
        if (!token) {
            Py_DECREF(klass);
            Py_DECREF(args);
            Py_DECREF(kwargs);
            return -1;
        }

        Py_DECREF(klass);
        Py_DECREF(args);
        Py_DECREF(kwargs);

        if (PyList_Append(Tokenizer_STACK(self), token)) {
            Py_XDECREF(token);
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
    Tokenizer_pop(self);
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
                for (i = 0; i < braces; i++) {
                        bracestr[i] = *"{";
                }
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

}

/*
    Parse an argument at the head of the wikicode string.
*/
static int
Tokenizer_parse_argument(Tokenizer* self)
{

}

/*
    Verify that there are no unsafe characters in the current stack. The route
    will be failed if the name contains any element of unsafes in it (not
    merely at the beginning or end). This is used when parsing a template name
    or parameter key, which cannot contain newlines.
*/
static int
Tokenizer_verify_safe(Tokenizer* self, Py_UNICODE* unsafes[])
{

}

/*
    Handle a template parameter at the head of the string.
*/
static int
Tokenizer_handle_template_param(Tokenizer* self)
{

}

/*
    Handle a template parameter's value at the head of the string.
*/
static int
Tokenizer_handle_template_param_value(Tokenizer* self)
{

}

/*
    Handle the end of a template at the head of the string.
*/
static PyObject*
Tokenizer_handle_template_end(Tokenizer* self)
{

}

/*
    Handle the separator between an argument's name and default.
*/
static int
Tokenizer_handle_argument_separator(Tokenizer* self)
{

}

/*
    Handle the end of an argument at the head of the string.
*/
static PyObject*
Tokenizer_handle_argument_end(Tokenizer* self)
{

}

/*
    Parse an internal wikilink at the head of the wikicode string.
*/
static int
Tokenizer_parse_wikilink(Tokenizer* self)
{

}

/*
    Handle the separator between a wikilink's title and its text.
*/
static int
Tokenizer_handle_wikilink_separator(Tokenizer* self)
{

}

/*
    Handle the end of a wikilink at the head of the string.
*/
static PyObject*
Tokenizer_handle_wikilink_end(Tokenizer* self)
{

}

/*
    Parse a section heading at the head of the wikicode string.
*/
static int
Tokenizer_parse_heading(Tokenizer* self)
{

}

/*
    Handle the end of a section heading at the head of the string.
*/
static PyObject*
Tokenizer_handle_heading_end(Tokenizer* self)
{

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

}

/*
    Parse an HTML comment at the head of the wikicode string.
*/
static int
Tokenizer_parse_comment(Tokenizer* self)
{

}

/*
    Parse the wikicode string, using context for when to stop.
*/
static PyObject*
Tokenizer_parse(Tokenizer* self, Py_ssize_t context)
{
    Py_ssize_t fail_contexts = LC_TEMPLATE | LC_ARGUMENT | LC_HEADING | LC_COMMENT;

    PyObject *this;
    Py_UNICODE *this_data, *next, *next_next, *last;
    Py_ssize_t this_context;
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
            return Tokenizer_handle_heading_end(self);
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

    PyObject* globals = PyEval_GetGlobals();
    PyObject* locals = PyEval_GetLocals();
    PyObject* fromlist = PyList_New(0);

    tokens = PyImport_ImportModuleLevel("tokens", globals, locals, fromlist, 1);
    Py_DECREF(fromlist);
}

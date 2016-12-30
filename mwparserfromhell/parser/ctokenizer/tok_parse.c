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

#include "tok_parse.h"
#include "contexts.h"
#include "definitions.h"
#include "tag_data.h"
#include "tok_support.h"
#include "tokens.h"

#define DIGITS    "0123456789"
#define HEXDIGITS "0123456789abcdefABCDEF"
#define ALPHANUM  "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
#define URISCHEME "abcdefghijklmnopqrstuvwxyz0123456789+.-"

#define MAX_BRACES 255
#define MAX_ENTITY_SIZE 8

typedef struct {
    PyObject* title;
    int level;
} HeadingData;

/* Forward declarations */

static PyObject* Tokenizer_really_parse_external_link(
    Tokenizer*, int, Textbuffer*);
static int Tokenizer_parse_entity(Tokenizer*);
static int Tokenizer_parse_comment(Tokenizer*);
static int Tokenizer_handle_dl_term(Tokenizer*);
static int Tokenizer_parse_tag(Tokenizer*);

/*
    Determine whether the given code point is a marker.
*/
static int is_marker(Unicode this)
{
    int i;

    for (i = 0; i < NUM_MARKERS; i++) {
        if (MARKERS[i] == this)
            return 1;
    }
    return 0;
}

/*
    Given a context, return the heading level encoded within it.
*/
static int heading_level_from_context(uint64_t n)
{
    int level;

    n /= LC_HEADING_LEVEL_1;
    for (level = 1; n > 1; n >>= 1)
        level++;
    return level;
}

/*
    Sanitize the name of a tag so it can be compared with others for equality.
*/
static PyObject* strip_tag_name(PyObject* token, int take_attr)
{
    PyObject *text, *rstripped, *lowered;

    if (take_attr) {
        text = PyObject_GetAttrString(token, "text");
        if (!text)
            return NULL;
        rstripped = PyObject_CallMethod(text, "rstrip", NULL);
        Py_DECREF(text);
    }
    else
        rstripped = PyObject_CallMethod(token, "rstrip", NULL);
    if (!rstripped)
        return NULL;
    lowered = PyObject_CallMethod(rstripped, "lower", NULL);
    Py_DECREF(rstripped);
    return lowered;
}

/*
    Parse a template at the head of the wikicode string.
*/
static int Tokenizer_parse_template(Tokenizer* self, int has_content)
{
    PyObject *template;
    Py_ssize_t reset = self->head;
    uint64_t context = LC_TEMPLATE_NAME;

    if (has_content)
        context |= LC_HAS_TEMPLATE;

    template = Tokenizer_parse(self, context, 1);
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
    int has_content = 0;
    PyObject *tokenlist;

    self->head += 2;
    while (Tokenizer_read(self, 0) == '{' && braces < MAX_BRACES) {
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
            if (Tokenizer_parse_template(self, has_content))
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
            if (Tokenizer_parse_template(self, has_content))
                return -1;
            if (BAD_ROUTE) {
                char text[MAX_BRACES + 1];
                RESET_ROUTE();
                for (i = 0; i < braces; i++) text[i] = '{';
                text[braces] = '\0';
                if (Tokenizer_emit_text_then_stack(self, text))
                    return -1;
                return 0;
            }
            else
                braces -= 2;
        }
        else
            braces -= 3;
        if (braces) {
            has_content = 1;
            self->head++;
        }
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

    if (self->topstack->context & LC_TEMPLATE_NAME) {
        if (!(self->topstack->context & (LC_HAS_TEXT | LC_HAS_TEMPLATE))) {
            Tokenizer_fail_route(self);
            return -1;
        }
        self->topstack->context ^= LC_TEMPLATE_NAME;
    }
    else if (self->topstack->context & LC_TEMPLATE_PARAM_VALUE)
        self->topstack->context ^= LC_TEMPLATE_PARAM_VALUE;
    if (self->topstack->context & LC_TEMPLATE_PARAM_KEY) {
        stack = Tokenizer_pop(self);
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

    stack = Tokenizer_pop(self);
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

    if (self->topstack->context & LC_TEMPLATE_NAME) {
        if (!(self->topstack->context & (LC_HAS_TEXT | LC_HAS_TEMPLATE)))
            return Tokenizer_fail_route(self);
    }
    else if (self->topstack->context & LC_TEMPLATE_PARAM_KEY) {
        stack = Tokenizer_pop(self);
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
    PyObject *extlink, *wikilink, *kwargs;

    reset = self->head + 1;
    self->head += 2;
    // If the wikilink looks like an external link, parse it as such:
    extlink = Tokenizer_really_parse_external_link(self, 1, NULL);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset + 1;
        // Otherwise, actually parse it as a wikilink:
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
        return 0;
    }
    if (!extlink)
        return -1;
    if (self->topstack->context & LC_EXT_LINK_TITLE) {
        // In this exceptional case, an external link that looks like a
        // wikilink inside of an external link is parsed as text:
        Py_DECREF(extlink);
        self->head = reset;
        if (Tokenizer_emit_text(self, "[["))
            return -1;
        return 0;
    }
    if (Tokenizer_emit_text(self, "[")) {
        Py_DECREF(extlink);
        return -1;
    }
    kwargs = PyDict_New();
    if (!kwargs) {
        Py_DECREF(extlink);
        return -1;
    }
    PyDict_SetItemString(kwargs, "brackets", Py_True);
    if (Tokenizer_emit_kwargs(self, ExternalLinkOpen, kwargs)) {
        Py_DECREF(extlink);
        return -1;
    }
    if (Tokenizer_emit_all(self, extlink)) {
        Py_DECREF(extlink);
        return -1;
    }
    Py_DECREF(extlink);
    if (Tokenizer_emit(self, ExternalLinkClose))
        return -1;
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
    static const char* valid = URISCHEME;
    Textbuffer* buffer;
    PyObject* scheme;
    Unicode this;
    int slashes, i;

    if (Tokenizer_push(self, LC_EXT_LINK_URI))
        return -1;
    if (Tokenizer_read(self, 0) == '/' && Tokenizer_read(self, 1) == '/') {
        if (Tokenizer_emit_text(self, "//"))
            return -1;
        self->head += 2;
    }
    else {
        buffer = Textbuffer_new(&self->text);
        if (!buffer)
            return -1;
        while ((this = Tokenizer_read(self, 0))) {
            i = 0;
            while (1) {
                if (!valid[i])
                    goto end_of_loop;
                if (this == valid[i])
                    break;
                i++;
            }
            Textbuffer_write(buffer, this);
            if (Tokenizer_emit_char(self, this)) {
                Textbuffer_dealloc(buffer);
                return -1;
            }
            self->head++;
        }
        end_of_loop:
        if (this != ':') {
            Textbuffer_dealloc(buffer);
            Tokenizer_fail_route(self);
            return 0;
        }
        if (Tokenizer_emit_char(self, ':')) {
            Textbuffer_dealloc(buffer);
            return -1;
        }
        self->head++;
        slashes = (Tokenizer_read(self, 0) == '/' &&
                   Tokenizer_read(self, 1) == '/');
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
        if (!is_scheme(scheme, slashes)) {
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
    static const char* valid = URISCHEME;
    Textbuffer *scheme_buffer = Textbuffer_new(&self->text);
    PyObject *scheme;
    Unicode chunk;
    Py_ssize_t i;
    int slashes, j;

    if (!scheme_buffer)
        return -1;
    // We have to backtrack through the textbuffer looking for our scheme since
    // it was just parsed as text:
    for (i = self->topstack->textbuffer->length - 1; i >= 0; i--) {
        chunk = Textbuffer_read(self->topstack->textbuffer, i);
        if (Py_UNICODE_ISSPACE(chunk) || is_marker(chunk))
            goto end_of_loop;
        j = 0;
        do {
            if (!valid[j]) {
                Textbuffer_dealloc(scheme_buffer);
                FAIL_ROUTE(0);
                return 0;
            }
        } while (chunk != valid[j++]);
        Textbuffer_write(scheme_buffer, chunk);
    }
    end_of_loop:
    Textbuffer_reverse(scheme_buffer);
    scheme = Textbuffer_render(scheme_buffer);
    if (!scheme) {
        Textbuffer_dealloc(scheme_buffer);
        return -1;
    }
    slashes = (Tokenizer_read(self, 0) == '/' &&
               Tokenizer_read(self, 1) == '/');
    if (!is_scheme(scheme, slashes)) {
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
    if (Tokenizer_emit_textbuffer(self, scheme_buffer))
        return -1;
    if (Tokenizer_emit_char(self, ':'))
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
static int Tokenizer_handle_free_link_text(
    Tokenizer* self, int* parens, Textbuffer* tail, Unicode this)
{
    #define PUSH_TAIL_BUFFER(tail, error)                            \
        if (tail && tail->length > 0) {                              \
            if (Textbuffer_concat(self->topstack->textbuffer, tail)) \
                return error;                                        \
            if (Textbuffer_reset(tail))                              \
                return error;                                        \
        }

    if (this == '(' && !(*parens)) {
        *parens = 1;
        PUSH_TAIL_BUFFER(tail, -1)
    }
    else if (this == ',' || this == ';' || this == '\\' || this == '.' ||
             this == ':' || this == '!' || this == '?' ||
             (!(*parens) && this == ')'))
        return Textbuffer_write(tail, this);
    else
        PUSH_TAIL_BUFFER(tail, -1)
    return Tokenizer_emit_char(self, this);
}

/*
    Return whether the current head is the end of a free link.
*/
static int
Tokenizer_is_free_link(Tokenizer* self, Unicode this, Unicode next)
{
    // Built from Tokenizer_parse()'s end sentinels:
    Unicode after = Tokenizer_read(self, 2);
    uint64_t ctx = self->topstack->context;

    return (!this || this == '\n' || this == '[' || this == ']' ||
        this == '<' || this == '>'  || (this == '\'' && next == '\'') ||
        (this == '|' && ctx & LC_TEMPLATE) ||
        (this == '=' && ctx & (LC_TEMPLATE_PARAM_KEY | LC_HEADING)) ||
        (this == '}' && next == '}' &&
            (ctx & LC_TEMPLATE || (after == '}' && ctx & LC_ARGUMENT))));
}

/*
    Really parse an external link.
*/
static PyObject*
Tokenizer_really_parse_external_link(Tokenizer* self, int brackets,
                                     Textbuffer* extra)
{
    Unicode this, next;
    int parens = 0;

    if (brackets ? Tokenizer_parse_bracketed_uri_scheme(self) :
                   Tokenizer_parse_free_uri_scheme(self))
        return NULL;
    if (BAD_ROUTE)
        return NULL;
    this = Tokenizer_read(self, 0);
    if (!this || this == '\n' || this == ' ' || this == ']')
        return Tokenizer_fail_route(self);
    if (!brackets && this == '[')
        return Tokenizer_fail_route(self);
    while (1) {
        this = Tokenizer_read(self, 0);
        next = Tokenizer_read(self, 1);
        if (this == '&') {
            PUSH_TAIL_BUFFER(extra, NULL)
            if (Tokenizer_parse_entity(self))
                return NULL;
        }
        else if (this == '<' && next == '!'
                 && Tokenizer_read(self, 2) == '-'
                 && Tokenizer_read(self, 3) == '-') {
            PUSH_TAIL_BUFFER(extra, NULL)
            if (Tokenizer_parse_comment(self))
                return NULL;
        }
        else if (!brackets && Tokenizer_is_free_link(self, this, next)) {
            self->head--;
            return Tokenizer_pop(self);
        }
        else if (!this || this == '\n')
            return Tokenizer_fail_route(self);
        else if (this == '{' && next == '{' && Tokenizer_CAN_RECURSE(self)) {
            PUSH_TAIL_BUFFER(extra, NULL)
            if (Tokenizer_parse_template_or_argument(self))
                return NULL;
        }
        else if (this == ']')
            return Tokenizer_pop(self);
        else if (this == ' ') {
            if (brackets) {
                if (Tokenizer_emit(self, ExternalLinkSeparator))
                    return NULL;
                self->topstack->context ^= LC_EXT_LINK_URI;
                self->topstack->context |= LC_EXT_LINK_TITLE;
                self->head++;
                return Tokenizer_parse(self, 0, 0);
            }
            if (Textbuffer_write(extra, ' '))
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

    if (!text)
        return -1;
    split = PyObject_CallMethod(text, "split", "si", ":", 1);
    Py_DECREF(text);
    if (!split)
        return -1;
    scheme = PyList_GET_ITEM(split, 0);
    length = PyUnicode_GET_LENGTH(scheme);
    Py_DECREF(split);
    self->topstack->textbuffer->length -= length;
    return 0;
}

/*
    Parse an external link at the head of the wikicode string.
*/
static int Tokenizer_parse_external_link(Tokenizer* self, int brackets)
{
    #define INVALID_CONTEXT self->topstack->context & AGG_NO_EXT_LINKS
    #define NOT_A_LINK                                        \
        if (!brackets && self->topstack->context & LC_DLTERM) \
            return Tokenizer_handle_dl_term(self);            \
        return Tokenizer_emit_char(self, Tokenizer_read(self, 0))

    Py_ssize_t reset = self->head;
    PyObject *link, *kwargs;
    Textbuffer *extra;

    if (INVALID_CONTEXT || !(Tokenizer_CAN_RECURSE(self))) {
        NOT_A_LINK;
    }
    extra = Textbuffer_new(&self->text);
    if (!extra)
        return -1;
    self->head++;
    link = Tokenizer_really_parse_external_link(self, brackets, extra);
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
    if (extra->length > 0)
        return Tokenizer_emit_textbuffer(self, extra);
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
    while (Tokenizer_read(self, 0) == '=') {
        best++;
        self->head++;
    }
    context = LC_HEADING_LEVEL_1 << (best > 5 ? 5 : best - 1);
    heading = (HeadingData*) Tokenizer_parse(self, context, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset + best - 1;
        for (i = 0; i < best; i++) {
            if (Tokenizer_emit_char(self, '='))
                return -1;
        }
        self->global ^= GL_HEADING;
        return 0;
    }
#ifdef IS_PY3K
    level = PyLong_FromSsize_t(heading->level);
#else
    level = PyInt_FromSsize_t(heading->level);
#endif
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
            if (Tokenizer_emit_char(self, '=')) {
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
    Py_ssize_t reset = self->head;
    int best, i, current, level, diff;
    HeadingData *after, *heading;
    PyObject *stack;

    self->head += 1;
    best = 1;
    while (Tokenizer_read(self, 0) == '=') {
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
                if (Tokenizer_emit_char(self, '='))
                    return NULL;
            }
        }
        self->head = reset + best - 1;
    }
    else {
        for (i = 0; i < best; i++) {
            if (Tokenizer_emit_char(self, '=')) {
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
    PyObject *kwargs, *charobj, *textobj;
    Unicode this;
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
    this = Tokenizer_read(self, 0);
    if (!this) {
        Tokenizer_fail_route(self);
        return 0;
    }
    if (this == '#') {
        numeric = 1;
        if (Tokenizer_emit(self, HTMLEntityNumeric))
            return -1;
        self->head++;
        this = Tokenizer_read(self, 0);
        if (!this) {
            Tokenizer_fail_route(self);
            return 0;
        }
        if (this == 'x' || this == 'X') {
            hexadecimal = 1;
            kwargs = PyDict_New();
            if (!kwargs)
                return -1;
            if (!(charobj = PyUnicode_FROM_SINGLE(this))) {
                Py_DECREF(kwargs);
                return -1;
            }
            PyDict_SetItemString(kwargs, "char", charobj);
            Py_DECREF(charobj);
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
        this = Tokenizer_read(self, 0);
        if (this == ';') {
            if (i == 0)
                FAIL_ROUTE_AND_EXIT()
            break;
        }
        if (i == 0 && this == '0') {
            zeroes++;
            self->head++;
            continue;
        }
        if (i >= MAX_ENTITY_SIZE)
            FAIL_ROUTE_AND_EXIT()
        if (is_marker(this))
            FAIL_ROUTE_AND_EXIT()
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
        if (Tokenizer_emit_char(self, '&'))
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
    Unicode this;

    self->head += 4;
    if (Tokenizer_push(self, 0))
        return -1;
    while (1) {
        this = Tokenizer_read(self, 0);
        if (!this) {
            comment = Tokenizer_pop(self);
            Py_XDECREF(comment);
            self->head = reset;
            return Tokenizer_emit_text(self, "<!--");
        }
        if (this == '-' && Tokenizer_read(self, 1) == this &&
                            Tokenizer_read(self, 2) == '>') {
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
            if (self->topstack->context & LC_FAIL_NEXT) {
                /* _verify_safe() sets this flag while parsing a template or
                   link when it encounters what might be a comment -- we must
                   unset it to let _verify_safe() know it was correct: */
                self->topstack->context ^= LC_FAIL_NEXT;
            }
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
    PyObject *tokens, *kwargs, *tmp, *pad_first, *pad_before_eq, *pad_after_eq;

    if (data->context & TAG_QUOTED) {
        kwargs = PyDict_New();
        if (!kwargs)
            return -1;
        tmp = PyUnicode_FROM_SINGLE(data->quoter);
        if (!tmp)
            return -1;
        PyDict_SetItemString(kwargs, "char", tmp);
        Py_DECREF(tmp);
        if (Tokenizer_emit_first_kwargs(self, TagAttrQuote, kwargs))
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
static int Tokenizer_handle_tag_space(
    Tokenizer* self, TagData* data, Unicode text)
{
    uint64_t ctx = data->context;
    uint64_t end_of_value = (ctx & TAG_ATTR_VALUE &&
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
        if (Textbuffer_write(data->pad_before_eq, text))
            return -1;
    }
    if (ctx & TAG_QUOTED && !(ctx & TAG_NOTE_SPACE)) {
        if (Tokenizer_emit_char(self, text))
            return -1;
    }
    else if (data->context & TAG_ATTR_READY)
        return Textbuffer_write(data->pad_first, text);
    else if (data->context & TAG_ATTR_VALUE)
        return Textbuffer_write(data->pad_after_eq, text);
    return 0;
}

/*
    Handle regular text inside of an HTML open tag.
*/
static int Tokenizer_handle_tag_text(Tokenizer* self, Unicode text)
{
    Unicode next = Tokenizer_read(self, 1);

    if (!is_marker(text) || !Tokenizer_CAN_RECURSE(self))
        return Tokenizer_emit_char(self, text);
    else if (text == next && next == '{')
        return Tokenizer_parse_template_or_argument(self);
    else if (text == next && next == '[')
        return Tokenizer_parse_wikilink(self);
    else if (text == '<')
        return Tokenizer_parse_tag(self);
    return Tokenizer_emit_char(self, text);
}

/*
    Handle all sorts of text data inside of an HTML open tag.
*/
static int Tokenizer_handle_tag_data(
    Tokenizer* self, TagData* data, Unicode chunk)
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
        if (chunk == '=') {
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
    else {  // data->context & TAG_ATTR_VALUE assured
        escaped = (Tokenizer_read_backwards(self, 1) == '\\' &&
                   Tokenizer_read_backwards(self, 2) != '\\');
        if (data->context & TAG_NOTE_QUOTE) {
            data->context ^= TAG_NOTE_QUOTE;
            if ((chunk == '"' || chunk == '\'') && !escaped) {
                data->context |= TAG_QUOTED;
                data->quoter = chunk;
                data->reset = self->head;
                if (Tokenizer_push(self, self->topstack->context))
                    return -1;
                return 0;
            }
        }
        else if (data->context & TAG_QUOTED) {
            if (chunk == data->quoter && !escaped) {
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
                so = strip_tag_name(first, 1);
                sc = strip_tag_name(
                    PyList_GET_ITEM(self->topstack->stack, 1), 1);
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
    Textbuffer* buffer;
    PyObject *buf_tmp, *end_tag, *start_tag;
    Unicode this, next;
    Py_ssize_t reset;
    int cmp;

    while (1) {
        this = Tokenizer_read(self, 0);
        next = Tokenizer_read(self, 1);
        if (!this)
            return Tokenizer_fail_route(self);
        else if (this == '<' && next == '/') {
            self->head += 2;
            reset = self->head - 1;
            buffer = Textbuffer_new(&self->text);
            if (!buffer)
                return NULL;
            while ((this = Tokenizer_read(self, 0)), 1) {
                if (this == '>') {
                    buf_tmp = Textbuffer_render(buffer);
                    if (!buf_tmp)
                        return NULL;
                    end_tag = strip_tag_name(buf_tmp, 0);
                    Py_DECREF(buf_tmp);
                    if (!end_tag)
                        return NULL;
                    start_tag = strip_tag_name(
                        PyList_GET_ITEM(self->topstack->stack, 1), 1);
                    if (!start_tag)
                        return NULL;
                    cmp = PyUnicode_Compare(start_tag, end_tag);
                    Py_DECREF(end_tag);
                    Py_DECREF(start_tag);
                    if (cmp)
                        goto no_matching_end;
                    if (Tokenizer_emit(self, TagOpenClose))
                        return NULL;
                    if (Tokenizer_emit_textbuffer(self, buffer))
                        return NULL;
                    if (Tokenizer_emit(self, TagCloseClose))
                        return NULL;
                    return Tokenizer_pop(self);
                }
                if (!this || this == '\n') {
                    no_matching_end:
                    Textbuffer_dealloc(buffer);
                    self->head = reset;
                    if (Tokenizer_emit_text(self, "</"))
                        return NULL;
                    break;
                }
                Textbuffer_write(buffer, this);
                self->head++;
            }
        }
        else if (this == '&') {
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
    int depth = 1, is_instance;

    len = PyList_GET_SIZE(self->topstack->stack);
    for (index = 2; index < len; index++) {
        token = PyList_GET_ITEM(self->topstack->stack, index);
        is_instance = PyObject_IsInstance(token, TagOpenOpen);
        if (is_instance == -1)
            return NULL;
        else if (is_instance == 1)
            depth++;
        is_instance = PyObject_IsInstance(token, TagCloseOpen);
        if (is_instance == -1)
            return NULL;
        else if (is_instance == 1) {
            depth--;
            if (depth == 0)
                break;
        }
    }
    if (!token || depth > 0)
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
    TagData *data = TagData_new(&self->text);
    PyObject *token, *text, *trash;
    Unicode this, next;
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
        this = Tokenizer_read(self, 0);
        next = Tokenizer_read(self, 1);
        can_exit = (!(data->context & (TAG_QUOTED | TAG_NAME)) ||
                    data->context & TAG_NOTE_SPACE);
        if (!this) {
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
        else if (this == '>' && can_exit) {
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
            if (is_single_only(text)) {
                Py_DECREF(text);
                return Tokenizer_handle_single_only_tag_end(self);
            }
            if (is_parsable(text)) {
                Py_DECREF(text);
                return Tokenizer_parse(self, 0, 0);
            }
            Py_DECREF(text);
            return Tokenizer_handle_blacklisted_tag(self);
        }
        else if (this == '/' && next == '>' && can_exit) {
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
    Unicode this;

    self->head += 2;
    buf = Textbuffer_new(&self->text);
    if (!buf)
        return -1;
    while (1) {
        this = Tokenizer_read(self, pos);
        if (Py_UNICODE_ISSPACE(this) || is_marker(this)) {
            name = Textbuffer_render(buf);
            if (!name) {
                Textbuffer_dealloc(buf);
                return -1;
            }
            if (!is_single_only(name))
                FAIL_ROUTE(0);
            Py_DECREF(name);
            break;
        }
        Textbuffer_write(buf, this);
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
        return Tokenizer_emit_char(self, '<');
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
    uint64_t context;
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
            return Tokenizer_emit_char(self, '\'') ? -1 : 1;
        if (self->topstack->context & LC_STYLE_ITALICS) {
            self->topstack->context |= LC_STYLE_PASS_AGAIN;
            return Tokenizer_emit_text(self, "'''");
        }
        if (Tokenizer_emit_char(self, '\''))
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
    uint64_t context = self->topstack->context, ticks = 2, i;

    self->head += 2;
    while (Tokenizer_read(self, 0) == '\'') {
        self->head++;
        ticks++;
    }
    if (ticks > 5) {
        for (i = 0; i < ticks - 5; i++) {
            if (Tokenizer_emit_char(self, '\''))
                return NULL;
        }
        ticks = 5;
    }
    else if (ticks == 4) {
        if (Tokenizer_emit_char(self, '\''))
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
                if (Tokenizer_emit_char(self, '\''))
                    return NULL;
                return Tokenizer_pop(self);
            }
            if (context & LC_STYLE_ITALICS)
                self->topstack->context |= LC_STYLE_PASS_AGAIN;
        }
        for (i = 0; i < ticks; i++) {
            if (Tokenizer_emit_char(self, '\''))
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
    PyObject *kwargs, *markup;
    Unicode code = Tokenizer_read(self, 0);

    if (code == ';')
        self->topstack->context |= LC_DLTERM;
    kwargs = PyDict_New();
    if (!kwargs)
        return -1;
    if (!(markup = PyUnicode_FROM_SINGLE(code))) {
        Py_DECREF(kwargs);
        return -1;
    }
    PyDict_SetItemString(kwargs, "wiki_markup", markup);
    Py_DECREF(markup);
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
    Unicode marker = Tokenizer_read(self, 1);

    if (Tokenizer_handle_list_marker(self))
        return -1;
    while (marker == '#' || marker == '*' || marker == ';' ||
           marker == ':') {
        self->head++;
        if (Tokenizer_handle_list_marker(self))
            return -1;
        marker = Tokenizer_read(self, 1);
    }
    return 0;
}

/*
    Handle a wiki-style horizontal rule (----) in the string.
*/
static int Tokenizer_handle_hr(Tokenizer* self)
{
    PyObject *markup, *kwargs;
    Textbuffer *buffer = Textbuffer_new(&self->text);
    int i;

    if (!buffer)
        return -1;
    self->head += 3;
    for (i = 0; i < 4; i++) {
        if (Textbuffer_write(buffer, '-'))
            return -1;
    }
    while (Tokenizer_read(self, 1) == '-') {
        if (Textbuffer_write(buffer, '-'))
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
    if (Tokenizer_read(self, 0) == ':')
        return Tokenizer_handle_list_marker(self);
    return Tokenizer_emit_char(self, '\n');
}

/*
    Emit a table tag.
*/
static int
Tokenizer_emit_table_tag(Tokenizer* self, const char* open_open_markup,
                         const char* tag, PyObject* style, PyObject* padding,
                         const char* close_open_markup, PyObject* contents,
                         const char* open_close_markup)
{
    PyObject *open_open_kwargs, *open_open_markup_unicode, *close_open_kwargs,
             *close_open_markup_unicode, *open_close_kwargs,
             *open_close_markup_unicode;

    open_open_kwargs = PyDict_New();
    if (!open_open_kwargs)
        goto fail_decref_all;
    open_open_markup_unicode = PyUnicode_FromString(open_open_markup);
    if (!open_open_markup_unicode) {
        Py_DECREF(open_open_kwargs);
        goto fail_decref_all;
    }
    PyDict_SetItemString(open_open_kwargs, "wiki_markup",
                         open_open_markup_unicode);
    Py_DECREF(open_open_markup_unicode);
    if (Tokenizer_emit_kwargs(self, TagOpenOpen, open_open_kwargs))
        goto fail_decref_all;
    if (Tokenizer_emit_text(self, tag))
        goto fail_decref_all;

    if (style) {
        if (Tokenizer_emit_all(self, style))
            goto fail_decref_all;
        Py_DECREF(style);
    }

    close_open_kwargs = PyDict_New();
    if (!close_open_kwargs)
        goto fail_decref_padding_contents;
    if (close_open_markup && strlen(close_open_markup) != 0) {
        close_open_markup_unicode = PyUnicode_FromString(close_open_markup);
        if (!close_open_markup_unicode) {
            Py_DECREF(close_open_kwargs);
            goto fail_decref_padding_contents;
        }
        PyDict_SetItemString(close_open_kwargs, "wiki_markup",
                             close_open_markup_unicode);
        Py_DECREF(close_open_markup_unicode);
    }
    PyDict_SetItemString(close_open_kwargs, "padding", padding);
    Py_DECREF(padding);
    if (Tokenizer_emit_kwargs(self, TagCloseOpen, close_open_kwargs))
        goto fail_decref_contents;

    if (contents) {
        if (Tokenizer_emit_all(self, contents))
            goto fail_decref_contents;
        Py_DECREF(contents);
    }

    open_close_kwargs = PyDict_New();
    if (!open_close_kwargs)
        return -1;
    open_close_markup_unicode = PyUnicode_FromString(open_close_markup);
    if (!open_close_markup_unicode) {
        Py_DECREF(open_close_kwargs);
        return -1;
    }
    PyDict_SetItemString(open_close_kwargs, "wiki_markup",
                         open_close_markup_unicode);
    Py_DECREF(open_close_markup_unicode);
    if (Tokenizer_emit_kwargs(self, TagOpenClose, open_close_kwargs))
        return -1;
    if (Tokenizer_emit_text(self, tag))
        return -1;
    if (Tokenizer_emit(self, TagCloseClose))
        return -1;
    return 0;

    fail_decref_all:
    Py_XDECREF(style);
    fail_decref_padding_contents:
    Py_DECREF(padding);
    fail_decref_contents:
    Py_DECREF(contents);
    return -1;
}

/*
    Handle style attributes for a table until an ending token.
*/
static PyObject* Tokenizer_handle_table_style(Tokenizer* self, Unicode end_token)
{
    TagData *data = TagData_new(&self->text);
    PyObject *padding, *trash;
    Unicode this;
    int can_exit;

    if (!data)
        return NULL;
    data->context = TAG_ATTR_READY;

    while (1) {
        this = Tokenizer_read(self, 0);
        can_exit = (!(data->context & TAG_QUOTED) || data->context & TAG_NOTE_SPACE);
        if (this == end_token && can_exit) {
            if (data->context & (TAG_ATTR_NAME | TAG_ATTR_VALUE)) {
                if (Tokenizer_push_tag_buffer(self, data)) {
                    TagData_dealloc(data);
                    return NULL;
                }
            }
            if (Py_UNICODE_ISSPACE(this))
                Textbuffer_write(data->pad_first, this);
            padding = Textbuffer_render(data->pad_first);
            TagData_dealloc(data);
            if (!padding)
                return NULL;
            return padding;
        }
        else if (!this || this == end_token) {
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
    Parse a wikicode table by starting with the first line.
*/
static int Tokenizer_parse_table(Tokenizer* self)
{
    Py_ssize_t reset = self->head;
    PyObject *style, *padding;
    PyObject *table = NULL;
    self->head += 2;

    if(Tokenizer_push(self, LC_TABLE_OPEN))
        return -1;
    padding = Tokenizer_handle_table_style(self, '\n');
    if (BAD_ROUTE) {
        RESET_ROUTE();
        self->head = reset;
        if (Tokenizer_emit_char(self, '{'))
            return -1;
        return 0;
    }
    if (!padding)
        return -1;
    style = Tokenizer_pop(self);
    if (!style) {
        Py_DECREF(padding);
        return -1;
    }

    self->head++;
    table = Tokenizer_parse(self, LC_TABLE_OPEN, 1);
    if (BAD_ROUTE) {
        RESET_ROUTE();
        Py_DECREF(padding);
        Py_DECREF(style);
        self->head = reset;
        if (Tokenizer_emit_char(self, '{'))
            return -1;
        return 0;
    }
    if (!table) {
        Py_DECREF(padding);
        Py_DECREF(style);
        return -1;
    }

    if (Tokenizer_emit_table_tag(self, "{|", "table", style, padding, NULL,
                                 table, "|}"))
        return -1;
    // Offset displacement done by _parse()
    self->head--;
    return 0;
}

/*
    Parse as style until end of the line, then continue.
*/
static int Tokenizer_handle_table_row(Tokenizer* self)
{
    PyObject *padding, *style, *row, *trash;
    self->head += 2;

    if (!Tokenizer_CAN_RECURSE(self)) {
        if (Tokenizer_emit_text(self, "|-"))
            return -1;
        self->head -= 1;
        return 0;
    }

    if(Tokenizer_push(self, LC_TABLE_OPEN | LC_TABLE_ROW_OPEN))
        return -1;
    padding = Tokenizer_handle_table_style(self, '\n');
    if (BAD_ROUTE) {
        trash = Tokenizer_pop(self);
        Py_XDECREF(trash);
        return 0;
    }
    if (!padding)
        return -1;
    style = Tokenizer_pop(self);
    if (!style) {
        Py_DECREF(padding);
        return -1;
    }

    // Don't parse the style separator
    self->head++;
    row = Tokenizer_parse(self, LC_TABLE_OPEN | LC_TABLE_ROW_OPEN, 1);
    if (!row) {
        Py_DECREF(padding);
        Py_DECREF(style);
        return -1;
    }

    if (Tokenizer_emit_table_tag(self, "|-", "tr", style, padding, NULL, row, ""))
        return -1;
    // Offset displacement done by _parse()
    self->head--;
    return 0;
}

/*
    Parse as normal syntax unless we hit a style marker, then parse style
    as HTML attributes and the remainder as normal syntax.
*/
static int
Tokenizer_handle_table_cell(Tokenizer* self, const char *markup,
                            const char *tag, uint64_t line_context)
{
    uint64_t old_context = self->topstack->context;
    uint64_t cell_context;
    Py_ssize_t reset;
    PyObject *padding, *cell, *style = NULL;
    const char *close_open_markup = NULL;

    self->head += strlen(markup);
    reset = self->head;

    if (!Tokenizer_CAN_RECURSE(self)) {
        if (Tokenizer_emit_text(self, markup))
            return -1;
        self->head--;
        return 0;
    }

    cell = Tokenizer_parse(self, LC_TABLE_OPEN | LC_TABLE_CELL_OPEN |
                           LC_TABLE_CELL_STYLE | line_context, 1);
    if (!cell)
        return -1;
    cell_context = self->topstack->context;
    self->topstack->context = old_context;

    if (cell_context & LC_TABLE_CELL_STYLE) {
        Py_DECREF(cell);
        self->head = reset;
        if(Tokenizer_push(self, LC_TABLE_OPEN | LC_TABLE_CELL_OPEN |
                          line_context))
            return -1;
        padding = Tokenizer_handle_table_style(self, '|');
        if (!padding)
            return -1;
        style = Tokenizer_pop(self);
        if (!style) {
            Py_DECREF(padding);
            return -1;
        }
        // Don't parse the style separator
        self->head++;
        cell = Tokenizer_parse(self, LC_TABLE_OPEN | LC_TABLE_CELL_OPEN |
                               line_context, 1);
        if (!cell) {
            Py_DECREF(padding);
            Py_DECREF(style);
            return -1;
        }
        cell_context = self->topstack->context;
        self->topstack->context = old_context;
    }
    else {
        padding = PyUnicode_FromString("");
        if (!padding) {
            Py_DECREF(cell);
            return -1;
        }
    }

    if (style) {
        close_open_markup = "|";
    }
    if (Tokenizer_emit_table_tag(self, markup, tag, style, padding,
                                 close_open_markup, cell, ""))
        return -1;
    // Keep header/cell line contexts
    self->topstack->context |= cell_context & (LC_TABLE_TH_LINE | LC_TABLE_TD_LINE);
    // Offset displacement done by parse()
    self->head--;
    return 0;
}

/*
    Returns the context, stack, and whether to reset the cell for style
    in a tuple.
*/
static PyObject*
Tokenizer_handle_table_cell_end(Tokenizer* self, int reset_for_style)
{
    if (reset_for_style)
        self->topstack->context |= LC_TABLE_CELL_STYLE;
    else
        self->topstack->context &= ~LC_TABLE_CELL_STYLE;
    return Tokenizer_pop_keeping_context(self);
}

/*
    Return the stack in order to handle the table row end.
*/
static PyObject* Tokenizer_handle_table_row_end(Tokenizer* self)
{
    return Tokenizer_pop(self);
}

/*
    Return the stack in order to handle the table end.
*/
static PyObject* Tokenizer_handle_table_end(Tokenizer* self)
{
    self->head += 2;
    return Tokenizer_pop(self);
}

/*
    Handle the end of the stream of wikitext.
*/
static PyObject* Tokenizer_handle_end(Tokenizer* self, uint64_t context)
{
    PyObject *token, *text, *trash;
    int single;

    if (context & AGG_FAIL) {
        if (context & LC_TAG_BODY) {
            token = PyList_GET_ITEM(self->topstack->stack, 1);
            text = PyObject_GetAttrString(token, "text");
            if (!text)
                return NULL;
            single = is_single(text);
            Py_DECREF(text);
            if (single)
                return Tokenizer_handle_single_tag_end(self);
        }
        else {
            if (context & LC_TABLE_CELL_OPEN) {
                trash = Tokenizer_pop(self);
                Py_XDECREF(trash);
                context = self->topstack->context;
            }
            if (context & AGG_DOUBLE) {
                trash = Tokenizer_pop(self);
                Py_XDECREF(trash);
            }
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
Tokenizer_verify_safe(Tokenizer* self, uint64_t context, Unicode data)
{
    if (context & LC_FAIL_NEXT)
        return -1;
    if (context & LC_WIKILINK_TITLE) {
        if (data == ']' || data == '{') {
            self->topstack->context |= LC_FAIL_NEXT;
        } else if (data == '\n' || data == '[' || data == '}' || data == '>') {
            return -1;
        } else if (data == '<') {
            if (Tokenizer_read(self, 1) == '!')
                self->topstack->context |= LC_FAIL_NEXT;
            else
                return -1;
        }
        return 0;
    }
    if (context & LC_EXT_LINK_TITLE)
        return (data == '\n') ? -1 : 0;
    if (context & LC_TAG_CLOSE)
        return (data == '<') ? -1 : 0;
    if (context & LC_TEMPLATE_NAME) {
        if (data == '{') {
            self->topstack->context |= LC_HAS_TEMPLATE | LC_FAIL_NEXT;
            return 0;
        }
        if (data == '}' || (data == '<' && Tokenizer_read(self, 1) == '!')) {
            self->topstack->context |= LC_FAIL_NEXT;
            return 0;
        }
        if (data == '[' || data == ']' || data == '<' || data == '>') {
            return -1;
        }
        if (data == '|')
            return 0;
        if (context & LC_HAS_TEXT) {
            if (context & LC_FAIL_ON_TEXT) {
                if (!Py_UNICODE_ISSPACE(data))
                    return -1;
            }
            else if (data == '\n')
                self->topstack->context |= LC_FAIL_ON_TEXT;
        }
        else if (!Py_UNICODE_ISSPACE(data))
            self->topstack->context |= LC_HAS_TEXT;
    }
    else {
        if (context & LC_FAIL_ON_EQUALS) {
            if (data == '=') {
                return -1;
            }
        }
        else if (context & LC_FAIL_ON_LBRACE) {
            if (data == '{' || (Tokenizer_read_backwards(self, 1) == '{' &&
                                Tokenizer_read_backwards(self, 2) == '{')) {
                if (context & LC_TEMPLATE)
                    self->topstack->context |= LC_FAIL_ON_EQUALS;
                else
                    self->topstack->context |= LC_FAIL_NEXT;
                return 0;
            }
            self->topstack->context ^= LC_FAIL_ON_LBRACE;
        }
        else if (context & LC_FAIL_ON_RBRACE) {
            if (data == '}') {
                self->topstack->context |= LC_FAIL_NEXT;
                return 0;
            }
            self->topstack->context ^= LC_FAIL_ON_RBRACE;
        }
        else if (data == '{')
            self->topstack->context |= LC_FAIL_ON_LBRACE;
        else if (data == '}')
            self->topstack->context |= LC_FAIL_ON_RBRACE;
    }
    return 0;
}

/*
    Returns whether the current head has leading whitespace.
    TODO: treat comments and templates as whitespace, allow fail on non-newline spaces.
*/
static int Tokenizer_has_leading_whitespace(Tokenizer* self)
{
    int offset = 1;
    Unicode current_character;
    while (1) {
        current_character = Tokenizer_read_backwards(self, offset);
        if (!current_character || current_character == '\n')
            return 1;
        else if (!Py_UNICODE_ISSPACE(current_character))
            return 0;
        offset++;
    }
}

/*
    Parse the wikicode string, using context for when to stop. If push is true,
    we will push a new context, otherwise we won't and context will be ignored.
*/
PyObject* Tokenizer_parse(Tokenizer* self, uint64_t context, int push)
{
    uint64_t this_context;
    Unicode this, next, next_next, last;
    PyObject* temp;

    if (push) {
        if (Tokenizer_push(self, context))
            return NULL;
    }
    while (1) {
        this = Tokenizer_read(self, 0);
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
        if (!this)
            return Tokenizer_handle_end(self, this_context);
        next = Tokenizer_read(self, 1);
        last = Tokenizer_read_backwards(self, 1);
        if (this == next && next == '{') {
            if (Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_template_or_argument(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == '|' && this_context & LC_TEMPLATE) {
            if (Tokenizer_handle_template_param(self))
                return NULL;
        }
        else if (this == '=' && this_context & LC_TEMPLATE_PARAM_KEY) {
            if (Tokenizer_handle_template_param_value(self))
                return NULL;
        }
        else if (this == next && next == '}' && this_context & LC_TEMPLATE)
            return Tokenizer_handle_template_end(self);
        else if (this == '|' && this_context & LC_ARGUMENT_NAME) {
            if (Tokenizer_handle_argument_separator(self))
                return NULL;
        }
        else if (this == next && next == '}' && this_context & LC_ARGUMENT) {
            if (Tokenizer_read(self, 2) == '}') {
                return Tokenizer_handle_argument_end(self);
            }
            if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == next && next == '[' && Tokenizer_CAN_RECURSE(self)) {
            if (!(this_context & AGG_NO_WIKILINKS)) {
                if (Tokenizer_parse_wikilink(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == '|' && this_context & LC_WIKILINK_TITLE) {
            if (Tokenizer_handle_wikilink_separator(self))
                return NULL;
        }
        else if (this == next && next == ']' && this_context & LC_WIKILINK)
            return Tokenizer_handle_wikilink_end(self);
        else if (this == '[') {
            if (Tokenizer_parse_external_link(self, 1))
                return NULL;
        }
        else if (this == ':' && !is_marker(last)) {
            if (Tokenizer_parse_external_link(self, 0))
                return NULL;
        }
        else if (this == ']' && this_context & LC_EXT_LINK_TITLE)
            return Tokenizer_pop(self);
        else if (this == '=' && !(self->global & GL_HEADING)) {
            if (!last || last == '\n') {
                if (Tokenizer_parse_heading(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == '=' && this_context & LC_HEADING)
            return (PyObject*) Tokenizer_handle_heading_end(self);
        else if (this == '\n' && this_context & LC_HEADING)
            return Tokenizer_fail_route(self);
        else if (this == '&') {
            if (Tokenizer_parse_entity(self))
                return NULL;
        }
        else if (this == '<' && next == '!') {
            next_next = Tokenizer_read(self, 2);
            if (next_next == Tokenizer_read(self, 3) && next_next == '-') {
                if (Tokenizer_parse_comment(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == '<' && next == '/' && Tokenizer_read(self, 2)) {
            if (this_context & LC_TAG_BODY ?
                Tokenizer_handle_tag_open_close(self) :
                Tokenizer_handle_invalid_tag_start(self))
                return NULL;
        }
        else if (this == '<' && !(this_context & LC_TAG_CLOSE)) {
            if (Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_tag(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this == '>' && this_context & LC_TAG_CLOSE)
            return Tokenizer_handle_tag_close_close(self);
        else if (this == next && next == '\'' && !self->skip_style_tags) {
            temp = Tokenizer_parse_style(self);
            if (temp != Py_None)
                return temp;
        }
        else if ((!last || last == '\n') && (this == '#' || this == '*' || this == ';' || this == ':')) {
            if (Tokenizer_handle_list(self))
                return NULL;
        }
        else if ((!last || last == '\n') && (this == '-' && this == next &&
                 this == Tokenizer_read(self, 2) &&
                 this == Tokenizer_read(self, 3))) {
            if (Tokenizer_handle_hr(self))
                return NULL;
        }
        else if ((this == '\n' || this == ':') && this_context & LC_DLTERM) {
            if (Tokenizer_handle_dl_term(self))
                return NULL;
            // Kill potential table contexts
            if (this == '\n')
                self->topstack->context &= ~LC_TABLE_CELL_LINE_CONTEXTS;
        }

        // Start of table parsing
        else if (this == '{' && next == '|' && Tokenizer_has_leading_whitespace(self)) {
            if (Tokenizer_CAN_RECURSE(self)) {
                if (Tokenizer_parse_table(self))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
        }
        else if (this_context & LC_TABLE_OPEN) {
            if (this == '|' && next == '|' && this_context & LC_TABLE_TD_LINE) {
                if (this_context & LC_TABLE_CELL_OPEN)
                    return Tokenizer_handle_table_cell_end(self, 0);
                else if (Tokenizer_handle_table_cell(self, "||", "td", LC_TABLE_TD_LINE))
                    return NULL;
            }
            else if (this == '|' && next == '|' && this_context & LC_TABLE_TH_LINE) {
                if (this_context & LC_TABLE_CELL_OPEN)
                    return Tokenizer_handle_table_cell_end(self, 0);
                else if (Tokenizer_handle_table_cell(self, "||", "th", LC_TABLE_TH_LINE))
                    return NULL;
            }
            else if (this == '!' && next == '!' && this_context & LC_TABLE_TH_LINE) {
                if (this_context & LC_TABLE_CELL_OPEN)
                    return Tokenizer_handle_table_cell_end(self, 0);
                else if (Tokenizer_handle_table_cell(self, "!!", "th", LC_TABLE_TH_LINE))
                    return NULL;
            }
            else if (this == '|' && this_context & LC_TABLE_CELL_STYLE) {
                return Tokenizer_handle_table_cell_end(self, 1);
            }
            // On newline, clear out cell line contexts
            else if (this == '\n' && this_context & LC_TABLE_CELL_LINE_CONTEXTS) {
                self->topstack->context &= ~LC_TABLE_CELL_LINE_CONTEXTS;
                if (Tokenizer_emit_char(self, this))
                    return NULL;
            }
            else if (Tokenizer_has_leading_whitespace(self)) {
                if (this == '|' && next == '}') {
                    if (this_context & LC_TABLE_CELL_OPEN)
                        return Tokenizer_handle_table_cell_end(self, 0);
                    if (this_context & LC_TABLE_ROW_OPEN)
                        return Tokenizer_handle_table_row_end(self);
                    else
                        return Tokenizer_handle_table_end(self);
                }
                else if (this == '|' && next == '-') {
                    if (this_context & LC_TABLE_CELL_OPEN)
                        return Tokenizer_handle_table_cell_end(self, 0);
                    if (this_context & LC_TABLE_ROW_OPEN)
                        return Tokenizer_handle_table_row_end(self);
                    else if (Tokenizer_handle_table_row(self))
                        return NULL;
                }
                else if (this == '|') {
                    if (this_context & LC_TABLE_CELL_OPEN)
                        return Tokenizer_handle_table_cell_end(self, 0);
                    else if (Tokenizer_handle_table_cell(self, "|", "td", LC_TABLE_TD_LINE))
                        return NULL;
                }
                else if (this == '!') {
                    if (this_context & LC_TABLE_CELL_OPEN)
                        return Tokenizer_handle_table_cell_end(self, 0);
                    else if (Tokenizer_handle_table_cell(self, "!", "th", LC_TABLE_TH_LINE))
                        return NULL;
                }
                else if (Tokenizer_emit_char(self, this))
                    return NULL;
            }
            else if (Tokenizer_emit_char(self, this))
                return NULL;
            // Raise BadRoute to table start
            if (BAD_ROUTE)
                return NULL;
        }
        else if (Tokenizer_emit_char(self, this))
            return NULL;
        self->head++;
    }
}

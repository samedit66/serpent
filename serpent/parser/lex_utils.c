#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "./include/strbuf.h"
#include "./include/strlist.h"

void
remove_underscores(char *str_num) {
    int i, j;
    i = j = 0;

    while (str_num[i]) {
        if (str_num[i] == '_') {
            i++;
            continue;
        }

        str_num[j++] = str_num[i++];
    }

    str_num[j] = '\0';
}

void
parse_int(char *str_num, int64_t *int_num, int base) {
    int offset = 0;
    switch (base) {
        case 2:
        case 8:
        case 16:
            offset = 2;
    }

    remove_underscores(str_num);

    *int_num = strtol(str_num + offset, NULL, base);
}

void
parse_real(char *str_num, double *real_num) {
    *real_num = strtod(str_num, NULL);
}

char 
convert_decimal_encoded_char(char *encoded_ch) {
    return (char) atoi(encoded_ch + 2);
}

bool
is_delim(int ch) { 
    static char *delims = " \n\t*/\\-+:;,.()[]{}^<>=";
    return strchr(delims, ch) != NULL;
}

bool
is_end(int ch) {
    return ch == EOF || ch == '\0';
}

bool
is_oct_digit(int ch) {
    return '0' <= ch && ch <= '7';
}

bool
is_bin_digit(int ch) {
    return ch == '0' || ch == '1';
}

bool
is_possible_part_of_integer(int ch, int base) {
    switch (base) {
        case 10:
            return '0' <= ch && ch <= '9';
        case 2:
            return is_bin_digit(ch);
        case 8:
            return is_oct_digit(ch);
        case 16:
            return isxdigit(ch);
    }

    return ch == '_';
}

bool
is_possible_part_of_real(int ch) {
    return ch == 'e' || ch == '.' || (ch != '_' && is_possible_part_of_integer(ch, 10));
}

char*
escape(char *str) {
    if (!str) return NULL;

    StringBuffer *strbuf = StringBuffer_empty();
    int len = strlen(str);
    for (int i = 0; i < len; i++, str++) {
        switch (*str) {
            // case '\0': StringBuffer_append(strbuf, "\\0");  break;
            // case '\a': StringBuffer_append(strbuf, "\\a");  break;
            case '\b': StringBuffer_append(strbuf, "\\b");  break;
            case '\f': StringBuffer_append(strbuf, "\\f");  break;
            case '\n': StringBuffer_append(strbuf, "\\n");  break;
            case '\r': StringBuffer_append(strbuf, "\\r");  break;
            case '\t': StringBuffer_append(strbuf, "\\t");  break;
            // case '\v': StringBuffer_append(strbuf, "\\v");  break;
            case '\\': StringBuffer_append(strbuf, "\\\\"); break;
            case '/': StringBuffer_append(strbuf, "\\/"); break;
            // case '\?': StringBuffer_append(strbuf, "\\\?"); break;
            // case '\'': StringBuffer_append(strbuf, "\\\'"); break;
            case '\"': StringBuffer_append(strbuf, "\\\""); break;
            default:
                // Код ниже был закомментирован в процессе реализации поддержки
                // utf8 для идентификаторов и строк. Возникла проблема при
                // добавлении кириллицы, т.к. символы двухбайтные,
                // isprint(*str) была ложной, из-за этого искажались символы.
                // Когда-нибудь будет пофикшено...
                /*
                if (isprint(*str)) {
                    StringBuffer_append_char(strbuf, *str);
                }
                else {
                    // Потенциально способно вызвать segfault, в силу того
                    // что добавление символов идет в обход любого append...
                    int size = sprintf(strbuf->buffer, "\\%03o", *str);
                    strbuf->size += size;
                }
                */
                StringBuffer_append_char(strbuf, *str);
                break;
        }
    }

    return StringBuffer_extract_string(strbuf);
}

static inline int
left_space_count(const char *str) {
    return strspn(str, " \t");
}

static inline void
shift_left(char *str, int shift_size) {
    int len = strlen(str);

    int i;
    for (i = 0; i + shift_size < len; i++) {
        str[i] = str[i + shift_size];
    }

    str[i] = '\0';
}

void
adjust_unaligned_verbatim_string(const StringList *verbatim_str) {
    int lines_count = StringList_size(verbatim_str);
    if (lines_count == 0)
        return;

    // 1) Определяем наименьшее кол-во пробелов в начале строки
    int min_space_count, current_space_count;

    min_space_count = left_space_count(StringList_get(verbatim_str, 0));
    if (min_space_count == 0) {
        return;
    }

    for (int i = 1; i < lines_count; i++) {
        current_space_count = left_space_count(StringList_get(verbatim_str, i));

        if (current_space_count < min_space_count)
            min_space_count = current_space_count;
    }

    // 2) Удаляем наименьшее кол-во пробелов из каждой строки
    for (int i = 0; i < lines_count; i++) {
        shift_left(StringList_get(verbatim_str, i), min_space_count);
    }
}   

// Взято из: https://stackoverflow.com/a/61692729
int
strlen_utf8(const char *utf8_str) {
    int len = 0;
    for (int i = 0; *utf8_str != 0; ++len) {
        int v01 = ((*utf8_str & 0x80) >> 7) & ((*utf8_str & 0x40) >> 6);
        int v2 = (*utf8_str & 0x20) >> 5;
        int v3 = (*utf8_str & 0x10) >> 4;
        utf8_str += 1 + ((v01 << v2) | (v01 & v3));
    }
    return len;
}

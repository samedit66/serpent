%{
    #include <ctype.h>
    #include <stdio.h>
    #include <stdint.h>
    #include <stdbool.h>
    #include <string.h>
    #include <ctype.h>

    #include "./include/lex_utils.h"
    #include "./include/strbuf.h"
    #include "./include/strlist.h"
    #include "eiffel.tab.h"

    #define yyterminate() return EOI

    #define YY_USER_ACTION \
        yylloc.first_line = yylloc.last_line; \
        yylloc.first_column = yylloc.last_column; \
        for (int i = 0; yytext[i] != '\0'; i++) { \
            if (yytext[i] == '\n') { \
                yylloc.last_line++; \
                yylloc.last_column = 0; \
            } \
            else { \
                yylloc.last_column++; \
            } \
        }

    #ifdef DEBUG_LEXER
        #define LOG_F(lineno, msg, ...) {\
            printf("Line %d: ", lineno);\
            printf(msg, __VA_ARGS__);\
        }
    #else
        #define LOG_F(lineno, msg, ...)
    #endif

    #define LOG_LEXEM_AT_LINENO(lineno, lexem_type, lexem)\
        LOG_F(lineno, "found %s: \"%s\"\n", lexem_type, lexem)

    #define LOG_LEXEM(lexem_type, lexem)\
        LOG_LEXEM_AT_LINENO(yylineno, lexem_type, lexem)

    #ifdef COLORFUL
        #define RED_TEXT "\033[31m%s\033[0m"
        #define UNDERSCORED_TEXT "\033[4m%s\033[0m"
    #else
        #define RED_TEXT "%s"
        #define UNDERSCORED_TEXT "%s"
    #endif
    
    #define ERROR_F(lineno, msg, ...) {\
        fprintf(stderr, "Lexer error, line %d: " RED_TEXT ": ", lineno, "error");\
        fprintf(stderr, msg, __VA_ARGS__);\
        fprintf(stderr, "\n");\
    }

    #define ERROR_AT_LINENO(lineno, msg)\
        fprintf(stderr, "Lexer error, line %d: " RED_TEXT ": %s\n", lineno, "error", msg)

    #define ERROR(msg) ERROR_AT_LINENO(yylineno, msg)

    #define SKIP_UNTIL_CHAR_IN(charset) { \
        char ch; \
        do { \
            ch = input(); \
            if (ch == '\n') yylineno++; \
        } while (!is_end(ch) && strchr((charset), ch) == NULL); \
    }

    #define SKIP_UNTIL_DELIMETER(current_ch) {\
        StringBuffer_clear(buf);\
        StringBuffer_append(buf, yytext);\
        char ch = (current_ch);\
        do {\
            StringBuffer_append_char(buf, ch);\
            ch = input();\
        } while (!is_end(ch) && !is_delim(ch));\
    }
%}

%option 8bit
%option noyywrap
%option yylineno
%option never-interactive
%option array


ALPHA      [A-Za-z]
U1         [\x80-\xbf]
U2         [\xc2-\xdf]
U3         [\xe0-\xef]
U4         [\xf0-\xf4]
UALPHA     ({ALPHA}|{U2}{U1}|{U3}{U1}{U1}|{U4}{U1}{U1}{U1})

IDENTIFIER (({UALPHA}|_)({UALPHA}|[_0-9])*)

WHITESPACE [ \n\t\r]+

DIGIT   [0-9]
INT_10  ({DIGIT}+_+)*{DIGIT}+

HEXIT    [0-9a-fA-F]
INT_16   0[xX]({HEXIT}+_+)*{HEXIT}+

OCTIT    [0-7]
INT_8    0[cCoO]({OCTIT}+_+)*{OCTIT}+

BINIT    [01]
INT_2    0[bB]({BINIT}+_+)*{BINIT}+

REAL_NUMBER_PART           {DIGIT}+
REAL_NUMBER                {REAL_NUMBER_PART}?\.{REAL_NUMBER_PART}|{REAL_NUMBER_PART}\.{REAL_NUMBER_PART}?
REAL_NUMBER_EXPONENT       ({REAL_NUMBER}|{REAL_NUMBER_PART})[eE][\-+]?{REAL_NUMBER_PART}


%x SINGLE_LINE_COMMENT
%x CHARACTER
%x STRING
%x VERBATIM_ALIGNED_STRING


%%

%{
    // Используется для хранения номера строки найденной лексемы (см. INT_10, INT_8 и все остальные числа)
    int line;

    // Хранит следующий символ (см. те же правила)
    char next;

    // Хранит считанное целое число
    int int_value;

    // Основание системы счисления для целого числа
    int base;

    // Хранит считанное дробное число
    double real_value;

    // Буффер для хранение комплексных лексем
    StringBuffer *buf = StringBuffer_empty();

    // Буффер для хранения aligned verbatim строки
    StringList *verbatim_str = StringList_new();
%}

":="					{ LOG_LEXEM("operator", ":="); return ASSIGN_TO; }
"="						{ LOG_LEXEM("operator", "EQUALS"); return '='; }
"/="					{ LOG_LEXEM("operator", "NOT_EQUALS"); return NEQ; }
"<" 					{ LOG_LEXEM("operator", "LESS"); return '<'; }
"<=" 					{ LOG_LEXEM("operator", "LESS_OR_EQUAL"); return LE; }
">" 					{ LOG_LEXEM("operator", "GREATER"); return '>'; }
">=" 					{ LOG_LEXEM("operator", "GREATER_OR_EQUAL"); return GE; }
"and" 					{ LOG_LEXEM("operator", "AND"); return AND; }
"xor" 					{ LOG_LEXEM("operator", "XOR"); return XOR; }
"or" 					{ LOG_LEXEM("operator", "OR"); return OR; } 
"not" 					{ LOG_LEXEM("operator", "NOT"); return NOT;}
and{WHITESPACE}then 	{ LOG_LEXEM("operator", "AND_THEN"); return AND_THEN; }
or{WHITESPACE}else 	    { LOG_LEXEM("operator", "OR_ELSE"); return OR_ELSE; }
"implies" 				{ LOG_LEXEM("operator", "IMPLIES"); return IMPLIES; }
"//"					{ LOG_LEXEM("operator", "DIV"); return INT_DIV; }
"\\\\"					{ LOG_LEXEM("operator", "MOD"); return MOD; }
"+" 					{ LOG_LEXEM("operator", "+"); return '+'; }
"-" 					{ LOG_LEXEM("operator", "-"); return '-'; }
"*" 					{ LOG_LEXEM("operator", "*"); return '*'; }
"/"						{ LOG_LEXEM("operator", "/"); return '/'; }
"^" 					{ LOG_LEXEM("operator", "^"); return '^'; }
";" 					{ LOG_LEXEM("operator", ";"); return ';'; }
"!!"                    { LOG_LEXEM("operator", "!!") return BANG_BANG; }

"->"                    { LOG_LEXEM("symbol", "->"); return RARROW; }
"<<"                    { LOG_LEXEM("symbol", "<<"); return OPEN_MANIFEST_ARRAY; }
">>"                    { LOG_LEXEM("symbol", ">>"); return CLOSE_MANIFEST_ARRAY; }
"(" 					{ LOG_LEXEM("symbol", "("); return '('; }
")" 					{ LOG_LEXEM("symbol", ")"); return ')'; }
"{" 					{ LOG_LEXEM("symbol", "{"); return '{'; }
"}" 					{ LOG_LEXEM("symbol", "}"); return '}'; }
"[" 					{ LOG_LEXEM("symbol", "["); return '['; }
"]" 					{ LOG_LEXEM("symbol", "]"); return ']'; }
":" 					{ LOG_LEXEM("symbol", ":"); return ':'; }
".."                    { LOG_LEXEM("symbol", ".."); return TWO_DOTS; }
"." 					{ LOG_LEXEM("symbol", "."); return '.'; }
"," 					{ LOG_LEXEM("symbol", ","); return ','; }

"all" 					{ LOG_LEXEM("keyword", "ALL"); }
"across"                { LOG_LEXEM("keyword", "ACROSS"); }
"agent"                 { LOG_LEXEM("keyword", "AGENT"); }
"alias"                 { LOG_LEXEM("keyword", "ALIAS"); return ALIAS; }
"as"                    { LOG_LEXEM("keyword", "AS"); return AS; }
"assign"                { LOG_LEXEM("keyword", "ASSIGN"); }
"attribute"             { LOG_LEXEM("keyword", "ATTRIBUTE"); }
"class" 				{ LOG_LEXEM("keyword", "CLASS"); return CLASS; }
"check"                 { LOG_LEXEM("keyword", "CHECK"); }
"convert"               { LOG_LEXEM("keyword", "CONVERT"); }
"create" 				{ LOG_LEXEM("keyword", "CREATE"); return CREATE; }
"Current" 				{ LOG_LEXEM("keyword", "CURRENT"); return CURRENT; }
"do" 					{ LOG_LEXEM("keyword", "DO"); return DO; }
"debug"                 { LOG_LEXEM("keyword", "DEBUG"); }
"deferred"              { LOG_LEXEM("keyword", "DEFERRED"); return DEFERRED; }
"else" 					{ LOG_LEXEM("keyword", "ELSE"); return ELSE; }
"elseif" 				{ LOG_LEXEM("keyword", "ELSEIF"); return ELSEIF; }
"end" 					{ LOG_LEXEM("keyword", "END"); return END; }
"ensure"                { LOG_LEXEM("keyword", "ENSURE"); return ENSURE; }
"expanded"              { LOG_LEXEM("keyword", "EXPANDED"); }
"export"                { LOG_LEXEM("keyword", "EXPORT"); }
"external"              { LOG_LEXEM("keyword", "EXTERNAL"); return EXTERNAL; }
"feature" 				{ LOG_LEXEM("keyword", "FEATURE"); return FEATURE; }
"from" 					{ LOG_LEXEM("keyword", "FROM"); return FROM; }
"False"                 { LOG_LEXEM("keyword", "FALSE"); return FALSE_KW; }
"frozen"                { LOG_LEXEM("keyword", "FROZEN"); }
"if" 					{ LOG_LEXEM("keyword", "IF"); return IF; }
"inherit" 				{ LOG_LEXEM("keyword", "INHERIT"); return INHERIT; }
"inspect"               { LOG_LEXEM("keyword", "INSPECT"); return INSPECT; }
"invariant"             { LOG_LEXEM("keyword", "INVARIANT"); }
"local" 				{ LOG_LEXEM("keyword", "LOCAL"); return LOCAL; }
"loop" 					{ LOG_LEXEM("keyword", "LOOP"); return LOOP;}
"like"                  { LOG_LEXEM("keyword", "LIKE"); return LIKE; }
"note" 					{ LOG_LEXEM("keyword", "NOTE"); }
"obsolete"              { LOG_LEXEM("keyword", "OBSOLETE"); }
"old"                   { LOG_LEXEM("keyword", "OLD"); }
"once"                  { LOG_LEXEM("keyword", "ONCE"); return ONCE; }
"only"                  { LOG_LEXEM("keyword", "ONLY"); }
"Precursor" 			{ LOG_LEXEM("keyword", "PRECURSOR"); return PRECURSOR; }
"redefine" 				{ LOG_LEXEM("keyword", "REDEFINE"); return REDEFINE; }
"rename" 				{ LOG_LEXEM("keyword", "RENAME"); return RENAME; }
"Result" 				{ LOG_LEXEM("keyword", "RESULT"); return RESULT; }
"require"               { LOG_LEXEM("keyword", "REQUIRE"); return REQUIRE; }
"rescue"                { LOG_LEXEM("keyword", "RESCUE"); }
"retry"                 { LOG_LEXEM("keyword", "RETRY"); }
"separate"              { LOG_LEXEM("keyword", "SEPARATE"); }
"select" 				{ LOG_LEXEM("keyword", "SELECT"); return SELECT; }
"then" 					{ LOG_LEXEM("keyword", "THEN"); return THEN; }
"True"                  { LOG_LEXEM("keyword", "TRUE");  return TRUE_KW; }
"undefine" 				{ LOG_LEXEM("keyword", "UNDEFINE"); return UNDEFINE; }
"until" 				{ LOG_LEXEM("keyword", "UNTIL"); return UNTIL; }
"variant"               { LOG_LEXEM("keyword", "VARIANT"); }
"Void"                  { LOG_LEXEM("keyword", "VOID");  return VOID; }
"when"                  { LOG_LEXEM("keyword", "WHEN"); return WHEN; }

"TUPLE"                 { LOG_LEXEM("keyword", "TUPLE"); return TUPLE; }


--.*\n? { LOG_LEXEM("single line comment", yytext); }

<CHARACTER,STRING>%\/[0-9]{1,3}\/ {
    StringBuffer_append_char(buf, convert_decimal_encoded_char(yytext));
}
<CHARACTER,STRING>%%      { StringBuffer_append_char(buf, '%'); }
<CHARACTER,STRING>%[nN]   { StringBuffer_append_char(buf, '\n'); }
<CHARACTER,STRING>%[tT]   { StringBuffer_append_char(buf, '\t'); }
<CHARACTER,STRING>%[aA]   { StringBuffer_append_char(buf, '@'); }
<CHARACTER,STRING>%[bB]   { StringBuffer_append_char(buf, '\b'); }
<CHARACTER,STRING>%[cC]   { StringBuffer_append_char(buf, '^'); }
<CHARACTER,STRING>%[dD]   { StringBuffer_append_char(buf, '$'); }
<CHARACTER,STRING>%[fF]   { StringBuffer_append_char(buf, '\f'); }
<CHARACTER,STRING>%[hH]   { StringBuffer_append_char(buf, '\\'); }
<CHARACTER,STRING>%[lL]   { StringBuffer_append_char(buf, '~'); }
<CHARACTER,STRING>%[qQ]   { StringBuffer_append_char(buf, '`'); }
<CHARACTER,STRING>%[rR]   { StringBuffer_append_char(buf, '\r'); }
<CHARACTER,STRING>%[sS]   { StringBuffer_append_char(buf, '#'); }
<CHARACTER,STRING>%[uU]   { StringBuffer_append_char(buf, '\0'); }
<CHARACTER,STRING>%[vV]   { StringBuffer_append_char(buf, '\v'); }
<CHARACTER,STRING>%\(     { StringBuffer_append_char(buf, '['); }
<CHARACTER,STRING>%\)     { StringBuffer_append_char(buf, ']'); }
<CHARACTER,STRING>%\<     { StringBuffer_append_char(buf, '{'); }
<CHARACTER,STRING>%\>     { StringBuffer_append_char(buf, '}'); }
<CHARACTER,STRING>%\"     { StringBuffer_append_char(buf, '\"'); }
<CHARACTER,STRING>%\'     { StringBuffer_append_char(buf, '\''); }
<CHARACTER,STRING>%(.|\n) {
    ERROR("invalid escape sequence");
    SKIP_UNTIL_CHAR_IN("'\n");
    BEGIN(INITIAL);
    return CHAR_CONST;
}

<CHARACTER>[^\'\n]* {
    StringBuffer_append(buf, yytext);

    int code_points = strlen_utf8(buf->buffer);
    if (code_points > 1) {
        ERROR_F(yylineno, "expected only one character in singles quotes, but got: '%s'", buf->buffer);
        StringBuffer_clear(buf);
        SKIP_UNTIL_CHAR_IN("'\n");
        BEGIN(INITIAL);
        return CHAR_CONST;
    }
}

<CHARACTER>\n {
    ERROR_AT_LINENO(yylineno-1, "unclosed character literal");
    BEGIN(INITIAL);
    return CHAR_CONST;
}

<CHARACTER><<EOF>> {
    ERROR("unclosed character literal");
    BEGIN(INITIAL);
    return CHAR_CONST;
}

<CHARACTER>\' {
    int code_points = strlen_utf8(buf->buffer);
    if (code_points == 0) {
        ERROR("empty characters are not permitted");
        BEGIN(INITIAL);
        return CHAR_CONST;
    }
    else if (code_points > 1) {
        ERROR_F(yylineno, "expected only one character in singles quotes, but got: '%s'", buf->buffer);
        StringBuffer_clear(buf);
        BEGIN(INITIAL);
        return CHAR_CONST;
    }
    else {
        LOG_LEXEM("character", buf->buffer);
        BEGIN(INITIAL);
        // Символы (CHARACTER) могут быть более одного байта в длину,
        // чтобы не морочится с сохранением их в int (хотя это тоже возможно),
        // сохраняем их в string_value, и далее тот, кто обрабатывает JSON-дерево,
        // будет с этим разбираться
        yylval.string_value = escape(buf->buffer);
        return CHAR_CONST;
    }
}

<STRING>[^\"\n%]* { StringBuffer_append(buf, yytext); }

<STRING>\n {
    ERROR_AT_LINENO(yylineno-1, "unclosed string");
    StringBuffer_clear(buf);
    BEGIN(INITIAL);
    return STRING_CONST;
}

<STRING><<EOF>> {
    ERROR("unclosed string");
    StringBuffer_clear(buf);
    BEGIN(INITIAL);
    return STRING_CONST;
}

<STRING>\" {
    // Добавил проверку на режим дебага, чтобы не выделять память,
    // на экранирование строки, если это не нужно
    #ifdef DEBUG_LEXER
        char* escaped = escape(buf->buffer);
        LOG_LEXEM("string content", escaped);
        free(escaped);
    #endif

    BEGIN(INITIAL);
    yylval.string_value = escape(buf->buffer);
    return STRING_CONST;
}

\"\[\n {
    StringBuffer_clear(buf);
    StringList_clear(verbatim_str);
    BEGIN(VERBATIM_ALIGNED_STRING);
}

<VERBATIM_ALIGNED_STRING>[ \t]*\]\"[ \t]*\n? {
    adjust_unaligned_verbatim_string(verbatim_str);
    // TODO: Когда-нибудь переписать через StringList_join
    // UPDATE: StringList_join использовать не получится, т.к.
    // тогда нужно контроллировать утечки памяти и где-то освобождать указатель
    // на строку, которую создает StringList_join
    for (int i = 0; i < StringList_size(verbatim_str); i++) {
        StringBuffer_append(buf, StringList_get(verbatim_str, i));
    }

    // Добавил проверку на режим дебага, чтобы не выделять память,
    // на экранирование строки, если это не нужно
    #ifdef DEBUG_LEXER
        char* escaped = escape(buf->buffer);
        LOG_LEXEM("verbatim string", escaped);
        free(escaped);
    #endif

    BEGIN(INITIAL);
    yylval.string_value = escape(buf->buffer);
    return STRING_CONST;
}

<VERBATIM_ALIGNED_STRING>.*\n { StringList_push(verbatim_str, yytext); }

<VERBATIM_ALIGNED_STRING><<EOF>> {
    ERROR("unclosed verbatim string");
    StringList_clear(verbatim_str);
    BEGIN(INITIAL);
    return STRING_CONST;
}

\" {
    StringBuffer_clear(buf);
    BEGIN(STRING);
}

\' {
    StringBuffer_clear(buf);
    BEGIN(CHARACTER);
}

{IDENTIFIER} {
    StringBuffer_clear(buf);
    StringBuffer_append(buf, yytext);
    LOG_LEXEM("identifier", buf->buffer);
    yylval.ident = buf->buffer;
    return IDENT_LIT;
}

{INT_10} {
    base = 10;
    goto process_integer;
}

{INT_16} {
    base = 16;
    goto process_integer;
}

{INT_8} {
    base = 8;
    goto process_integer;
}

{INT_2} {
    base = 2;
    goto process_integer;
}

%{
process_integer:
    // Запоминаем строку, на которой было найдено число,
    // т.к. при запросе следующего символа он может оказаться новой строкой,
    // и увеличить yylineno
    line = yylineno;

    next = input();

    if (!is_end(next) && !is_possible_part_of_integer(next, base) && !is_delim(next)) {
        StringBuffer_clear(buf);

        SKIP_UNTIL_DELIMETER(next);

        unput(next);
        ERROR_F(line, "invalid integer with base %d literal: \"%s\"", base, buf->buffer);
        break;
    }

    unput(next);
    parse_int(yytext, &int_value, base);
    LOG_F(line, "integer %s with base %d literal", yytext, base);
    yylval.int_value = int_value;
    return INT_CONST;
%}

{REAL_NUMBER} { goto process_real; }

{REAL_NUMBER_EXPONENT} { goto process_real; }

%{
process_real:
    // Запоминаем строку, на которой было найдено число,
    // т.к. при запросе следующего символа он может оказаться новой строкой,
    // и увеличить yylineno
    line = yylineno;

    next = input();

    // Сначала пытаемся распознать символ задания диапазона "..":
    // если последний символ считанного текста это точка, и следующий символ тоже точка,
    // значит это диапазон.
    if (yytext[strlen(yytext) - 1] == '.' && next == '.') {
        unput(next);
        REJECT;
    }
    else if (yytext[strlen(yytext) - 1] == '.' && isalpha(next) && next != 'e') {
        unput(next);
        REJECT;
    }

    if (!is_end(next) && !is_possible_part_of_real(next) && !is_delim(next)) {
        StringBuffer_clear(buf);

        SKIP_UNTIL_DELIMETER(next);

        unput(next);
        ERROR_F(line, "invalid real literal: \"%s\"", buf->buffer);
        break;
    }

    unput(next);
    parse_real(yytext, &real_value);
    LOG_LEXEM("real number literal", yytext);
    yylval.real_value = real_value;
    return REAL_CONST;
%}

{WHITESPACE} { }

. {
    if (yytext[0] != '\0')
        LOG_F(yylineno, "unknown symbol, code: %x\n", yytext[0]);
}


%%

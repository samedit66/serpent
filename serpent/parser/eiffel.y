%locations

%{
    #include <stdio.h>
    #include <stdbool.h>
    #include <stdlib.h>
    #include <string.h>
    #include <unistd.h>

    #include "./include/ast.h"

    extern int yylex(void);
    extern void yyrestart(FILE *infile);
    void yyerror(const char *str);

    int errors_count = 0;

    char *current_file_path = NULL;
    Json *found_classes = NULL;

    #define YYDEBUG 1
    #define LOG_NODE(msg) printf("Found node: %s\n", msg)

    struct YYLTYPE current_node_loc;
    #define YYLLOC_DEFAULT(Current, Rhs, N)\
        do {\
            if (N) {\
                (Current).first_line = YYRHSLOC (Rhs, 1).first_line;\
                (Current).first_column = YYRHSLOC (Rhs, 1).first_column;\
                (Current).last_line = YYRHSLOC (Rhs, N).last_line;\
                (Current).last_column  = YYRHSLOC (Rhs, N).last_column;\
            }\
            else {\
                (Current).first_line = (Current).last_line = YYRHSLOC (Rhs, 0).last_line;\
                (Current).first_column = (Current).last_column = YYRHSLOC (Rhs, 0).last_column;\
            }\
            current_node_loc = (Current);\
        } while (0)
%}

%define parse.error verbose

%union {
    int int_value;
    double real_value;
    char *string_value;
    char *ident;
    struct Json *tree;
}

%start class_list

%token EOI 0 "end of file"

%token <int_value> INT_CONST
%token <real_value> REAL_CONST
%token <ident> IDENT_LIT 
%token <string_value> CHAR_CONST
%token <string_value> STRING_CONST

%type <tree> constant expr
%type <tree> manifest_array manifest_array_content manifest_array_content_opt

%type <tree> assign_stmt writable

%type <tree> simple_call precursor_call call
%type <tree> params_list comma_separated_exprs
%type <tree> bracket_access
%type <tree> if_expr elseif_expr_opt elseif_expr

%type <tree> stmt stmt_list stmt_list_opt
%type <tree> loop_stmt
%type <tree> inspect_stmt
%type <tree> when_clauses_opt when_clauses choices_opt choices choice
%type <tree> if_stmt elseif_clauses_opt elseif_clauses else_clause_opt

%type <tree> feature_list feature
%type <tree> name_and_type type_spec routine_body args_list_opt args_list

%type <tree> class_declaration class_header inheritance_opt creators_opt features_clause_opt
%type <tree> formal_generics_opt formal_generics generic
%type <tree> creators
%type <tree> inheritance inheritance_clause parent rename_clause undefine_clause_opt redefine_clause_opt select_clause_opt
%type <tree> rename_list
%type <tree> undefine_clause
%type <tree> redefine_clause
%type <tree> select_clause
%type <tree> features_clause clients_opt clients

%type <tree> do_part
%type <tree> then_part_opt then_part
%type <tree> local_part var_decl_list
%type <tree> require_part_opt require_part
%type <tree> ensure_part_opt ensure_part
%type <tree> condition_list condition

%type <tree> ident_list

%type <tree> type generic_type type_list

%type <tree> class_list

%type <tree> create_stmt
%type <tree> constructor_call

%type <tree> manifest_tuple

%type <tree> create_expr object_type

%token
    INT_DIV "//"
    MOD "\\"
%token
    AND "and"
    OR "or"
    NOT "not" 
    AND_THEN "and then"
    OR_ELSE "or else"
%token
    NEQ "/="
    LE "<="
    GE ">="
%token ASSIGN_TO ":="
%token END "end"
%token
    IF "if"
    THEN "then"
    ELSEIF "elseif"
    ELSE "else"
%token
    FROM "from"
    UNTIL "until"
    LOOP "loop"
%token
    WHEN "when"
    INSPECT "inspect"
    TWO_DOTS ".."
%token CLASS "class"
%token LIKE "like"
%token DO "do"
%token
    INTEGER "INTEGER"
    REAL"REAL"
    STRING_KW "STRING"
    CHARACTER "CHARACTER"
    BOOLEAN "BOOLEAN"
    ARRAY "ARRAY"
    TUPLE "TUPLE"
%token
    FEATURE "feature"
    CREATE "create"
%token LOCAL "local"
%token
    REQUIRE "require"
    ENSURE "ensure"
%token
    CURRENT "current"
    PRECURSOR "precursor"
    RESULT "Result"
%token RARROW "->"
%token
    AS "as"
    INHERIT "inherit"
    REDEFINE "redefine"
    RENAME "rename"
    UNDEFINE "undefine"
    SELECT "select"
%token
    TRUE_KW "True" 
    FALSE_KW "False" 
    VOID "Void"
%token
    OPEN_MANIFEST_ARRAY "<<"
    CLOSE_MANIFEST_ARRAY ">>"
%token BANG_BANG "!!"
%token DEFERRED "deferred"
%token EXTERNAL "external"
%token ALIAS "alias"

%nonassoc DEFERRED
%nonassoc EFFECTIVE

%nonassoc FIELD
%nonassoc ROUTINE
%nonassoc ASSIGN_TO
%nonassoc LOWER_THAN_EXPR
%nonassoc LOWER_THAN_PARENS
%nonassoc '(' ')'
%right IMPLIES
%left OR OR_ELSE XOR
%left AND AND_THEN
%right NOT
%left '<' '>' LE GE '=' NEQ
%left '+' '-'
%left '*' '/' INT_DIV MOD
%right '^'
%nonassoc UMINUS UPLUS
%nonassoc LOWER_THAN_BRACKETS
%left '[' ']'
%right '.'
%nonassoc CREATE

%%

/* ********************************************************************/
/* Описание программы: набор классов */
class_list: class_declaration { if (found_classes == NULL) found_classes = mk_list(); add_to_list(found_classes, $1); }
          | class_list class_declaration { add_to_list(found_classes, $2);  }
          ;

class_declaration: class_header inheritance_opt creators_opt features_clause_opt END { $$ = mk_class_decl($1, $2, $3, $4); }
                 ;

/* Заголовок класса */
class_header: CLASS IDENT_LIT formal_generics_opt { $$ = mk_effective_class_header($2, $3); }
            | DEFERRED CLASS IDENT_LIT formal_generics_opt { $$ = mk_deferred_class_header($3, $4); }
            ;

formal_generics_opt: /* empty */ { $$ = mk_list(); }
                   | '[' formal_generics ']' { $$ = $2; }
                   ;

formal_generics: generic { $$ = mk_list(); $$ = add_to_list($$, $1); }
               | formal_generics ',' generic { $$ = add_to_list($1, $3); }
               ;

generic: type { $$ = mk_generic($1); }
       | type RARROW type { $$ = mk_constrained_generic($1, $3); }
       ;

/* Секция конструкторов */
creators_opt: /* empty */ { $$ = mk_list(); }
            | creators { $$ = $1; }
            ;

creators: CREATE ident_list { $$ = $2; }
        ;


/* ********************************************************************/
/* Секция наследования */
inheritance_opt: /* empty */ { $$ = mk_list(); }
               | INHERIT inheritance { $$ = $2; }
               ;

inheritance: inheritance_clause { $$ = mk_list(); $$ = add_to_list($$, $1); }
           | inheritance inheritance_clause { $$ = add_to_list($1, $2); }
           ;

inheritance_clause: parent { $$ = mk_inherit_clause($1, mk_list(), mk_list(), mk_list(), mk_list()); }
                  | parent rename_clause undefine_clause_opt redefine_clause_opt select_clause_opt END { $$ = mk_inherit_clause($1, $2, $3, $4, $5); }
                  | parent undefine_clause redefine_clause_opt select_clause_opt END { $$ = mk_inherit_clause($1, mk_list(), $2, $3, $4); }
                  | parent redefine_clause select_clause_opt END { $$ = mk_inherit_clause($1, mk_list(), mk_list(), $2, $3); }
                  | parent select_clause END { $$ = mk_inherit_clause($1, mk_list(), mk_list(), mk_list(), $2); }
                  ;

parent: IDENT_LIT formal_generics_opt { $$ = mk_parent_info($1, $2); }
      ;

/* Секция переименования */
rename_clause: RENAME rename_list { $$ = $2; }
             ;

rename_list: IDENT_LIT AS IDENT_LIT { $$ = mk_list(); $$ = add_to_list($$, mk_alias($1, $3)); }
           | rename_list IDENT_LIT AS IDENT_LIT { $$ = add_to_list($1, mk_alias($2, $4)); }
           | rename_list ',' IDENT_LIT AS IDENT_LIT { $$ = add_to_list($1, mk_alias($3, $5)); }
           ;


/* Секция undefine */
undefine_clause_opt: /* empty */ { $$ = mk_list(); }
                   | undefine_clause { $$ = $1; }
                   ;

undefine_clause: UNDEFINE ident_list { $$ = $2; }
               ;


/* Секция переопределения */
redefine_clause_opt: /* empty */ { $$ = mk_list(); }
                   | redefine_clause { $$ = $1; }
                   ;

redefine_clause: REDEFINE ident_list { $$ = $2;  }
               ;


/* Секция select */
select_clause_opt: /* empty */ { $$ = mk_list(); }
                 | select_clause { $$ = $1; }
                 ;

select_clause: SELECT ident_list { $$ = $2; }
             ;


/* ********************************************************************/
/* Описание feature класса */
features_clause_opt: /* empty */ { $$ = mk_list(); }
                   | features_clause { $$ = $1; }
                   ;

features_clause: FEATURE clients_opt feature_list { $$ = add_to_list(mk_list(), mk_feature_clause($2, $3)); }
               | features_clause FEATURE clients_opt feature_list { $$ = add_to_list($1, mk_feature_clause($3, $4)); }
               ;

clients_opt: /* empty */ { $$ = mk_list(); }
           | clients { $$ = $1; }
           ;

clients: '{' ident_list '}' { $$ = $2; }
       ;


/* ********************************************************************/
/* Описание типов */
type: IDENT_LIT { $$ = mk_type($1); }
    // Типы ниже определены в стандартной библиотеке:
    // | INTEGER { $$ = mk_integer_type(); }
    // | REAL { $$ = mk_real_type(); }
    // | STRING_KW { $$ = mk_string_type(); }
    // | CHARACTER { $$ = mk_character_type(); }
    // | BOOLEAN { $$ = mk_boolean_type(); }
    | LIKE CURRENT { $$ = mk_like_current_type(); }
    | LIKE IDENT_LIT { $$ = mk_like_other_field_type($2); }
    | generic_type { $$ = $1; }
    ;

generic_type: IDENT_LIT '[' type_list ']' { $$ = mk_generic_user_type($1, $3); }
            // Массив стал типом определенным в стандартной библиотеке
            // | ARRAY '[' type ']' { $$ = mk_generic_array_type(add_to_list(mk_list(), $3)); }
            | TUPLE '[' type_list ']' { $$ = mk_generic_tuple_type($3); }
            | TUPLE                   { $$ = mk_generic_tuple_type(mk_list()); }
            ;

type_list: type { $$ = mk_list(); $$ = add_to_list($$, $1); }
         | type_list ';' type { $$ = add_to_list($1, $3);  }
         ;


/* ********************************************************************/
/* Описания для полей и методов класса */
feature_list: feature { $$ = add_to_list(mk_list(), $1); }
            | feature_list feature { $$ = add_to_list($1, $2); }
            ;

/*
Поддерживаются:
1) Объявление вида (атрибуты): a, b: INTEGER

2) Указание константных атрибутов класса: pi: REAL = 3.14

3) Методы, не принимающие параметров и ничего не возвращающие:
    a, b, c do
        ...
    end

4) Указание метода, ничего не принимающего, но возвращающего что-то:
    f: REAL do
        ...
    end

5) Указание аргументов:
    f (a: INTEGER, b: REAL) do
        ...
    end

    Пустые скобки также поддерживаются

6) Все вместе:
    f, g (a: INTEGER, b: REAL): STRING do
        ...
    end
*/
feature: name_and_type { $$ = mk_class_field($1); }
       | name_and_type '=' constant { $$ = mk_class_constant($1, $3); }
       | ident_list routine_body { $$ = mk_void_routine_with_no_args($1, $2); }
       | name_and_type routine_body { $$ = mk_routine_with_no_args($1, $2); }
       | ident_list '(' args_list_opt ')' routine_body { $$ = mk_void_routine_with_args($1, $3, $5); }
       | ident_list '(' args_list_opt ')' type_spec routine_body { $$ = mk_routine_with_args($1, $3, $5, $6); }
       ;

/* Список имен с заданным типом */
name_and_type: ident_list type_spec { $$ = mk_name_and_type($1, $2); }
             ;

ident_list: IDENT_LIT { $$ = mk_list(); $$ = add_ident_to_list($$, $1); }
          | ident_list ',' IDENT_LIT { $$ = add_ident_to_list($1, $3); }

type_spec: ':' type { $$ = $2; }
         ;

/* Список аргументов */
args_list_opt: /* empty */ { $$ = mk_list(); }
             | args_list { $$ = $1; }
             ;

args_list: name_and_type { $$ = add_to_list(mk_list(), mk_feature_parameter($1)); }
         | args_list ';' name_and_type { $$ = add_to_list($1, mk_feature_parameter($3)); }
         ;

/* Тело метода */
routine_body: require_part_opt do_part then_part_opt ensure_part_opt END { $$ = mk_effective_routine_body(NULL, $1, $2, $3, $4); }
            | local_part require_part_opt do_part then_part_opt ensure_part_opt END { $$ = mk_effective_routine_body($1, $2, $3, $4, $5); }
            | require_part_opt then_part ensure_part_opt END { $$ = mk_effective_routine_body(NULL, $1, NULL, $2, $3); }
            | local_part require_part_opt then_part ensure_part_opt END { $$ = mk_effective_routine_body($1, $2, NULL, $3, $4); }
            | require_part_opt DEFERRED ensure_part_opt END { $$ = mk_deferred_routine_body($1, $3); }
            | require_part_opt EXTERNAL STRING_CONST ALIAS STRING_CONST ensure_part_opt END { $$ = mk_external_routine_body($3, $5, $1, $6); }
            ;

local_part: LOCAL var_decl_list { $$ = $2; }
          ;

var_decl_list: name_and_type { $$ = add_to_list(mk_list(), mk_local_var_decl($1)); }
             | var_decl_list name_and_type { $$ = add_to_list($1, mk_local_var_decl($2)); }
             ;

/* Секция предусловий */
require_part_opt: /* empty */ { $$ = mk_list(); }
                | require_part { $$ = $1; }
                ;

require_part: REQUIRE condition_list { $$ = $2; }
            | REQUIRE condition_list ';' { $$ = $2; }
            ;

condition_list: condition { $$ = add_to_list(mk_list(), $1); }
              | condition_list condition { $$ = add_to_list($1, $2); }
              | condition_list ';' condition { $$ = add_to_list($1, $3); }
              ;

/*
Необходимо сделать приоритет данных правил ниже чем expr,
т.к. возникают shift/reduce конфликты со следующим примером: require 3 + 4
Либо это один condition, либо два (3 и +4). Несмотря на то, что эта конструкция
некорректна (с точки зрения семантики), нужно убедится, что даже она распознает правильно
*/
condition: expr %prec LOWER_THAN_EXPR { $$ = mk_tagged_cond(NULL, $1); }
         | IDENT_LIT ':' expr %prec LOWER_THAN_EXPR { $$ = mk_tagged_cond($1, $3); }
         ;

/* Секция инструкций метода */
do_part: DO stmt_list_opt { $$ = $2; }
       ;

/* Секция then */
then_part_opt: /* empty */ { $$ = NULL; }
             | then_part { $$ = $1; }
             ;

then_part: THEN expr { $$ = $2; }
         ;

/* Секция постусловий  */
ensure_part_opt: /* empty */ { $$ = mk_list(); }
               | ensure_part { $$ = $1; }
               ;

ensure_part: ENSURE condition_list { $$ = $2; }
           | ENSURE condition_list ';' { $$ = $2; }
           ;


/* ********************************************************************/
/* Описание инструкций */
stmt_list_opt: /* empty */ { $$ = mk_list(); }
             | stmt_list   { $$ = $1; }
             ;

stmt_list: stmt           { $$ = mk_list(); if ($1 != NULL) $$ = add_to_list($$, $1); }
         | stmt_list stmt { if ($2 != NULL) $$ = add_to_list($1, $2); }
         ;

stmt: assign_stmt  { $$ = $1; }
    | if_stmt      { $$ = $1; }
    | loop_stmt    { $$ = $1; }
    | inspect_stmt { $$ = $1;}
    | call         { $$ = $1; }
    | create_stmt  { $$ = $1; }
    | error ';'    { yyerrok; }
    | ';'          { $$ = NULL; }
    ;


/* ********************************************************************/
/* Оператор создание объекта */
create_stmt: CREATE constructor_call                      { $$ = mk_create(NULL, $2); }
           | CREATE '{' object_type '}' constructor_call    { $$ = mk_create($3, $5); }
           | BANG_BANG constructor_call                   { $$ = mk_create(NULL, $2); }
           | BANG_BANG '{' object_type '}' constructor_call { $$ = mk_create($3, $5); }
           ;

constructor_call: IDENT_LIT                  { $$ = mk_constructor_call($1, NULL); }
                | IDENT_LIT '.' simple_call  { $$ = mk_constructor_call($1, $3); }
                ;


/* ********************************************************************/
/* Описание оператора присваивания */
assign_stmt: writable ASSIGN_TO expr { $$ = mk_assign_stmt($1, $3);  }
           ;

writable: IDENT_LIT { $$ = mk_ident_lit($1); }
        | RESULT { $$ = mk_result_const(); }
        | bracket_access { $$ = $1; }
        ;


/* ********************************************************************/
/* Описание оператора цикла */
loop_stmt: FROM stmt_list_opt UNTIL expr LOOP stmt_list_opt END { $$ = mk_loop_stmt($2, $4, $6); }
         ;


/* ********************************************************************/
/* Описание оператора выбора */
inspect_stmt: INSPECT expr when_clauses_opt else_clause_opt END { $$ = mk_inspect_stmt($2, $3, $4); }
            ;

when_clauses_opt: /* empty */  { $$ = mk_list(); }
                | when_clauses { $$ = $1; }
                ;

when_clauses: WHEN choices_opt THEN stmt_list_opt { $$ = mk_list(); $$ = add_alt_when_clause($$, $2, $4); }
            | when_clauses WHEN choices_opt THEN stmt_list_opt { $$ = add_alt_when_clause($1, $3, $5); }
            ;

choices_opt: /* empty */ { $$ = mk_list(); }
           | choices { $$ = $1; }
           ;

choices: choice { $$ = mk_list(); $$ = add_to_list($$, $1); }
       | choices ',' choice { $$ = add_to_list($1, $3);  }
       ;

choice: expr { $$ = $1; }
      | expr TWO_DOTS expr { $$ = mk_choice_interval($1, $3); }
      ;


/* ********************************************************************/
/* Описание оператора ветвления */
if_stmt: IF expr THEN stmt_list_opt elseif_clauses_opt else_clause_opt END { $$ = mk_if_stmt($2, $4, $5, $6); }
       ;

elseif_clauses_opt: /* empty */    { $$ = mk_list(); }
                  | elseif_clauses { $$ = $1; }
                  ;

elseif_clauses: ELSEIF expr THEN stmt_list_opt { $$ = mk_list(); $$ = add_elseif_stmt($$, $2, $4); }
              | elseif_clauses ELSEIF expr THEN stmt_list_opt { $$ = add_elseif_stmt($1, $3, $5); }

else_clause_opt: /* empty */        { $$ = mk_list(); }
               | ELSE stmt_list_opt { $$ = $2; }
               ;


/* ********************************************************************/
/* Описание вызова метода */

/*
Поддерживаются:
1) Обычный вызов со скобками и без: g(a, b, c); f(); fi
2) Вызов метода родительского класса с тем же именем: Precursor(1, 2, 3)
3) Через Result: Result.f(a, b)
4) Вызов метода у объекта через Current: Current.f(a, b)
5) У произвольного выражения в круглых скобках: (1 + 2).out
6) Вызов метода у элемента массива: numbers[1].to_natural_8
7) Вызовы произвольной вложенности: Result.f.g(a, b, c)
*/
call: simple_call { $$ = mk_feature_with_unknown_owner_call($1); }
    | precursor_call { $$ = $1; }
    | RESULT         '.' simple_call { $$ = mk_feature_with_owner_call(mk_result_const(), $3); }
    | CURRENT        '.' simple_call { $$ = mk_feature_with_owner_call(mk_current_const(), $3); }
    | '(' expr ')'   '.' simple_call { $$ = mk_feature_with_owner_call($2, $5); }
    | bracket_access '.' simple_call { $$ = mk_feature_with_owner_call($1, $3); }
    | call           '.' simple_call { $$ = mk_feature_with_owner_call($1, $3); }
    | INT_CONST      '.' simple_call { $$ = mk_feature_with_owner_call(mk_int_const($1), $3); }
    | REAL_CONST     '.' simple_call { $$ = mk_feature_with_owner_call(mk_real_const($1), $3); }
    | CHAR_CONST     '.' simple_call { $$ = mk_feature_with_owner_call(mk_char_const($1), $3); }
    | STRING_CONST   '.' simple_call { $$ = mk_feature_with_owner_call(mk_string_const($1), $3); }
    | TRUE_KW        '.' simple_call { $$ = mk_feature_with_owner_call(mk_boolean_const(true), $3); } 
    | FALSE_KW       '.' simple_call { $$ = mk_feature_with_owner_call(mk_boolean_const(false), $3); } 
    ;

precursor_call: PRECURSOR %prec LOWER_THAN_EXPR { $$ = mk_precursor_no_args_call(NULL); }
              | PRECURSOR '(' params_list ')' { $$ = mk_precursor_args_call(NULL, $3); }
              | '{' IDENT_LIT '}' PRECURSOR %prec LOWER_THAN_EXPR { $$ = mk_precursor_no_args_call($2); }
              | '{' IDENT_LIT '}' PRECURSOR '(' params_list ')' { $$ = mk_precursor_args_call($2, $6); }
              ;

simple_call: IDENT_LIT %prec LOWER_THAN_PARENS { $$ = mk_simple_call_no_args($1); }
           | IDENT_LIT '(' params_list ')' { $$ = mk_simple_call($1, $3); }
           ;

params_list: /* empty */ { $$ = mk_list(); }
           | comma_separated_exprs { $$ = $1; }
           ;

comma_separated_exprs: expr { $$ = mk_list(); $$ = add_to_list($$, $1); }
                     | comma_separated_exprs ',' expr { $$ = add_to_list($1, $3); }
                     ;


/* ********************************************************************/
/* Тернарный оператор */
if_expr: IF expr THEN expr elseif_expr_opt ELSE expr END { $$ = mk_if_expr($2, $4, $5, $7); }

elseif_expr_opt: /* empty */ { $$ = mk_list();  }
               | elseif_expr { $$ = $1; }

elseif_expr: ELSEIF expr THEN expr { $$ = mk_list(); $$ = add_elseif_expr($$, $2, $4); }
           | elseif_expr ELSEIF expr THEN expr { $$ = add_elseif_expr($1, $3, $5); }


/* ********************************************************************/
/* Выражения и значения */

/* Взятие элемента через квадратный скобки */
bracket_access: call '[' expr ']' { $$ = mk_bracket_access($1, $3); }
              | constant '[' expr ']' { $$ = mk_bracket_access($1, $3); }
              | bracket_access '[' expr ']' { $$ = mk_bracket_access($1, $3); }
              ;

/* Константы */
constant: INT_CONST     { $$ = mk_int_const($1); }
        | REAL_CONST    { $$ = mk_real_const($1); }
        | CHAR_CONST    { $$ = mk_char_const($1); }
        | STRING_CONST  { $$ = mk_string_const($1); }
        | RESULT        { $$ = mk_result_const(); }
        | CURRENT       { $$ = mk_current_const(); }
        | TRUE_KW       { $$ = mk_boolean_const(true); } 
        | FALSE_KW      { $$ = mk_boolean_const(false); } 
        | VOID          { $$ = mk_void_const(); }
        ;


/* Кортеж */
manifest_tuple: '[' manifest_array_content_opt ']' { $$ = mk_manifest_tuple($2); }
              | '[' manifest_array_content ',' ']' { $$ = mk_manifest_tuple($2); }
              ;

/* Массив */
manifest_array: OPEN_MANIFEST_ARRAY manifest_array_content_opt CLOSE_MANIFEST_ARRAY { $$ = mk_manifest_array($2); }
              | OPEN_MANIFEST_ARRAY manifest_array_content ',' CLOSE_MANIFEST_ARRAY { $$ = mk_manifest_array($2); }
              ;

/* Содержимое кортежа/массива */
manifest_array_content_opt: /* empty */ { $$ = mk_list(); }
                          | manifest_array_content { $$ = $1; }
                          ;

manifest_array_content: expr { $$ = add_to_list(mk_list(), $1); }
                      | manifest_array_content ',' expr { $$ = add_to_list($1, $3); }
                      ;


/* create-выражение */
create_expr: CREATE '{' object_type '}'                    { $$ = mk_create_expr($3, NULL); }
           | CREATE '{' object_type '}' '.' simple_call    { $$ = mk_create_expr($3, $6); }
           | BANG_BANG '{' object_type '}'                 { $$ = mk_create_expr($3, NULL); }
           | BANG_BANG '{' object_type '}' '.' simple_call { $$ = mk_create_expr($3, $6); }
           ;

object_type: IDENT_LIT { $$ = mk_type($1); }
           | generic_type { $$ = $1; }
           ;


expr: constant %prec LOWER_THAN_BRACKETS { $$ = $1; }
    | expr '+' expr { $$ = mk_bin_op("add_op", $1, $3); }
    | expr '-' expr { $$ = mk_bin_op("sub_op", $1, $3); }       
    | expr '*' expr { $$ = mk_bin_op("mul_op", $1, $3); }       
    | expr '/' expr { $$ = mk_bin_op("div_op", $1, $3); }       
    | '(' expr ')'  { $$ = $2; }
    | '+' expr %prec UPLUS { $$ = mk_unary_op("unary_plus_op", $2); }
    | '-' expr %prec UMINUS { $$ = mk_unary_op("unary_minus_op", $2); }
    | expr INT_DIV expr { $$ = mk_bin_op("int_div_op", $1, $3); }
    | expr MOD expr { $$ = mk_bin_op("mod_op", $1, $3); }       
    | expr '^' expr { $$ = mk_bin_op("exp_op", $1, $3); }
    | expr AND expr { $$ = mk_bin_op("and_op", $1, $3); }       
    | expr OR expr { $$ = mk_bin_op("or_op", $1, $3); }         
    | NOT expr { $$ = mk_unary_op("not_op", $2); }            
    | expr AND_THEN expr { $$ = mk_bin_op("and_then_op", $1, $3); }
    | expr OR_ELSE expr { $$ = mk_bin_op("or_else_op", $1, $3); }  
    | expr XOR expr { $$ = mk_bin_op("xor_op", $1, $3); }       
    | expr '<' expr { $$ = mk_bin_op("lt_op", $1, $3); }          
    | expr '>' expr { $$ = mk_bin_op("gt_op", $1, $3); }       
    | expr '=' expr { $$ = mk_bin_op("eq_op", $1, $3); }       
    | expr LE expr  { $$ = mk_bin_op("le_op", $1, $3); }       
    | expr GE expr  { $$ = mk_bin_op("ge_op", $1, $3); }       
    | expr NEQ expr { $$ = mk_bin_op("neq_op", $1, $3); }       
    | expr IMPLIES expr { $$ = mk_bin_op("implies_op", $1, $3); }
    | call %prec LOWER_THAN_BRACKETS { $$ = $1; }
    | bracket_access %prec LOWER_THAN_BRACKETS { $$ = $1; }
    | manifest_tuple { $$ = $1; }
    | manifest_array { $$ = $1; }
    | if_expr { $$ = $1; }
    | '(' error ')' { yyerrok; }
    | create_expr { $$ = $1; }
    ;
%%

void yyerror(const char *str) {
    errors_count++;
    fprintf(stderr, "Parser error, line %d: %s\n", yylloc.first_line, str);
}

/**
 * Переводит абстрактное синтакисеческое дерево в JSON, сохраняя его в файл
 * с заданным названием, либо печатая его на экран.
 *
 * @param file_name имя файла (NULL, если результат нужно напечатать на экран)
 * @param tree абстрактное синтакисеческое дерево
 * @param pretty true, если дерево должно быть красиво отформатированным
 * @return true, если получилось записать в файл или вывести на экран, иначе - false
 */
bool
write_output_tree(char *file_name, Json *tree, bool pretty) {
    char *json = pretty ? Json_to_pretty_string(tree) : Json_to_short_string(tree);

    if (file_name == NULL) {
        printf(json);
        free(json);
        return true;
    }

    FILE *output_file = fopen(file_name, "w");
    if (output_file == NULL) {
        free(json);
        return false;
    }

    fprintf(output_file, json);
    fclose(output_file);
    free(json);

    return true;
}

/**
 * Выполняет парсинг файлов. В случае ошибок (невозможности открыть файл),
 * печатает сообщения на экран. Если количество файлов - 0,
 * то выполняется парсинг из stdin.
 *
 * @param files_count количество файлов
 * @param file_names имена файлов
 */
void
parse_files(int files_count, char **file_names) {
    if (files_count == 0) {
        yyparse();
        return;
    }

    for (int i = 0; i < files_count; i++) {
        FILE *eiffel_file = fopen(file_names[i], "r");
        if (eiffel_file == NULL) {
            perror(file_names[i]);
            continue;
        }

        current_file_path = file_names[i];

        // Сброс текущих номеров строки и колонки для нового файла
        yylloc.first_line = 1;
        yylloc.first_column = 1;
        yylloc.last_line = 1;
        yylloc.last_column = 1;

        yyrestart(eiffel_file);
        yyparse();
    }
}

/**
 * Печатает на экран сообщение о количестве найденных ошибок.
 * 
 * @param errors_count количество случившихся ошибок
 */
void
show_parsing_result(int errors_count) {
    if (errors_count == 1)
        fprintf(stderr, "Failed to parse, got 1 syntax error\n");
    else if (errors_count > 1)
        fprintf(stderr, "Failed to parse, got %d syntax errors\n", errors_count);
}

/**
 * Обрабатывает аргументы командной строки для парсера.
 * Парсер умеет обрабатывать два аргумента: -o <имя выходного файла> и -p.
 * Первый из них указываем имя для выходного json-файла, второй обозначает,
 * что в результате должен быть сгенерирован красиво отформатированный json-файл.
 *
 * @param argv количество аргументов командной строки
 * @param argv список аргументов командной строки
 * @param pretty_json выходной параметр: нужно ли красивое форматирование
 * @param output_file_name выходной параметр: имя генерируемого файла (NULL, если имя не предоставлено)
 *
 * @return индекс первого не-опционного аргумента
 */
int
process_args(int argc, char **argv, bool *pretty_json, char **output_file_name) {
    *pretty_json = false;
    *output_file_name = NULL;

    int opt;
    while ((opt = getopt(argc, argv, "o:p")) != -1) {
        switch (opt) {
            case 'o':
                if (optarg == NULL)
                    fprintf(stderr, "Parser warning: no output file name provided, waiting for output from stdin");
                *output_file_name = optarg;
                break;
            case 'p':
                *pretty_json = true;
                break;
        }
    }

    return optind;
}

int
main(int argc, char **argv) {
    #ifdef DEBUG_PARSER
        yydebug = 1;
    #endif

    bool pretty_json;
    char *output_file_name;
    int file_start_idx = process_args(argc, argv, &pretty_json, &output_file_name); 

    int files_count = argc - file_start_idx;
    parse_files(files_count, argv + file_start_idx);

    show_parsing_result(errors_count);

    if (errors_count == 0) {
        Json *output_tree = mk_program(found_classes);

        if (!write_output_tree(output_file_name, output_tree, pretty_json)) {
            fprintf(stderr, "Failed to open output file");
            return EXIT_FAILURE;
        }

        return EXIT_SUCCESS;
    }

    return EXIT_FAILURE;
}

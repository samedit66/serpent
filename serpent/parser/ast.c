#include "./include/json.h"
#include "./include/lex_utils.h"
#include "./eiffel.tab.h"

extern YYLTYPE current_node_loc;
extern char *current_file_path; // В файле eiffel.y

Json*
mk_current_loc_info() {
    Json *loc = Json_new();

    Json_add_int_to_object(loc, "first_line", current_node_loc.first_line);
    Json_add_int_to_object(loc, "first_column", current_node_loc.first_column);
    Json_add_int_to_object(loc, "last_line", current_node_loc.last_line);
    Json_add_int_to_object(loc, "last_column", current_node_loc.last_column);

    if (current_file_path == NULL)
        Json_add_null_to_object(loc, "filename");
    else
        Json_add_string_to_object(loc, "filename", escape(current_file_path));

    return loc;
}

void
add_type_to_node(Json *node, char *type_name) {
    Json_add_string_to_object(node, "type", type_name);
    Json_add_object_to_object(node, "location", mk_current_loc_info());
}

Json*
mk_int_const(int val) {
    Json *node = Json_new();
    add_type_to_node(node, "int_const");
    Json_add_int_to_object(node, "value", val);
    return node;
}

Json*
mk_char_const(char *char_const) {
    Json *node = Json_new();
    add_type_to_node(node, "char_const");
    Json_add_string_to_object(node, "value", char_const);
    return node;
}

Json*
mk_real_const(double val) {
    Json *node = Json_new();
    add_type_to_node(node, "real_const");
    Json_add_double_to_object(node, "value", val);
    return node;
}

Json*
mk_string_const(char *val) {
    Json *node = Json_new();
    add_type_to_node(node, "string_const");
    Json_add_string_to_object(node, "value", val);
    return node;
}

Json*
mk_result_const() {
    Json *node = Json_new();
    add_type_to_node(node, "result_const");
    return node;
}

Json*
mk_current_const() {
    Json *node = Json_new();
    add_type_to_node(node, "current_const");
    return node;
}

Json*
mk_boolean_const(bool val) {
    Json *node = Json_new();
    add_type_to_node(node, "boolean_const");
    Json_add_bool_to_object(node, "value", val);
    return node;
}

Json*
mk_void_const() {
    Json *node = Json_new();
    add_type_to_node(node, "void_const");
    return node;
}

Json*
mk_ident_lit(char *ident) {
    Json *node = Json_new();
    add_type_to_node(node, "ident_lit");
    Json_add_string_to_object(node, "value", ident);
    return node;
}

Json*
mk_bin_op(char *op_name, Json *left, Json *right) {
    Json *node = Json_new();
    add_type_to_node(node, "binop");
    Json_add_string_to_object(node, "binop_type", op_name);
    Json_add_object_to_object(node, "left", left);
    Json_add_object_to_object(node, "right", right);
    return node;
}

Json*
mk_unary_op(char *op_name, Json *arg) {
    Json *node = Json_new();
    add_type_to_node(node, "unop");
    Json_add_string_to_object(node, "unop_type", op_name);
    Json_add_object_to_object(node, "arg", arg);\
    return node;
}

Json*
mk_simple_call(char *feature_name, Json *args_list) {
    Json *simple_call = Json_new();
    Json_add_string_to_object(simple_call, "name", feature_name);
    Json_add_array_to_object(simple_call, "args_list", args_list);
    return simple_call;
}

Json*
mk_list() {
    return Json_new();
}

Json*
add_to_list(Json *list, Json *element) {
    Json_add_object_to_array(list, element);
    return list;
}

Json*
add_ident_to_list(Json *list, char *ident) {
    Json_add_string_to_array(list, ident);
    return list;
}

Json*
mk_simple_call_no_args(char *feature_name) {
    return mk_simple_call(feature_name, mk_list());
}

Json*
mk_precursor_args_call(char *parent_name, Json *args_list) {
    Json *node = Json_new();
    add_type_to_node(node, "precursor_call");
    if (parent_name == NULL)
        Json_add_null_to_object(node, "parent_name");
    else
        Json_add_string_to_object(node, "parent_name", parent_name);
    Json_add_array_to_object(node, "args_list", args_list);
    return node;
}

Json*
mk_precursor_no_args_call(char *parent_name) {
    return mk_precursor_args_call(parent_name, mk_list());
}

Json*
mk_feature_with_owner_call(Json *owner, Json *feature) {
    Json *node = Json_new();
    add_type_to_node(node, "feature_call");
    
    if (owner != NULL)
        Json_add_object_to_object(node, "owner", owner);
    else
        Json_add_null_to_object(node, "owner");
    Json_add_object_to_object(node, "feature", feature);
    return node;
}

Json*
mk_feature_with_unknown_owner_call(Json *feature) {
    return mk_feature_with_owner_call(NULL, feature);
}

Json*
mk_bracket_access(Json *source, Json *index) {
    Json *node = Json_new();
    add_type_to_node(node, "bracket_access");
    Json_add_object_to_object(node, "source", source);
    Json_add_object_to_object(node, "index", index);
    return node;
}

Json*
mk_if_expr(Json *cond, Json *then_expr, Json *alt_exprs, Json *else_expr) {
    Json *node = Json_new();
    add_type_to_node(node, "if_expr");
    Json_add_object_to_object(node, "cond", cond);
    Json_add_object_to_object(node, "then_expr", then_expr);
    Json_add_array_to_object(node, "elseif_exprs", alt_exprs);
    Json_add_object_to_object(node, "else_expr", else_expr);
    return node;
}

Json*
add_elseif_expr(Json *alts, Json *cond, Json *expr) {
    Json *alt = Json_new();
    add_type_to_node(alt, "elseif_expr");
    Json_add_object_to_object(alt, "cond", cond);
    Json_add_object_to_object(alt, "expr", expr);
    Json_add_object_to_array(alts, alt);
    return alts;
}

Json*
mk_program(Json *program) {
    Json *node = Json_new();
    //add_type_to_node(node, "root");
    Json_add_array_to_object(node, "classes", program);
    return node;
}

Json*
mk_if_stmt(Json *cond, Json *then_stmt_list, Json *alt_stmts, Json *else_stmt_list) {
    Json *node = Json_new();
    add_type_to_node(node, "if_stmt");
    Json_add_object_to_object(node, "cond", cond);
    Json_add_array_to_object(node, "then_clause", then_stmt_list);
    Json_add_array_to_object(node, "elseif_clauses", alt_stmts);
    Json_add_array_to_object(node, "else_clause", else_stmt_list);
    return node;
}

Json*
add_elseif_stmt(Json *alts, Json *cond, Json *stmt_list) {
    Json *alt = Json_new();
    add_type_to_node(alt, "elseif_clause");
    Json_add_object_to_object(alt, "cond", cond);
    Json_add_array_to_object(alt, "body", stmt_list);
    Json_add_object_to_array(alts, alt);
    return alts;
}

Json*
mk_assign_stmt(Json *left, Json *right) {
    Json *node = Json_new();
    add_type_to_node(node, "assign_stmt");
    Json_add_object_to_object(node, "left", left);
    Json_add_object_to_object(node, "right", right);
    return node;
}

Json*
mk_loop_stmt(Json *init_stmt_list, Json *cond, Json *body_stmt_list) {
    Json *node = Json_new();
    add_type_to_node(node, "loop_stmt");
    Json_add_array_to_object(node, "init", init_stmt_list);
    Json_add_object_to_object(node, "cond", cond);
    Json_add_array_to_object(node, "body", body_stmt_list);
    return node;
}

Json*
mk_inspect_stmt(Json *expr, Json *when_clauses, Json *else_stmt_list) {
    Json *node = Json_new();
    add_type_to_node(node, "inspect_stmt");
    Json_add_object_to_object(node, "expr", expr);
    Json_add_array_to_object(node, "when_clauses", when_clauses);
    Json_add_array_to_object(node, "else_clause", else_stmt_list);
    return node;
}

Json*
add_alt_when_clause(Json *when_clauses, Json *choices, Json *body) {
    Json *when_stmt = Json_new();
    add_type_to_node(when_stmt, "when_clause");
    Json_add_array_to_object(when_stmt, "choices", choices);
    Json_add_array_to_object(when_stmt, "body", body);
    Json_add_object_to_array(when_clauses, when_stmt);
    return when_clauses;
}

Json*
mk_choice_interval(Json *start, Json *end) {
    Json *node = Json_new();
    add_type_to_node(node, "choice_interval");
    Json_add_object_to_object(node, "start", start);
    Json_add_object_to_object(node, "end", end);
    return node;
}

Json*
mk_type(char *type_name) {
    Json *user_type = Json_new();
    add_type_to_node(user_type, "type_spec");
    Json_add_string_to_object(user_type, "type_name", type_name);
    return user_type;
}

Json*
mk_integer_type() {
    return mk_type("INTEGER");
}

Json*
mk_real_type() {
    return mk_type("REAL");
}

Json*
mk_string_type() {
    return mk_type("STRING");
}

Json*
mk_character_type() {
    return mk_type("CHARACTER");
}

Json*
mk_boolean_type() {
    return mk_type("BOOLEAN");
}

Json*
mk_like_type(Json *like_what) {
    Json *type_spec_like = Json_new();
    add_type_to_node(type_spec_like, "type_spec_like");
    Json_add_object_to_object(type_spec_like, "like_what", like_what);
    return type_spec_like;
}

Json*
mk_like_current_type() {
    return mk_like_type(mk_current_const());
}

Json*
mk_like_other_field_type(char *field_name) {
    return mk_like_type(mk_ident_lit(field_name));
}

Json*
mk_generic_user_type(char *type_name, Json *type_list) {
    Json *generic_type_spec = Json_new();
    add_type_to_node(generic_type_spec, "generic_type_spec");
    Json_add_string_to_object(generic_type_spec, "type_name", type_name);
    Json_add_array_to_object(generic_type_spec, "type_list", type_list);
    return generic_type_spec;
}

Json*
mk_generic_array_type(Json *type_list) {
    return mk_generic_user_type("ARRAY", type_list);
}

Json*
mk_generic_tuple_type(Json *type_list) {
    return mk_generic_user_type("TUPLE", type_list);
}

Json*
mk_class_decl(Json *header, Json *inheritance, Json *creators, Json *features) {
    Json *class_decl = Json_new();

    add_type_to_node(class_decl, "class_decl");
    Json_add_object_to_object(class_decl, "header", header);
    Json_add_array_to_object(class_decl, "inheritance", inheritance);
    Json_add_array_to_object(class_decl, "creators", creators);
    Json_add_array_to_object(class_decl, "features", features);

    return class_decl;
}

Json*
mk_class_header(char *class_name, Json *generics_list, bool is_deferred) {
    Json *class_header = Json_new();

    Json_add_string_to_object(class_header, "name", class_name);
    Json_add_bool_to_object(class_header, "is_deferred", is_deferred);
    Json_add_array_to_object(class_header, "generics", generics_list);

    return class_header;
}

Json*
mk_parent_info(char *parent_class_name, Json *generics_list) {
    Json *class_header = Json_new();

    Json_add_string_to_object(class_header, "name", parent_class_name);
    Json_add_array_to_object(class_header, "generics", generics_list);

    return class_header;
}

Json*
mk_effective_class_header(char *class_name, Json *generics_list) {
    return mk_class_header(class_name, generics_list, false);
}

Json*
mk_deferred_class_header(char *class_name, Json *generics_list) {
    return mk_class_header(class_name, generics_list, true);
}

Json*
mk_constrained_generic(Json *generic_type, Json *parent) {
    Json *constrained_generic = Json_new();

    add_type_to_node(constrained_generic, "generic");
    Json_add_object_to_object(constrained_generic, "generic_type", generic_type);
    
    if (parent == NULL)
        Json_add_null_to_object(constrained_generic, "parent");
    else
        Json_add_object_to_object(constrained_generic, "parent", parent);

    return constrained_generic;
}

Json*
mk_generic(Json *generic_type) {
    return mk_constrained_generic(generic_type, NULL);
}

Json*
mk_inherit_clause(Json *parent, Json *rename_clause, Json *undefine_clause, Json *redefine_clause, Json *select_clause) {
    Json *inherit_clause = Json_new();

    add_type_to_node(inherit_clause, "parent");
    Json_add_object_to_object(inherit_clause, "parent_header", parent);
    Json_add_array_to_object(inherit_clause, "rename_clause", rename_clause);
    Json_add_array_to_object(inherit_clause, "undefine_clause", undefine_clause);
    Json_add_array_to_object(inherit_clause, "redefine_clause", redefine_clause);
    Json_add_array_to_object(inherit_clause, "select_clause", select_clause);

    return inherit_clause;
}

Json*
mk_alias(char *original_name, char *alias_name) {
    Json *alias = Json_new();

    add_type_to_node(alias, "alias");
    Json_add_string_to_object(alias, "original_name", original_name);
    Json_add_string_to_object(alias, "alias_name", alias_name);

    return alias;
}

Json*
mk_feature_clause(Json *clients, Json *feature_list) {
    Json *feature_clause = Json_new();

    add_type_to_node(feature_clause, "feature_clause");
    Json_add_array_to_object(feature_clause, "clients", clients);
    Json_add_array_to_object(feature_clause, "feature_list", feature_list);

    return feature_clause;
}

Json*
mk_class_field(Json *name_and_type) {
    Json *class_field = Json_new();

    add_type_to_node(class_field, "class_field");
    Json_add_object_to_object(class_field, "name_and_type", name_and_type);

    return class_field;
}

Json*
mk_class_constant(Json *name_and_type, Json *constant) {
    Json *class_constant = Json_new();

    add_type_to_node(class_constant, "class_constant");
    Json_add_object_to_object(class_constant, "name_and_type", name_and_type);
    Json_add_object_to_object(class_constant, "constant_value", constant);

    return class_constant;
}

Json*
mk_name_and_type(Json *names, Json *type_spec) {
    Json *name_and_type = Json_new();

    Json_add_object_to_object(name_and_type, "field_type", type_spec);
    Json_add_array_to_object(name_and_type, "names", names);

    return name_and_type;
}

Json*
mk_local_var_decl(Json *name_and_type) {
    Json *var_decl = Json_new();

    add_type_to_node(var_decl, "var_decl");
    Json_add_object_to_object(var_decl, "name_and_type", name_and_type);

    return var_decl;
}

Json*
mk_routine_with_args(Json *names, Json *params_list, Json *return_type, Json *routine_body) {
    Json *routine = Json_new();

    add_type_to_node(routine, "class_routine");
    Json *name_and_type = mk_name_and_type(names, return_type);
    Json_add_object_to_object(routine, "name_and_type", name_and_type);
    Json_add_array_to_object(routine, "params", params_list);
    Json_add_object_to_object(routine, "body", routine_body);

    return routine;
}

Json*
mk_void_routine_with_args(Json *names, Json *params_list, Json *routine_body) {
    return mk_routine_with_args(names, params_list, mk_type("<VOID>"), routine_body);
}

Json*
mk_void_routine_with_no_args(Json *names, Json *routine_body) {
    return mk_void_routine_with_args(names, mk_list(), routine_body);
}

Json*
mk_routine_with_no_args(Json *name_and_type, Json *routine_body) {
    Json *routine = Json_new();

    add_type_to_node(routine, "class_routine");
    Json_add_object_to_object(routine, "name_and_type", name_and_type);
    Json_add_array_to_object(routine, "params", mk_list());
    Json_add_object_to_object(routine, "body", routine_body);

    return routine;
}

Json*
mk_routine_body(bool is_deferred, Json *local, Json *require, Json *do_clause, Json *then, Json *ensure) {
    Json *routine_body = Json_new();

    add_type_to_node(routine_body, "routine_body");
    Json_add_bool_to_object(routine_body, "is_deferred", is_deferred);
    Json_add_array_to_object(routine_body, "local", local == NULL ? mk_list() : local);
    Json_add_array_to_object(routine_body, "require", require == NULL ? mk_list() : require);
    Json_add_array_to_object(routine_body, "do", do_clause == NULL ? mk_list() : do_clause);
    if (then == NULL)
        Json_add_null_to_object(routine_body, "then");
    else
        Json_add_object_to_object(routine_body, "then", then);
    Json_add_array_to_object(routine_body, "ensure", ensure == NULL ? mk_list() : ensure);

    return routine_body;
}

Json*
mk_effective_routine_body(Json *local, Json *require, Json *do_clause, Json *then, Json *ensure) {
    return mk_routine_body(false, local, require, do_clause, then, ensure);
}

Json*
mk_deferred_routine_body(Json *require, Json *ensure) {
    return mk_routine_body(true, mk_list(), require, NULL, NULL, ensure);
}

Json*
mk_tagged_cond(char *tag, Json *cond) {
    Json *tagged_cond = Json_new();

    add_type_to_node(tagged_cond, "tagged_cond");

    if (tag == NULL)
        Json_add_null_to_object(tagged_cond, "tag");
    else
        Json_add_string_to_object(tagged_cond, "tag", tag);
    
    Json_add_object_to_object(tagged_cond, "cond", cond);

    return tagged_cond;
}

Json*
mk_manifest_array(Json *manifest_array_content) {
    Json *manifest_array = Json_new();

    add_type_to_node(manifest_array, "manifest_array");
    Json_add_array_to_object(manifest_array, "content", manifest_array_content);

    return manifest_array;
}

Json*
mk_manifest_tuple(Json *manifest_tuple_content) {
    Json *manifest_tuple = Json_new();

    add_type_to_node(manifest_tuple, "manifest_tuple");
    Json_add_array_to_object(manifest_tuple, "content", manifest_tuple_content);

    return manifest_tuple;
}

Json*
mk_create(Json *object_type, Json *constructor_call) {
    Json *create = Json_new();

    add_type_to_node(create, "create_stmt");
    
    if (object_type != NULL)
        Json_add_object_to_object(create, "object_type", object_type);
    else
        Json_add_null_to_object(create, "object_type");

    Json_add_object_to_object(create, "constructor_call", constructor_call);

    return create;
}

Json*
mk_create_expr(Json *object_type, Json *constructor_call) {
    Json *create_expr = Json_new();

    add_type_to_node(create_expr, "create_expr");
    Json_add_object_to_object(create_expr, "object_type", object_type);
    Json_add_object_to_object(create_expr, "constructor_call", constructor_call);

    return create_expr;
}

Json*
mk_feature_parameter(Json *name_and_type) {
    Json *parameter = Json_new();

    add_type_to_node(parameter, "parameter");
    Json_add_object_to_object(parameter, "name_and_type", name_and_type);

    return parameter;
}

Json*
mk_external_routine_body(char *language_name, char *external_routine_name, Json *require, Json *ensure) {
    Json *external_routine_body = Json_new();

    add_type_to_node(external_routine_body, "external_routine_body");
    Json_add_string_to_object(external_routine_body, "language", language_name);
    Json_add_string_to_object(external_routine_body, "alias", external_routine_name);
    Json_add_array_to_object(external_routine_body, "require", require == NULL ? mk_list() : require);
    Json_add_array_to_object(external_routine_body, "ensure", ensure == NULL ? mk_list() : ensure);

    return external_routine_body;
}

Json*
mk_constructor_call(char *object_name, Json *call) {
    Json *constructor = Json_new();

    add_type_to_node(constructor, "constructor_call");
    Json_add_string_to_object(constructor, "object", object_name);
    
    if (call == NULL)
        Json_add_null_to_object(constructor, "feature");
    else
        Json_add_object_to_object(constructor, "feature", call);

    return constructor;
}

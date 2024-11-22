#include "./include/json.h"
#include "./include/strbuf.h"

Json*
Json_new() {
    Json *object_or_array = (Json*) malloc(sizeof(Json));
    object_or_array->first = object_or_array->last = NULL;
    return object_or_array;
}

static Field*
_Json_new_field(Json *json, char *field_name, JsonValueType value_type) {
    Field *prev_field = json->last;

    Field *new_field = (Field*) malloc(sizeof(Field));
    new_field->value_type = value_type;
    new_field->field_name = field_name == NULL ? field_name : strdup(field_name);
    new_field->next_field = NULL;

    if (prev_field != NULL)
        prev_field->next_field = new_field;
    else
        json->first = new_field;
    
    json->last = new_field;
    return new_field;
}

Json*
Json_add_string_to_object(Json *object, char *field_name, char *value) {
    Field *new_field = _Json_new_field(object, field_name, JSON_STRING);
    new_field->str_value = value;
    return object;
}

Json*
Json_add_double_to_object(Json *object, char *field_name, double value) {
    Field *new_field = _Json_new_field(object, field_name, JSON_DOUBLE);
    new_field->double_value = value;
    return object;
}

Json*
Json_add_int_to_object(Json *object, char *field_name, int value) {
    Field *new_field = _Json_new_field(object, field_name, JSON_INT);
    new_field->int_value = value;
    return object;
}

Json*
Json_add_object_to_object(Json *object, char *field_name, Json *object_value) {
    Field *new_field = _Json_new_field(object, field_name, JSON_OBJECT);
    new_field->object_or_array = object_value;
    return object;
}

Json*
Json_add_array_to_object(Json *object, char *field_name, Json *array) {
    Field *new_field = _Json_new_field(object, field_name, JSON_ARRAY);
    new_field->object_or_array = array;
    return object;
}

Json*
Json_add_bool_to_object(Json *object, char *field_name, bool value) {
    Field *new_field = _Json_new_field(object, field_name, JSON_BOOL);
    new_field->bool_value = value;
    return object;
}

Json*
Json_add_null_to_object(Json *object, char *field_name) {
    Field *new_field = _Json_new_field(object, field_name, JSON_NULL);
    return object;
}

Json*
Json_add_string_to_array(Json *array, char *value) {
    return Json_add_string_to_object(array, NULL, value);
}

Json*
Json_add_double_to_array(Json *array, double value) {
    return Json_add_double_to_object(array, NULL, value);
}

Json*
Json_add_int_to_array(Json *array, int value) {
    return Json_add_int_to_object(array, NULL, value);
}

Json*
Json_add_object_to_array(Json *array, Json *object) {
    return Json_add_object_to_object(array, NULL, object);
}

Json*
Json_add_array_to_array(Json *array, Json *array_value) {
    return Json_add_array_to_object(array, NULL, array_value);
}

Json*
Json_add_bool_to_array(Json *array, bool value) {
    return Json_add_bool_to_object(array, NULL, value);
}

Json*
Json_add_null_to_array(Json *array) {
    return Json_add_null_to_object(array, NULL);
}

static inline void
_indent(StringBuffer *strbuf, int indent_level, char *indent_value) {
    for (int i = 0; i < indent_level; i++) {
        StringBuffer_append(strbuf, indent_value);
    }
}

static inline void
_append_int_to_buf(StringBuffer *strbuf, int value) {
    char buffer[20];
    itoa(value, buffer, 10);
    StringBuffer_append(strbuf, buffer);
}

static inline void
_append_double_to_buf(StringBuffer *strbuf, double value) {
    char buffer[20];
    sprintf(buffer, "%f", value);
    StringBuffer_append(strbuf, buffer);
}

static inline void
_append_string_to_buf(StringBuffer *strbuf, char *string) {
    StringBuffer_append(strbuf, "\"");
    StringBuffer_append(strbuf, string);
    StringBuffer_append(strbuf, "\"");
}

static inline void
_append_bool_to_buf(StringBuffer *strbuf, bool value) {
    if (value)
        StringBuffer_append(strbuf, "true");
    else
        StringBuffer_append(strbuf, "false");
}

static char*
_Json_field_as_string(Field *field, int indent_level, char *indent_value) {
    StringBuffer *strbuf = StringBuffer_empty();

    switch (field->value_type) {
        case JSON_STRING:
            _append_string_to_buf(strbuf, field->str_value);
            break;
        case JSON_INT:
            _append_int_to_buf(strbuf, field->int_value);
            break;
        case JSON_DOUBLE:
            _append_double_to_buf(strbuf, field->double_value);
            break;
        case JSON_BOOL:
            _append_bool_to_buf(strbuf, field->bool_value);
            break;
        case JSON_NULL:
            StringBuffer_append(strbuf, "null");
            break;
        case JSON_OBJECT:
        case JSON_ARRAY:
            Json *object_or_array = field->object_or_array;

            if (field->value_type == JSON_ARRAY)
                StringBuffer_append(strbuf, "[");
            else
                StringBuffer_append(strbuf, "{");

            indent_level++;
            Field *current_field = object_or_array->first;

            if (current_field != NULL)
                StringBuffer_append(strbuf, "\n");

            while (current_field != NULL) {
                _indent(strbuf, indent_level, indent_value);

                // Если это объект, то необходимо добавить имя поля перед самим значением
                if (field->value_type == JSON_OBJECT) {
                    _append_string_to_buf(strbuf, current_field->field_name);
                    StringBuffer_append(strbuf, ": ");
                }

                StringBuffer_append(
                    strbuf,
                    _Json_field_as_string(current_field, indent_level, indent_value)
                );

                if (field->value_type == JSON_ARRAY) {
                    if (current_field->next_field != NULL)
                        StringBuffer_append(strbuf, ",\n");
                    else
                        StringBuffer_append(strbuf, "\n");
                }
                else {
                    StringBuffer_append(strbuf, ";\n");
                }

                current_field = current_field->next_field;
            }

            indent_level--;
            _indent(strbuf, indent_level, indent_value);

            if (field->value_type == JSON_ARRAY)
                StringBuffer_append(strbuf, "]");
            else
                StringBuffer_append(strbuf, "}");
            break;
    }

    char *raw_buffer = strdup(strbuf->buffer);
    StringBuffer_delete(strbuf);
    return raw_buffer;
}

char*
Json_object_as_string(Json *json) {
    Field *root = (Field*) malloc(sizeof(Field));
    root->value_type = JSON_OBJECT;
    root->object_or_array = json;

    char *stringified = _Json_field_as_string(root, 0, "    ");

    free(root);

    return stringified;
}

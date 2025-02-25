from serpent.semantic_checker.type_check import TClass, TMethod, TField

from serpent.codegen.constant_pool import get_type_descriptor


def make_general_class(classes: list[TClass]) -> TClass:
    """
    Создаёт общий класс <GENERAL>, объединяя все методы и поля из списка классов.
    Если находятся дублирующиеся методы (одинаковая сигнатура: имя, возвращаемый тип и типы аргументов)
    или поля (одинаковое имя и тип), они не добавляются повторно.
    
    :param classes: Список объектов TClass, из которых будут извлечены методы и поля.
    :return: Новый объект TClass с именем "<GENERAL>", содержащий объединённые уникальные методы и поля.
    """
    def method_signature_key(method: TMethod) -> tuple:
        # Формируем ключ по: имя метода, дескриптор возвращаемого типа,
        # а затем дескрипторы всех параметров (порядок имеет значение)
        ret_desc = get_type_descriptor(method.return_type)
        params_desc = tuple(get_type_descriptor(param_type) for _, param_type in method.parameters)
        return (method.method_name, ret_desc, params_desc)

    def field_signature_key(field: TField) -> tuple:
        # Для поля ключ состоит из имени и дескриптора типа
        return (field.name, get_type_descriptor(field.expr_type))
    
    seen_methods = {}
    seen_fields = {}
    unique_methods: list[TMethod] = []
    unique_fields: list[TField] = []
    
    for cls in classes:
        for method in cls.methods:
            key = method_signature_key(method)
            if key not in seen_methods:
                seen_methods[key] = True
                unique_methods.append(method)
        for field in cls.fields:
            key = field_signature_key(field)
            if key not in seen_fields:
                seen_fields[key] = True
                unique_fields.append(field)
    
    return TClass(class_name="<GENERAL>", methods=unique_methods, fields=unique_fields)

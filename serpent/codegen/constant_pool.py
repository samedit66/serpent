from dataclasses import dataclass

from serpent.semantic_checker.symtab import Type
from serpent.semantic_checker.type_check import (
    TExpr,
    TIntegerConst,
    TRealConst,
    TCharacterConst,
    TStringConst,
    TBoolConst,
    TVoidConst,
    TFeatureCall,
    TCreateExpr,
    TBinaryOp,
    TUnaryOp,
    TVariable,
    TStatement,
    TAssignment,
    TIfStmt,
    TLoopStmt,
    TRoutineCall,
    TField,
    TMethod,
    TExternalMethod,
    TUserDefinedMethod,
    TClass)


@dataclass(frozen=True)
class CONSTANT:
    index: int


@dataclass(frozen=True)
class CONSTANT_Utf8(CONSTANT):
    text: str


@dataclass(frozen=True)
class CONSTANT_Integer(CONSTANT):
    const: int


@dataclass(frozen=True)
class CONSTANT_Float(CONSTANT):
    const: float


@dataclass(frozen=True)
class CONSTANT_String(CONSTANT):
    string_index: int


@dataclass(frozen=True)
class CONSTANT_NameAndType(CONSTANT):
    name_const_index: int
    type_const_index: int


@dataclass(frozen=True)
class CONSTANT_Class(CONSTANT):
    name_index: int


@dataclass(frozen=True)
class CONSTANT_Fieldref(CONSTANT):
    class_index: int
    name_and_type_index: int


@dataclass(frozen=True)
class CONSTANT_Methodref(CONSTANT):
    class_index: int
    name_and_type_index: int


class ConstantPool:
    def __init__(self) -> None:
        self.constant_pool: list[CONSTANT] = []

    @property
    def next_index(self) -> int:
        return len(self.constant_pool) + 1

    def find_or_create_constant_utf8(self, utf8_text: str) -> int:
        for constant in self.constant_pool:
            if isinstance(constant, CONSTANT_Utf8) and constant.text == utf8_text:
                return constant.index
        new_const = CONSTANT_Utf8(self.next_index, utf8_text)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_class(self, class_name: str) -> int:
        utf8_const_index = self.find_or_create_constant_utf8(class_name)
        class_const = CONSTANT_Class(self.next_index, utf8_const_index)
        self.constant_pool.append(class_const)
        return class_const.index

    def add_constant_integer(self, value: int) -> int:
        for constant in self.constant_pool:
            if isinstance(constant, CONSTANT_Integer) and constant.const == value:
                return constant.index
        new_const = CONSTANT_Integer(self.next_index, value)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_float(self, value: float) -> int:
        for constant in self.constant_pool:
            if isinstance(constant, CONSTANT_Float) and constant.const == value:
                return constant.index
        new_const = CONSTANT_Float(self.next_index, value)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_string(self, utf8_index: int) -> int:
        for constant in self.constant_pool:
            if isinstance(constant, CONSTANT_String) and constant.string_index == utf8_index:
                return constant.index
        new_const = CONSTANT_String(self.next_index, utf8_index)
        self.constant_pool.append(new_const)
        return new_const.index


# --- Вспомогательные функции для дескрипторов и обхода AST ---

def add_package_prefix(class_name: str, package: str = "org.eiffel.base") -> str:
    parts = [*package.split("."), class_name]
    return "/".join(parts)


def get_type_descriptor(typ: Type) -> str:
    """
    Генерирует дескриптор типа для виртуальной машины Java.
    Для примитивных типов используется однобуквенное обозначение,
    для ссылочных типов возвращается формат "L<fully-qualified-name>;"
    """
    if typ.full_name == "<VOID>":
        return "V"
    # Если имя уже содержит '/', считаем его полностью квалифицированным
    fq_name = typ.name if "/" in typ.name else add_package_prefix(typ.name)
    return f"L{fq_name};"


def get_method_descriptor(method: TMethod) -> str:
    """
    Формирует дескриптор метода.
    """
    params_desc = "".join(get_type_descriptor(param_type) for _, param_type in method.parameters)
    # При отсутствии информации о возвращаемом типе считаем, что метод является процедурой.
    return_desc = get_type_descriptor(method.return_type)
    return f"({params_desc}){return_desc}"


def find_constant_class_index(constant_pool: ConstantPool, fq_class_name: str) -> int:
    """
    Ищет в пуле констант константу типа CONSTANT_Class, ссылающуюся на данный fully-qualified name.
    """
    for const in constant_pool.constant_pool:
        if isinstance(const, CONSTANT_Class):
            for utf8_const in constant_pool.constant_pool:
                if isinstance(utf8_const, CONSTANT_Utf8) and utf8_const.index == const.name_index:
                    if utf8_const.text == fq_class_name:
                        return const.index
    raise ValueError(f"Class constant for {fq_class_name} not found in constant pool.")


def process_expression_literals(expr: TExpr, constant_pool: ConstantPool) -> None:
    """
    Рекурсивно обходит выражение и добавляет в пул констант литералы:
      - TIntegerConst  -> CONSTANT_Integer
      - TRealConst     -> CONSTANT_Float
      - TStringConst   -> CONSTANT_String (через CONSTANT_Utf8)
      - TCharacterConst-> добавляется как целочисленное значение (ordinal)
      - TBoolConst     -> представляется как 1/0 (CONSTANT_Integer)
    Также рекурсивно обрабатываются составные выражения.
    """
    if isinstance(expr, TIntegerConst):
        constant_pool.add_constant_integer(expr.value)
    elif isinstance(expr, TRealConst):
        constant_pool.add_constant_float(expr.value)
    elif isinstance(expr, TStringConst):
        utf8_idx = constant_pool.find_or_create_constant_utf8(expr.value)
        constant_pool.add_constant_string(utf8_idx)
    elif isinstance(expr, TCharacterConst):
        constant_pool.add_constant_integer(ord(expr.value))
    elif isinstance(expr, TBoolConst):
        constant_pool.add_constant_integer(1 if expr.value else 0)
    elif isinstance(expr, TFeatureCall):
        if expr.owner is not None:
            process_expression_literals(expr.owner, constant_pool)
        for arg in expr.arguments:
            process_expression_literals(arg, constant_pool)
    elif isinstance(expr, TCreateExpr):
        for arg in expr.arguments:
            process_expression_literals(arg, constant_pool)
    elif isinstance(expr, TBinaryOp):
        process_expression_literals(expr.left, constant_pool)
        process_expression_literals(expr.right, constant_pool)
    elif isinstance(expr, TUnaryOp):
        process_expression_literals(expr.argument, constant_pool)
    # Для TVariable и TVoidConst ничего не делаем.


def process_statement_literals(stmt: TStatement, constant_pool: ConstantPool) -> None:
    """
    Рекурсивно обходит оператор и обрабатывает все входящие в него выражения.
    """
    if isinstance(stmt, TAssignment):
        process_expression_literals(stmt.lvalue, constant_pool)
        process_expression_literals(stmt.rvalue, constant_pool)
    elif isinstance(stmt, TIfStmt):
        process_expression_literals(stmt.condition, constant_pool)
        for s in stmt.then_branch:
            process_statement_literals(s, constant_pool)
        for s in stmt.else_branch:
            process_statement_literals(s, constant_pool)
        for cond, stmts in stmt.elseif_branches:
            process_expression_literals(cond, constant_pool)
            for s in stmts:
                process_statement_literals(s, constant_pool)
    elif isinstance(stmt, TLoopStmt):
        for s in stmt.init_stmts:
            process_statement_literals(s, constant_pool)
        process_expression_literals(stmt.until_cond, constant_pool)
        for s in stmt.body:
            process_statement_literals(s, constant_pool)
    elif isinstance(stmt, TRoutineCall):
        process_expression_literals(stmt.feature_call, constant_pool)


# --- Функция формирования Constant Pool для класса ---

def get_external_method_descriptor(method: TExternalMethod) -> str:
    """
    Формирует дескриптор метода, где первым параметром всегда является this типа General,
    а затем идут остальные параметры, сгенерированные с использованием get_type_descriptor.
    
    Например, если метод имеет параметры (int, float) и возвращает void, дескриптор будет:
      (Lcom/eiffel/base/General;IF)V
    """
    # Жёстко задаём тип для this, как указано: GENERAL -> "Lcom/eiffel/base/GENERAL;"
    this_descriptor = "Lcom/eiffel/base/GENERAL;"
    # Генерируем дескрипторы для остальных параметров
    params_desc = "".join(get_type_descriptor(param_type) for _, param_type in method.parameters)
    # Собираем дескриптор с учетом того, что первый параметр — это this
    full_params_desc = this_descriptor + params_desc

    # Дескриптор возвращаемого типа
    return_desc = get_type_descriptor(method.return_type)
    return f"({full_params_desc}){return_desc}"

def process_external_method(constant_pool: ConstantPool, method: TExternalMethod) -> None:
    """
    Обрабатывает ExternalMethod и создаёт в пуле констант записи для вызова
    статического Java-метода на основе alias, например:
      alias "com.eiffel.base.Any.write"
    Предполагается, что метод принимает один параметр типа General и возвращает void.
    """
    full_alias = method.alias  # например, "com.eiffel.base.Any.write"
    parts = full_alias.split('.')
    if len(parts) < 2:
        raise ValueError(f"Incorrect alias: '{full_alias}'")
    
    # Имя метода – последний компонент, а имя класса – всё, что до него
    java_method_name = parts[-1]
    java_class_name = ".".join(parts[:-1])
    
    # Преобразуем имя класса в формат с разделителями '/'
    fq_java_class_name = java_class_name.replace('.', '/')
    
    # Добавляем CONSTANT_Class для Java-класса
    class_const_idx = constant_pool.add_constant_class(fq_java_class_name)
    
    # Добавляем CONSTANT_Utf8 для имени метода
    method_name_idx = constant_pool.find_or_create_constant_utf8(java_method_name)
    
    # Формируем дескриптор метода.
    # В данном примере метод статический и принимает один параметр типа General,
    # который должен быть представлен как "Lcom/eiffel/base/General;"
    method_descriptor = get_external_method_descriptor(method)
    method_desc_idx = constant_pool.find_or_create_constant_utf8(method_descriptor)
    
    # Создаём CONSTANT_NameAndType для метода
    nat_method = CONSTANT_NameAndType(
        constant_pool.next_index,
        name_const_index=method_name_idx,
        type_const_index=method_desc_idx
    )
    constant_pool.constant_pool.append(nat_method)
    nat_method_idx = nat_method.index
    
    # Создаём CONSTANT_Methodref, ссылающуюся на класс и NameAndType
    methodref = CONSTANT_Methodref(
        constant_pool.next_index,
        class_index=class_const_idx,
        name_and_type_index=nat_method_idx
    )
    constant_pool.constant_pool.append(methodref)


def make_constant_pool(tclass: TClass) -> ConstantPool:
    """
    Формирует Constant Pool для заданного класса tclass. В пул добавляются:
      - Константа для полного имени класса.
      - Для каждого поля:
          * CONSTANT_Utf8 для имени поля.
          * CONSTANT_Utf8 для дескриптора типа поля.
          * CONSTANT_NameAndType для поля.
          * CONSTANT_Fieldref, ссылающаяся на класс и NameAndType.
      - Для каждого метода:
          * CONSTANT_Utf8 для имени метода.
          * CONSTANT_Utf8 для дескриптора метода.
          * CONSTANT_NameAndType для метода.
          * CONSTANT_Methodref, ссылающаяся на класс и NameAndType.
      - Кроме того, если в теле метода встречаются литералы (числовые, строковые и т.п.),
        они добавляются в пул.
    """
    constant_pool = ConstantPool()

    # Добавляем константу для класса.
    fq_class_name = add_package_prefix(tclass.class_name)
    constant_pool.add_constant_class(fq_class_name)

    # Обработка полей класса.
    for field in tclass.fields:
        # Добавляем имя поля (CONSTANT_Utf8).
        field_name_idx = constant_pool.find_or_create_constant_utf8(field.name)
        # Получаем дескриптор типа поля.
        field_descriptor = get_type_descriptor(field.expr_type)
        field_desc_idx = constant_pool.find_or_create_constant_utf8(field_descriptor)
        # Создаем CONSTANT_NameAndType для поля.
        nat_field = CONSTANT_NameAndType(
            constant_pool.next_index,
            name_const_index=field_name_idx,
            type_const_index=field_desc_idx
        )
        constant_pool.constant_pool.append(nat_field)
        nat_field_idx = nat_field.index
        # Создаем CONSTANT_Fieldref, ссылающуюся на класс и NameAndType.
        class_const_idx = find_constant_class_index(constant_pool, fq_class_name)
        fieldref = CONSTANT_Fieldref(
            constant_pool.next_index,
            class_index=class_const_idx,
            name_and_type_index=nat_field_idx
        )
        constant_pool.constant_pool.append(fieldref)

    # Обработка методов класса.
    for method in tclass.methods:
        if isinstance(method, TExternalMethod):
            # Обрабатываем внешний метод с использованием alias.
            process_external_method(constant_pool, method)
        else:
            # Добавляем имя метода.
            method_name_idx = constant_pool.find_or_create_constant_utf8(method.method_name)
            # Формируем дескриптор метода.
            method_descriptor = get_method_descriptor(method)
            method_desc_idx = constant_pool.find_or_create_constant_utf8(method_descriptor)
            # Создаем CONSTANT_NameAndType для метода.
            nat_method = CONSTANT_NameAndType(
                constant_pool.next_index,
                name_const_index=method_name_idx,
                type_const_index=method_desc_idx
            )
            constant_pool.constant_pool.append(nat_method)
            nat_method_idx = nat_method.index
            # Создаем CONSTANT_Methodref, ссылающуюся на класс и NameAndType.
            class_const_idx = find_constant_class_index(constant_pool, fq_class_name)
            methodref = CONSTANT_Methodref(
                constant_pool.next_index,
                class_index=class_const_idx,
                name_and_type_index=nat_method_idx
            )
            constant_pool.constant_pool.append(methodref)

            # Если метод определен пользователем, обходим его тело для поиска литералов.
            if isinstance(method, TUserDefinedMethod):
                for stmt in method.body:
                    process_statement_literals(stmt, constant_pool)

    return constant_pool


def pretty_print_constant_pool(pool: ConstantPool) -> None:
    print("Constant Pool:")
    print("-" * 40)
    for const in pool.constant_pool:
        if isinstance(const, CONSTANT_Utf8):
            print(f"{const.index:3}: CONSTANT_Utf8      : '{const.text}'")
        elif isinstance(const, CONSTANT_Integer):
            print(f"{const.index:3}: CONSTANT_Integer   : {const.const}")
        elif isinstance(const, CONSTANT_Float):
            print(f"{const.index:3}: CONSTANT_Float     : {const.const}")
        elif isinstance(const, CONSTANT_String):
            print(f"{const.index:3}: CONSTANT_String    : string_index={const.string_index}")
        elif isinstance(const, CONSTANT_NameAndType):
            print(f"{const.index:3}: CONSTANT_NameAndType: name_index={const.name_const_index}, type_index={const.type_const_index}")
        elif isinstance(const, CONSTANT_Class):
            print(f"{const.index:3}: CONSTANT_Class     : name_index={const.name_index}")
        elif isinstance(const, CONSTANT_Fieldref):
            print(f"{const.index:3}: CONSTANT_Fieldref  : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        elif isinstance(const, CONSTANT_Methodref):
            print(f"{const.index:3}: CONSTANT_Methodref : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        else:
            print(f"{const.index:3}: Unknown constant type: {const}")
    print("-" * 40)


from abc import ABC, abstractmethod
from dataclasses import dataclass
import struct

from serpent.errors import CompilerError
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
from serpent.codegen.byte_utils import *


DEFAULT_PACKAGE = "com.eiffel.base"
"""Пакет, в котором будут все классы, объявленные программистом
или в стандартной библиотеке
"""

ROOT_CLASS_NAME = "GENERAL"
"""Название корневого класса, который будет обладать всеми методами всех
классов в программе. Является родителем класса ANY, определенного в
стандартной библиотеки Eiffel
"""

PLATFORM_CLASS_NAME = "PLATFORM"
"""Название класса из RTL-библиотеки, который определяет способы
одностороннего (Eiffel -> Java) взиамодействия между Eiffel и Java классами.
Является родителем для класса GENERAL
"""

COMPILER_NAME = "serpent"
"""Имя компилятора, используется в отладочных целях при печати
сообщений об ошибках
"""


@dataclass(frozen=True)
class CONSTANT(ABC):
    index: int

    @property
    @abstractmethod
    def tag(self) -> int: ...

    @abstractmethod
    def to_bytes(self) -> bytes: ...


@dataclass(frozen=True)
class CONSTANT_Utf8(CONSTANT):
    text: str

    @property
    def tag(self) -> int:
        return 1
    
    def to_bytes(self) -> bytes:
        text_bytes = u1_seq(self.text)
        return merge_bytes(u1(self.tag), u2(len(text_bytes)), text_bytes)


@dataclass(frozen=True)
class CONSTANT_Integer(CONSTANT):
    const: int

    @property
    def tag(self) -> int:
        return 3
    
    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s4(self.const))


@dataclass(frozen=True)
class CONSTANT_Float(CONSTANT):
    const: float

    @property
    def tag(self) -> int:
        return 4
    
    def to_bytes(self) -> bytes:
        # Упаковываем float в 4 байта в формате IEEE 754 (big-endian)
        return merge_bytes(u1(self.tag), struct.pack(">f", self.const))


@dataclass(frozen=True)
class CONSTANT_String(CONSTANT):
    string_index: int

    @property
    def tag(self) -> int:
        return 8

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.string_index))


@dataclass(frozen=True)
class CONSTANT_NameAndType(CONSTANT):
    name_const_index: int
    type_const_index: int

    @property
    def tag(self) -> int:
        return 12

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.name_const_index), u2(self.type_const_index))


@dataclass(frozen=True)
class CONSTANT_Class(CONSTANT):
    name_index: int

    @property
    def tag(self) -> int:
        return 7

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.name_index))


@dataclass(frozen=True)
class CONSTANT_Fieldref(CONSTANT):
    class_index: int
    name_and_type_index: int

    @property
    def tag(self) -> int:
        return 9

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.class_index), u2(self.name_and_type_index))


@dataclass(frozen=True)
class CONSTANT_Methodref(CONSTANT):
    class_index: int
    name_and_type_index: int

    @property
    def tag(self) -> int:
        return 10

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.class_index), u2(self.name_and_type_index))


class ConstantPool:
    def __init__(self) -> None:
        self.constant_pool: list[CONSTANT] = [None]

    def __iter__(self):
        return iter(self.constant_pool[1:])

    @property
    def next_index(self) -> int:
        return len(self.constant_pool)

    @property
    def count(self) -> int:
        # Для совместимости с использованием в ClassFile
        return len(self.constant_pool)

    def to_bytes(self) -> bytes:
        # Объединяем байтовые представления всех констант, начиная с индекса 1
        return merge_bytes(*(constant.to_bytes() for constant in self.constant_pool[1:]))

    def _filter_constants(self, constant_type) -> list[CONSTANT]:
        return [const for const in self.constant_pool if isinstance(const, constant_type)]

    def _find_constant(self, constant_type, predicate) -> int:
        """
        Ищет константу заданного типа, удовлетворяющую условию predicate.
        Возвращает индекс найденной константы или -1, если ничего не найдено.
        """
        for const in self._filter_constants(constant_type):
            if predicate(const):
                return const.index
        return -1

    def get_constant(self, index: int) -> CONSTANT:
        assert self.constant_pool[index] is not None
        return self.constant_pool[index]

    def add_constant_utf8(self, utf8_text: str) -> int:
        index = self._find_constant(CONSTANT_Utf8, lambda c: c.text == utf8_text)
        if index != -1:
            return index
        new_const = CONSTANT_Utf8(self.next_index, utf8_text)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_class(self, fq_class_name: str) -> int:
        index = self.find_constant_class_index(fq_class_name)
        if index != -1:
            return index
        utf8_index = self.add_constant_utf8(fq_class_name)
        class_const = CONSTANT_Class(self.next_index, utf8_index)
        self.constant_pool.append(class_const)
        return class_const.index

    def add_constant_integer(self, value: int) -> int:
        index = self._find_constant(CONSTANT_Integer, lambda c: c.const == value)
        if index != -1:
            return index
        new_const = CONSTANT_Integer(self.next_index, value)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_float(self, value: float) -> int:
        index = self._find_constant(CONSTANT_Float, lambda c: c.const == value)
        if index != -1:
            return index
        new_const = CONSTANT_Float(self.next_index, value)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_string(self, utf8_text: str) -> int:
        utf8_index = self.add_constant_utf8(utf8_text)
        index = self._find_constant(CONSTANT_String, lambda c: c.string_index == utf8_index)
        if index != -1:
            return index
        new_const = CONSTANT_String(self.next_index, utf8_index)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_fieldref(self, fq_class_name: str, field_name: str, field_desc: str) -> int:
        """
        Добавляет или находит Fieldref для поля с именем field_name и дескриптором field_desc в классе fq_class_name.
        """
        field_name_idx = self.add_constant_utf8(field_name)
        field_desc_idx = self.add_constant_utf8(field_desc)

        # Находим или создаём запись NameAndType для поля
        nat_index = self._find_constant(
            CONSTANT_NameAndType,
            lambda nat: nat.name_const_index == field_name_idx and nat.type_const_index == field_desc_idx
        )
        if nat_index == -1:
            nat = CONSTANT_NameAndType(self.next_index, name_const_index=field_name_idx, type_const_index=field_desc_idx)
            self.constant_pool.append(nat)
            nat_index = nat.index

        class_const_idx = self.add_constant_class(fq_class_name)
        index = self._find_constant(
            CONSTANT_Fieldref,
            lambda fref: fref.class_index == class_const_idx and fref.name_and_type_index == nat_index
        )
        if index != -1:
            return index

        fieldref = CONSTANT_Fieldref(self.next_index, class_index=class_const_idx, name_and_type_index=nat_index)
        self.constant_pool.append(fieldref)
        return fieldref.index

    def add_methodref(self, fq_class_name: str, method_name: str, method_desc: str) -> int:
        """
        Добавляет или находит Methodref для метода с именем method_name и дескриптором method_desc в классе fq_class_name.
        """
        methodref_index = self.find_constant_methodref(fq_class_name, method_name)
        if methodref_index != -1:
            return methodref_index

        class_const_idx = self.add_constant_class(fq_class_name)
        method_name_idx = self.add_constant_utf8(method_name)
        method_desc_idx = self.add_constant_utf8(method_desc)

        nat = CONSTANT_NameAndType(self.next_index, name_const_index=method_name_idx, type_const_index=method_desc_idx)
        self.constant_pool.append(nat)
        nat_index = nat.index

        methodref = CONSTANT_Methodref(self.next_index, class_index=class_const_idx, name_and_type_index=nat_index)
        self.constant_pool.append(methodref)
        return methodref.index

    def find_constant_fieldref(self, fq_class_name: str, field_name: str) -> int:
        for fieldref in self._filter_constants(CONSTANT_Fieldref):
            class_index = fieldref.class_index
            nat_index = fieldref.name_and_type_index

            class_const = self.get_constant(class_index)  # Получаем объект CONSTANT_Class
            nat_const = self.get_constant(nat_index)  # Получаем объект CONSTANT_NameAndType

            fieldref_class_name = self.get_constant(class_const.name_index).text  # Достаем текстовое имя класса
            fieldref_field_name = self.get_constant(nat_const.name_const_index).text  # Достаем имя поля

            if fieldref_class_name == fq_class_name and fieldref_field_name == field_name:
                return fieldref.index
        return -1
    
    def find_constant_methodref(self, fq_class_name: str, method_name: str) -> int:
        for methodref in self._filter_constants(CONSTANT_Methodref):  # Исправленный фильтр
            class_index = methodref.class_index
            nat_index = methodref.name_and_type_index
    
            class_const = self.get_constant(class_index)  # Получаем объект CONSTANT_Class
            nat_const = self.get_constant(nat_index)  # Получаем объект CONSTANT_NameAndType
    
            methodref_class_name = self.get_constant(class_const.name_index).text  # Достаем имя класса
            methodref_method_name = self.get_constant(nat_const.name_const_index).text  # Достаем имя метода
    
            if methodref_class_name == fq_class_name and methodref_method_name == method_name:
                return methodref.index
        return -1

    def find_constant_class_index(self, fq_class_name: str) -> int:
        for const in self._filter_constants(CONSTANT_Class):
            for utf8_const in self._filter_constants(CONSTANT_Utf8):
                if utf8_const.index == const.name_index and utf8_const.text == fq_class_name:
                    return const.index
        return -1

    def find_constant_string_index(self, utf8_text: str) -> int:
        for const_string in self._filter_constants(CONSTANT_String):
            utf8_const = self.get_constant(const_string.string_index)
            if utf8_const.text == utf8_text:
                return const_string.index
        return -1 

    def add_field(self, fq_class_name: str, field: TField) -> int:
        field_desc = get_type_descriptor(field.expr_type)
        return self.add_fieldref(fq_class_name, field.name, field_desc)

    def add_method(self, fq_class_name: str, method: TUserDefinedMethod) -> int:
        method_desc = get_method_descriptor(method)
        return self.add_methodref(fq_class_name, method.method_name, method_desc)


def split_package_path(package: str) -> list[str]:
    return package.split(".")


def make_fully_qualifed_name(parts: list[str]) -> str:
    return "/".join(parts)


def add_package_prefix(class_name: str, package: str = DEFAULT_PACKAGE) -> str:
    return make_fully_qualifed_name(
        split_package_path(package) + [class_name])


def get_type_descriptor(typ: Type) -> str:
    """
    Генерирует дескриптор типа для виртуальной машины Java.
    Для примитивных типов используется однобуквенное обозначение,
    для ссылочных типов возвращается формат "L<fully-qualified-name>;"
    """
    if typ.name == "<VOID>":
        return "V"
    # Если имя уже содержит '/', считаем его полностью квалифицированным
    fq_name = typ.name if "/" in typ.name else add_package_prefix(typ.name)
    return f"L{fq_name};"


def get_method_descriptor(method: TMethod) -> str:
    """
    Формирует дескриптор метода.
    """
    params_desc = "".join(get_type_descriptor(param_type) for _, param_type in method.parameters)
    return_desc = get_type_descriptor(method.return_type)
    return f"({params_desc}){return_desc}"


def process_expression_literals(
        expr: TExpr,
        constant_pool: ConstantPool,
        current_class: TClass,
        rest_classes: list[TClass]) -> None:
    match expr:
        case TIntegerConst(value=value):
            constant_pool.add_constant_integer(value)
        case TRealConst(value=value):
            constant_pool.add_constant_float(value)
        case TStringConst(value=value):
            constant_pool.add_constant_string(value)
        case TCharacterConst(value=value):
            raise NotImplementedError
        case TBoolConst(value=value):
            # constant_pool.add_constant_integer(int(value))
            raise NotImplementedError
        case TFeatureCall(expr_type=expr_type, feature_name=feature_name, arguments=arguments, owner=owner):
            fq_class_name = add_package_prefix(expr_type.full_name)
            constant_pool.add_constant_class(fq_class_name)

            if owner is not None:
                method = find_method(rest_classes, feature_name)
                constant_pool.add_method(add_package_prefix(owner.expr_type.full_name), method)
                process_expression_literals(owner, constant_pool, current_class, rest_classes)
            else:
                method = find_method([current_class], feature_name)
                constant_pool.add_method(add_package_prefix(current_class.class_name), method)

            for arg in arguments:
                process_expression_literals(arg, constant_pool, current_class, rest_classes)
        case TCreateExpr(expr_type=expr_type, constructor_name=constructor_name, arguments=arguments):
            fq_class_name = add_package_prefix(expr_type.full_name)
            constant_pool.add_constant_class(fq_class_name)

            method = find_method([current_class] + rest_classes, constructor_name)
            constant_pool.add_method(method)

            for arg in arguments:
                process_expression_literals(arg, constant_pool, current_class, rest_classes)
        case TBinaryOp(left=left, right=right):
            process_expression_literals(left, constant_pool, current_class, rest_classes)
            process_expression_literals(right, constant_pool, current_class, rest_classes)
        case TUnaryOp(argument=argument):
            process_expression_literals(argument, constant_pool, current_class, rest_classes)
    # Для TVariable и TVoidConst ничего не делаем.


def process_statement_literals(
        stmt: TStatement,
        constant_pool: ConstantPool,
        current_class: TClass,
        rest_classes: list[TClass]) -> None:
    match stmt:
        case TAssignment(lvalue=lvalue, rvalue=rvalue):
            process_expression_literals(lvalue, constant_pool, current_class, rest_classes)
            process_expression_literals(rvalue, constant_pool, current_class, rest_classes)
        case TIfStmt(
                condition=condition,
                then_branch=then_branch,
                else_branch=else_branch,
                elseif_branches=elseif_branches):
            process_expression_literals(condition, constant_pool, current_class, rest_classes)
            for s in then_branch:
                process_statement_literals(s, constant_pool, current_class, rest_classes)
            for s in else_branch:
                process_statement_literals(s, constant_pool, current_class, rest_classes)
            for cond, stmts in elseif_branches:
                process_expression_literals(cond, constant_pool, current_class, rest_classes)
                for s in stmts: process_statement_literals(s, constant_pool, current_class, rest_classes)
        case TLoopStmt(
                init_smtmts=init_stmts,
                until_cond=until_cond,
                body=body):
            for s in init_stmts:
                process_statement_literals(s, constant_pool, current_class, rest_classes)
            process_expression_literals(until_cond, constant_pool, current_class, rest_classes)
            for s in body:
                process_statement_literals(s, constant_pool)
        case TRoutineCall(feature_call=feature_call):
            process_expression_literals(feature_call, constant_pool, current_class, rest_classes)
        case _: assert False


def get_external_method_descriptor(method: TExternalMethod) -> str:
    fq_name = make_fully_qualifed_name(split_package_path(DEFAULT_PACKAGE) + [PLATFORM_CLASS_NAME])
    platform_descriptor = f"L{fq_name};"

    # В качестве типов параметров устанавливаем всем параметрам
    # класса PLATFORM - это позволит реализовать взаимодействие между
    # кодом на Eiffel и Java
    params_desc = "".join(platform_descriptor * len(method.parameters))
    full_params_desc = platform_descriptor + params_desc

    # Аналогично поступаем для всех дескрипторов, которые не являются void
    return_desc = get_type_descriptor(method.return_type)
    if return_desc != "V":
        return_desc = platform_descriptor

    return f"({full_params_desc}){return_desc}"


def process_external_method(constant_pool: ConstantPool, method: TExternalMethod) -> None:
    full_alias = method.alias
    parts = split_package_path(full_alias)
    if len(parts) < 2:
        raise CompilerError(
            f"Alias '{full_alias}' is not a correct reference to a Java method",
            source=COMPILER_NAME)
    
    java_method_name = parts[-1]
    fq_java_class_name = make_fully_qualifed_name(parts[:-1])
    
    class_const_idx = constant_pool.add_constant_class(fq_java_class_name)
    method_name_idx = constant_pool.add_constant_utf8(java_method_name)
    
    method_descriptor = get_external_method_descriptor(method)
    method_desc_idx = constant_pool.add_constant_utf8(method_descriptor)
    
    nat_method = CONSTANT_NameAndType(
        constant_pool.next_index,
        name_const_index=method_name_idx,
        type_const_index=method_desc_idx
    )
    constant_pool.constant_pool.append(nat_method)
    nat_method_idx = nat_method.index
    
    methodref = CONSTANT_Methodref(
        constant_pool.next_index,
        class_index=class_const_idx,
        name_and_type_index=nat_method_idx
    )
    constant_pool.constant_pool.append(methodref)


def find_method(classes: list[TClass], method_name: str) -> TMethod:
    for cls in classes:
        for method in cls.methods:
            if method.method_name == method_name:
                return method
    assert False


def find_field(classes: list[TClass], field_name: str) -> TField:
    for cls in classes:
        for field in cls.fields:
            if field.name == field_name:
                return field
    assert False


def make_constant_pool(tclass: TClass, rest_classes: list[TClass]) -> ConstantPool:
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
        constant_pool.add_field(fq_class_name, field)

    for method in tclass.methods:
        if isinstance(method, TExternalMethod):
            process_external_method(constant_pool, method)
        else:
            assert isinstance(method, TUserDefinedMethod)

            constant_pool.add_method(fq_class_name, method)
            for stmt in method.body:
                process_statement_literals(stmt, constant_pool, tclass, rest_classes)

    return constant_pool


def pretty_print_constant_pool(pool: ConstantPool) -> None:
    print("Constant Pool:")
    print("-" * 40)
    for const in pool:
        if isinstance(const, CONSTANT_Utf8):
            print(f"{const.index:3}: CONSTANT_Utf8       : '{const.text}'")
        elif isinstance(const, CONSTANT_Integer): 
            print(f"{const.index:3}: CONSTANT_Integer    : {const.const}")
        elif isinstance(const, CONSTANT_Float): 
            print(f"{const.index:3}: CONSTANT_Float      : {const.const}")
        elif isinstance(const, CONSTANT_String): 
            print(f"{const.index:3}: CONSTANT_String     : string_index={const.string_index}")
        elif isinstance(const, CONSTANT_NameAndType):
            print(f"{const.index:3}: CONSTANT_NameAndType: name_index={const.name_const_index}, type_index={const.type_const_index}")
        elif isinstance(const, CONSTANT_Class):
            print(f"{const.index:3}: CONSTANT_Class      : name_index={const.name_index}")
        elif isinstance(const, CONSTANT_Fieldref): 
            print(f"{const.index:3}: CONSTANT_Fieldref   : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        elif isinstance(const, CONSTANT_Methodref): 
            print(f"{const.index:3}: CONSTANT_Methodref  : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        else:
            print(f"{const.index:3}: Unknown constant type: {const}")
    print("-" * 40)

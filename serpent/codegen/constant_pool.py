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
        self.constant_pool: list[CONSTANT] = []

    @property
    def constants_count(self) -> int:
        return len(self.constant_pool)

    @property
    def next_index(self) -> int:
        return len(self.constant_pool) + 1

    def filter_constants(self, constant_type) -> list[CONSTANT]:
        return [
            constant
            for constant in self.constant_pool
            if isinstance(constant, constant_type)]

    def add_constant_utf8(self, utf8_text: str) -> int:
        for constant in self.filter_constants(CONSTANT_Utf8):
            if constant.text == utf8_text:
                return constant.index
            
        new_const = CONSTANT_Utf8(self.next_index, utf8_text)
        self.constant_pool.append(new_const)
        return new_const.index
    
    def add_constant_class(self, fq_class_name: str) -> int:
        class_const_index = self.find_constant_class_index(class_name)
        if class_const_index != -1:
            return class_const_index

        utf8_const_index = self.add_constant_utf8(class_name)
        class_const = CONSTANT_Class(self.next_index, utf8_const_index)
        self.constant_pool.append(class_const)
        return class_const.index

    def add_constant_integer(self, value: int) -> int:
        for constant in self.filter_constants(CONSTANT_Integer):
            if constant.const == value:
                return constant.index
            
        new_const = CONSTANT_Integer(self.next_index, value)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_float(self, value: float) -> int:
        for constant in self.filter_constants(CONSTANT_Float):
            if constant.const == value:
                return constant.index
            
        new_const = CONSTANT_Float(self.next_index, value)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_string(self, utf8_index: int) -> int:
        for constant in self.filter_constants(CONSTANT_String):
            if constant.string_index == utf8_index:
                return constant.index
            
        new_const = CONSTANT_String(self.next_index, utf8_index)
        self.constant_pool.append(new_const)
        return new_const.index

    def add_constant_fieldref(self, field: TField, fq_class_name: str) -> int:
        field_name_idx = self.add_constant_utf8(field.name)

        field_desc = get_type_descriptor(field.expr_type)
        field_desc_idx = self.add_constant_utf8(field_desc)

        nat_const = CONSTANT_NameAndType(
            self.next_index,
            name_const_index=field_name_idx,
            type_const_index=field_desc_idx)
        self.constant_pool.append(nat_const)
        nat_const_idx = nat_const.index

        class_const_idx = self.find_constant_class_index(fq_class_name)
        assert class_const_idx != -1

        fieldref = CONSTANT_Fieldref(
            self.next_index,
            class_index=class_const_idx,
            name_and_type_index=nat_const_idx)
        self.constant_pool.append(fieldref)

        return fieldref.index

    def add_constant_methodref(self, method: TUserDefinedMethod, fq_class_name: str) -> int:
        method_name_idx = self.add_constant_utf8(method.method_name)

        method_desc = get_method_descriptor(method)
        method_desc_idx = self.add_constant_utf8(method_desc)

        nat_method = CONSTANT_NameAndType(
            self.next_index,
            name_const_index=method_name_idx,
            type_const_index=method_desc_idx)
        self.constant_pool.append(nat_method)
        nat_method_idx = nat_method.index

        class_const_idx = self.find_constant_class_index(fq_class_name)
        assert class_const_idx != -1

        methodref = CONSTANT_Methodref(
            self.next_index,
            class_index=class_const_idx,
            name_and_type_index=nat_method_idx)
        self.constant_pool.append(methodref)

        return methodref.index

    def find_constant_methodref_index(self, fq_class_name: str, method_name: str, method_desc: str) -> int:
        # TODO: когда-нибудь произвести рефакторинг...
        # Сначала находим индекс класса по полному имени
        class_index = self.find_constant_class_index(fq_class_name)
        if class_index == -1:
            return -1

        # Ищем среди всех CONSTANT_Methodref
        for methodref in self.filter_constants(CONSTANT_Methodref):
            if methodref.class_index != class_index:
                continue  # не тот класс

            # Получаем индекс записи CONSTANT_NameAndType, связанной с этим methodref
            nat_index = methodref.name_and_type_index
            # Ищем соответствующую запись CONSTANT_NameAndType
            for nat in self.filter_constants(CONSTANT_NameAndType):
                if nat.index != nat_index:
                    continue

                # Извлекаем имя метода и дескриптор из соответствующих записей CONSTANT_Utf8
                actual_name = None
                actual_desc = None
                for utf8 in self.filter_constants(CONSTANT_Utf8):
                    if utf8.index == nat.name_const_index:
                        actual_name = utf8.text
                    if utf8.index == nat.type_const_index:
                        actual_desc = utf8.text

                # Сравниваем с искомыми значениями
                if actual_name == method_name and actual_desc == method_desc:
                    return methodref.index

        return -1

    def find_constant_class_index(self, fq_class_name: str) -> int:
        for const in self.filter_constants(CONSTANT_Class):
            for utf8_const in self.filter_constants(CONSTANT_Utf8):
                if (utf8_const.index == const.name_index
                        and utf8_const.text == fq_class_name):
                    return const.index
        return -1


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
    return_desc = get_type_descriptor(method.return_type)
    return f"({params_desc}){return_desc}"


def process_expression_literals(expr: TExpr, constant_pool: ConstantPool) -> None:
    """
    Рекурсивно обходит выражение и добавляет в пул констант литералы:
      - TIntegerConst  -> CONSTANT_Integer
      - TRealConst     -> CONSTANT_Float
      - TStringConst   -> CONSTANT_String (через CONSTANT_Utf8)
      - TCharacterConst-> пока не реализован
      - TBoolConst     -> представляется как 1/0 (CONSTANT_Integer)
    Также рекурсивно обрабатываются составные выражения.
    """
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
            constant_pool.add_constant_integer(int(value))
        case TFeatureCall(arguments=arguments, owner=owner):
            if owner is not None:
                process_expression_literals(owner, constant_pool)
            for arg in arguments:
                process_expression_literals(arg, constant_pool)
        case TCreateExpr(arguments=arguments):
            for arg in arguments:
                process_expression_literals(arg, constant_pool)
        case TBinaryOp(left=left, right=right):
            process_expression_literals(left, constant_pool)
            process_expression_literals(right, constant_pool)
        case TUnaryOp(argument=argument):
            process_expression_literals(argument, constant_pool)
    # Для TVariable и TVoidConst ничего не делаем.


def process_statement_literals(stmt: TStatement, constant_pool: ConstantPool) -> None:
    """
    Рекурсивно обходит оператор и обрабатывает все входящие в него выражения.
    """
    match stmt:
        case TAssignment(lvalue=lvalue, rvalue=rvalue):
            process_expression_literals(lvalue, constant_pool)
            process_expression_literals(rvalue, constant_pool)
        case TIfStmt(
                condition=condition,
                then_branch=then_branch,
                else_branch=else_branch,
                elseif_branches=elseif_branches):
            process_expression_literals(condition, constant_pool)
            for s in then_branch:
                process_statement_literals(s, constant_pool)
            for s in else_branch:
                process_statement_literals(s, constant_pool)
            for cond, stmts in elseif_branches:
                process_expression_literals(cond, constant_pool)
                for s in stmts: process_statement_literals(s, constant_pool)


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
        constant_pool.add_constant_fieldref(field, fq_class_name)

    for method in tclass.methods:
        if isinstance(method, TExternalMethod):
            process_external_method(constant_pool, method)
        else:
            assert isinstance(method, TUserDefinedMethod)

            constant_pool.add_constant_methodref(method, fq_class_name)
            for stmt in method.body:
                process_statement_literals(stmt, constant_pool)

    return constant_pool


def pretty_print_constant_pool(pool: ConstantPool) -> None:
    print("Constant Pool:")
    print("-" * 40)
    for const in pool.constant_pool:
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

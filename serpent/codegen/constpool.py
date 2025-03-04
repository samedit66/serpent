from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import struct
from typing import Iterable

from serpent.errors import CompilerError
from serpent.semantic_checker.symtab import Type
from serpent.semantic_checker.type_check import *
from serpent.codegen.byte_utils import *


DEFAULT_PACKAGE = "com.eiffel"
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
class ConstPool:
    """Таблица констант для конкретного класса Eiffel.
    Особенность данной таблицы (а точнее особенность методов поиска констант)
    заключается в отсутствии перегружаемых методов -- т.е. у каждого метода
    уникальное имя, за счет этого поиск Methodref осуществляется проще
    """
    fq_class_name: str
    """Полное квалифицированное имя класса, для которого составляется таблица"""
    constants: list[CONSTANT] = field(default_factory=list)
    """Список всех констант, которые встречаются в теле класса"""
    external_methods: dict[str, str] = field(default_factory=dict)
    """Список всех внешних методов, нужен на этапе генерации TFeatureCall"""

    def __post_init__(self) -> None:
        self.add_class(self.fq_class_name)

    def __iter__(self) -> Iterable[CONSTANT]:
        return iter(self.constants)

    def to_bytes(self) -> bytes:
        """Возвращает таблицу констант непосредственно в виде байтов"""
        return b"".join(const.to_bytes() for const in self.constants)
    
    def is_external(self, method_name: str) -> bool:
        return method_name in self.external_methods

    def get_alias_for_external_method(self, method_name: str) -> str:
        return self.external_methods[method_name]

    @property
    def count(self) -> int:
        return len(self.constants)

    @property
    def next_index(self) -> int:
        """Индекс следующей добавляемой константы"""
        return len(self.constants) + 1
    
    def get_by_index(self, index: int) -> CONSTANT:
        """Возвращает константу по ее индексу в таблице"""
        return self.constants[index]

    def find_constant(self, predicate) -> CONSTANT | None:
        """Возвращает первую константу, удовлетворяющую предикату"""
        for constant in self.constants:
            if predicate(constant):
                return constant
        return None

    def find_methodref(self, method_name: str, fq_class_name: str | None = None) -> int:
        """Ищет номер константы Methodref с заданным именем метода"""
        fq_class_name = fq_class_name or self.fq_class_name

        methodref = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Methodref)
                and c.method_name == method_name
                and c.fq_class_name == fq_class_name)
        assert methodref is not None, f"{fq_class_name}: {method_name}"

        return methodref.index
    
    def find_fieldref(self, field_name: str, fq_class_name: str | None = None) -> int:
        """Ищет номер константы Fieldref с заданным именем метода"""
        fq_class_name = fq_class_name or self.fq_class_name

        fieldref = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Fieldref)
                and c.field_name == field_name
                and c.fq_class_name == fq_class_name)
        assert fieldref is not None, f"{fq_class_name}: {field_name}"

        return fieldref.index

    def find_class(self, fq_class_name: str) -> int:
        class_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Class)
                and c.class_name == fq_class_name)
        assert class_const is not None, fq_class_name
        return class_const.index
    
    def find_string(self, text: str) -> int:
        string_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_String)
                and c.text == text)
        assert string_const is not None, text
        return string_const.index

    def add_methodref(
            self,
            method_name: str,
            desc: str,
            fq_class_name: str | None = None) -> int:
        try:
            methodref_index = self.find_methodref(method_name, fq_class_name)
            return methodref_index
        except AssertionError:
            class_index = self.add_class(fq_class_name)
            nat_index = self.add_name_and_type(method_name, desc)
            methodref = CONSTANT_Methodref(
                self.next_index,
                method_name,
                desc,
                fq_class_name,
                class_index,
                nat_index)
            self.constants.append(methodref)
            return methodref.index

    def add_fieldref(
            self,
            field_name: str,
            desc: str,
            fq_class_name: str | None = None) -> int:
        try:
            fieldref_index = self.find_fieldref(field_name, fq_class_name)
            return fieldref_index
        except AssertionError:
            class_index = self.add_class(fq_class_name)
            nat_index = self.add_name_and_type(field_name, desc)
            fieldref = CONSTANT_Fieldref(
                self.next_index,
                field_name,
                desc,
                fq_class_name,
                class_index,
                nat_index)
            self.constants.append(fieldref)
            return fieldref.index

    def add_name_and_type(self, name: str, type: str) -> int:
        nat = self.find_constant(
            lambda c: isinstance(c, CONSTANT_NameAndType)
                and c.name == name
                and c.type == type)
        
        if nat is None:
            name_index = self.add_utf8(name)
            type_index = self.add_utf8(type)
            nat = CONSTANT_NameAndType(
                self.next_index, name, type, name_index, type_index)
            self.constants.append(nat)
            
        return nat.index

    def add_class(self, class_name: str) -> int:
        class_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Class)
                and c.class_name == class_name)

        if class_const is None:
            name_index = self.add_utf8(class_name)
            class_const = CONSTANT_Class(
                self.next_index, class_name, name_index)
            self.constants.append(class_const)
            
        return class_const.index

    def add_utf8(self, text: str) -> int:
        utf8_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Utf8)
                and c.text == text)

        if utf8_const is None:
            utf8_const = CONSTANT_Utf8(self.next_index, text)
            self.constants.append(utf8_const)

        return utf8_const.index

    def add_string(self, text: str) -> int:
        string_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_String)
                and c.text == text)

        if string_const is None:
            string_index = self.add_utf8(text)
            string_const = CONSTANT_String(
                self.next_index, text, string_index)
            self.constants.append(string_const)
            
        return string_const.index

    def add_integer(self, value: int) -> int:
        integer_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Integer)
                and c.const == value)

        if integer_const is None:
            integer_const = CONSTANT_Integer(
                self.next_index, value)
            self.constants.append(integer_const)
            
        return integer_const.index

    def add_float(self, value: float) -> int:
        float_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Float)
                and c.const == value)

        if float_const is not None:
            float_const = CONSTANT_Float(
                self.next_index, value)
            self.constants.append(float_const)
            
        return float_const.index
        

def make_const_pool(current: TClass, rest: list[TClass]) -> ConstPool:
    """Создает таблицу констант для current класса.
    Делает это неэффэективным, но простым способом: для гарантии того,
    что любой встреченный метод уже был определен в каком-то из классов,
    запихивает в таблицу констант каждого класса все константы (поля и методы)
    из всех других классов
    """
    pool = ConstPool(
        fq_class_name=add_package_prefix(
            current.class_name))

    # Заполняем пулл констант всеми полями и методами
    # всех классов в системе (включая тот, для которого
    # составляется таблица констант)
    for class_ in rest + [current]:
        fq_class_name = add_package_prefix(class_.class_name)
        
        for field in class_.fields:
            field_type = get_type_descriptor(field.expr_type)
            pool.add_fieldref(field.name, field_type, fq_class_name)

        for method in class_.methods:
            method_type = get_method_descriptor(
                [param_type for (_, param_type) in method.parameters],
                method.return_type)
            pool.add_methodref(method.method_name, method_type, fq_class_name)

    for method in current.methods:
        match method:
            case TExternalMethod(
                    method_name=method_name,
                    return_type=return_type,
                    parameters=parameters,
                    alias=alias):
                parts = split_package_path(alias)
                if len(parts) < 2:
                    raise CompilerError(
                        f"Alias '{alias}' is not a correct reference to a Java method, "
                        f"see method '{method.method_name}' of class '{pool.fq_class_name}'",
                        source=COMPILER_NAME)
                # В обход всего и вся добавляем имя внешнего метода
                pool.external_methods[method_name] = alias
                java_method_name = parts[-1]
                fq_class_name = make_fully_qualifed_name(parts[:-1])
                external_method_type = get_external_method_descriptor(
                    [param_type for (_, param_type) in parameters], return_type)
                pool.add_methodref(
                    java_method_name, external_method_type, fq_class_name)
            case TUserDefinedMethod(body=body):
                for stmt in body:
                    process_statement_literals(stmt, pool)
        
    return pool


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
    text: str
    string_index: int

    @property
    def tag(self) -> int:
        return 8

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.string_index))


@dataclass(frozen=True)
class CONSTANT_NameAndType(CONSTANT):
    name: str
    type: str
    name_const_index: int
    type_const_index: int

    @property
    def tag(self) -> int:
        return 12

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.name_const_index), u2(self.type_const_index))


@dataclass(frozen=True)
class CONSTANT_Class(CONSTANT):
    class_name: str
    name_index: int

    @property
    def tag(self) -> int:
        return 7

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.name_index))


@dataclass(frozen=True)
class CONSTANT_Fieldref(CONSTANT):
    field_name: str
    type: str
    fq_class_name: str
    class_index: int
    name_and_type_index: int

    @property
    def tag(self) -> int:
        return 9

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.class_index), u2(self.name_and_type_index))


@dataclass(frozen=True)
class CONSTANT_Methodref(CONSTANT):
    method_name: str
    type: str
    fq_class_name: str
    class_index: int
    name_and_type_index: int

    @property
    def tag(self) -> int:
        return 10

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.class_index), u2(self.name_and_type_index))


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


def get_method_descriptor(args_types: list[Type], return_type: Type) -> str:
    params_desc = "".join(get_type_descriptor(arg_type) for arg_type in args_types)
    return_desc = get_type_descriptor(return_type)
    return f"({params_desc}){return_desc}"


def process_expression_literals(expr: TExpr, pool: ConstPool) -> None:
    match expr:
        case TIntegerConst(value=value):
            pool.add_integer(value)
        case TRealConst(value=value):
            pool.add_float(value)
        case TStringConst(value=value):
            pool.add_string(value)
        case TCharacterConst(value=value):
            pool.add_string(value)
        case TBoolConst(value=value):
            pass
        case TFeatureCall(
                feature_name=method_name,
                arguments=arguments,
                owner=owner):
            if owner is None:
                fq_class_name = None
            else:
                fq_class_name = add_package_prefix(owner.expr_type.full_name)

            # Данный вызов необходим для проверки того, что
            # заданная константа уже существует, т.к. к этому моменту
            # она точно должна быть. В случае отсутсвия выбросится AssertionError
            # с указанием какой метод и в каком классе не был найден
            pool.find_methodref(method_name, fq_class_name)
            for arg in arguments:
                process_expression_literals(arg, pool)
        case TCreateExpr(
                expr_type=expr_type,
                constructor_name=method_name,
                arguments=arguments):
            fq_class_name = add_package_prefix(expr_type.full_name)

            # Данный вызов необходим для проверки того, что
            # заданная константа уже существует, т.к. к этому моменту
            # она точно должна быть. В случае отсутсвия выбросится AssertionError
            # с указанием какой метод и в каком классе не был найден
            pool.find_methodref(method_name, fq_class_name)
            for arg in arguments:
                process_expression_literals(arg, pool)
        case TBinaryOp(left=left, right=right):
            process_expression_literals(left, pool)
            process_expression_literals(right, pool)
        case TUnaryOp(argument=argument):
            process_expression_literals(argument, pool)
        # Для TVariable и TVoidConst ничего не делаем


def process_statement_literals(stmt: TStatement, pool: ConstPool) -> None:
    match stmt:
        case TAssignment(lvalue=lvalue, rvalue=rvalue):
            process_expression_literals(lvalue, pool)
            process_expression_literals(rvalue, pool)
        case TIfStmt(
                condition=condition,
                then_branch=then_branch,
                else_branch=else_branch,
                elseif_branches=elseif_branches):
            process_expression_literals(condition, pool)
            for s in then_branch:
                process_statement_literals(s, pool)
            for s in else_branch:
                process_statement_literals(s, pool)
            for cond, stmts in elseif_branches:
                process_expression_literals(cond, pool)
                for s in stmts: process_statement_literals(s, pool)
        case TLoopStmt(
                init_stmts=init_stmts,
                until_cond=until_cond,
                body=body):
            for s in init_stmts:
                process_statement_literals(s, pool)
            process_expression_literals(until_cond, pool)
            for s in body:
                process_statement_literals(s, pool)
        case TRoutineCall(feature_call=feature_call):
            process_expression_literals(feature_call, pool)
        case _: assert False, stmt


def get_external_method_descriptor(args_types: list[Type], return_type: Type) -> str:
    type_mapping = {
        add_package_prefix("INTEGER"): "I",
        add_package_prefix("FLOAT"): "F",
        add_package_prefix("STRING"): "Ljava/lang/String;",
        add_package_prefix("BOOLEAN"): "I",
        add_package_prefix("CHARACTER"): "Ljava/lang/String;",
    }
    this = f"L{add_package_prefix(PLATFORM_CLASS_NAME)};"

    descriptors = []
    for typ in args_types + [return_type]:
        fq_class_name = add_package_prefix(typ.full_name)
        desc = type_mapping.get(fq_class_name, this)

        #if fq_class_name not in type_mapping:
        #    raise CompilerError(
        #        f"Unsupported type '{typ.name}' (fully-qualified: '{fq_class_name}'). "
        #        "Allowed types for Java–Eiffel external methods are: INTEGER, FLOAT, STRING, BOOLEAN, and CHARACTER.")

        descriptors.append(desc)

    full_params_desc = "".join(descriptors[:-1])
    return_desc = descriptors[-1]
    return f"({this}{full_params_desc}){return_desc}"


def pretty_print_const_pool(pool: ConstPool) -> None:
    print("Constant Pool:")
    print("-" * 40)
    for const in pool:
        if isinstance(const, CONSTANT_Utf8):
            print(f"{const.index:3}: Utf8       : '{const.text}'")
        elif isinstance(const, CONSTANT_Integer): 
            print(f"{const.index:3}: Integer    : {const.const}")
        elif isinstance(const, CONSTANT_Float): 
            print(f"{const.index:3}: Float      : {const.const}")
        elif isinstance(const, CONSTANT_String): 
            print(f"{const.index:3}: String     : string_index={const.string_index}")
        elif isinstance(const, CONSTANT_NameAndType):
            print(f"{const.index:3}: NameAndType: name_index={const.name_const_index}, type_index={const.type_const_index}")
        elif isinstance(const, CONSTANT_Class):
            print(f"{const.index:3}: Class      : name_index={const.name_index}")
        elif isinstance(const, CONSTANT_Fieldref): 
            print(f"{const.index:3}: Fieldref   : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        elif isinstance(const, CONSTANT_Methodref): 
            print(f"{const.index:3}: Methodref  : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        else:
            print(f"{const.index:3}: Unknown constant type: {const}")
    print("-" * 40)

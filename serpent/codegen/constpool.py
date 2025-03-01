from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import struct

from serpent.codegen.byte_utils import *


class ConstantNotFoundError(Exception): ...


@dataclass(frozen=True)
class ConstPool:
    """Таблица констант для конкретного класса Eiffel.
    Особенность данной таблицы (а точнее особенность методов поиска констант)
    заключается в отсутствии перегружаемых методов -- т.е. у каждого метода
    уникальное имя, за счет этого поиск Methodref осуществляется проще
    """
    fq_class_name: str
    """Полное квалифицированное имя класса, для которого составляется таблица"""
    constants: list[CONSTANT]
    """Список всех констант для данного класса"""

    def __post_init__(self) -> None:
        self.add_class(self.fq_class_name)

    def to_bytes(self) -> bytes:
        """Возвращает таблицу констант непосредственно в виде байтов"""
        return b"".join(const.to_bytes() for const in self.constants)
    
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
                and self.get_by_index(c.class_index).class_name == fq_class_name)
        assert methodref is not None, f"{fq_class_name}: {method_name}"

        return methodref.index
    
    def find_fieldref(self, field_name: str, fq_class_name: str | None = None) -> int:
        """Ищет номер константы Fieldref с заданным именем метода"""
        fq_class_name = fq_class_name or self.fq_class_name

        fieldref = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Fieldref)
                and c.field_name == field_name
                and self.get_by_index(c.class_index).class_name == fq_class_name)
        assert fieldref is not None, f"{fq_class_name}: {field_name}"

        return fieldref.index

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
                self.next_index, class_index, nat_index)
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
                self.next_index, class_index, nat_index)
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

        if utf8_const is not None:
            utf8_const = CONSTANT_Utf8(self.next_index, text)
            self.constants.append(utf8_const)

        return utf8_const.index

    def add_string(self, text: str) -> int:
        string_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_String)
                and c.text == text)

        if string_const is not None:
            string_index = self.add_utf8(text)
            string_const = CONSTANT_String(
                self.next_index, text, string_index)
            self.constants.append(string_const)
            
        return string_const.index

    def add_integer(self, value: int) -> int:
        integer_const = self.find_constant(
            lambda c: isinstance(c, CONSTANT_Integer)
                and c.const == value)

        if integer_const is not None:
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
    class_index: int
    name_and_type_index: int

    @property
    def tag(self) -> int:
        return 10

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.class_index), u2(self.name_and_type_index))

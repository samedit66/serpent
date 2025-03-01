from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


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

    def to_bytes(self) -> bytes:
        """Возвращает таблицу констант непосредственно в виде байтов"""
        return b"".join(const.to_bytes() for const in self.constants)
    
    @property
    def next_index(self) -> int:
        """Индекс следующей добавляемой константы"""
        return len(self.constants) + 1
    
    def find_methodref(self, method_name: str) -> int:
        """Ищет номер константы Methodref с заданным именем метода"""
        utf8_const_index = -1
        for constant in self.constants:
            if isinstance(constant, CONSTANT_Utf8) and constant.text == method_name:
                utf8_const_index = constant.index
                break
        assert utf8_const_index != -1, method_name

        nat_const_index = -1
        for constant in self.constants:
            if (isinstance(constant, CONSTANT_NameAndType)
                    and constant.name_const_index == utf8_const_index):
                nat_const_index = constant.index
                break
        assert nat_const_index != -1, method_name

        methodref_index = -1
        for constant in self.constants:
            if (isinstance(constant, CONSTANT_Methodref) 
                    and constant.name_and_type_index == nat_const_index):
                methodref_index = constant.index
                break
        assert methodref_index != -1, method_name

        return methodref_index
    
    def find_fieldref(self, field_name: str) -> int:
        """Ищет номер константы Fieldref с заданным именем поля"""
        utf8_const_index = -1
        for constant in self.constants:
            if isinstance(constant, CONSTANT_Utf8) and constant.text == field_name:
                utf8_const_index = constant.index
                break
        assert utf8_const_index != -1, field_name

        nat_const_index = -1
        for constant in self.constants:
            if (isinstance(constant, CONSTANT_NameAndType)
                    and constant.name_const_index == utf8_const_index):
                nat_const_index = constant.index
                break
        assert nat_const_index != -1, field_name

        fieldref_index = -1
        for constant in self.constants:
            if (isinstance(constant, CONSTANT_Fieldref)
                    and constant.name_and_type_index == nat_const_index):
                fieldref_index = constant.index
                break
        assert fieldref_index != -1, field_name

        return fieldref_index

    def add_methodref(self, method_name: str, desc: str) -> int:
        ...

    def add_fieldref(self, field_name: str, desc: str) -> int:
        ...

    def add_name_and_type(self) -> int:
        ...

    def add_class(self, class_name: str) -> int:
        utf8_index = self.add_utf8(class_name)
        class_index = -1
        for const in self.constants:
            if isinstance(const, CONSTANT_Class) and const.name_index == utf8_index:
                class_index = const.index
                break
        
        if class_index == -1:
            const = CONSTANT_Class(self.next_index, utf8_index)
            class_index = const.index

        return class_index

    def add_utf8(self, text: str) -> int:
        utf8_index = -1
        for const in self.constants:
            if isinstance(const, CONSTANT_Utf8) and const.text == text:
                utf8_index = const.index
                break

        if utf8_index == -1:
            const = CONSTANT_Utf8(self.next_index, text)
            utf8_index = const.index

        return utf8_index

    def add_string(self, text: str) -> int:
        utf8_index = -1
        for const in self.constants:
            if isinstance(const, CONSTANT_Utf8) and const.text == text:
                utf8_index = const.index
                break

        if utf8_index == -1:
            const = CONSTANT_Utf8(self.next_index, text)
            utf8_index = const.index

        return utf8_index

    def add_integer(self, value: int) -> int:
        ...

    def add_float(self, value: float) -> int:
        ...
        

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



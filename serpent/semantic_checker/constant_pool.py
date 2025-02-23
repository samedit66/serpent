from dataclasses import dataclass


@dataclass(frozen=True)
class CONSTANT:
    index: int


@dataclass(frozen=True)
class CONSTANT_Utf8:
    text: str


@dataclass(frozen=True)
class CONSTANT_Integer:
    const: int


@dataclass(frozen=True)
class CONSTANT_Float:
    const: float


@dataclass(frozen=True)
class CONSTANT_String:
    string_index: int


@dataclass(frozen=True)
class CONSTANT_NameAndType:
    name_const_index: int
    type_const_index: int


@dataclass(frozen=True)
class CONSTANT_Class:
    name_index: int


@dataclass(frozen=True)
class CONSTANT_Fieldref:
    class_index: int
    name_and_type_index: int


@dataclass(frozen=True)
class CONSTANT_Methodref:
    class_index: int
    name_and_type_index: int


class ConstantPool:
    pass

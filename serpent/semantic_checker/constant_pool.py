from dataclasses import dataclass


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
    const_utf8: int


@dataclass(frozen=True)
class CONSTANT_NameAndType:
    name_const: int
    type_const: int


@dataclass(frozen=True)
class CONSTANT_Class:
    name_const: int


@dataclass(frozen=True)
class CONSTANT_Fieldref:
    class_const: int
    name_and_type_const: int


@dataclass(frozen=True)
class CONSTANT_Methodref:
    class_const: int
    name_and_type_const: int


class ConstantPool:
    ...

from dataclasses import dataclass, field

from serpent.semantic_checker.type_check import TField
from serpent.codegen.constant_pool import ConstantPool, get_type_descriptor


ACC_PUBLIC = 0x01
ACC_SUPER = 0x02


@dataclass(frozen=True)
class ClassFile:
    minor_version: int
    major_version: int
    constant_pool: ConstantPool
    access_flags: int
    this_class: int
    super_class: int

    @property
    def magic(self) -> int:
        return 0xcafebabe

    @property
    def constant_pool_count(self) -> int:
        return self.constant_pool.count + 1
    
    @property
    def interfaces_count(self) -> int:
        return 0
    
    @property
    def fields_count(self) -> int:
        raise NotImplementedError

    @property
    def methods_count(self) -> int:
        raise NotImplementedError

    @property
    def attributes_count(self) -> int:
        return 0


@dataclass(frozen=True)
class FieldInfo:
    access_flags: int
    name_index: int
    descriptor_index: int

    @property
    def attributes_count(self) -> int:
        return 0


@dataclass(frozen=True)
class FieldsTable:
    fields: list[FieldInfo] = field(default_factory=list)

    def add_field(self,
                  tfield: TField,
                  constant_pool: ConstantPool,
                  access_flags: int = ACC_PUBLIC) -> None:
        name_index = constant_pool.add_constant_utf8(tfield.name)
        descriptor = get_type_descriptor(tfield.expr_type)
        descriptor_index = constant_pool.add_constant_utf8(descriptor)
        field_info = FieldInfo(access_flags, name_index, descriptor_index)
        self.fields.append(field_info)

    @property
    def count(self) -> int:
        return len(self.fields)


@dataclass(frozen=True)
class LocalTable:
    variables: list[tuple[str, int]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.variables) + 1

    def __getitem__(self, variable_name: str) -> int:
        index = -1
        for v, i in self.variables:
            if v == variable_name:
                index = i

        if index == -1:
            index = self.count
            self.variables.append((variable_name, index))

        return index


@dataclass(frozen=True)
class CodeAttribute:
    attribute_name_index: int
    local_table: LocalTable

    @property
    def attribute_length(self) -> int:
        raise NotImplementedError
    
    @property
    def max_stack(self) -> int:
        return 1024
    
    @property
    def max_locals(self) -> int:
        raise self.local_table.count
    
    @property
    def code_length(self) -> int:
        raise NotImplementedError
    
    @property
    def exception_table_length(self) -> int:
        return 0

    @property
    def attributes_count(self) -> int:
        return 0


@dataclass(frozen=True)
class MethodInfo:
    access_flags: int
    name_index: int
    descriptor_index: int
    code: CodeAttribute

    @property
    def attributes_count(self) -> int:
        return 1
    

@dataclass(frozen=True)
class MethodsTable:
    methods: list[MethodInfo] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.methods)

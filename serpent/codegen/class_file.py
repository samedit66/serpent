from __future__ import annotations
from dataclasses import dataclass, field

from serpent.semantic_checker.type_check import (
    TClass,
    TMethod,
    TUserDefinedMethod,
    TField)
from serpent.codegen.constpool import (
    ConstPool,
    add_package_prefix,
    get_type_descriptor,
    get_method_descriptor,
    make_const_pool)
from serpent.codegen.bytecommand import *
from serpent.codegen.genbytecode import (
    LocalTable,
    bytecode_size,
    generate_bytecode_for_method)
from serpent.codegen.byte_utils import *


ACC_PUBLIC = 0x0001
ACC_SUPER = 0x0020


@dataclass(frozen=True)
class ClassFile:
    minor_version: int
    major_version: int
    constant_pool: ConstPool
    access_flags: int
    this_class: int
    super_class: int
    fields_table: FieldsTable
    methods_table: MethodsTable

    @property
    def magic(self) -> int:
        return 0xcafebabe

    @property
    def cp_count_plus_one(self) -> int:
        return self.constant_pool.count + 1
    
    @property
    def interfaces_count(self) -> int:
        return 0
    
    @property
    def fields_count(self) -> int:
        raise self.fields_table.count

    @property
    def methods_count(self) -> int:
        raise self.methods_table.count

    @property
    def attributes_count(self) -> int:
        return 0
    
    def to_bytes(self) -> bytes:
        # Получаем байтовое представление константного пула.
        # Предполагается, что у объекта constant_pool есть метод to_bytes().
        cp_bytes = self.constant_pool.to_bytes()

        # Кодирование таблицы полей.
        # Каждый элемент таблицы полей кодируется следующим образом:
        #   u2 access_flags, u2 name_index, u2 descriptor_index, u2 attributes_count (обычно 0)
        fields_bytes = b"".join(
            merge_bytes(
                u2(field.access_flags),
                u2(field.name_index),
                u2(field.descriptor_index),
                u2(field.attributes_count)
            )
            for field in self.fields_table.fields
        )

        # Функция для кодирования атрибута Code метода.
        # Формат атрибута Code (таблица 5 спецификации):
        #   u2 attribute_name_index,
        #   u4 attribute_length (12 + длина кода),
        #   u2 max_stack,
        #   u2 max_locals,
        #   u4 code_length,
        #   u1[code_length] – байт-код,
        #   u2 exception_table_length (0),
        #   u2 attributes_count (0)
        def encode_code_attribute(code: CodeAttribute) -> bytes:
            # Вычисляем длину байткода как сумму размеров всех команд
            code_length = sum(cmd.size() for cmd in code.bytecode)
            # Длина атрибута: 2 (max_stack) + 2 (max_locals) + 4 (code_length) +
            # code_length + 2 (exception_table_length) + 2 (attributes_count) = 12 + code_length
            attribute_length = 12 + code_length
            code_bytes = merge_bytes(*(cmd.to_bytes() for cmd in code.bytecode))
            return merge_bytes(
                u2(code.attribute_name_index),
                u4(attribute_length),
                u2(code.max_stack),
                # Вместо свойства code.max_locals (в нашем определении – raise)
                # используем количество локальных переменных из local_table
                u2(code.local_table.count),
                u4(code_length),
                code_bytes,
                u2(code.exception_table_length),
                u2(code.attributes_count)
            )

        # Кодирование таблицы методов.
        # Каждый метод кодируется так:
        #   u2 access_flags,
        #   u2 name_index,
        #   u2 descriptor_index,
        #   u2 attributes_count (обычно 1, если есть Code),
        #   затем идут атрибуты метода (у нас только Code)
        methods_bytes = b"".join(
            merge_bytes(
                u2(method.access_flags),
                u2(method.name_index),
                u2(method.descriptor_index),
                u2(method.attributes_count),
                encode_code_attribute(method.code)
            )
            for method in self.methods_table.methods
        )

        # Собираем итоговое байтовое представление class‑файла.
        # Порядок полей согласно спецификации:
        #   u4 magic,
        #   u2 minor_version,
        #   u2 major_version,
        #   u2 constant_pool_count,
        #   constant_pool,
        #   u2 access_flags,
        #   u2 this_class,
        #   u2 super_class,
        #   u2 interfaces_count,
        #   [interfaces],
        #   u2 fields_count,
        #   fields_table,
        #   u2 methods_count,
        #   methods_table,
        #   u2 attributes_count
        return merge_bytes(
            u4(self.magic),
            u2(self.minor_version),
            u2(self.major_version),
            u2(self.cp_count_plus_one),
            cp_bytes,
            u2(self.access_flags),
            u2(self.this_class),
            u2(self.super_class),
            u2(self.interfaces_count),
            u2(self.fields_table.count),
            fields_bytes,
            u2(self.methods_table.count),
            methods_bytes,
            u2(self.attributes_count)
        )


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
                  constant_pool: ConstPool,
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
class CodeAttribute:
    attribute_name_index: int
    local_table: LocalTable
    bytecode: list[ByteCommand] = field(default_factory=list)

    @property
    def attribute_length(self) -> int:
        # Длина атрибута: 2 (max_stack) + 2 (max_locals) + 4 (code_length) +
        # code_length + 2 (exception_table_length) + 2 (attributes_count) = 12 + code_length
        attribute_length = 12 + self.code_length
        return attribute_length
    
    @property
    def max_stack(self) -> int:
        return 1024
    
    @property
    def max_locals(self) -> int:
        raise self.local_table.count
    
    @property
    def code_length(self) -> int:
        raise sum(cmd.size() for cmd in self.bytecode)
    
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
    
    def add_method(self,
                   tmethod: TMethod,
                   fq_class_name: str,
                   constant_pool: ConstPool,
                   access_flags: int = ACC_PUBLIC) -> None:
        name_index = constant_pool.add_utf8(tmethod.method_name)
        descriptor = get_method_descriptor([typ for (_, typ) in tmethod.parameters], tmethod.return_type)
        descriptor_index = constant_pool.add_utf8(descriptor)

        code_name_index = constant_pool.add_utf8("Code")
        local_table = LocalTable()
        bytecode = generate_bytecode_for_method(tmethod, fq_class_name, constant_pool, local_table)
        code = CodeAttribute(code_name_index, local_table, bytecode)

        method_info = MethodInfo(access_flags, name_index, descriptor_index, code)
        self.methods.append(method_info)


def make_default_integer_constructor(constant_pool: ConstPool) -> MethodInfo:
    constructor_index = constant_pool.add_methodref(
        method_name="<init>",
        method_desc="(I)V",
        fq_class_name=add_package_prefix("INTEGER"))

    general_constructor_index = constant_pool.add_methodref(
        method_name="<init>",
        method_desc="(I)V",
        fq_class_name=add_package_prefix("GENERAL"))

    bytecode = [ InvokeSpecial(general_constructor_index) ]
    code = CodeAttribute(constant_pool.add_utf8("Code"), LocalTable(), bytecode)

    methodref = constant_pool.get_constant(general_constructor_index)
    nat_index = methodref.name_and_type_index
    nat = constant_pool.get_constant(nat_index)

    name_index = nat.name_const_index
    descriptor_index = nat.type_const_index

    return MethodInfo(ACC_PUBLIC, name_index, descriptor_index, code)


def make_class_file(
        current_class: TClass,
        rest_classes: list[TClass],
        super_class_index: int | None = None) -> ClassFile:
    constant_pool = make_const_pool(current_class, rest_classes)

    if super_class_index is None:
        constant_pool.add_class(add_package_prefix("Object", package="java.lang"))
        super_class_index = 0

    fields_table = FieldsTable()
    for field in current_class.fields:
        fields_table.add_field(field, constant_pool)

    fq_class_name = add_package_prefix(current_class.class_name)
    methods_table = MethodsTable()
    for method in current_class.methods:
        methods_table.add_method(method, fq_class_name, constant_pool, ACC_PUBLIC)

    this_class_index = constant_pool.add_class(fq_class_name)

    return ClassFile(
        minor_version=0,
        major_version=52,
        constant_pool=constant_pool,
        access_flags=ACC_PUBLIC | ACC_SUPER,
        this_class=this_class_index,
        super_class=super_class_index,
        fields_table=fields_table,
        methods_table=methods_table)

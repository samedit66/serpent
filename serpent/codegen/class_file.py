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
    generate_bytecode_for_method)
from serpent.codegen.byte_utils import *


ACC_PUBLIC = 0x0001
ACC_SUPER = 0x0020
ACC_STATIC = 0x0008
ACC_VARARGS = 0x0080


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
        name_index = constant_pool.add_utf8(tfield.name)
        descriptor = get_type_descriptor(tfield.expr_type)
        descriptor_index = constant_pool.add_utf8(descriptor)
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


def is_builtin_type(type_name: str) -> bool:
    return (type_name in ["INTEGER", "REAL", "CHARACTER", "STRING", "BOOLEAN"]
            or type_name.startswith("ARRAY["))


def make_default_constructor_for_builtin_type(
        builtin_type_name: str, pool: ConstPool) -> MethodInfo:
    desc_mapping = {
        "STRING": f"(Ljava/lang/String;)V",
        "CHARACTER": f"(Ljava/lang/String;)V",
        "INTEGER": f"(I)V",
        "REAL": f"(F)V",
        "BOOLEAN": f"(I)V"
    }

    if builtin_type_name.startswith("ARRAY["):
        desc = f"(II)V"
    else:
        desc = desc_mapping[builtin_type_name]

    fq_class_name = add_package_prefix(builtin_type_name)

    constructor_index = pool.add_methodref(
        method_name="<init>",
        desc=desc,
        fq_class_name=fq_class_name)

    general_constructor_index = pool.add_methodref(
        method_name="<init>",
        desc=desc,
        fq_class_name=add_package_prefix("GENERAL"))

    bytecode = [ InvokeSpecial(general_constructor_index) ]
    code = CodeAttribute(pool.add_utf8("Code"), LocalTable(), bytecode)

    methodref = pool.get_by_index(constructor_index)
    nat_index = methodref.name_and_type_index
    nat = pool.pool.get_by_index(nat_index)

    name_index = nat.name_const_index
    descriptor_index = nat.type_const_index

    return MethodInfo(ACC_PUBLIC, name_index, descriptor_index, code)


def make_default_constructor(type_name: str, pool: ConstPool) -> MethodInfo:
    fq_class_name = add_package_prefix(type_name)
    desc = "()V"

    constructor_index = pool.add_methodref(
        method_name="<init>",
        desc=desc,
        fq_class_name=fq_class_name)

    general_constructor_index = pool.add_methodref(
        method_name="<init>",
        desc=desc,
        fq_class_name=add_package_prefix("GENERAL"))

    bytecode = [ InvokeSpecial(general_constructor_index) ]
    code = CodeAttribute(pool.add_utf8("Code"), LocalTable(), bytecode)

    methodref = pool.get_by_index(constructor_index)
    nat_index = methodref.name_and_type_index
    nat = pool.get_by_index(nat_index)

    name_index = nat.name_const_index
    descriptor_index = nat.type_const_index

    return MethodInfo(ACC_PUBLIC, name_index, descriptor_index, code)


def make_default_constructors_for_general_class(pool: ConstPool) -> list[MethodInfo]:
    descs = [
        "(Ljava/lang/String;)V",
        "(I)V",
        "(F)V",
        "(II)V",
        "()V"
    ]

    fq_class_name = add_package_prefix("GENERAL")
    fq_object_name = add_package_prefix("PLATFORM")

    methods = []
    for desc in descs:
        constructor_index = pool.add_methodref(
            method_name="<init>",
            desc=desc,
            fq_class_name=fq_class_name)
        print(constructor_index)

        general_constructor_index = pool.add_methodref(
            method_name="<init>",
            desc=desc,
            fq_class_name=fq_object_name)

        bytecode = [ InvokeSpecial(general_constructor_index) ]
        code = CodeAttribute(pool.add_utf8("Code"), LocalTable(), bytecode)

        methodref = pool.get_by_index(constructor_index)
        nat = pool.get_by_index(methodref.name_and_type_index)

        name_index = nat.name_const_index
        descriptor_index = nat.type_const_index

        methods.append(
            MethodInfo(ACC_PUBLIC, name_index, descriptor_index, code))

    return methods


def make_class_file(
        current_class: TClass,
        rest_classes: list[TClass],
        minor_version: int = 0,
        major_version: int = 52,
        entry_point_method: str | None = None) -> ClassFile:
    constant_pool = make_const_pool(current_class, rest_classes)

    fq_general_class_name = add_package_prefix("GENERAL")
    constant_pool.add_class(fq_general_class_name)
    super_class_index = constant_pool.find_class(fq_general_class_name)

    fields_table = FieldsTable()
    for field in current_class.fields:
        fields_table.add_field(field, constant_pool)

    fq_class_name = add_package_prefix(current_class.class_name)
    methods_table = MethodsTable()

    if current_class.class_name == "GENERAL":
        methods = make_default_constructors_for_general_class(
            constant_pool)
        methods_table.methods.extend(methods)
    elif is_builtin_type(current_class.class_name):
        default_constructor = make_default_constructor_for_builtin_type(
            current_class.class_name, constant_pool)
        methods_table.methods.append(default_constructor)
    else:
        default_constructor = make_default_constructor(
            current_class.class_name, constant_pool)
        methods_table.methods.append(default_constructor)

    for method in current_class.methods:
        methods_table.add_method(method, fq_class_name, constant_pool, ACC_PUBLIC)

    this_class_index = constant_pool.add_class(fq_class_name)

    # Данный класс является точкой входа в программу:
    # необходимо сгенерировать метод main, в который необходимо 
    # добавить метод следующего вида:
    # public static void main (String[] args) {
    #     APPLICATION app = new APPLICATION();
    #     app.make();     
    # }
    # Т.е. вызывается конструктор, указанный в качестве entry_point_method,
    # и с него начинается выполнение всего приложения
    if entry_point_method is not None:
        root_class_name = fq_class_name

        # TODO: проверка на то, что указанный метод,
        # реально является конструктором, который не принимает никаких аргументов
        main_index = constant_pool.add_methodref(
            method_name="main",
            desc="([Ljava/lang/String;)V",
            fq_class_name=root_class_name)
        root_class_index = constant_pool.find_class(root_class_name)
        init_index = constant_pool.find_methodref(
            method_name="<init>",
            fq_class_name=root_class_name,
            desc="()V")
        entry_point_index = constant_pool.find_methodref(
            method_name=entry_point_method,
            fq_class_name=root_class_name,
            desc="()V")
        
        bytecode = [
            New(root_class_index),
            Dup(),
            InvokeSpecial(init_index),
            InvokeVirtual(entry_point_index),
            Return()]
        
        code = CodeAttribute(
            constant_pool.add_utf8("Code"),
            LocalTable(),
            bytecode)
        
        methodref = constant_pool.get_by_index(main_index)
        nat = constant_pool.get_by_index(methodref.name_and_type_index)

        name_index = nat.name_const_index
        descriptor_index = nat.type_const_index

        main_method = MethodInfo(
            ACC_PUBLIC | ACC_STATIC | ACC_VARARGS,
            name_index,
            descriptor_index, code)
        methods_table.methods.append(main_method)

    return ClassFile(
        minor_version=minor_version,
        major_version=major_version,
        constant_pool=constant_pool,
        access_flags=ACC_PUBLIC | ACC_SUPER,
        this_class=this_class_index,
        super_class=super_class_index,
        fields_table=fields_table,
        methods_table=methods_table)

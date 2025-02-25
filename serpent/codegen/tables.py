from dataclasses import dataclass, field

from serpent.semantic_checker.type_check import (
    TClass,
    TUserDefinedMethod,
    TExternalMethod,
    TMethod,
    TField)

from serpent.codegen.constant_pool import (
    ConstantPool,
    get_type_descriptor,
    get_method_descriptor,
    add_package_prefix)
from serpent.codegen.bytecode import Bytecode


# Флаги доступа
ACC_PUBLIC    = 0x0001
ACC_SUPER     = 0x0002
ACC_STATIC    = 0x0008
ACC_FINAL     = 0x0010
ACC_ABSTRACT  = 0x0400


@dataclass(frozen=True)
class FieldTableEntry:
    access_flags: int          # u2 флаги доступа
    name_index: int            # u2 индекс CONSTANT_Utf8 с именем поля
    descriptor_index: int      # u2 индекс CONSTANT_Utf8 с дескриптором поля
    attributes_count: int      # u2 количество атрибутов поля
    attributes: list = field(default_factory=list)  # список атрибутов (пуст)


@dataclass
class FieldTable:
    entries: list[FieldTableEntry] = field(default_factory=list)


@dataclass(frozen=True)
class CodeAttribute:
    attribute_name_index: int   # u2 индекс CONSTANT_Utf8 с именем "Code"
    attribute_length: int       # u4 длина атрибута Code (без первых 6 байт)
    max_stack: int              # u2 размер стека операндов
    max_locals: int             # u2 количество локальных переменных
    code_length: int            # u4 длина байт-кода метода
    code: list[Bytecode]        # массив байт-кода
    exception_table_length: int # u2 количество записей в таблице исключений (обычно 0)
    attributes_count: int       # u2 количество атрибутов внутри Code (обычно 0)


@dataclass(frozen=True)
class MethodTableEntry:
    access_flags: int           # u2 флаги доступа
    name_index: int             # u2 индекс CONSTANT_Utf8 с именем метода
    descriptor_index: int       # u2 индекс CONSTANT_Utf8 с дескриптором метода
    attributes_count: int       # u2 количество атрибутов метода
    attributes: list = field(default_factory=list)  # список атрибутов (например, атрибут Code)


@dataclass
class MethodTable:
    entries: list[MethodTableEntry] = field(default_factory=list)


# Класс, описывающий Class-файл
@dataclass
class ClassFile:
    magic: int                   # u4 магическое число (0xCAFEBABE)
    minor_version: int           # u2 малая версия
    major_version: int           # u2 большая версия
    constant_pool_count: int     # u2 количество элементов в пуле констант +1
    constant_pool: list          # список констант (CONSTANT)
    access_flags: int            # u2 флаги доступа класса
    this_class: int              # u2 индекс в пуле констант, описывающей данный класс
    super_class: int             # u2 индекс в пуле констант, описывающей родительский класс (0 для <GENERAL>)
    interfaces: list[int]        # таблица индексов интерфейсов (пустая, если не используется)
    fields_count: int            # u2 количество полей (без наследуемых)
    field_table: FieldTable      # таблица полей
    methods_count: int           # u2 количество методов (без наследуемых)
    method_table: MethodTable    # таблица методов
    attributes_count: int        # u2 количество атрибутов класса (обычно 0)
    attributes: list             # список атрибутов класса (обычно пуст)


# Вспомогательные функции для формирования ключей (для фильтрации дубликатов)

def field_signature_key(field: TField) -> tuple[str, str]:
    return (field.name, get_type_descriptor(field.expr_type))


def method_signature_key(method: TMethod) -> tuple[str, str]:
    ret_desc = get_type_descriptor(method.return_type)
    params_desc = tuple(get_type_descriptor(param_type) for _, param_type in method.parameters)
    return (method.method_name, ret_desc, params_desc)


# Функции создания таблиц с учётом фильтрации (для класса, отличного от <GENERAL>)

def create_field_table(tclass: TClass, constant_pool: ConstantPool, inherited_keys: set = None) -> FieldTable:
    entries = []
    for field_obj in tclass.fields:
        key = field_signature_key(field_obj)
        # Если inherited_keys переданы, пропускаем поле, если оно уже объявлено в родительском (<GENERAL>) классе
        if inherited_keys is not None and key in inherited_keys:
            continue
        entry = FieldTableEntry(
            access_flags=ACC_PUBLIC,  # поля публичные по условию
            name_index=constant_pool.find_or_create_constant_utf8(field_obj.name),
            descriptor_index=constant_pool.find_or_create_constant_utf8(get_type_descriptor(field_obj.expr_type)),
            attributes_count=0,
            attributes=[]
        )
        entries.append(entry)
    return FieldTable(entries=entries)


def create_method_table(tclass: TClass, constant_pool: ConstantPool, inherited_keys: set = None) -> MethodTable:
    entries = []
    for method in tclass.methods:
        key = method_signature_key(method)
        if inherited_keys is not None and key in inherited_keys:
            continue
        if isinstance(method, TExternalMethod):
            access_flags = ACC_PUBLIC | ACC_STATIC
            attributes = []
            attr_count = 0
        else:
            access_flags = ACC_PUBLIC  # для пользовательских методов
            # Вычисляем количество локальных переменных: если метод не статический,
            # то индекс 0 – это this, затем параметры и локальные переменные
            locals_count = 1 + len(method.parameters)
            if isinstance(method, TUserDefinedMethod):
                locals_count += len(method.variables)
            code_attr_name_index = constant_pool.find_or_create_constant_utf8("Code")
            code_attribute = CodeAttribute(
                attribute_name_index=code_attr_name_index,
                attribute_length=12,
                max_stack=1000,
                max_locals=locals_count,
                code_length=0,
                code=[],
                exception_table_length=0,
                attributes_count=0
            )
            attributes = [code_attribute]
            attr_count = 1

        entry = MethodTableEntry(
            access_flags = access_flags,
            name_index = constant_pool.find_or_create_constant_utf8(method.method_name),
            descriptor_index = constant_pool.find_or_create_constant_utf8(get_method_descriptor(method)),
            attributes_count = attr_count,
            attributes = attributes
        )
        entries.append(entry)
    return MethodTable(entries=entries)


# Функция создания ClassFile
def create_class_file(tclass: TClass, constant_pool: ConstantPool, general_class: TClass) -> ClassFile:
    """
    Создаёт объект ClassFile для класса tclass.
    Если tclass не является <GENERAL>, то поля и методы, объявленные в <GENERAL>,
    не включаются в таблицы, так как они уже присутствуют в родительском классе.
    """
    # Если класс не <GENERAL>, вычисляем ключи для полей и методов, объявленных в <GENERAL>
    if tclass.class_name != "<GENERAL>":
        inherited_field_keys = {field_signature_key(f) for f in general_class.fields}
    else:
        inherited_field_keys = None

    # Создаём таблицы полей и методов с фильтрацией
    field_table = create_field_table(tclass, constant_pool, inherited_field_keys)
    method_table = create_method_table(tclass, constant_pool)

    # Определяем индекс текущего класса в пуле констант
    fq_this_class = add_package_prefix(tclass.class_name)
    this_class_index = constant_pool.add_constant_class(fq_this_class)
    # Для родителя: если класс уже <GENERAL>, родителя нет (0), иначе родитель – <GENERAL>
    if tclass.class_name == "<GENERAL>":
        super_class_index = 0
    else:
        fq_super_class = add_package_prefix("<GENERAL>")
        super_class_index = constant_pool.add_constant_class(fq_super_class)

    access_flags = ACC_PUBLIC | ACC_SUPER  # согласно спецификации, обязательно ACC_SUPER
    cp_count = len(constant_pool.constant_pool) + 1
    minor_version = 0
    major_version = 52  # например, для Java 8
    interfaces = []     # без интерфейсов
    attributes = []     # атрибутов класса нет

    return ClassFile(
        magic=0xcafebabe,
        minor_version=minor_version,
        major_version=major_version,
        constant_pool_count=cp_count,
        constant_pool=constant_pool.constant_pool,
        access_flags=access_flags,
        this_class=this_class_index,
        super_class=super_class_index,
        interfaces=interfaces,
        fields_count=len(field_table.entries),
        field_table=field_table,
        methods_count=len(method_table.entries),
        method_table=method_table,
        attributes_count=0,
        attributes=attributes,
    )

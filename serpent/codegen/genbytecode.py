from serpent.semantic_checker.type_check import *

from serpent.codegen.constant_pool import (
    ConstantPool,
    add_package_prefix,
    get_type_descriptor)
from serpent.codegen.bytecommand import *
from serpent.codegen.class_file import LocalTable


def generate_bytecode_for_integer_const(
        const: TIntegerConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("INTEGER")
    integer_class_idx = constant_pool.add_constant_class(fq_class_name)

    fq_general_class_name = add_package_prefix("GENERAL")
    methodref_idx = constant_pool.add_methodref(
        fq_general_class_name,
        method_name="<init>",
        method_desc="(I)V")

    bytecode = [
        New(integer_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_real_const(
        const: TRealConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("REAL")
    real_class_idx = constant_pool.add_constant_class(fq_class_name)

    fq_general_class_name = add_package_prefix("GENERAL")
    methodref_idx = constant_pool.add_methodref(
        fq_general_class_name,
        method_name="<init>",
        method_desc="(F)V")

    bytecode = [
        New(real_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_bool_const(
        const: TBoolConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("BOOLEAN")
    bool_class_idx = constant_pool.add_constant_class(fq_class_name)

    fq_general_class_name = add_package_prefix("GENERAL")
    methodref_idx = constant_pool.add_methodref(
        fq_general_class_name,
        method_name="<init>",
        method_desc="(Z)V")

    bytecode = [
        New(bool_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_string_const(
        const: TStringConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("STRING")
    string_class_idx = constant_pool.add_constant_class(fq_class_name)

    fq_general_class_name = add_package_prefix("GENERAL")
    methodref_idx = constant_pool.add_methodref(
        fq_general_class_name,
        method_name="<init>",
        method_desc="(Ljava/lang/String;)V")

    bytecode = [
        New(string_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_character_const(
        const: TCharacterConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("CHARACTER")
    char_class_idx = constant_pool.add_constant_class(fq_class_name)

    fq_general_class_name = add_package_prefix("GENERAL")
    methodref_idx = constant_pool.add_methodref(
        fq_general_class_name,
        method_name="<init>",
        method_desc="(Ljava/lang/String;)V")

    bytecode = [
        New(char_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_void_const() -> list[ByteCommand]:
    return [Aconst_null()]


def generate_bytecode_for_create_expr(
        tcreate_expr: TCreateExpr,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    create_fq_class_name = add_package_prefix(tcreate_expr.expr_type.full_name)
    class_index = constant_pool.add_constant_class(create_fq_class_name)
    
    bytecode = [
        New(class_index),
        Dup()
    ]

    init_idx = constant_pool.add_methodref(
        fq_class_name=create_fq_class_name,
        method_name="<init>",
        method_desc="()V")
    bytecode.extend(
        [InvokeSpecial(init_idx), Dup()])

    for arg in tcreate_expr.arguments:
        arg_bytecode = generate_bytecode_for_expr(arg, fq_class_name, constant_pool, local_table)
        bytecode.extend(arg_bytecode)

    constructor_desc = "".join(get_type_descriptor(arg.expr_type) for arg in tcreate_expr.arguments)
    constructor_idx = constant_pool.add_methodref(
        fq_class_name=create_fq_class_name,
        method_name=tcreate_expr.constructor_name,
        method_desc=f"({constructor_desc})V")
    bytecode.append(InvokeVirtual(constructor_idx))

    return bytecode


def generate_bytecode_for_feature_call(
        tfeature_call: TFeatureCall,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []
    
    if tfeature_call.owner is None:
        bytecode.append(Aload(0))
    else:
        bytecode.extend(
            generate_bytecode_for_expr(
                tfeature_call.owner,
                fq_class_name,
                constant_pool,
                local_table))

    for arg in tfeature_call.arguments:
        arg_bytecode = generate_bytecode_for_expr(
            arg, fq_class_name, constant_pool, local_table)
        bytecode.extend(arg_bytecode)

    if tfeature_call.owner is None:
        methoref_idx = constant_pool.find_constant_methodref(
            fq_class_name, tfeature_call.feature_name)
        
        print(1, fq_class_name, tfeature_call.feature_name)
    else:
        owner_fq_class_name = add_package_prefix(tfeature_call.owner.expr_type.full_name)
        methoref_idx = constant_pool.find_constant_methodref(
            owner_fq_class_name, tfeature_call.feature_name)
    
        print(2, owner_fq_class_name, tfeature_call.feature_name)
    assert methoref_idx != -1
    bytecode.append(InvokeVirtual(methoref_idx))

    return bytecode


def generate_bytecode_for_field(
        tfield: TField,
        fq_class_name: str,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    field_index = constant_pool.add_field(fq_class_name, tfield)
    return [GetField(field_index)]


def generate_bytecode_for_variable(
        tvariable: TVariable,
        local_table: LocalTable) -> list[ByteCommand]:
    variable_index = local_table[tvariable.name]
    return [Aload(variable_index)]


def generate_bytecode_for_expr(
        texpr: TExpr,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    match texpr:
        case TIntegerConst():
            return generate_bytecode_for_integer_const(texpr, constant_pool)
        case TRealConst():
            return generate_bytecode_for_real_const(texpr, constant_pool)
        case TBoolConst():
            return generate_bytecode_for_bool_const(texpr, constant_pool)
        case TCharacterConst():
            return generate_bytecode_for_character_const(texpr, constant_pool)
        case TStringConst():
            return generate_bytecode_for_string_const(texpr, constant_pool)
        case TStringConst():
            return generate_bytecode_for_void_const(texpr)
        case TCreateExpr():
            return generate_bytecode_for_create_expr(
                texpr, fq_class_name, constant_pool, local_table)
        case TFeatureCall():
            return generate_bytecode_for_feature_call(
                texpr, fq_class_name, constant_pool, local_table)
        case TField():
            return generate_bytecode_for_field(texpr, fq_class_name, constant_pool)
        case TVariable():
            return generate_bytecode_for_variable(texpr, local_table)
        case _:
            raise NotImplementedError


def generate_bytecode_for_assignment(
        tassignment: TAssignment,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    lvalue = tassignment.lvalue
    rvalue = tassignment.rvalue

    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(lvalue, fq_class_name, constant_pool, local_table))
    bytecode.extend(generate_bytecode_for_expr(rvalue, fq_class_name, constant_pool, local_table))

    match lvalue:
        case TField() as tfield:
            field_index = constant_pool.add_field(fq_class_name, tfield)
            bytecode.append(PutField(field_index))
        case TVariable() as tvariable:
            variable_index = local_table[tvariable.name]
            bytecode.append(Astore(variable_index))

    return bytecode


def generate_bytecode_for_smmt(
        tstmt: TStatement,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    match tstmt:
        case TAssignment():
            return generate_bytecode_for_assignment(
                tstmt, fq_class_name, constant_pool, local_table)
        case _: assert False

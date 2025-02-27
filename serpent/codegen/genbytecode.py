from serpent.semantic_checker.type_check import (
    TExpr,
    TCreateExpr,
    TStatement,
    TAssignment)

from serpent.codegen.constant_pool import ConstantPool, add_package_prefix, get_type_descriptor
from serpent.codegen.bytecommand import *


def generate_bytecode_for_literal(
        literal: TExpr,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    raise NotImplementedError


def generate_bytecode_for_create_expr(
        tcreate_expr: TCreateExpr,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix(tcreate_expr.expr_type.full_name)
    class_index = constant_pool.add_constant_class(fq_class_name)
    
    bytecode = [
        New(class_index),
        Dup()
    ]

    init_idx = constant_pool.add_methodref(
        fq_class_name=fq_class_name,
        method_name="<init>",
        method_desc="()V")
    bytecode.extend([ InvokeSpecial(init_idx), Dup() ])

    for arg in tcreate_expr.arguments:
        arg_bytecode = generate_bytecode_for_expr(arg)
        bytecode.extend(arg_bytecode)

    constructor_desc = "".join(get_type_descriptor(arg.expr_type) for arg in tcreate_expr.arguments)
    constructor_idx = constant_pool.add_methodref(
        fq_class_name=fq_class_name,
        method_name=tcreate_expr.constructor_name,
        method_desc=f"({constructor_desc})V")
    bytecode.append(InvokeVirtual(constructor_idx))

    return bytecode


def generate_bytecode_for_expr(texpr: TExpr) -> list[ByteCommand]:
    match texpr:
        case TCreateExpr() as tcreate_expr:
            return generate_bytecode_for_create_expr(tcreate_expr)
        case _:
            raise NotImplementedError


def generate_bytecode_for_assignment(tassignment: TAssignment) -> list[ByteCommand]:
    ...


def generate_bytecode_for_smmt(tstmt: TStatement) -> list[ByteCommand]:
    ...

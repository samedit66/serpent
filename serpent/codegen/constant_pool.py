from abc import ABC, abstractmethod
from dataclasses import dataclass
import struct

from serpent.errors import CompilerError
from serpent.semantic_checker.symtab import Type
from serpent.semantic_checker.type_check import *
from serpent.codegen.byte_utils import *
from serpent.codegen.constpool import *


DEFAULT_PACKAGE = "com.eiffel.base"
"""Пакет, в котором будут все классы, объявленные программистом
или в стандартной библиотеке
"""

ROOT_CLASS_NAME = "GENERAL"
"""Название корневого класса, который будет обладать всеми методами всех
классов в программе. Является родителем класса ANY, определенного в
стандартной библиотеки Eiffel
"""

PLATFORM_CLASS_NAME = "PLATFORM"
"""Название класса из RTL-библиотеки, который определяет способы
одностороннего (Eiffel -> Java) взиамодействия между Eiffel и Java классами.
Является родителем для класса GENERAL
"""

COMPILER_NAME = "serpent"
"""Имя компилятора, используется в отладочных целях при печати
сообщений об ошибках
"""


def split_package_path(package: str) -> list[str]:
    return package.split(".")


def make_fully_qualifed_name(parts: list[str]) -> str:
    return "/".join(parts)


def add_package_prefix(class_name: str, package: str = DEFAULT_PACKAGE) -> str:
    return make_fully_qualifed_name(
        split_package_path(package) + [class_name])


def get_type_descriptor(typ: Type) -> str:
    """
    Генерирует дескриптор типа для виртуальной машины Java.
    Для примитивных типов используется однобуквенное обозначение,
    для ссылочных типов возвращается формат "L<fully-qualified-name>;"
    """
    if typ.name == "<VOID>":
        return "V"
    # Если имя уже содержит '/', считаем его полностью квалифицированным
    fq_name = typ.name if "/" in typ.name else add_package_prefix(typ.name)
    return f"L{fq_name};"


def get_method_descriptor(args_types: list[Type], return_type: Type) -> str:
    params_desc = "".join(get_type_descriptor(arg_type) for arg_type in args_types)
    return_desc = get_type_descriptor(return_type)
    return f"({params_desc}){return_desc}"


def process_expression_literals(expr: TExpr, pool: ConstPool) -> None:
    match expr:
        case TIntegerConst(value=value):
            pool.add_integer(value)
        case TRealConst(value=value):
            pool.add_float(value)
        case TStringConst(value=value):
            pool.add_string(value)
        case TCharacterConst(value=value):
            raise NotImplementedError
        case TBoolConst(value=value):
            raise NotImplementedError
        case TFeatureCall(
                expr_type=return_type,
                feature_name=method_name,
                arguments=arguments,
                owner=owner):
            type = get_method_descriptor(
                args_types=[arg.expr_type for arg in arguments],
                return_type=return_type)

            if owner is None:
                fq_class_name = None
            else:
                fq_class_name = add_package_prefix(owner.expr_type.full_name)
                pool.add_class(fq_class_name)
            
            pool.add_methodref(method_name, type, fq_class_name)
            for arg in arguments:
                process_expression_literals(arg, pool)
        case TCreateExpr(
                expr_type=expr_type,
                constructor_name=method_name,
                arguments=arguments):
            fq_class_name = add_package_prefix(expr_type.full_name)
            pool.add_class(fq_class_name)

            type = get_method_descriptor(
                args_types=[arg.expr_type for arg in arguments],
                return_type=return_type)

            pool.add_methodref(method_name, type, fq_class_name)
            for arg in arguments:
                process_expression_literals(arg, pool)
        case TBinaryOp(left=left, right=right):
            process_expression_literals(left, pool)
            process_expression_literals(right, pool)
        case TUnaryOp(argument=argument):
            process_expression_literals(argument, pool)
        # Для TVariable и TVoidConst ничего не делаем


def process_statement_literals(stmt: TStatement, pool: ConstPool) -> None:
    match stmt:
        case TAssignment(lvalue=lvalue, rvalue=rvalue):
            process_expression_literals(lvalue, pool)
            process_expression_literals(rvalue, pool)
        case TIfStmt(
                condition=condition,
                then_branch=then_branch,
                else_branch=else_branch,
                elseif_branches=elseif_branches):
            process_expression_literals(condition, pool)
            for s in then_branch:
                process_statement_literals(s, pool)
            for s in else_branch:
                process_statement_literals(s, pool)
            for cond, stmts in elseif_branches:
                process_expression_literals(cond, pool)
                for s in stmts: process_statement_literals(s, pool)
        case TLoopStmt(
                init_smtmts=init_stmts,
                until_cond=until_cond,
                body=body):
            for s in init_stmts:
                process_statement_literals(s, pool)
            process_expression_literals(until_cond, pool)
            for s in body:
                process_statement_literals(s, pool)
        case TRoutineCall(feature_call=feature_call):
            process_expression_literals(feature_call, pool)
        case _: assert False


def get_external_method_descriptor(method: TExternalMethod) -> str:
    fq_name = make_fully_qualifed_name(split_package_path(DEFAULT_PACKAGE) + [PLATFORM_CLASS_NAME])
    platform_descriptor = f"L{fq_name};"

    # В качестве типов параметров устанавливаем всем параметрам
    # класса PLATFORM - это позволит реализовать взаимодействие между
    # кодом на Eiffel и Java
    params_desc = "".join(platform_descriptor * len(method.parameters))
    full_params_desc = platform_descriptor + params_desc

    # Аналогично поступаем для всех дескрипторов, которые не являются void
    return_desc = get_type_descriptor(method.return_type)
    if return_desc != "V":
        return_desc = platform_descriptor

    return f"({full_params_desc}){return_desc}"


def process_external_method(pool: ConstPool, method: TExternalMethod) -> None:
    full_alias = method.alias
    parts = split_package_path(full_alias)
    if len(parts) < 2:
        raise CompilerError(
            f"Alias '{full_alias}' is not a correct reference to a Java method, "
            f"see method '{method.method_name}' of class '{pool.fq_class_name}'"
            source=COMPILER_NAME)

    method_desc = get_method_descriptor(
        [param. for arg in method.parameters]
    )
    
    pool.add_methodref(java_method_name, method_desc, fq_)

    nat_method = NameAndType(
        pool.next_index,
        name_const_index=method_name_idx,
        type_const_index=method_desc_idx
    )
    pool.pool.append(nat_method)
    nat_method_idx = nat_method.index
    
    methodref = Methodref(
        pool.next_index,
        class_index=class_const_idx,
        name_and_type_index=nat_method_idx
    )
    pool.pool.append(methodref)


def find_method(classes: list[TClass], method_name: str) -> TMethod:
    for cls in classes:
        for method in cls.methods:
            if method.method_name == method_name:
                return method
    assert False


def find_field(classes: list[TClass], field_name: str) -> TField:
    for cls in classes:
        for field in cls.fields:
            if field.name == field_name:
                return field
    assert False


def make_const_pool(tclass: TClass) -> ConstPool:
    fq_class_name = add_package_prefix(tclass.class_name)
    pool = ConstPool(fq_class_name)

    for field in tclass.fields:
        pool.add_field(fq_class_name, field)

    for method in tclass.methods:
        if isinstance(method, TExternalMethod):
            process_external_method(pool, method)
        else:
            assert isinstance(method, TUserDefinedMethod)

            pool.add_method(fq_class_name, method)
            for stmt in method.body:
                process_statement_literals(stmt, pool)

    return pool


def pretty_print_pool(pool: ConstantPool) -> None:
    print("Constant Pool:")
    print("-" * 40)
    for const in pool:
        if isinstance(const, Utf8):
            print(f"{const.index:3}: Utf8       : '{const.text}'")
        elif isinstance(const, Integer): 
            print(f"{const.index:3}: Integer    : {const.const}")
        elif isinstance(const, Float): 
            print(f"{const.index:3}: Float      : {const.const}")
        elif isinstance(const, String): 
            print(f"{const.index:3}: String     : string_index={const.string_index}")
        elif isinstance(const, NameAndType):
            print(f"{const.index:3}: NameAndType: name_index={const.name_const_index}, type_index={const.type_const_index}")
        elif isinstance(const, Class):
            print(f"{const.index:3}: Class      : name_index={const.name_index}")
        elif isinstance(const, Fieldref): 
            print(f"{const.index:3}: Fieldref   : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        elif isinstance(const, Methodref): 
            print(f"{const.index:3}: Methodref  : class_index={const.class_index}, name_and_type_index={const.name_and_type_index}")
        else:
            print(f"{const.index:3}: Unknown constant type: {const}")
    print("-" * 40)

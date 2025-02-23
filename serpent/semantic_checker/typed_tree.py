from __future__ import annotations
from dataclasses import dataclass, field

from serpent.tree.expr import *
from serpent.errors import CompilerError
from serpent.semantic_checker.analyze_inheritance import FlattenClass
from serpent.semantic_checker.symtab import (
    Type,
    LocalSymbolTable,
    ClassHierarchy,
    GlobalClassTable,
    type_of_class_decl_type,
    make_class_symtab)


@dataclass
class TExpr(ABC):
    expr_type: Type 


class TConstantValue(TExpr, ABC):
    pass


@dataclass(frozen=True)
class TIntegerConst(TConstantValue):
    value: int


@dataclass(frozen=True)
class TRealConst(TConstantValue):
    value: float


@dataclass(frozen=True)
class TCharacterConst(TConstantValue):
    value: str


@dataclass(frozen=True)
class TStringConst(TConstantValue):
    value: str


@dataclass(frozen=True)
class TBoolConst(TConstantValue):
    value: bool


@dataclass
class TVoidConst(TConstantValue):
    pass


@dataclass(frozen=True)
class TFeatureCall(TExpr):
    feature_name: str
    arguments: list[TExpr] = field(default_factory=list)
    owner_type: Type


@dataclass(frozen=True)
class TCreateExpr(TExpr):
    constructor_name: str
    arguments: list[TExpr] = field(default_factory=list)


@dataclass(frozen=True)
class TElseifExprBranch(TExpr):
    condition: TExpr
    expr: TExpr


@dataclass(frozen=True)
class TIfExpr(TExpr):
    condition: TExpr
    then_expr: TExpr
    else_expr: TExpr
    elseif_exprs: list[TElseifExprBranch] = field(default_factory=list)


@dataclass(frozen=True)
class TBinaryOp(TExpr):
    left: TExpr
    right: TExpr


@dataclass(frozen=True)
class TUnaryOp(TExpr):
    argument: TExpr


@dataclass(frozen=True)
class TAndOp(TBinaryOp):
    pass


@dataclass(frozen=True)
class TOrOp(TBinaryOp):
    pass


@dataclass(frozen=True)
class TNotOp(TUnaryOp):
    pass


@dataclass(frozen=True)
class TAndThenOp(TBinaryOp):
    pass


@dataclass(frozen=True)
class TOrElseOp(TBinaryOp):
    pass


@dataclass(frozen=True)
class TXorOp(TBinaryOp):
    pass


@dataclass(frozen=True)
class TImpliesOp(TBinaryOp):
    pass


@dataclass(frozen=True)
class Variable(TExpr):
    name: str


def annotate_constant_expr(const_expr: Expr) -> TExpr:
    match const_expr:
        case IntegerConst(value=value):
            return TIntegerConst(Type("INTEGER"), value)
        case RealConst(value=value):
            return TRealConst(Type("REAL"), value)
        case CharacterConst(value=value):
            return TCharacterConst(Type("CHARACTER"), value)
        case StringConst(value=value):
            return TStringConst(Type("STRING"), value=value)
        case BoolConst(value=value):
            return TBoolConst(Type("BOOLEAN"), value=value)
        case VoidConst():
            return TVoidConst(Type("NONE"))
    assert False


def annotate_feature_call(feature_call: FeatureCall, symtab: LocalSymbolTable) -> TFeatureCall:
    ...


def annotate_precursor_call(precursor_call: PrecursorCall, symtab: LocalSymbolTable) -> TFeatureCall:
    ...


def annotate_if_expr():
    ...


def annotate_with_types(expr: Expr,
                        symtab: LocalSymbolTable,
                        hierarchy: ClassHierarchy,
                        global_class_table: GlobalClassTable,
                        flatten_class_mapping: dict[str, FlattenClass]) -> TExpr:
    match expr:
        case ConstantValue():
            return annotate_constant_expr(expr)
        case FeatureCall(feature_name=name, owner=owner) as fcall:
            if owner is not None:
                owner_expr = annotate_with_types(
                    owner,
                    symtab,
                    hierarchy,
                    global_class_table,
                    flatten_class_mapping)
                
                class_symtab = global_class_table.get_class_table(
                    owner_expr.expr_type.full_name)
            else:
                mangled_name = symtab.mangle_name(name)
                if symtab.has_local(mangled_name):
                    local_type = symtab.type_of(mangled_name)
                    return Variable(local_type, mangled_name)
                
                class_symtab = symtab.class_symtab

            mangled_name = symtab.class_symtab.mangle_name(name)
            if not symtab.class_symtab.has_feature(mangled_name):
                raise CompilerError
            
            expr_type = symtab.class_symtab.type_of_feature(mangled_name)

            arguments = [
                annotate_with_types(
                    arg,
                    symtab,
                    hierarchy,
                    global_class_table,
                    flatten_class_mapping)
                for arg in fcall.arguments
            ]

            # Где-то тут надо провалидировать сигнатуру фичи
            # и типы аргументов реально переданных

            return TFeatureCall(expr_type, mangled_name, arguments)
        case PrecursorCall() as pcall:
            return annotate_precursor_call(pcall, symtab)
        case CreateExpr(object_type=object_type, constructor_call=constructor_call):
            if not isinstance(object_type, ClassType):
                raise CompilerError
            expr_type = type_of_class_decl_type(object_type)

            if expr_type.name not in hierarchy:
                raise CompilerError
            
            if not global_class_table.has_class_table(expr_type.full_name):
                flatten_cls = flatten_class_mapping[expr_type.name]
                new_class_symtab = make_class_symtab(object_type, flatten_cls, hierarchy)
                global_class_table.add_class_table(new_class_symtab)

            class_symtab = global_class_table.get_class_table(expr_type.full_name)

            if constructor_call is None:
                constructor_name = "default_create"
                arguments = []
            else:
                constructor_name = constructor_call.feature_name
                arguments = constructor_call.arguments

            mangled_name = class_symtab.mangle_name(constructor_name)
            if not class_symtab.has_feature(mangled_name):
                raise CompilerError
            if not class_symtab.is_constructor(mangled_name):
                raise CompilerError

            arguments = [
                annotate_with_types(
                    arg,
                    symtab,
                    hierarchy,
                    global_class_table,
                    flatten_class_mapping)
                for arg in arguments
            ]

            # Где-то тут надо провалидировать сигнатуру конструктора
            # и типы аргументов реально переданных

            return TCreateExpr(expr_type, mangled_name, arguments)

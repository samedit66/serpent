from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field

from .abstract_node import *
from serpent.tree.type_decl import ClassType, make_type_decl


class Expr(Node, ABC):
    pass


class ConstantValue(Expr, ABC):
    pass


@dataclass(match_args=True, kw_only=True)
class IntegerConst(ConstantValue):
    value: int


@dataclass(match_args=True, kw_only=True)
class RealConst(ConstantValue):
    value: float


@dataclass(match_args=True, kw_only=True)
class CharacterConst(ConstantValue):
    value: str


@dataclass(match_args=True, kw_only=True)
class StringConst(ConstantValue):
    value: str


@dataclass(match_args=True, kw_only=True)
class BoolConst(ConstantValue):
    value: bool


class VoidConst(ConstantValue):
    pass


@dataclass(match_args=True, kw_only=True)
class ManifestTuple(Expr):
    values: list[Expr]


@dataclass(match_args=True, kw_only=True)
class ManifestArray(Expr):
    values: list[Expr]


class ResultConst(Expr):
    pass


class CurrentConst(Expr):
    pass


@dataclass(match_args=True, kw_only=True)
class FeatureCall(Expr):
    feature_name: str
    arguments: list[Expr] = field(default_factory=list)
    owner: Expr | None = None


@dataclass(match_args=True, kw_only=True)
class PrecursorCall(Expr):
    arguments: list[Expr] = field(default_factory=list)
    ancestor_name: str | None = None


@dataclass(match_args=True, kw_only=True)
class CreateExpr(Expr):
    object_type: ClassType
    constructor_call: FeatureCall | None = None


@dataclass(match_args=True, kw_only=True)
class ElseifExprBranch(Expr):
    condition: Expr
    expr: Expr


@dataclass(match_args=True, kw_only=True)
class IfExpr(Expr):
    condition: Expr
    then_expr: Expr
    else_expr: Expr
    elseif_exprs: list[ElseifExprBranch] = field(default_factory=list)


@dataclass(match_args=True, kw_only=True)
class BracketAccess(Expr):
    indexed_expr: Expr
    indices: list[Expr]


@dataclass(match_args=True, kw_only=True)
class BinaryOp(Expr):
    left: Expr
    right: Expr


class BinaryFeature(BinaryOp, FeatureCall):

    def __init__(
            self,
            location: Location,
            symbol_name: str,
            feature_name: str,
            left: Expr,
            right: Expr) -> None:
        BinaryOp.__init__(self, location=location, left=left, right=right)
        FeatureCall.__init__(
            self,
            location=location,
            feature_name=feature_name,
            arguments=[right],
            owner=left)
        self.symbol_name = symbol_name


@dataclass(match_args=True, kw_only=True)
class UnaryOp(Expr):
    argument: Expr


class UnaryFeature(UnaryOp, FeatureCall):

    def __init__(
            self,
            location: Location,
            symbol_name: str,
            feature_name: str,
            argument: Expr) -> None:
        UnaryOp.__init__(self, location=location, argument=argument)
        FeatureCall.__init__(
            self,
            location=location,
            feature_name=feature_name,
            owner=argument)
        self.symbol_name = symbol_name


class BracketAccess(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "[]", "item", left, right)


class AddOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "+", "plus", left, right)


class SubOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "-", "minus", left, right)


class MulOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "*", "product", left, right)


class DivOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "/", "quotinent", left, right)


class MinusOp(UnaryFeature):

    def __init__(self, *, location: Location, argument: Expr) -> None:
        super().__init__(location, "-", "opposite", argument)


class PlusOp(UnaryFeature):

    def __init__(self, *, location: Location, argument: Expr) -> None:
        super().__init__(location, "+", "identity", argument)


class IntDivOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "//", "integer_qiotient", left, right)


class ModOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "\\\\", "integer_remainder", left, right)


class PowOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "^", "power", left, right)


class LtOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "<", "is_less", left, right)


class GtOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, ">", "is_greater", left, right)


class EqOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "=", "is_equal", left, right)


class NeqOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "/=", "is_not_equal", left, right)


class LeOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, "<=", "is_less_equal", left, right)


class GeOp(BinaryFeature):

    def __init__(self, *, location: Location, left: Expr, right: Expr) -> None:
        super().__init__(location, ">=", "is_greater_equal", left, right)


class AndOp(BinaryOp):
    pass


class OrOp(BinaryOp):
    pass


class NotOp(UnaryOp):
    pass


class AndThenOp(BinaryOp):
    pass


class OrElseOp(BinaryOp):
    pass


class XorOp(BinaryOp):
    pass


class ImpliesOp(BinaryOp):
    pass


def make_expr(expr_dict: dict) -> Expr:
    location = Location(**expr_dict["location"])
    match expr_dict["type"]:
        case "int_const":
            return IntegerConst(
                location=location,
                value=expr_dict["value"],
            )
        case "real_const":
            return RealConst(
                location=location,
                value=expr_dict["value"],
            )
        case "char_const":
            return CharacterConst(
                location=location,
                value=expr_dict["value"]
            )
        case "string_const":
            unescaped = (expr_dict["value"]
                         .encode("raw_unicode_escape")
                         .decode("unicode_escape")
                         )
            return StringConst(
                location=location,
                value=unescaped,
            )
        case "boolean_const":
            return BoolConst(
                location=location,
                value=expr_dict["value"],
            )
        case "result_const":
            return ResultConst(location=location)
        case "current_const":
            return CurrentConst(location=location)
        case "void_const":
            return VoidConst(location=location)
        case "manifest_tuple":
            return make_manifest_tuple(expr_dict)
        case "manifest_array":
            return make_manifest_array(expr_dict)
        case "feature_call":
            return make_feature_call(expr_dict)
        case "precursor_call":
            return make_precursor_call(expr_dict)
        case "bracket_access":
            return make_bracket_access(expr_dict)
        case "if_expr":
            return make_if_expr(expr_dict)
        case "create_expr":
            return make_create_expr(expr_dict)
        case "binop":
            return make_bin_op(expr_dict)
        case "unop":
            return make_unary_op(expr_dict)
        case unknown_type:
            raise UnknownNodeTypeError(
                f"Unknown expression type: {unknown_type}")


def make_manifest_tuple(manifest_tuple_dict: dict) -> ManifestTuple:
    return ManifestTuple(
        location=Location(**manifest_tuple_dict["location"]),
        values=[make_expr(value) for value in manifest_tuple_dict["content"]],
    )


def make_manifest_array(manifest_array_dict: dict) -> ManifestArray:
    return ManifestArray(
        location=Location(**manifest_array_dict["location"]),
        values=[make_expr(value) for value in manifest_array_dict["content"]],
    )


def make_feature_call(feature_call_dict: dict) -> FeatureCall:
    return FeatureCall(
        location=Location(**feature_call_dict["location"]),
        feature_name=feature_call_dict["feature"]["name"],
        arguments=[
            make_expr(arg) for arg in feature_call_dict["feature"]["args_list"]],
        owner=make_expr(
            feature_call_dict["owner"]) if feature_call_dict["owner"] else None,
    )


def make_precursor_call(precursor_call_dict: dict) -> PrecursorCall:
    return PrecursorCall(
        location=Location(**precursor_call_dict["location"]),
        arguments=[make_expr(arg) for arg in precursor_call_dict["args_list"]],
        ancestor_name=precursor_call_dict["parent_name"],
    )


def make_bracket_access(bracket_access_dict: dict) -> BracketAccess:
    return BracketAccess(
        location=Location(**bracket_access_dict["location"]),
        left=make_expr(bracket_access_dict["source"]),
        indices=make_expr(bracket_access_dict["index"]),
    )


def make_if_expr(if_expr_dict: dict) -> IfExpr:
    return IfExpr(
        location=Location(**if_expr_dict["location"]),
        condition=make_expr(if_expr_dict["cond"]),
        then_expr=make_expr(if_expr_dict["then_expr"]),
        else_expr=make_expr(if_expr_dict["else_expr"]),
        elseif_exprs=[
            ElseifExprBranch(
                location=Location(**elseif_expr_dict["location"]),
                condition=make_expr(elseif_expr_dict["cond"]),
                expr=make_expr(elseif_expr_dict["expr"]),
            )
            for elseif_expr_dict in if_expr_dict["elseif_exprs"]
        ]
    )


def make_constructor_call(constructor_call: dict) -> FeatureCall:
    return FeatureCall(
        location=None,
        feature_name=constructor_call["name"],
        arguments=[
            make_expr(arg) for arg in constructor_call["args_list"]],)


def make_create_expr(create_expr_dict: dict) -> CreateExpr:
    return CreateExpr(
        location=Location(
            **create_expr_dict["location"]),
        object_type=make_type_decl(create_expr_dict["object_type"]),
        constructor_call=(
            make_constructor_call(
                create_expr_dict["constructor_call"]) if create_expr_dict["constructor_call"] else None),
    )


def make_bin_op(bin_op_dict: dict) -> BinaryOp:
    bin_type_mapping = {
        "add_op": AddOp,
        "sub_op": SubOp,
        "mul_op": MulOp,
        "div_op": DivOp,
        "int_div_op": IntDivOp,
        "mod_op": ModOp,
        "pow_op": PowOp,
        "and_op": AndOp,
        "or_op": OrOp,
        "and_then_op": AndThenOp,
        "or_else_op": OrElseOp,
        "implies_op": ImpliesOp,
        "xor_op": XorOp,
        "lt_op": LtOp,
        "gt_op": GtOp,
        "le_op": LeOp,
        "ge_op": GeOp,
        "eq_op": EqOp,
        "neq_op": NeqOp,
    }

    node_type = bin_op_dict["binop_type"]
    op_class = bin_type_mapping.get(node_type)
    if op_class is None:
        raise UnknownNodeTypeError(
            f"Unknown binary expression type: {node_type}")

    return op_class(
        location=Location(**bin_op_dict["location"]),
        left=make_expr(bin_op_dict["left"]),
        right=make_expr(bin_op_dict["right"]),
    )


def make_unary_op(unary_op_dict: dict) -> UnaryOp:
    unary_op_mapping = {
        "unary_minus_op": MinusOp,
        "unary_plus_op": PlusOp,
        "not_op": NotOp,
    }

    node_type = unary_op_dict["unop_type"]
    op_class = unary_op_mapping.get(node_type)
    if op_class is None:
        raise UnknownNodeTypeError(
            f"Unknown unary expression type: {node_type}")

    return op_class(
        location=Location(**unary_op_dict["location"]),
        argument=make_expr(unary_op_dict["arg"]),
    )

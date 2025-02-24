from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field

from .abstract_node import *
from .expr import (
    Expr,
    FeatureCall,
    PrecursorCall,
    BracketAccess,
    make_expr,
    make_feature_call,
    make_precursor_call)
from serpent.tree.type_decl import ClassType, make_type_decl


class Statement(Node, ABC):
    pass


@dataclass(match_args=True, kw_only=True)
class Assignment(Statement):
    target: str | Expr
    value: Expr


@dataclass(match_args=True, kw_only=True)
class CreateStmt(Statement):
    constructor_call: ConstructorCall
    object_type: ClassType | None


@dataclass(match_args=True, kw_only=True)
class ConstructorCall(Node):
    object_name: str
    constructor_name: str
    arguments: list[Expr] = field(default_factory=list)


@dataclass(match_args=True, kw_only=True)
class ElseifBranch(Statement):
    condition: Expr
    body: list[Statement]


@dataclass(match_args=True, kw_only=True)
class IfStmt(Statement):
    condition: Expr
    then_branch: list[Statement]
    else_branch: list[Statement]
    elseif_branches: list[ElseifBranch]


@dataclass(match_args=True, kw_only=True)
class LoopStmt(Statement):
    init_stmts: list[Statement]
    until_cond: Expr
    body: list[Statement]


class Choice(Node, ABC):
    pass


@dataclass(match_args=True, kw_only=True)
class ValueChoice(Choice):
    value: Expr


@dataclass(match_args=True, kw_only=True)
class IntervalChoice(Choice):
    start: Expr
    end: Expr


@dataclass(match_args=True, kw_only=True)
class WhenBranch(Statement):
    choices: list[Choice]
    body: list[Statement]


@dataclass(match_args=True, kw_only=True)
class InspectStmt(Statement):
    expr: Expr
    when_branches: list[WhenBranch]
    else_branch: list[Statement]


@dataclass(match_args=True, kw_only=True)
class RoutineCall(Statement):
    feature_call: FeatureCall


@dataclass(kw_only=True)
class PrecursorCallStmt(Statement):
    precursor_call: PrecursorCall


def make_stmt(stmt_dict: dict) -> Statement:
    match stmt_dict["type"]:
        case "assign_stmt":
            return make_assignment_stmt(stmt_dict)
        case "create_stmt":
            return make_create_stmt(stmt_dict)
        case "if_stmt":
            return make_if_stmt(stmt_dict)
        case "loop_stmt":
            return make_loop_stmt(stmt_dict)
        case "inspect_stmt":
            return make_inspect_stmt(stmt_dict)
        case "feature_call":
            return make_call_stmt(stmt_dict)
        case "precursor_call":
            return make_precursor_stmt(stmt_dict)
        case unknown_node_type:
            raise UnknownNodeTypeError(
                f"Unknown statement type: {unknown_node_type}")


def make_create_stmt(create_stmt_dict: dict) -> CreateStmt:
    return CreateStmt(
        location=Location(**create_stmt_dict["location"]),
        constructor_call=make_constructor_call(
            create_stmt_dict["constructor_call"]),
        object_type=(
            make_type_decl(create_stmt_dict["object_type"])
            if create_stmt_dict["object_type"] is not None else None),
    )


def make_constructor_call(constructor_call_dict: dict) -> ConstructorCall:
    constructor_name = (
        "default_create"
        if constructor_call_dict["feature"] is None
        else constructor_call_dict["feature"]["name"]
    )
    args_list = (
        []
        if constructor_call_dict["feature"] is None
        else constructor_call_dict["feature"]["args_list"]
    )
    return ConstructorCall(
        location=Location(**constructor_call_dict["location"]),
        object_name=constructor_call_dict["object"],
        constructor_name=constructor_name,
        arguments=[make_expr(arg) for arg in args_list],
    )


def make_assignment_stmt(assignment_stmt_dict: dict) -> Assignment | RoutineCall:
    left = assignment_stmt_dict["left"]
    assignment = Assignment(
        location=Location(
            **assignment_stmt_dict["location"]),
        target=left["value"] if left["type"] == "ident_lit" else make_expr(left),
        value=make_expr(
            assignment_stmt_dict["right"]),
    )
    
    if isinstance(assignment.target, BracketAccess):
        put_call = FeatureCall(
            location=assignment.location,
            feature_name="put",
            arguments=[assignment.value, assignment.target.right],
            owner=assignment.target.left)
        return RoutineCall(
            location=assignment.location,
            feature_call=put_call)
    
    return assignment


def make_if_stmt(if_stmt_dict: dict) -> IfStmt:
    return IfStmt(
        location=Location(**if_stmt_dict["location"]),
        condition=make_expr(if_stmt_dict["cond"]),
        then_branch=make_stmts(if_stmt_dict["then_clause"]),
        else_branch=make_stmts(if_stmt_dict["else_clause"]),
        elseif_branches=[
            ElseifBranch(
                location=Location(**elseif_branch_dict["location"]),
                condition=make_expr(elseif_branch_dict["cond"]),
                body=make_stmts(elseif_branch_dict["body"]),
            )
            for elseif_branch_dict in if_stmt_dict["elseif_clauses"]
        ],
    )


def make_loop_stmt(loop_stmt_dict: dict) -> LoopStmt:
    return LoopStmt(
        location=Location(**loop_stmt_dict["location"]),
        init_stmts=make_stmts(loop_stmt_dict["init"]),
        until_cond=make_expr(loop_stmt_dict["cond"]),
        body=make_stmts(loop_stmt_dict["body"]),
    )


def make_inspect_stmt(inspect_stmt_dict: dict) -> InspectStmt:
    return InspectStmt(
        location=Location(**inspect_stmt_dict["location"]),
        expr=make_expr(inspect_stmt_dict["expr"]),
        when_branches=[
            WhenBranch(
                location=Location(**when_branch_dict["location"]),
                choices=[
                    make_when_choice(choice_dict)
                    for choice_dict in when_branch_dict["choices"]
                ],
                body=make_stmts(when_branch_dict["body"]),
            )
            for when_branch_dict in inspect_stmt_dict["when_clauses"]
        ],
        else_branch=make_stmts(inspect_stmt_dict["else_clause"]),
    )


def make_when_choice(choice_dict: dict) -> Choice:
    if choice_dict["type"] == "choice_interval":
        return IntervalChoice(
            location=Location(**choice_dict["location"]),
            start=make_expr(choice_dict["start"]),
            end=make_expr(choice_dict["end"]),
        )

    choice_expr = make_expr(choice_dict)
    return ValueChoice(
        location=choice_expr.location,
        value=choice_expr,
    )


def make_call_stmt(call_stmt_dict: dict) -> RoutineCall:
    return RoutineCall(
        location=Location(**call_stmt_dict["location"]),
        feature_call=make_feature_call(call_stmt_dict),
    )


def make_precursor_stmt(precursor_call_stmt: dict) -> PrecursorCallStmt:
    return PrecursorCallStmt(
        location=Location(**precursor_call_stmt["location"]),
        precursor_call=make_precursor_call(precursor_call_stmt),
    )


def make_stmts(stmts: list) -> list[Statement]:
    return [make_stmt(stmt_dict) for stmt_dict in stmts]

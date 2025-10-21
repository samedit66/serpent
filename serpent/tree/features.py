from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field

from .abstract_node import *
from .type_decl import TypeDecl, ClassType, make_type_decl
from .stmts import Statement, Assignment, IfStmt, make_stmt
from .expr import Expr, ResultConst, FeatureCall, make_expr


@dataclass(match_args=True, kw_only=True)
class Feature(Node, ABC):
    name: str
    clients: list[str]


@dataclass(match_args=True, kw_only=True)
class Field(Feature):
    value_type: TypeDecl


@dataclass(match_args=True, kw_only=True)
class Constant(Feature):
    value_type: TypeDecl
    constant_value: Expr


@dataclass(match_args=True, kw_only=True)
class Parameter(Node):
    name: str
    value_type: TypeDecl


@dataclass(match_args=True, kw_only=True)
class LocalVarDecl(Node):
    name: str
    value_type: TypeDecl


@dataclass(match_args=True, kw_only=True)
class Condition(Node):
    condition_expr: Expr
    tag: str | None = None


@dataclass(match_args=True, kw_only=True)
class BaseMethod(Feature, ABC):
    return_type: TypeDecl
    parameters: list[Parameter] = field(default_factory=list)
    require: list[Condition] = field(default_factory=list)
    ensure: list[Condition] = field(default_factory=list)


@dataclass(match_args=True, kw_only=True)
class Method(BaseMethod):
    is_deferred: bool
    is_once: bool
    do: list[Statement] = field(default_factory=list)
    local_var_decls: list[LocalVarDecl] = field(default_factory=list)


@dataclass(match_args=True, kw_only=True)
class ExternalMethod(BaseMethod):
    language: str
    alias: str


def make_feature_list(feature_clauses: list) -> list[Feature]:
    features: list[Feature] = []

    for feature_clause in feature_clauses:
        # По умолчанию, если клиенты не указаны,
        # клиентом считается ANY класс и его наследники
        clients = feature_clause["clients"] or ["ANY"]

        for feature_dict in feature_clause["feature_list"]:
            feature_dicts = separate_declarations(feature_dict)

            for feature_dict in feature_dicts:
                match feature_dict["type"]:
                    case "class_field":
                        features.append(make_field(clients, feature_dict))
                    case "class_constant":
                        features.append(make_constant(clients, feature_dict))
                    case "class_routine":
                        match feature_dict["body"]["type"]:
                            case "routine_body":
                                method = make_method(clients, feature_dict)

                                if method.is_once:
                                    if isinstance(method.return_type, ClassType) and method.return_type.name != "<VOID>":
                                        once_field = Field(
                                            location=None,
                                            name=f"${method.name}",
                                            clients=method.clients,
                                            value_type=method.return_type,
                                        )
                                        features.append(once_field)

                                        once_do = [
                                            IfStmt(
                                                location=None,
                                                condition=FeatureCall(
                                                    location=None,
                                                    feature_name="is_void",
                                                    arguments=[
                                                        FeatureCall(
                                                            location=None,
                                                            feature_name=once_field.name,
                                                        )
                                                    ]
                                                ),
                                                then_branch=[
                                                    *method.do,
                                                    Assignment(
                                                        location=None,
                                                        target=once_field.name,
                                                        value=ResultConst(location=None),
                                                    )
                                                ],
                                                else_branch=[
                                                    Assignment(
                                                        location=None,
                                                        target=ResultConst(location=None),
                                                        value=FeatureCall(
                                                            location=None,
                                                            feature_name=once_field.name,
                                                        )
                                                    )
                                                ]
                                            )
                                        ]

                                        method.do = once_do
                                    elif isinstance(method.return_type, ClassType) and method.return_type.name == "<VOID>":
                                        once_field = Field(
                                            location=None,
                                            name=f"${method.name}",
                                            clients=method.clients,
                                            value_type=ClassType(location=None, name="BOOLEAN"),
                                        )
                                        features.append(once_field)

                                        once_do = [
                                            IfStmt(
                                                location=None,
                                                condition=FeatureCall(
                                                    location=None,
                                                    feature_name=once_field.name,
                                                ),
                                                then_branch=method.do,
                                                else_branch=[]
                                            )
                                        ]

                                        method.do = once_do

                                features.append(method)
                            case "external_routine_body":
                                features.append(
                                    make_external_method(
                                        clients, feature_dict))
                            case unknown_body_type:
                                raise UnknownNodeTypeError(
                                    f"Unknown feature body type: {unknown_body_type}")
                    case unknown_feature_type:
                        raise UnknownNodeTypeError(
                            f"Unknown feature node type: {unknown_feature_type}")

    return features


def make_field(clients: list[str], field_dict: dict) -> Field:
    return Field(
        location=Location(**field_dict["location"]),
        name=field_dict["name_and_type"]["name"],
        clients=clients,
        value_type=make_type_decl(field_dict["name_and_type"]["field_type"]),
    )


def make_constant(clients: list[str], constant_dict: dict) -> Constant:
    return Constant(
        location=Location(**constant_dict["location"]),
        name=constant_dict["name_and_type"]["name"],
        clients=clients,
        value_type=make_type_decl(
            constant_dict["name_and_type"]["field_type"]),
        constant_value=make_expr(
            constant_dict["constant_value"]),
    )


def make_parameters(parameters_list: list) -> list[Parameter]:
    parameters: list[Parameter] = []

    for parameter_dict in parameters_list:
        parameter_dicts = separate_declarations(parameter_dict)

        parameters.extend(
            Parameter(
                location=Location(**parameter_dict["location"]),
                name=parameter_dict["name_and_type"]["name"],
                value_type=make_type_decl(parameter_dict["name_and_type"]["field_type"]),
            )
            for parameter_dict in parameter_dicts
        )

    return parameters


def make_local_var_decls(var_decl_list: list) -> list[LocalVarDecl]:
    var_decls: list[LocalVarDecl] = []

    for var_decl_dict in var_decl_list:
        var_decls_dicts = separate_declarations(var_decl_dict)

        var_decls.extend(
            LocalVarDecl(
                location=Location(**var_decl_dict["location"]),
                name=var_decl_dict["name_and_type"]["name"],
                value_type=make_type_decl(var_decl_dict["name_and_type"]["field_type"]),
            )
            for var_decl_dict in var_decls_dicts
        )

    return var_decls


def make_conditions(condition_list: list) -> list[Condition]:
    conditions = []

    for condition_dict in condition_list:
        condition = Condition(
            location=Location(**condition_dict["location"]),
            condition_expr=make_expr(condition_dict["cond"]),
            tag=condition_dict["tag"],
        )
        conditions.append(condition)

    return conditions


def make_do(method_dict: dict) -> list[Statement]:
    body = method_dict["body"]
    stmts = [make_stmt(stmt_dict) for stmt_dict in body["do"]]

    then = body["then"]
    if then is not None:
        stmts.append(
            Assignment(
                location=Location(**then["location"]),
                target=ResultConst(location=None),
                value=make_expr(then)
            )
        )

    return stmts


def make_method(clients: list[str], method_dict: dict) -> Method:
    is_deferred = method_dict["body"]["routine_type"] == "deferred"
    is_once = method_dict["body"]["routine_type"] == "once"
    return Method(
        location=Location(**method_dict["location"]),
        name=method_dict["name_and_type"]["name"],
        clients=clients,
        is_deferred=is_deferred,
        is_once=is_once,
        return_type=make_type_decl(method_dict["name_and_type"]["field_type"]),
        parameters=make_parameters(method_dict["params"]),
        do=make_do(method_dict),
        local_var_decls=make_local_var_decls(method_dict["body"]["local"]),
        require=make_conditions(method_dict["body"]["require"]),
        ensure=make_conditions(method_dict["body"]["ensure"]),
    )


def make_external_method(
        clients: list[str],
        external_method_dict: dict) -> ExternalMethod:
    return ExternalMethod(
        location=Location(**external_method_dict["location"]),
        name=external_method_dict["name_and_type"]["name"],
        clients=clients,
        language=external_method_dict["body"]["language"],
        return_type=make_type_decl(
            external_method_dict["name_and_type"]["field_type"]),
        parameters=make_parameters(
            external_method_dict["params"]),
        alias=external_method_dict["body"]["alias"],
        require=make_conditions(
            external_method_dict["body"]["require"]),
        ensure=make_conditions(
            external_method_dict["body"]["ensure"]),
    )


def separate_declarations(decl_node_dict: dict) -> list:
    """Используется для разделения деклараций полей, методов, констант
    и параметров, объявленных "вместе":
    Необходимо объявления вида
            a, b: INTEGER;
    перевести в
            a: INTEGER; b: INTEGER;

    Недостаток данного разделения заключается в том, что частично
    теряется информация о месте объявления - сохраняются только номера строк

    :param decl_node_dict: Узел объявления
    :return: Преобразованный, "разделенный", список узлов, также в виде словарей
    """
    separated = []

    location = decl_node_dict["location"]
    name_and_type = decl_node_dict["name_and_type"]
    names = name_and_type["names"]
    for name in names:
        name_and_type_ = {
            "field_type": name_and_type["field_type"],
            "name": name
        }
        decl_node_dict_ = {
            **decl_node_dict,
            "location": location,
            "name_and_type": name_and_type_
        }

        separated.append(decl_node_dict_)

    return separated

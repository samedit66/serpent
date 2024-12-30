from __future__ import annotations
from abc import ABC
from dataclasses import dataclass

from tree.base import (
    IdentifierList,
    UnknownNodeTypeError,
    is_empty_node,
    )
from tree.type_decl import ConcreteType
from tree.statements import StatementList
from tree.expressions import (
    Expression,
    ConstantValue,
    )


class Feature(ABC):
    
    @staticmethod
    def from_dict(feature_dict: dict) -> Feature:
        node_type = feature_dict["type"]
        match node_type:
            case "class_routine":
                return Method.from_dict(feature_dict)
            case "class_field":
                return Field.from_dict(feature_dict)
            case "class_constant":
                return Constant.from_dict(feature_dict)
            case _:
                raise UnknownNodeTypeError(f"Unknown feature type: {node_type}")


@dataclass(match_args=True)
class Field(Feature):
    names_list: IdentifierList
    value_type: ConcreteType

    @classmethod
    def from_dict(cls, class_field: dict) -> Field:
        names_list = class_field["name_and_type"]["names"]
        value_type = ConcreteType.from_dict(class_field["name_and_type"]["field_type"])
        return cls(names_list, value_type)


@dataclass(match_args=True)
class Constant(Feature):
    name: IdentifierList
    constant_type: ConcreteType
    constant_value: ConstantValue

    @classmethod
    def from_dict(cls, class_field: dict) -> Constant:
        names_list = class_field["name_and_type"]["names"]
        value_type = ConcreteType.from_dict(class_field["name_and_type"]["field_type"])
        constant_value = Expression.from_dict(class_field["constant_value"])
        return cls(names_list, value_type, constant_value)


@dataclass(match_args=True)
class Parameter:
    names: IdentifierList
    parameter_type: ConcreteType

    @classmethod
    def from_dict(cls, parameter_dict: dict) -> Parameter:
        names = parameter_dict["names"]
        parameter_type = ConcreteType.from_dict(parameter_dict["field_type"])
        return cls(names, parameter_type)


@dataclass(match_args=True)
class ParameterList:
    parameters: list[Parameter]

    @classmethod
    def from_list(cls, params: list) -> ParameterList:
        parameters = [Parameter.from_dict(param) for param in params]
        return cls(parameters)


type VariableDecl = Field

@dataclass(match_args=True)
class LocalSection:
    variables: list[VariableDecl]

    @classmethod
    def from_list(cls, var_decls: list) -> LocalSection:
        variables = [Field.from_dict(var_decl) for var_decl in var_decls]
        return cls(variables)


@dataclass(match_args=True)
class Condition:
    condition_expr: Expression
    tag: str | None = None

    @classmethod
    def from_dict(cls, cond_dict: dict) -> Condition:
        condition_expr = Expression.from_dict(cond_dict["cond"])
        tag = cond_dict.get("tag")
        return cls(condition_expr, tag)


@dataclass(match_args=True)
class RequireSection:
    conditions: list[Condition]

    @classmethod
    def from_list(cls, cond_list: list) -> RequireSection:
        conditions = [Condition.from_dict(cond) for cond in cond_list]
        return cls(conditions)


@dataclass(match_args=True)
class DoSection:
    body: StatementList

    @classmethod
    def from_list(cls, do_list: list) -> DoSection:
        return StatementList.from_list(do_list)


@dataclass(match_args=True)
class ThenSection:
    result_expr: Expression

    @classmethod
    def from_dict(cls, expr_dict: dict) -> ThenSection:
        return cls(Expression.from_dict(expr_dict))


@dataclass(match_args=True)
class EnsureSection:
    conditions: list[Condition]

    @classmethod
    def from_list(cls, cond_list: list) -> EnsureSection:
        conditions = [Condition.from_dict(cond) for cond in cond_list]
        return cls(conditions)


@dataclass(match_args=True)
class Method(Feature):
    name: IdentifierList
    return_type: ConcreteType
    parameters: ParameterList
    do_section: DoSection
    local_section: LocalSection
    require_section: RequireSection
    ensure_section: EnsureSection
    then_section: ThenSection | None = None

    @classmethod
    def from_dict(cls, class_routine: dict) -> Method:
        names_list = class_routine["name_and_type"]["names"]
        return_type = ConcreteType.from_dict(class_routine["name_and_type"]["field_type"])
        parameters = ParameterList.from_list(class_routine["params"])

        routine_dict = class_routine["body"]

        local_section = LocalSection.from_list(routine_dict["local"])
        require_section = RequireSection.from_list(routine_dict["require"])
        do_section = DoSection.from_list(routine_dict["do"])
        then_section = (
            None if is_empty_node(routine_dict["then"])
            else ThenSection.from_dict(routine_dict["then"])
            )
        ensure_section = EnsureSection.from_list(routine_dict["ensure"])

        return cls(
            name=names_list,
            return_type=return_type,
            parameters=parameters,
            do_section=do_section,
            local_section=local_section,
            require_section=require_section,
            then_section=then_section,
            ensure_section=ensure_section,
            )


@dataclass(match_args=True)
class FeatureList:
    clients: IdentifierList
    features: list[Feature]

    @classmethod
    def from_list(cls, feature_list: list) -> FeatureList:
        clients = feature_list["clients"]
        features = [
            Feature.from_dict(feature_dict)
            for feature_dict in feature_list["feature_list"]
        ]
        return cls(clients, features)

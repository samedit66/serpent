from __future__ import annotations
from dataclasses import dataclass, field

from .abstract_node import *
from .features import Feature, make_feature_list
from .type_decl import ClassType, GenericSpec, make_type_decl


@dataclass(kw_only=True)
class Alias(Node):
    original_name: str
    alias_name: str


@dataclass(kw_only=True)
class SelectedFeatures:
    class_name: str
    selected_features: list[str]


@dataclass(kw_only=True)
class Parent(Node):
    class_name: str
    select: SelectedFeatures
    generics: list[GenericSpec] = field(default_factory=list)
    rename: list[Alias] = field(default_factory=list)
    undefine: list[str] = field(default_factory=list)
    redefine: list[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.class_name)


@dataclass(kw_only=True)
class ClassDecl(Node):
    class_name: str
    is_deferred: bool = True
    generics: list[GenericSpec] = field(default_factory=list)
    inherit: list[Parent] = field(default_factory=list)
    create: list[str] = field(default_factory=list)
    features: list[Feature] = field(default_factory=list)


def make_class_decl(class_decl_dict: dict) -> ClassDecl:
    class_decl = ClassDecl(
        location=Location(**class_decl_dict["location"]),
        class_name=class_decl_dict["header"]["name"],
        is_deferred=class_decl_dict["header"]["is_deferred"],
        generics=[
            make_generic(generic_dict)
            for generic_dict in class_decl_dict["header"]["generics"]
        ],
        inherit=[
            Parent(
                location=Location(**parent_dict["location"]),
                class_name=parent_dict["parent_header"]["name"],
                generics=[
                    make_generic(generic_dict)
                    for generic_dict in parent_dict["parent_header"]["generics"]
                ],
                rename=[
                    Alias(
                        location=Location(**pair_dict["location"]),
                        original_name=pair_dict["original_name"],
                        alias_name=pair_dict["alias_name"],
                    )
                    for pair_dict in parent_dict["rename_clause"]
                ],
                undefine=parent_dict["undefine_clause"],
                redefine=parent_dict["redefine_clause"],
                select=SelectedFeatures(
                    class_name=parent_dict["parent_header"]["name"],
                    selected_features=parent_dict["select_clause"]),
            )
            for parent_dict in class_decl_dict["inheritance"]
        ],
        create=class_decl_dict["creators"],
        features=make_feature_list(class_decl_dict["features"]),
    )

    # В случае, если у класса не было явно указанных родителей,
    # устанавливаем в качестве родителя ANY
    if not class_decl.inherit and class_decl.class_name != "ANY":
        class_decl.inherit = [
            Parent(
                location=None,
                class_name="ANY",
                select=SelectedFeatures(
                    class_name="ANY",
                    selected_features=[]))]

    return class_decl


def make_generic(generic_dict: dict) -> GenericSpec:
    if generic_dict["parent"]:
        required_parent = make_type_decl(generic_dict["parent"])
    else:
        required_parent = ClassType(location=None, name="ANY")

    return GenericSpec(
        location=Location(**generic_dict["location"]),
        template_type_name=generic_dict["generic_type"]["type_name"],
        required_parent=required_parent,
    )

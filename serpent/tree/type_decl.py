from __future__ import annotations
from dataclasses import dataclass, field

from .abstract_node import *


@dataclass
class TypeDecl(Node, ABC): pass


@dataclass(match_args=True, kw_only=True)
class ClassType(TypeDecl):
    name: str
    generics: list[TypeDecl] = field(default_factory=list)


@dataclass(match_args=True, kw_only=True)
class TupleType(TypeDecl):
    generics: list[TypeDecl] = field(default_factory=list)


@dataclass(match_args=True, kw_only=True)
class GenericSpec(Node):
    template_type_name: str
    required_parent: TypeDecl


@dataclass
class LikeCurrent(TypeDecl):
    pass


@dataclass(match_args=True, kw_only=True)
class LikeFeature(TypeDecl):
    feature_name: str


def make_type_decl(type_decl_dict: dict) -> TypeDecl:
    match type_decl_dict["type"]:
        case "type_spec":
            return make_simple_type_decl(type_decl_dict)
        case "type_spec_like":
            return make_like_type_decl(type_decl_dict)
        case "generic_type_spec":
            return make_generic_type_decl(type_decl_dict)
        case unkwnown_type_decl:
            raise UnknownNodeTypeError(
                f"Unknown type declaration: {unkwnown_type_decl}")


def make_simple_type_decl(simple_decl_dict: dict) -> TypeDecl:
    type_name = simple_decl_dict["type_name"]
    location = Location(**simple_decl_dict["location"])
    return ClassType(
        location=location,
        name=type_name,
        generics=[],
    )


def make_like_type_decl(like_decl_dict: dict) -> TypeDecl:
    location = Location(**like_decl_dict["location"])
    like_what_value = like_decl_dict["like_what"]
    match like_what_value["type"]:
        case "current_const":
            return LikeCurrent(location=location)
        case "ident_lit":
            return LikeFeature(
                location=location,
                feature_name=like_what_value["value"],
            )
        case unknown_value:
            raise UnknownNodeTypeError(
                f"Unknown value type of like spec: {unknown_value}")


def make_generic_type_decl(generic_decl_dict: dict) -> TypeDecl:
    location = Location(**generic_decl_dict["location"])
    type_name = generic_decl_dict["type_name"]
    generics = [
        make_type_decl(element_type)
        for element_type in generic_decl_dict["type_list"]
    ]

    if type_name == "TUPLE":
        return TupleType(location=location, name="TUPLE", generics=generics)

    return ClassType(location=location, name=type_name, generics=generics)

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Iterable

from serpent.tree.class_decl import ClassDecl, GenericSpec
from serpent.tree.type_decl import TypeDecl, ClassType, LikeCurrent, LikeFeature
from serpent.tree.features import BaseMethod, Field, Constant, Method, ExternalMethod, Feature, Parameter, LocalVarDecl
from serpent.semantic_checker.analyze_inheritance import FlattenClass, FeatureRecord
from serpent.errors import CompilerError


class ClassHierarchy:

    def __init__(self, classes: Iterable[ClassDecl]) -> None:
        self.hierarchy = {"<VOID>": []}

        for decl in classes:
            parents = [p.class_name for p in decl.inherit]
            self.hierarchy[decl.class_name] = parents

    def __contains__(self, class_name: str) -> bool:
        return class_name in self.hierarchy

    def conforms_to(self, child_name: str, parent_name: str) -> bool:
        if child_name == "NONE":
            return True
        if child_name == parent_name:
            return True

        assert child_name in self.hierarchy
        parents = self.hierarchy[child_name]
        if not parents:
            return False

        return (parent_name in parents
                or any(self.conforms_to(p, parent_name) for p in parents))


@dataclass(frozen=True)
class Type:
    name: str
    generics: list[Type] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.generics)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Type):
            return NotImplemented
        return self.name == other.name and self.generics == other.generics

    def __repr__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        if self.generics:
            generics_str = ",".join(map(str, self.generics))
            return f"{self.name}[{generics_str}]"
        return self.name

    def conforms_to(self, other: Type, hierarchy: ClassHierarchy) -> bool:
        # Специальный случай: тип NONE всегда соответствует
        if self.name == "NONE":
            return True

        # Сначала проверяем, что базовый тип (без учёта дженериков)
        # соответствует
        if not hierarchy.conforms_to(self.name, other.name):
            return False

        # Если родительский тип не указывает дженерики (т.е. является "сырым"),
        # то мы считаем, что соответствие установлено
        if not other.generics:
            return True

        # Если родительский тип указывает дженерики, то их число должно
        # совпадать
        if len(self.generics) != len(other.generics):
            return False

        # Проверяем попарно, что каждый аргумент дженерика дочернего типа соответствует
        # соответствующему аргументу родительского типа
        for child_generic, parent_generic in zip(
                self.generics, other.generics):
            if not child_generic.conforms_to(parent_generic, hierarchy):
                return False

        return True


def type_of_class_decl_type(type_decl: ClassType) -> Type:
    generics = []
    for generic_decl in type_decl.generics:
        if not isinstance(generic_decl, ClassType):
            raise CompilerError(
                "Generic type declarations must be concrete types, not generics",
                generic_decl.location)

        type_of = type_of_class_decl_type(generic_decl)
        if type_of.name == "NONE":
            raise CompilerError(
                f"It is not allowed to annotate objects with type of 'NONE' class",
                generic_decl.location)

        generics.append(type_of_class_decl_type(generic_decl))
    return Type(name=type_decl.name, generics=generics)


@dataclass(frozen=True)
class ClassSymbolTable:
    type_of: Type
    """Тип класса"""

    is_deferred: bool
    """Является ли класс отложенными (абстрактным)"""

    feature_clients_map: dict[str, list[Type]]
    """Отображение имени фичи в список клиентов, которые могут её вызвать"""

    feature_value_type_map: dict[str, Type]
    """Отображение имени фичи в тип ее значения: для полей и констант - их типы,
    для метода - тип возвращаемого значения
    """

    feature_node_map: dict[str, Feature]
    """Отображение имени фичи в соответствующий узел
    абстрактного синтаксического дерева
    """

    constructors: list[str]
    """Список конструкторов, которые есть у данного класса"""

    class_interface: list[str]
    """Интерфейс класса: набор всех фич, которые достались классу
    и каким-либо образом могут быть у него вызвана извне"""

    generic_map: dict[str, Type]
    """Отображение имени шаблонного параметра в конкретный тип
    (если у класса есть дженерики)"""

    feature_signatures_map: dict[str, list[tuple[str, Type]]]
    """Отображение имени фичи в ее сигнатуру"""

    variables: dict[str, list[tuple[str, Type]]]
    """Отображение имени фичи в таблицу локальных переменных фичи"""

    @property
    def full_type_name(self) -> str:
        return self.type_of.full_name

    @property
    def short_type_name(self) -> str:
        return self.type_of.name

    def has_feature(
            self,
            feature_name: str,
            self_called: bool = False) -> bool:
        """Проверяет наличие заданной фичи в классе. Список фич
        отличается в зависимости от того, кому необходимо узнать наличие фичи:
        в случае, если происходит вызов метода без указания объекта, у которого он
        вызывается (случай когда `self_called = True`), поиск производится
        по всем методам, включая прекурсоры и переименованный методы, иначе,
        если `self_called = False`, поиск производится только в интерфейсе класса
        """
        if self_called:
            return feature_name in self.feature_node_map
        return feature_name in self.class_interface

    def can_be_called(
            self,
            feature_name: str,
            hierarchy: ClassHierarchy,
            caller_type: Type | None = None) -> bool:
        """Проверяет, может ли заданная фича быть вызванной у объекта
        с учетом того, какой класс вызывает этот метод
        """
        assert self.has_feature(feature_name) \
            or (caller_type is None and feature_name in self.feature_node_map)
        clients = self.feature_clients_map[feature_name]
        return any(caller_type.conforms_to(client, hierarchy)
                   for client in clients)

    def is_field(self, feature_name: str, self_called: bool = False) -> bool:
        """Проверяет, является ли заданная фича полем класса"""
        assert self.has_feature(feature_name, self_called)
        feature = self.feature_node_map[feature_name]
        return isinstance(feature, Field)

    def is_constant(
            self,
            feature_name: str,
            self_called: bool = False) -> bool:
        """Проверяет, является ли заданная фича константой"""
        assert self.has_feature(feature_name, self_called)
        feature = self.feature_node_map[feature_name]
        return isinstance(feature, Constant)

    def is_method(self, feature_name: str, self_called: bool = False) -> bool:
        """Проверяет, является ли заданная фича методом"""
        assert self.has_feature(feature_name, self_called)
        feature = self.feature_node_map[feature_name]
        return isinstance(feature, BaseMethod)

    def is_constructor(self, feature_name: str) -> bool:
        """Проверяет, является ли заданная фича конструктором"""
        return feature_name in self.constructors

    def type_of_feature(
            self,
            feature_name: str,
            self_called: bool = False) -> Type:
        """Возвращает тип для заданной фичи"""
        assert self.has_feature(feature_name, self_called)
        return self.feature_value_type_map[feature_name]

    def get_feature_signature(
            self, feature_name: str) -> list[tuple[str, Type]]:
        assert feature_name in self.feature_signatures_map
        return self.feature_signatures_map[feature_name]

    def get_feature_node(self, feature_name: str) -> Feature:
        assert feature_name in self.feature_signatures_map
        return self.feature_node_map[feature_name]

    def has_local(self, feature_name: str, local_name: str) -> bool:
        assert self.has_feature(feature_name, self_called=True)
        parameters = self.feature_signatures_map[feature_name]
        variables = self.variables[feature_name]
        return any(local_name == name for name, _ in parameters + variables)

    def type_of_local(self, feature_name: str, local_name: str) -> Type:
        assert self.has_local(feature_name, local_name)
        parameters = self.feature_signatures_map[feature_name]
        variables = self.variables[feature_name]
        all_locals = parameters + variables
        return next(t for (n, t) in all_locals if n == local_name)

    def get_variables(self, feature_name: str) -> Type:
        assert self.has_feature(feature_name, self_called=True)
        return self.variables[feature_name]


def check_generics(actuals, generic, hierarchy) -> None:
    pass


def make_generic_map(
        actuals: list[TypeDecl],
        generics: list[GenericSpec]) -> dict[str, Type]:
    template_names = [
        generic_spec.template_type_name
        for generic_spec in generics]

    actuals = [
        type_of_class_decl_type(actual)
        for actual in actuals]

    generic_map = {
        name: actual
        for name, actual in zip(template_names, actuals)}

    return generic_map


def features_of_flatten_class(
        flatten_cls: FlattenClass) -> tuple[list[FeatureRecord], list[FeatureRecord]]:
    precursors = [
        copy.replace(f, name=f"Precursor_{f.from_class}_{f.name}")
        for f in flatten_cls.precursors
    ]
    inherited = [
        copy.replace(f, name=f"{flatten_cls.class_name}_{f.name}")
        for f in flatten_cls.inherited
    ]
    own = [
        copy.replace(f, name=f"{f.from_class}_{f.name}")
        for f in flatten_cls.own + flatten_cls.constructors
    ]

    explicit = precursors + inherited + own
    implicit = [
        copy.replace(f, name=f"{f.from_class}_{f.name}")
        for f in (
            flatten_cls.renamed
            + flatten_cls.redefined
            + flatten_cls.undefined
            + flatten_cls.selected
            + flatten_cls.inherited)
    ]

    return explicit, implicit


def constructors_of(flatten_cls: FlattenClass) -> list[str]:
    return [f"{f.from_class}_{f.name}" for f in flatten_cls.constructors]


def check_clients_existence(
        feature: FeatureRecord,
        hierarchy: ClassHierarchy) -> None:
    for client in feature.node.clients:
        if client not in hierarchy:
            raise CompilerError(
                f"Client class '{client}' of feature '{
                    feature.name}' does not exist",
                location=feature.location)


def mangle_name(
        feature_name: str,
        class_name: str | None = None,
        is_precursor: bool = False) -> str:
    if class_name is not None:
        base = f"{class_name}_{feature_name}"
        return f"Precursor_{base}_{feature_name}" if is_precursor else base
    return f"local_{feature_name}"


def unmangle_name(
        mangled_name: str,
        is_local: bool = False) -> str:
    if is_local:
        prefix = "local_"
        return mangled_name[len(prefix):]
    precursor_prefix = "Precursor_"
    if mangled_name.startswith(precursor_prefix):
        mangled_name = mangled_name[len(precursor_prefix) + 1:]
    class_index = mangled_name.index("_") + 1
    return mangled_name[class_index:]


def class_name_of_mangled_name(mangled_name: str) -> str:
    precursor_prefix = "Precursor_"
    if mangled_name.startswith(precursor_prefix):
        mangled_name = mangled_name[len(precursor_prefix) + 1:]
    class_index = mangled_name.index("_")
    return mangled_name[:class_index]


def guess_type(
        type_decl: TypeDecl,
        class_decl_type: ClassDecl,
        feature_value_type_map: dict[str, Type],
        hierarchy: ClassHierarchy) -> Type:
    """Определяет тип параметра или локальной переменной"""
    match type_decl:
        case ClassType(location=location, name=name):
            if name not in hierarchy:
                raise CompilerError(
                    f"Unknown type '{name}'",
                    location=location)
            return type_of_class_decl_type(type_decl)
        case LikeCurrent(location=location):
            return type_of_class_decl_type(class_decl_type)
        case LikeFeature(location=location, feature_name=feature_name):
            mangled_name = mangle_name(
                feature_name, class_name=class_decl_type.name)
            if mangled_name not in feature_value_type_map:
                raise CompilerError(f"Unknown feature '{feature_name}'")
            return feature_value_type_map[mangled_name]
        case _: assert False, f"Got unexpected TypeDecl: {type_decl}"


def make_class_symtab(
        actuals: ClassType,
        flatten_cls: FlattenClass,
        hierarchy: ClassHierarchy) -> ClassSymbolTable:
    # Необходимо вставить код проверки корректности дженериков
    # 1. Совпадают по количеству
    # 2. conforms_to
    check_generics(
        actuals.generics,
        flatten_cls.class_decl.generics,
        hierarchy)
    generic_map = make_generic_map(
        actuals.generics, flatten_cls.class_decl.generics)

    # Получаем два списка фич:
    # explicit - фичи, которые доступны для вызова непосредственно
    # у объекта class_type_decl
    # implicit - фичи, которые неявно должны быть у класса,
    # для того чтобы он корректно работал (precursors, renamed, ...)
    explicit, implicit = features_of_flatten_class(flatten_cls)
    constructors = constructors_of(flatten_cls)
    class_interface = [feature.name for feature in explicit]
    feature_clients_map = {}
    feature_value_type_map = {}
    feature_node_map = {}
    class_type = type_of_class_decl_type(actuals)

    like_anchored = []
    for feature in explicit + implicit:
        assert feature.name not in feature_node_map, f"Feature '{
            feature.name}' already in"

        if isinstance(feature.node, (Field, Constant)):
            type_decl = feature.node.value_type
        elif isinstance(feature.node, BaseMethod):
            type_decl = feature.node.return_type
        else:
            assert False, f"Got unexpected Feature: {feature_node}"

        if isinstance(type_decl, ClassType):
            if type_decl.name in generic_map:
                type_of = generic_map[type_decl.name]
                feature_value_type_map[feature.name] = type_of
            elif type_decl.name in hierarchy:
                type_of = type_of_class_decl_type(type_decl)
                feature_value_type_map[feature.name] = type_of
            else:
                raise CompilerError(f"Unknown type '{type_decl.name}'",
                                    location=type_decl.location)
        elif isinstance(type_decl, LikeCurrent):
            type_of = type_of_class_decl_type(actuals)
            feature_value_type_map[feature.name] = type_of
        elif isinstance(type_decl, LikeFeature):
            like_anchored.append(
                (mangle_name(
                    type_decl.feature_name,
                    class_name=actuals.name),
                    feature))
            continue
        else:
            assert False, f"Got unexpected TypeDecl: {type_decl}"

        check_clients_existence(feature, hierarchy)
        feature_clients_map[feature.name] = [
            Type(class_name)
            for class_name in feature.node.clients]

        feature_node_map[feature.name] = feature.node

    not_found = 0
    while like_anchored:
        like_feature_name, feature = like_anchored.pop(0)

        if like_feature_name in feature_value_type_map:
            check_clients_existence(feature, hierarchy)

            feature_type = feature_value_type_map[like_feature_name]
            feature_value_type_map[feature.name] = feature_type
            feature_clients_map[feature.name] = feature.node.clients
            feature_node_map[feature.name] = feature.node

            not_found = 0
            continue

        like_anchored.append((like_feature_name, feature))
        not_found += 1
        if not_found == len(like_anchored):
            locations_info = ", ".join(
                f"'{like_feature_name}' in {f.location}"
                for like_feature_name, f in like_anchored
            )
            ending = "s" if not_found > 1 else ""
            raise CompilerError(
                f"Anchored to features that do not exist or are mutually recursive. See feature{ending}: {locations_info}")

    signatures = {}
    for feature_name, feature_node in feature_node_map.items():
        if isinstance(feature_node, (Field, Constant)):
            parameters = []
        elif isinstance(feature_node, BaseMethod):
            parameters = feature_node.parameters
        else:
            assert False, f"Got unexpected Feature: {feature_node}"

        typed_parameters = []
        for param in parameters:
            possible_feature_name = mangle_name(
                param.name, class_name=actuals.name)
            if possible_feature_name in feature_node_map:
                raise CompilerError(
                    f"Parameter '{
                        var_decl.name}' conflits with feature '{
                        var_decl.name}' of class '{
                        class_type.full_name}', consider different name")

            param_name = mangle_name(param.name)
            param_type = guess_type(
                param.value_type,
                actuals,
                feature_value_type_map,
                hierarchy)
            typed_parameters.append((param_name, param_type))

        signatures[feature_name] = typed_parameters

    local_variables = {}
    for feature_name, feature_node in feature_node_map.items():
        if isinstance(feature_node, (Field, Constant, ExternalMethod)):
            continue
        assert isinstance(
            feature_node, Method), "Expected 'feature_node' to be Method"

        typed_variables = []
        for var_decl in feature_node.local_var_decls:
            possible_feature_name = mangle_name(
                var_decl.name, class_name=actuals.name)
            if possible_feature_name in feature_node_map:
                raise CompilerError(
                    f"Variable '{
                        var_decl.name}' conflits with feature '{
                        var_decl.name}' of class '{
                        class_type.full_name}', consider different name")

            var_name = mangle_name(var_decl.name)
            var_type = guess_type(
                var_decl.value_type,
                actuals,
                feature_value_type_map,
                hierarchy)
            typed_variables.append((var_name, var_type))

        feature_return_type = feature_value_type_map[feature_name]
        if feature_return_type.full_name != "<VOID>":
            typed_variables.append(
                (mangle_name("Result"), feature_return_type))

        local_variables[feature_name] = typed_variables

    return ClassSymbolTable(
        type_of=class_type,
        is_deferred=flatten_cls.class_decl.is_deferred,
        feature_clients_map=feature_clients_map,
        feature_value_type_map=feature_value_type_map,
        feature_node_map=feature_node_map,
        constructors=constructors,
        class_interface=class_interface,
        generic_map=generic_map,
        feature_signatures_map=signatures,
        variables=local_variables)


class GlobalClassTable:

    def __init__(self) -> None:
        self.classes = []

    def add_class_table(self, class_symtab: ClassSymbolTable) -> None:
        assert not self.has_class_table(class_symtab.type_of.full_name)
        self.classes.append(class_symtab)

    def has_class_table(self, full_name: str) -> bool:
        return any(c.type_of.full_name == full_name for c in self.classes)

    def get_class_table(self, full_name: str) -> ClassSymbolTable:
        assert self.has_class_table(full_name)
        return next(
            c for c in self.classes if c.type_of.full_name == full_name)

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Iterable

from serpent.tree.class_decl import ClassDecl, GenericSpec
from serpent.tree.type_decl import TypeDecl, ClassType, LikeCurrent, LikeFeature
from serpent.tree.features import BaseMethod, Field, Constant, Method, Feature
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

        assert child_name in self.hierarchy
        parents = self.hierarchy[child_name]
        if not parents:
            return False

        return (parent_name in parents
                or any(self.conforms_to(child_name, p) for p in parents))


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
        if self.generics:
            generics_str = ",".join(map(str, self.generics))
            return f"{self.name}[{generics_str}]"
        return self.name

    def full_name(self) -> str:
        return repr(self)

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

    def has_feature(self, feature_name: str, self_called: bool = False) -> bool:
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

    def can_be_called(self, feature_name: str, caller_type: Type | None = None) -> bool:
        """Проверяет, может ли заданная фича быть вызванной у объекта
        с учетом того, какой класс вызывает этот метод
        """
        assert self.has_feature(feature_name) \
            or (caller_type is None and feature_name in self.feature_node_map)
        clients = self.feature_clients_map[feature_name]
        return any(caller_type.conforms_to(client) for client in clients)

    def is_field(self, feature_name: str, self_called: bool = False) -> bool:
        """Проверяет, является ли заданная фича полем класса"""
        assert self.has_feature(feature_name, self_called)
        feature = self.feature_node_map[feature_name]
        return isinstance(feature, Field)

    def is_constant(self, feature_name: str, self_called: bool = False) -> bool:
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

    def mangle_name(self, name: str) -> str:
        """Выполняет манглирование имени с учетом имени класса"""
        return f"{self.type_of.name}_{name}"

    def type_of_feature(self, feature_name: str, self_called: bool = False) -> Type:
        """Возвращает тип для заданной фичи"""
        assert self.has_feature(feature_name, self_called)
        return self.feature_value_type_map[feature_name]
    
    def add_feature_signature(self, feature_name: str, parameters: list[tuple[str, Type]]) -> None:
        assert not self.has_feature(feature_name)
        self.feature_signatures_map[feature_name] = parameters


def check_generics(actuals, generic, hierarchy) -> None:
    ...


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
        feature
        for feature in (
            flatten_cls.renamed
            + flatten_cls.redefined
            + flatten_cls.undefined
            + flatten_cls.selected)
    ]

    return explicit, implicit


def check_clients_existence(feature: FeatureRecord, hierarchy: ClassHierarchy) -> None:
    for client in feature.node.clients:
        if client not in hierarchy:
            raise CompilerError(
                    f"Client class '{client}' of feature '{feature.name}' does not exist",
                    location=feature.location)


def make_class_symtab(
        class_type_decl: ClassType,
        flatten_cls: FlattenClass,
        hierarchy: ClassHierarchy) -> ClassSymbolTable:
    # Необходимо вставить код проверки корректности дженериков
    # 1. Совпадают по количеству
    # 2. conforms_to
    generic_map = make_generic_map(
        class_type_decl.generics, flatten_cls.class_decl.generics)
    
    # Получаем два списка фич:
    # explicit - фичи, которые доступны для вызова непосредственно
    # у объекта class_type_decl
    # implicit - фичи, которые неявно должны быть у класса,
    # для того чтобы он корректно работал (precursors, renamed, ...)
    explicit, implicit = features_of_flatten_class(flatten_cls)

    class_interface = [feature.name for feature in explicit]
    feature_clients_map = {}
    feature_value_type_map = {}
    feature_node_map = {}
    class_type = type_of_class_decl_type(class_type_decl)
    constructors = [feature.name for feature in flatten_cls.constructors]

    like_anchored = []
    for feature in explicit + implicit:
        assert feature.name not in feature_node_map

        if isinstance(feature.node, (Field, Constant)):
            type_decl = feature.node.value_type
        elif isinstance(feature.node, BaseMethod):
            type_decl = feature.node.return_type
        else: assert False

        if isinstance(type_decl, ClassType):
            if type_decl.name in generic_map:
                feature_value_type_map[feature.name] = generic_map[type_decl.name]
            elif type_decl.name in hierarchy:
                feature_value_type_map[feature.name] = type_of_class_decl_type(type_decl)
            else: raise CompilerError(
                f"Unknown type '{type_decl.name}'", location=type_decl.location)
        elif isinstance(type_decl, LikeCurrent):
            feature_value_type_map[feature.name] = type_of_class_decl_type(class_type_decl)
        elif isinstance(type_decl, LikeFeature):
            mangled = f"{flatten_cls.class_name}_{type_decl.feature_name}"
            like_anchored.append((mangled, feature))
            continue
        else: assert False

        check_clients_existence(feature, hierarchy)
        feature_clients_map[feature.name] = [
            Type(class_name)
            for class_name in feature.node.clients]

        feature_node_map[feature.name] = feature.node

    not_found = 0
    while like_anchored:
        like_feature_name, feature = like_anchored.pop(0)

        if like_feature_name in feature_value_type_map:
            feature_type = feature_value_type_map[like_feature_name]
            feature_value_type_map[feature.name] = feature_type

            check_clients_existence(feature, hierarchy)
            feature_clients_map[feature.name] = feature.node.clients

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
    
    return ClassSymbolTable(
        type_of=class_type,
        is_deferred=flatten_cls.class_decl.is_deferred,
        feature_clients_map=feature_clients_map,
        feature_value_type_map=feature_value_type_map,
        feature_node_map=feature_node_map,
        constructors=constructors,
        class_interface=class_interface,
        generic_map=generic_map,
        feature_signatures_map={})


@dataclass(frozen=True)
class LocalSymbolTable:
    method_name: str
    parameters: list[tuple[str, Type]]
    variables: list[tuple[str, Type]]
    all_locals: dict[str, Type]
    class_symtab: ClassSymbolTable

    def has_local(self, local_name: str) -> bool:
        return local_name in self.variables or local_name in self.parameters

    def type_of(self, local_name: str) -> bool:
        assert self.has_local(local_name)
        return self.all_locals[local_name]
        
    def mangle_name(self, name: str) -> str:
        return f"local_{name}"


def make_local_symtab(
        method_name: str,
        method: BaseMethod,
        class_symtab: ClassSymbolTable,
        hierarchy: ClassHierarchy) -> LocalSymbolTable:
    
    def bindings_of(parameters_or_locals, local_type_name: str):
        bindings = []

        for param in parameters_or_locals:
            name = param.name
            param_type_decl = param.value_type

            mangled_name = class_symtab.mangle_name(name)
            if class_symtab.has_feature(mangled_name):
                raise CompilerError(
                    f"{local_type_name.capitalize()} '{name}' conflicts with feature '{name}' of class '{class_symtab.type_of.name}'",
                    location=method.location)

            mangled_name = f"local_{name}"
            if any(b[0] == mangled_name for b in bindings):
                raise CompilerError(
                    f"{local_type_name.capitalize()} '{name} already defined"
                )

            if isinstance(param_type_decl, ClassType):
                type_name = param_type_decl.name
                if type_name in class_symtab.generic_map:
                    param_type = class_symtab.generic_map[type_name]
                elif type_name in hierarchy:
                    param_type = type_of_class_decl_type(param_type_decl)
                else: raise CompilerError(
                    f"Unknown type '{type_name}'",
                    location=param_type_decl.location)
            elif isinstance(param_type_decl, LikeCurrent):
                param_type = class_symtab.type_of
            elif isinstance(param_type_decl, LikeFeature):
                feature_name = param_type_decl.feature_name

                feature_type = next(
                    (t for (n, t) in bindings if n == feature_name), None)
                if feature_type is None:
                    mangled_name = class_symtab.mangle_name(feature_name)
                    if not class_symtab.has_feature(mangled_name):
                        raise CompilerError(
                            f"{local_type_name.capitalize()} '{name}' uses 'like' for unknown feature '{feature_name}' in '{class_symtab.type_of.name}'",
                            location=method.location)

                    feature_type = class_symtab.type_of_feature(mangled_name)

                param_type = feature_type
            else: assert False

            bindings.append((mangled_name, param_type))
        
        return bindings
        
    parameters = bindings_of(method.parameters, "parameter")
    if not isinstance(method, Method):
        return LocalSymbolTable(
            method_name, parameters, [], dict(parameters), class_symtab)

    variables = bindings_of(method.local_var_decls, "variable")
    assert isinstance(method.return_type, ClassType)
    if method.return_type.name != "<VOID>":
        result_type = class_symtab.type_of_feature(
            class_symtab.mangle_name(method_name))
        variables.append(("local_Result", result_type))

    return LocalSymbolTable(
        method_name, parameters, variables, dict(parameters + variables), class_symtab)


class GlobalClassTable:
    
    def __init__(self) -> None:
        self.classes = []

    def add_class_table(self, class_symtab: ClassSymbolTable) -> None:
        self.classes.append(class_symtab)

    def has_class_table(self, full_name: str) -> bool:
        return any(c.type_of.full_name == full_name for c in self.classes)

    def get_class_table(self, full_name: str) -> ClassSymbolTable:
        assert self.has_class_table(full_name)
        return next(c for c in self.classes if c.full_name == full_name)

from __future__ import annotations
import copy
from collections import defaultdict
from dataclasses import dataclass

from ..tree import (
    ClassDecl,
    Parent,
    Feature,
    SelectedFeatures,
    Constant,
    Field,
    BaseMethod,
    Method,
    ClassType)
from ..tree.abstract_node import Location
from ..errors import CompilerError, ErrorCollector


@dataclass
class FeatureRecord:
    class_decl: str
    name: str
    node: Feature

    @property
    def from_class(self) -> str:
        return self.class_decl.class_name

    @property
    def location(self) -> Location:
        return self.node.location

    def __eq__(self, other: FeatureRecord) -> bool:
        return self.from_class == other.from_class and self.name == other.name


@dataclass
class FlattenClass:
    class_decl: ClassDecl
    renamed: list[FeatureRecord]
    undefined: list[FeatureRecord]
    redefined: list[FeatureRecord]
    precursors: list[FeatureRecord]
    selected: list[FeatureRecord]
    inherited: list[FeatureRecord]
    own: list[FeatureRecord]
    constructors: list[FeatureRecord]

    @property
    def class_name(self) -> str:
        return self.class_decl.class_name

    @property
    def explicit_features(self):
        return self.own + self.inherited + self.constructors


def check_rename_clause(
        parent: Parent,
        parent_features: list[FeatureRecord],
        own_child_features: list[FeatureRecord]) -> None:
    """Проверят, можно ли выполнить переименования фич, опираясь
    на имена фич для переименования, заданные родительские фичи и
    заданные фичи ребенка. Ошибочные ситуации возникают если:
    1) В правилах дублируются имена оригинальных фич;
    2) В правилах дублируются имена для переименования
    3) Указанные фичи не существуют в родители;
    4) У дочернего класса уже есть фича с именем для переименования.
    """
    rename_clause = parent.rename
    if not rename_clause:
        return

    # Проверка на наличие дублированных фич родителя
    seen = set()
    for rule in rename_clause:
        if rule.original_name in seen:
            raise CompilerError(
                f"Duplicate feature in rename clause: {
                    rule.original_name}",
                rule.location)
        seen.add(rule.original_name)

    # Проверка на наличие одних и тех же псевдонимов
    seen = set()
    for rule in rename_clause:
        if rule.alias_name in seen:
            raise CompilerError(
                f"Duplicate alias name: {
                    rule.alias_name}",
                rule.location)
        seen.add(rule.alias_name)

    # Проверка на наличие несуществующих фич родителя
    for rule in rename_clause:
        if not any(rule.original_name ==
                   feature.name for feature in parent_features):
            raise CompilerError(
                f"Nonexistent parent feature in rename clause: {
                    rule.original_name}",
                rule.location)

    # Проверка на то, что в дочернем классе нет фич с именем псевдонима
    for rule in rename_clause:
        if any(rule.alias_name == feature.name for feature in own_child_features):
            # Возможно, в сообщение также нужно добавить позицию
            # той фичи, которая конфликует с rule.alias_name
            raise CompilerError(
                f"Child class already has a feature called: \
                {rule.alias_name}", rule.location)


def rename(
        parent: Parent,
        parent_features: list[FeatureRecord]):
    rename_clause = parent.rename
    if not rename_clause:
        return [], parent_features

    inherired = []
    renamed = []

    for pf in parent_features:
        rule = next(
            (r for r in rename_clause if r.original_name == pf.name),
            None)

        if rule is None:
            inherired.append(pf)
            continue

        inherired.append(copy.replace(pf, name=rule.alias_name))
        renamed.append(pf)

    return renamed, inherired


def check_redefine_clause(
        parent: Parent,
        parent_features: list[FeatureRecord],
        own_child_features: list[FeatureRecord]) -> None:
    """Проверят, можно ли выполнить переопределение фич, опираясь
    на имена фич для переопределения, заданные родительские фичи и
    заданные фичи ребенка. Ошибочные ситуации возникают если:
    1) В списке дублируются имена фич;
    2) Указанные фичи не существуют в родители;
    3) Дочерний класс не переопределяет фичу;
    4) Попытка переопределить константу.
    """
    redefine_clause = parent.redefine
    if not redefine_clause:
        return

    # Проверка на дублирование фич в списке переопределяемых
    seen = set()
    for feature_name in redefine_clause:
        if feature_name in seen:
            raise CompilerError(
                f"Duplicate feature in redefine clause: '{feature_name}'",
                parent.location)
        seen.add(feature_name)

    # Проверка на наличие фич в родительском классе
    for feature_name in redefine_clause:
        if not any(feature_name == pf.name for pf in parent_features):
            raise CompilerError(
                f"Nonexistent parent feature in redefine clause: '{feature_name}'",
                parent.location)

    # Проверка, что дочерний класс действительно переопределяет фичу
    for feature_name in redefine_clause:
        if not any(feature_name == cf.name for cf in own_child_features):
            raise CompilerError(
                f"Child class does not redefine a feature: '{feature_name}'",
                parent.location)

    # Проверка, что не происходит попытка переопределить константу
    for feature_name in redefine_clause:
        parent_feature = next(
            pf.node for pf in parent_features if pf.name == feature_name)
        if isinstance(parent_feature, Constant):
            raise CompilerError(
                f"Redefinition of constant '{feature_name}' is not allowed",
                parent.location)
        elif isinstance(parent_feature, Method) and parent_feature.is_deferred:
            raise CompilerError(
                f"Cannot redefine feature '{
                    parent_feature.name}' of class '{
                    parent.class_name}' that is not yet defined. \
If you're trying to define it, just remove it from redefine clause",
                parent.location)


def redefine(
        parent: Parent,
        parent_features: list[FeatureRecord],
        own_child_features: list[FeatureRecord]):
    redefine_clause = parent.redefine
    if not redefine_clause:
        return [], [], parent_features

    inherited = []
    redefined = []
    precursors = []

    for pf in parent_features:
        if pf.name not in redefine_clause:
            inherited.append(pf)
            continue

        child_node = next(
            f.node for f in own_child_features if f.name == pf.name)
        redefined.append(copy.replace(pf, node=child_node))
        precursors.append(pf)

    return precursors, redefined, inherited


def check_undefine_clause(
        parent: Parent,
        parent_features: list[FeatureRecord],
        own_child_features: list[FeatureRecord]) -> None:
    """Проверят, можно ли выполнить undefine фич, опираясь
    на имена фич для undefine, заданные родительские фичи и
    заданные фичи ребенка. Ошибочные ситуации возникают если:
    1) В списке дублируются имена фич;
    2) Указанные фичи не существуют в родители;
    3) Дочерний класс уже имеет фичу с таким именем;
    4) Попытка сделать undefine константы.
    """
    undefine_clause = parent.undefine
    if not undefine_clause:
        return

    # Проверка на дублирование фич в undefine
    seen = set()
    for feature_name in undefine_clause:
        if feature_name in seen:
            raise CompilerError(
                f"Duplicate feature in undefine clause: {feature_name}",
                parent.location)
        seen.add(feature_name)

    # Проверка на существование фич, которые будут сделаны отложенными
    for feature_name in undefine_clause:
        if not any(feature_name == pf.name for pf in parent_features):
            raise CompilerError(
                f"Nonexistent parent feature in undefine clause: {feature_name}",
                parent.location)

    # Дочерний класс не может делать undefine какой-либо
    # родительской фичи и определять её - для этого необходимо
    # воспользоваться redefine
    for feature_name in undefine_clause:
        if any(feature_name == cf.name for cf in own_child_features):
            raise CompilerError(
                f"Child class already redefines feature: {feature_name}. \
Cannot undefine it. Consider moving it to redefine clause", parent.location)

    # Проверка, что не происходит попытка переопределить константу
    for feature_name in undefine_clause:
        parent_feature = next(
            pf for pf in parent_features if pf.name == feature_name).node

        if isinstance(parent_feature, Constant):
            raise CompilerError(
                f"Undefine of constant '{feature_name}' is not allowed",
                parent.location)
        elif isinstance(parent_feature, Method) and parent_feature.is_deferred:
            raise CompilerError(
                f"Cannot undefine feature '{feature_name}' twice -- it's already deferred in parent class",
                parent.location)


def undefine(
        parent: Parent,
        parent_features: list[FeatureRecord]):
    """Выполняет undefine родительских фич: фичи с заданными именами
    становятся отложенными
    """
    undefine_clause = parent.undefine
    if not undefine_clause:
        return parent_features

    inherited = []
    for pf in parent_features:
        if pf.name not in undefine_clause:
            inherited.append(pf)
            continue

        node = pf.node
        if isinstance(node, Field):
            node = Method(
                location=node.location,
                name=node.name,
                clients=node.clients,
                is_deferred=True,
                return_type=node.value_type,
            )
        elif isinstance(node, Method):
            node = copy.replace(node, is_deferred=True)

        inherited.append(copy.replace(pf, node=node))

    return inherited


def check_select_clause(
        select_clauses: dict[Parent, SelectedFeatures],
        parent_to_features: dict[str, list[FeatureRecord]],
        own_child_features: list[FeatureRecord]) -> None:
    if not any(
            select_clause.selected_features for select_clause in select_clauses.values()):
        return

    # Проверка отсутствия дубликатов во всех select clauses
    grouped_by_name = defaultdict(list)
    for parent, select_clause in select_clauses.items():
        for feature_name in select_clause.selected_features:
            grouped_by_name[feature_name].append(parent)
    for feature_name, parents in grouped_by_name.items():
        if len(parents) > 1:
            locations_info = ", ".join(str(p.location) for p in parents[1:])
            raise CompilerError(
                f"Duplicate feature '{feature_name}' in select clause, \
                    see also {locations_info}",
                location=parents[0].location)

    # Проверка, что фичи, указанные в select, действительно существуют
    for parent, select_clause in select_clauses.items():
        parent_features = parent_to_features[parent]

        nonexistent_features = [
            feature_name
            for feature_name in select_clause.selected_features
            if not any(feature_name == pf.name for pf in parent_features)]
        if nonexistent_features:
            ending = "" if len(nonexistent_features) == 1 else "s"
            raise CompilerError(
                f"Nonexistent parent feature{ending} in select clause: {
                    ", ".join(nonexistent_features)}",
                location=parent.location)

    # Проверка, что фича действительно определена в нескольких классах
    for feature_name in grouped_by_name:
        parents_with_feature = [
            parent.class_name
            for parent, features in parent_to_features.items()
            if any(feature_name == pf.name for pf in features)]

        if len(parents_with_feature) < 1:
            # Берем первого родителя, у которого такая фича есть
            parent = grouped_by_name[feature_name][0]
            raise CompilerError(
                f"Feature '{feature_name}' is not ambiguous; select clause is not required",
                location=parent.location)

    # Проверка, что фичи, указанные в select, не определены в ребенке
    already_defined_in_child = [
        cf
        for cf in own_child_features
        if cf.name in grouped_by_name
    ]
    if already_defined_in_child:
        # Для упрощения берем первую фичу, которая уже определена
        # в ребенке, и секцию наследования, где эта фича
        # упоминается в select clause
        feature = already_defined_in_child[0]
        parent = grouped_by_name[feature.name][0]
        raise CompilerError(
            f"Feature '{feature.name}' already defined in child class",
            location=parent.location)

    # TODO: По-хорошему, здесь же должна идти проверка, что выбранные фичи
    # действительно определены где-то в общем предке, но
    # чтобы не усложнять компилятор и данную функцию, этого здесь не
    # будет... Однако, это не повод переживать, т.к. программа все равно не
    # скомпилируется - сломается на этапе проверки типов


def select(
    select_clauses: list[SelectedFeatures],
    parent_to_features: dict[Parent, list[FeatureRecord]]
) -> tuple[dict[Parent, list[FeatureRecord]], list[FeatureRecord]]:
    if not any(clause.selected_features for clause in select_clauses):
        return parent_to_features, []

    select_map = {
        feature: clause.class_name
        for clause in select_clauses
        for feature in clause.selected_features
    }

    all_features = [pf for features in parent_to_features.values()
                    for pf in features]

    candidate_map = {
        feature: next(
            pf for pf in all_features
            if pf.name == feature and pf.from_class == desired_class
        )
        for feature, desired_class in select_map.items()
    }

    new_parent_to_features = {}
    selected_features = []
    for parent, features in parent_to_features.items():
        updated_features = []
        for pf in features:
            if pf.name in candidate_map:
                feature = candidate_map[pf.name]

                if pf.from_class == feature.from_class:
                    updated_features.append(pf)
                    continue

                new_pf = copy.replace(pf, node=feature.node)
                selected_features.append(new_pf)
            else:
                updated_features.append(pf)
        new_parent_to_features[parent] = updated_features

    return new_parent_to_features, selected_features


def check_create_clause(
        class_decl: ClassDecl,
        own_child_features: list[FeatureRecord]) -> None:
    create_clause = class_decl.create
    for feature_name in create_clause:
        # Проверка, что имя указанного конструктора действительно есть
        # среди определенных фич
        candidate = next(
            (cf for cf in own_child_features if cf.name == feature_name), None)
        if candidate is None:
            raise CompilerError(
                f"Creation procedure '{feature_name}' is not defined in the class '{
                    class_decl.class_name}'", class_decl.location)

        # Проверка, что найденная фича является методом
        if not isinstance(candidate.node, BaseMethod):
            raise CompilerError(
                f"Feature '{feature_name}' is not a method and cannot be a creation procedure in the class '{
                    class_decl.class_name}'", class_decl.location)

        # Проверка, что конструктор - фича, которая ничего не возвращает
        method = candidate.node
        if not (isinstance(method.return_type, ClassType)
                and method.return_type.name == "<VOID>"):
            raise CompilerError(
                f"Creation feature '{feature_name}' must be a procedure in the class '{
                    class_decl.class_name}'", class_decl.location)


def check_duplicate_features(features: list[FeatureRecord]) -> None:
    grouped_by_name = defaultdict(list)
    for feature in features:
        grouped_by_name[feature.name].append(feature)

    for feature_name, group in grouped_by_name.items():
        if len(group) > 1:
            feature = group[0]
            raise CompilerError(f"Duplicate feature '{feature_name}' in \
                                class '{feature.from_class}'", feature.location)


def merge(features: list[FeatureRecord],
          class_decl: ClassDecl) -> list[FeatureRecord]:
    grouped_by_name = defaultdict(list)
    for feature in features:
        grouped_by_name[feature.name].append(feature)

    inherited = []
    undefined = []
    for feature_name, features in grouped_by_name.items():
        effective = [
            feature
            for feature in features
            if not isinstance(feature.node, Method)
            or not feature.node.is_deferred
        ]

        deferred = [
            feature
            for feature in features
            if isinstance(feature.node, Method)
            and feature.node.is_deferred
        ]

        if len(effective) == 1:
            effective_feature = effective[0]

            # Если фича пришла из дочернего класса,
            # то мы не можем добавить ее в inherited -
            # иначе случится конфликт, когда мы будем объединять
            # inherited фичи и own фичи
            if effective_feature.from_class != class_decl.class_name:
                inherited.append(effective_feature)

            if len(deferred) > 0:
                undefined.extend(
                    copy.replace(feature, node=effective_feature.node)
                    for feature in deferred)
            continue

        if len(effective) == 0 and len(deferred) > 0:
            # Такая же проблема как и сверху, но -
            # данное решение чисто костыль и заплатка... Нет никакой гарантиии в том,
            # что это верный способ реализации
            non_own_features = [f for f in deferred if f.from_class != class_decl.class_name]
            if not non_own_features:
                continue

            inherited.append(non_own_features[0])
            undefined.extend(non_own_features[1:])
            continue

        assert len(effective) > 1

        locations_info = ", ".join(str(f.location) for f in features)
        raise CompilerError(
            f"Class '{
                class_decl.class_name}' got feature '{feature_name}' 2 or more times, see also {locations_info}",
            location=class_decl.location)

    return inherited, undefined


def remove_duplicates(features: list[FeatureRecord]) -> list[FeatureRecord]:
    seen = set()
    unique_features = []
    for feature in features:
        key = (feature.from_class, feature.name)
        if key not in seen:
            seen.add(key)
            unique_features.append(feature)
    return unique_features


def check_if_all_defined(
        features: list[FeatureRecord],
        class_decl: ClassDecl) -> None:
    deferred_features = [
        feature.node
        for feature in features
        if isinstance(feature.node, Method) and feature.node.is_deferred]

    if deferred_features and not class_decl.is_deferred:
        info_about_deferred_features = ', '.join([
            f"'{feature.name}' in {feature.location}"
            for feature in deferred_features])
        ending = "" if len(deferred_features) == 1 else "s"

        raise CompilerError(
            f"Class '{class_decl.class_name}' is not deferred but \
contains deferred feature{ending}: {info_about_deferred_features}",
            class_decl.location)


def split_create_features(
        all_features: list[FeatureRecord],
        constructors_names: list[str]):
    constructors = []
    features = []

    for feature in all_features:
        if feature.name in constructors_names:
            constructors.append(feature)
        else:
            features.append(feature)

    return constructors, features


def adapt(class_decl: ClassDecl,
          class_mapping: dict[str, ClassDecl]):
    own_child_features = [
        FeatureRecord(
            class_decl=class_decl,
            name=feature.name,
            node=feature)
        for feature in class_decl.features
    ]

    # 0 этап. Проверяем отсутствие дубликатов в собственных фичах
    check_duplicate_features(own_child_features)

    child_table = FlattenClass(
        class_decl=class_decl,
        renamed=[],
        undefined=[],
        redefined=[],
        precursors=[],
        selected=[],
        inherited=[],
        constructors=[],
        own=own_child_features)
    if not class_decl.inherit:
        check_create_clause(class_decl, own_child_features)
        constructors, own_child_features = split_create_features(
            own_child_features, class_decl.create)
        child_table.constructors = constructors
        child_table.own = own_child_features
        return child_table

    parent_to_features = {}
    select_clauses = {}

    for parent in class_decl.inherit:
        parent_decl = class_mapping[parent.class_name]
        parent_table = adapt(parent_decl, class_mapping)
        parent_features = parent_table.explicit_features

        # 1 этап. Применяем rename clause.
        check_rename_clause(
            parent,
            parent_features,
            own_child_features)
        renamed, parent_features = rename(parent, parent_features)

        # Добавляем в список renamed фичи из rename clause и унаследованные от
        # родителя.
        child_table.renamed.extend(renamed)
        child_table.renamed.extend(parent_table.renamed)

        # 2 этап. Применяем undefine clause.
        check_undefine_clause(
            parent,
            parent_features,
            own_child_features)
        parent_features = undefine(parent, parent_features)
        child_table.undefined.extend(parent_table.undefined)

        # 3 этап. Применяем redefine clause.
        check_redefine_clause(
            parent,
            parent_features,
            own_child_features)
        precursors, redefined, parent_features = redefine(
            parent, parent_features, own_child_features)

        _, parent_redefined, _ = redefine(
            parent, parent_table.redefined, own_child_features)
        redefined.extend(parent_redefined)
        child_table.redefined.extend(redefined)

        child_table.precursors.extend(precursors)
        child_table.precursors.extend(parent_table.precursors)

        # 4.1 этап. Добавляем selected фичи родителей и сохраняем
        # список фич родителя для анализа select дальше
        child_table.selected.extend(parent_table.selected)
        select_clauses[parent] = parent.select

        parent_to_features[parent] = parent_features

    # 4.2 этап. Применяем select clause.
    check_select_clause(
        select_clauses,
        parent_to_features,
        own_child_features)
    parent_to_features, selected_features = select(
        list(select_clauses.values()),
        parent_to_features)

    # 5 этап. Удаляем дубликаты, которые могли получится в процессе
    # наследования (одна и та же фича которая не менялась)
    all_features = remove_duplicates([
        feature
        for features in parent_to_features.values()
        for feature in features])

    own = child_table.own

    # 6 этап. "Сливаем" все фичи вместе
    inherited, undefined = merge(all_features + own, class_decl)
    check_if_all_defined(inherited + own, class_decl)

    child_table.renamed = remove_duplicates(child_table.renamed)
    child_table.undefined = remove_duplicates(
        child_table.undefined + undefined)
    child_table.redefined = remove_duplicates(child_table.redefined)
    child_table.precursors = remove_duplicates(child_table.precursors)
    child_table.inherited = inherited
    child_table.selected = remove_duplicates(selected_features)

    check_create_clause(class_decl, child_table.explicit_features)

    constructors, own = split_create_features(own, class_decl.create)
    child_table.constructors = constructors
    child_table.own = own

    return child_table


def analyze_inheritance(
        classes: list[ClassDecl],
        error_collector: ErrorCollector) -> list[FlattenClass]:
    class_mapping = {decl.class_name: decl for decl in classes}

    tables = []
    for decl in classes:
        try:
            tables.append(adapt(decl, class_mapping))
        except CompilerError as err:
            error_collector.add_error(err)

    if not error_collector.ok():
        return []

    return tables

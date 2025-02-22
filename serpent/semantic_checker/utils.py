from collections import defaultdict

from serpent.tree.features import *
from serpent.tree.type_decl import *
from serpent.semantic_checker.analyze_inheritance import FlattenClass, FeatureRecord


def show_feature_table(table: FlattenClass) -> str:
    """Отладочная процедура для печати интерфейса заданного
    класса по таблице фич"""
    ...
    lines = []

    lines.append(f"class interface {table.class_name}")
    lines.append("    --")
    lines.append(f"    -- Interface documentation for {table.class_name}")
    lines.append("    --")
    lines.append("")

    printable_features = (table.own
                          + table.inherited
                          + table.undefined
                          + table.selected)

    def get_type_name(type_decl: TypeDecl) -> str:
        if isinstance(type_decl, ClassType):
            if type_decl.name == "<VOID>":
                return ""
            return type_decl.name
        raise ValueError(f"Unsupported type declration: {type_decl}")

    def format_feature(feature: FeatureRecord, indent_size: int = 4) -> str:
        indent = " " * indent_size

        if isinstance(feature.node, (Field, Constant)):
            value_type = get_type_name(feature.node.value_type)
            return f"{indent}{feature.name}: {value_type}"
        elif isinstance(feature.node, BaseMethod):
            parameters = "; ".join(
                f"{param.name}: {get_type_name(param.value_type)}"
                for param in feature.node.parameters)
            if parameters != "":
                parameters = f" ({parameters})"
            return_type = get_type_name(feature.node.return_type)
            return f"{indent}{
                feature.name}{parameters}{
                ": " + return_type if return_type else ""}"
        else:
            raise ValueError("Unsupported type declration")

    grouped_by_class_name = defaultdict(list)
    for feature in printable_features:
        grouped_by_class_name[feature.from_class].append(feature)

    for class_name, features in grouped_by_class_name.items():
        section_title = f"feature(s) from {class_name}"
        lines.append(section_title)

        for feature in features:
            formatted_feature = format_feature(feature)
            lines.append(formatted_feature)
            lines.append("")

    lines.append(f"end of {table.class_name}\n")

    return "\n".join(lines)

from collections import defaultdict

from serpent.tree.features import *
from serpent.tree.type_decl import *
from serpent.semantic_checker.analyze_inheritance import FlattenClass, FeatureRecord
from serpent.semantic_checker.type_check import *


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


def pretty_print_node(node, indent=0) -> str:
    sp = "  " * indent
    if isinstance(node, TClass):
        lines = [f"{sp}class {node.class_name}:"]
        # Поля
        if node.fields:
            lines.append(f"{sp}  Fields:")
            for field in node.fields:
                lines.append(pretty_print_node(field, indent + 2))
        # Методы
        if node.methods:
            lines.append(f"{sp}  Methods:")
            for method in node.methods:
                lines.append(pretty_print_node(method, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, TField):
        return f"{sp}{node.name}: {node.expr_type.full_name}"

    elif isinstance(node, TExternalMethod):
        params = ", ".join(f"{n}: {t.full_name}" for n, t in node.parameters)
        return f"{sp}{node.method_name}({params}) external {node.language} alias \"{node.alias}\""

    elif isinstance(node, TUserDefinedMethod):
        params = ", ".join(f"{n}: {t.full_name}" for n, t in node.parameters)
        lines = [f"{sp}{node.method_name}({params}) do"]
        if node.variables:
            lines.append(f"{sp}  Locals:")
            for var, var_type in node.variables:
                lines.append(f"{sp}    {var}: {var_type.full_name}")
        if node.body:
            lines.append(f"{sp}  Body:")
            for stmt in node.body:
                lines.append(pretty_print_node(stmt, indent + 2))
        else:
            lines.append(f"{sp}  Body: ...")
        lines.append(f"{sp}end")
        return "\n".join(lines)

    elif isinstance(node, TAssignment):
        lines = [f"{sp}Assignment:"]
        lines.append(f"{sp}  LValue:")
        lines.append(pretty_print_node(node.lvalue, indent + 2))
        lines.append(f"{sp}  RValue:")
        lines.append(pretty_print_node(node.rvalue, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, TIfStmt):
        lines = [f"{sp}If:"]
        lines.append(f"{sp}  Condition:")
        lines.append(pretty_print_node(node.condition, indent + 2))
        lines.append(f"{sp}  Then:")
        for stmt in node.then_branch:
            lines.append(pretty_print_node(stmt, indent + 2))
        if node.elseif_branches:
            lines.append(f"{sp}  Elseif:")
            for cond, stmts in node.elseif_branches:
                lines.append(f"{sp}    Condition:")
                lines.append(pretty_print_node(cond, indent + 3))
                lines.append(f"{sp}    Body:")
                for s in stmts:
                    lines.append(pretty_print_node(s, indent + 3))
        lines.append(f"{sp}  Else:")
        for stmt in node.else_branch:
            lines.append(pretty_print_node(stmt, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, TLoopStmt):
        lines = [f"{sp}Loop:"]
        if node.init_stmts:
            lines.append(f"{sp}  Init:")
            for stmt in node.init_stmts:
                lines.append(pretty_print_node(stmt, indent + 2))
        lines.append(f"{sp}  Until:")
        lines.append(pretty_print_node(node.until_cond, indent + 2))
        if node.body:
            lines.append(f"{sp}  Body:")
            for stmt in node.body:
                lines.append(pretty_print_node(stmt, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, TRoutineCall):
        return f"{sp}RoutineCall:\n{
            pretty_print_node(
                node.feature_call,
                indent + 1)}"

    elif isinstance(node, TFeatureCall):
        owner_str = ""
        if node.owner:
            owner_str = pretty_print_node(node.owner, 0) + "."
        args_str = ", ".join(pretty_print_node(arg, 0)
                             for arg in node.arguments)
        return f"{sp}{owner_str}{node.feature_name}({args_str})"

    elif isinstance(node, TCreateExpr):
        args_str = ", ".join(pretty_print_node(arg, 0)
                             for arg in node.arguments)
        return f"{sp}new {node.constructor_name}({args_str})"

    elif isinstance(node, TBinaryOp):
        left = pretty_print_node(node.left, 0)
        right = pretty_print_node(node.right, 0)
        return f"{sp}({left} {node.operator_name} {right})"

    elif isinstance(node, TUnaryOp):
        arg = pretty_print_node(node.argument, 0)
        return f"{sp}({node.operator_name} {arg})"

    elif isinstance(node, TVariable):
        return f"{sp}{node.name}"

    elif isinstance(node, TIntegerConst):
        return f"{sp}{node.value}"

    elif isinstance(node, TRealConst):
        return f"{sp}{node.value}"

    elif isinstance(node, TCharacterConst):
        return f"{sp}'{node.value}'"

    elif isinstance(node, TStringConst):
        return f'{sp}"{node.value}"'

    elif isinstance(node, TBoolConst):
        return f"{sp}{node.value}"

    elif isinstance(node, TVoidConst):
        return f"{sp}void"

    elif isinstance(node, TExpr):
        return f"{sp}{node}"

    elif isinstance(node, TStatement):
        return f"{sp}{node}"

    else:
        return f"{sp}{node}"

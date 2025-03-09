from __future__ import annotations
from dataclasses import dataclass, field

from serpent.tree.expr import *
from serpent.tree.stmts import *
from serpent.tree.features import (
    Constant,
    Field,
    BaseMethod,
    ExternalMethod,
    Method)
from serpent.errors import CompilerError, ErrorCollector
from serpent.semantic_checker.analyze_inheritance import FlattenClass
from serpent.semantic_checker.symtab import (
    Type,
    ClassHierarchy,
    ClassSymbolTable,
    GlobalClassTable,
    type_of_class_decl_type,
    make_class_symtab,
    mangle_name,
    unmangle_name,
    class_name_of_mangled_name,
    GLOBAL_GENERIC_TABLE)


@dataclass(frozen=True)
class TExpr(ABC):
    expr_type: Type


@dataclass(frozen=True)
class TIntegerConst(TExpr):
    value: int


@dataclass(frozen=True)
class TRealConst(TExpr):
    value: float


@dataclass(frozen=True)
class TCharacterConst(TExpr):
    value: str


@dataclass(frozen=True)
class TStringConst(TExpr):
    value: str


@dataclass(frozen=True)
class TBoolConst(TExpr):
    value: bool


@dataclass(frozen=True)
class TVoidConst(TExpr):
    pass


@dataclass(frozen=True)
class TFeatureCall(TExpr):
    feature_name: str
    arguments: list[TExpr] = field(default_factory=list)
    owner: TExpr | None = None


@dataclass(frozen=True)
class TCreateExpr(TExpr):
    constructor_name: str
    arguments: list[TExpr] = field(default_factory=list)


@dataclass(frozen=True)
class TBinaryOp(TExpr):
    operator_name: str
    left: TExpr
    right: TExpr


@dataclass(frozen=True)
class TUnaryOp(TExpr):
    operator_name: str
    argument: TExpr


@dataclass(frozen=True)
class TVariable(TExpr):
    name: str


class TStatement(ABC):
    pass


@dataclass(frozen=True)
class TAssignment(TStatement):
    lvalue: TExpr
    rvalue: TExpr


@dataclass(frozen=True)
class TIfStmt(TStatement):
    condition: TExpr
    then_branch: list[TStatement]
    else_branch: list[TStatement]
    elseif_branches: list[tuple[TExpr, list[TStatement]]]


@dataclass(frozen=True)
class TLoopStmt(TStatement):
    init_stmts: list[TStatement]
    until_cond: TExpr
    body: list[TStatement]


@dataclass(frozen=True)
class TRoutineCall(TStatement):
    feature_call: TFeatureCall


@dataclass(frozen=True)
class TField(TExpr):
    name: str
    owner: TExpr | None = None


@dataclass(frozen=True)
class TMethod(ABC):
    method_name: str
    parameters: list[tuple[str, Type]]
    return_type: Type
    is_constructor: bool


@dataclass(frozen=True)
class TExternalMethod(TMethod):
    language: str
    alias: str


@dataclass(frozen=True)
class TUserDefinedMethod(TMethod):
    variables: list[tuple[str, Type]]
    body: list[TStatement]


@dataclass(frozen=True)
class TClass:
    class_name: str
    methods: list[TMethod]
    fields: list[TField]


def annotate_constant_expr(const_expr: Expr) -> TExpr:
    match const_expr:
        case IntegerConst(value=value):
            return TIntegerConst(Type("INTEGER"), value)
        case RealConst(value=value):
            return TRealConst(Type("REAL"), value)
        case CharacterConst(value=value):
            return TCharacterConst(Type("CHARACTER"), value)
        case StringConst(value=value):
            return TStringConst(Type("STRING"), value=value)
        case BoolConst(value=value):
            return TBoolConst(Type("BOOLEAN"), value=value)
        case VoidConst():
            return TVoidConst(Type("NONE"))
    assert False


def class_decl_type_of_type(t: Type) -> ClassType:
    generics = [class_decl_type_of_type(generic) for generic in t.generics]
    return ClassType(location=None, name=t.name, generics=generics)


def annotate_feature_call(
        feature_call: FeatureCall,
        context_method_name: str,
        symtab: ClassSymbolTable,
        hierarchy: ClassHierarchy,
        global_class_table: GlobalClassTable,
        flatten_class_mapping: dict[str, FlattenClass]):
    name = feature_call.feature_name
    owner = feature_call.owner

    printable_feature_name = (
        feature_call.symbol_name
        if isinstance(feature_call, (BinaryFeature, UnaryFeature)) else name)

    if owner is not None:
        typed_owner = annotate_expr_with_types(
            owner,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping,
            context_method_name=context_method_name)

        if not global_class_table.has_class_table(
                typed_owner.expr_type.full_name):
            flatten_cls = flatten_class_mapping[typed_owner.expr_type.name]

            # Костыль: из объекта Type (владельница фичи) создаем объект
            # декларации типа, для генерации соответствующей таблицы
            actual_type = class_decl_type_of_type(typed_owner.expr_type)
            owner_symtab = make_class_symtab(
                actual_type, flatten_cls, hierarchy)
            global_class_table.add_class_table(owner_symtab)

        callee_symtab = global_class_table.get_class_table(
            typed_owner.expr_type.full_name)
    else:
        typed_owner = None

        local_name = mangle_name(name)
        if symtab.has_local(context_method_name, local_name):
            variable_type = symtab.type_of_local(
                context_method_name, local_name)
            return TVariable(variable_type, local_name)

        callee_symtab = symtab

    feature_name = mangle_name(name, class_name=callee_symtab.full_type_name)
    if not callee_symtab.has_feature(
            feature_name,
            self_called=typed_owner is None):
        raise CompilerError(
            f"Unknown feature '{printable_feature_name}' of class {
                callee_symtab.short_type_name}",
            location=feature_call.location)

    if typed_owner is not None:
        if not callee_symtab.can_be_called(
                feature_name, hierarchy, symtab.type_of):
            raise CompilerError(
                f"Objects of class '{symtab.type_of.name}' are \
not allowed to call feature '{name}' of class '{callee_symtab.type_of.name}'"
            )

    value_type = callee_symtab.type_of_feature(feature_name)
    arguments = [
        annotate_expr_with_types(
            arg,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping,
            context_method_name=context_method_name)
        for arg in feature_call.arguments
    ]

    if callee_symtab.is_field(
            feature_name) or callee_symtab.is_constant(feature_name):
        if arguments:
            raise CompilerError(
                f"Feature '{printable_feature_name}' is not a method, arguments cannot be given",
                location=feature_call.location)

        if callee_symtab.is_field(feature_name):
            return TField(value_type, feature_name, typed_owner)
        else:
            constant_node = callee_symtab.get_feature_node(feature_name)
            assert isinstance(constant_node, Constant)

            return annotate_expr_with_types(
                constant_node.constant_value,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping,
                context_method_name=context_method_name)

    signature = callee_symtab.get_feature_signature(feature_name)
    if len(arguments) != len(signature):
        feature_node = callee_symtab.get_feature_node(feature_name)
        raise CompilerError(
            f"Wrong number of arguments given to feature '{printable_feature_name}', expected {
                len(signature)}, got {
                len(arguments)}. See definition at {
                feature_node.location}",
            location=feature_call.location)

    # Особый случай: с точки зрения Eiffel конструкция
    # 2 + 4.5 неверна, т.к. фича '+' класса INTEGER ожидает справа
    # выражений типа INTEGER, однако компилятор вставляет неявное
    # преобразование в REAL всякий раз, когда обнаруживает попытку
    # сложить INTEGER и REAL, а также при операциях ниже
    if name in [
            "plus",
            "minus",
            "product",
            "quotient",
            "integer_quotinent",
            "integer_remainder",
            "power",
            "is_less",
            "is_less_equal",
            "is_greater_equal",
            "is_greater",
            "is_equal",
            "is_not_equal"
            ] and typed_owner is not None and (typed_owner.expr_type.full_name in ["INTEGER", "REAL"]
                and len(arguments) == 1 and arguments[0].expr_type.full_name in ["INTEGER", "REAL"]):
        # Где-то тут было бы неплохо добавить проверку, что
        # метод to_real есть у того, у кого он вызывается

        if (typed_owner.expr_type.full_name == "REAL"
                and arguments[0].expr_type.full_name == "INTEGER"):
            to_real_name = mangle_name("to_real", class_name="INTEGER")
            arguments[0] = TFeatureCall(
                expr_type=Type("REAL"),
                feature_name=to_real_name,
                arguments=[],
                owner=arguments[0])
        elif (typed_owner.expr_type.full_name == "INTEGER"
                and arguments[0].expr_type.full_name == "REAL"):
            to_real_name = mangle_name("to_real", class_name="INTEGER")
            typed_owner = TFeatureCall(
                expr_type=Type("REAL"),
                feature_name=to_real_name,
                arguments=[],
                owner=typed_owner)
            
            new_callee_symtab = global_class_table.get_class_table("REAL")
            feature_name = mangle_name(name, class_name="REAL")
            signature = new_callee_symtab.get_feature_signature(feature_name)
            value_type = new_callee_symtab.type_of_feature(feature_name)

    for arg, (arg_name, arg_type) in zip(arguments, signature):
        if not arg.expr_type.conforms_to(arg_type, hierarchy):
            printable_arg_name = unmangle_name(arg_name, is_local=True)
            raise CompilerError(
                f"Type mismatch for argument '{printable_arg_name}' in feature '{printable_feature_name}': expected {arg_type}, got {
                    arg.expr_type}", location=feature_call.location)

    feature_call = TFeatureCall(
        value_type, feature_name, arguments, typed_owner)
    return feature_call


def annotate_precursor_call(
        precursor_call: PrecursorCall,
        context_method_name: str,
        symtab: ClassSymbolTable,
        hierarchy: ClassHierarchy,
        global_class_table: GlobalClassTable,
        flatten_class_mapping: dict[str, FlattenClass]) -> TFeatureCall:
    # Получаем класс и имя фичи, в контексте которой Precursor был вызван
    class_name = class_name_of_mangled_name(context_method_name)

    # При переопредлении методов, на уровне синтаксического дерева,
    # чтобы сохранить полиморфизм (т.е. возможно родительским классам
    # вызывать переопределенные у детей методы), например,
    # class A
    # feature f do ... end
    # end
    # class B
    # feature g (a: A) do a.f end
    # end
    # class C
    # inherit A redefine f end
    # feature f do print ("REDEFINED") end
    # end
    # В данном случае, если передать объект типа С
    # на место параметра a, то вызовется переопределенная версия из C.
    # В результате было принято решение копировать в родительский узел 
    # метода родителя узел переопределенного тела метода ребенка,
    # однако на этом этапе копировался и Precusor, что приводило к попытке
    # вызывать прекурсор родителя родителя и так далее. Поэтому мы проверяем,
    # что имя типа symtab совпадает с полученным именем класса из контекста метода,
    # иначе меняем их таким образом, чтобы ничего не поломалось
    unmangled_feature_name = unmangle_name(context_method_name)
    if class_name != symtab.full_type_name:
        class_name = symtab.full_type_name
        context_method_name = mangle_name(
            unmangled_feature_name, class_name=class_name)

    # Получаем имена всех родителей
    parents_names = [
        parent.class_name
        for parent in
        flatten_class_mapping[class_name].class_decl.inherit]

    # Формируем предполагаемый список возможных родительских фич
    possible_precursors = [
        f"Precursor_{parent_name}_{unmangled_feature_name}"
        for parent_name in parents_names]

    precursors = [
        precursor_name
        for precursor_name in possible_precursors
        if symtab.has_feature(precursor_name, self_called=True)]

    if len(precursors) == 0:
        raise CompilerError(
            f"No Precursor feature available for '{unmangled_feature_name}' -- are you sure you've redefined it?",
            location=precursor_call.location)
    elif len(precursors) == 1:
        precursor_name = precursors[0]

        parent_name = precursor_call.ancestor_name
        if parent_name is not None:
            given_precursor_name = f"Precursor_{parent_name}_{unmangled_feature_name}"
            if given_precursor_name != precursor_name:
                raise CompilerError(
                    f"Precursor mismatch for {unmangled_feature_name} -- given class '{parent_name}' does not exist or has no such feature",
                    location=precursor_call.location)
            precursor_name = given_precursor_name
    else:
        parent_name = precursor_call.ancestor_name
        if parent_name is None:
            raise CompilerError(
                f"Ambiguous Precursor call for '{unmangled_feature_name}': ancestor not specified",
                location=precursor_call.location)

        given_precursor_name = f"Precursor_{parent_name}_{unmangled_feature_name}"
        if given_precursor_name not in precursors:
            raise CompilerError(
                f"Invalid Precursor for '{unmangled_feature_name}': no Precursor for ancestor '{parent_name}' found",
                location=precursor_call.location)

        precursor_name = given_precursor_name

    value_type = symtab.type_of_feature(precursor_name)
    arguments = [
        annotate_expr_with_types(
            arg,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping,
            context_method_name=context_method_name)
        for arg in precursor_call.arguments
    ]

    feature_name = context_method_name
    if symtab.is_field(feature_name):
        if arguments:
            raise CompilerError(
                f"Precursor for feature '{unmangled_feature_name}' is not a method, arguments cannot be given",
                location=precursor_call.location)

        return TField(value_type, feature_name)

    assert not symtab.is_constant(
        feature_name), f"Expected '{unmangled_feature_name}' to be not Constant"

    signature = symtab.get_feature_signature(feature_name)
    if len(arguments) != len(signature):
        feature_node = symtab.get_feature_node(feature_name)
        raise CompilerError(
            f"Wrong number of arguments given to Precursor of feature '{unmangled_feature_name}', expected {
                len(signature)}, got {
                len(arguments)}. See definition at {
                feature_node.location}",
            location=precursor_call.location)

    for arg, (arg_name, arg_type) in zip(arguments, signature):
        if not arg.expr_type.conforms_to(arg_type, hierarchy):
            printable_arg_name = unmangle_name(arg_name, is_local=True)
            raise CompilerError(
                f"Type mismatch for argument '{printable_arg_name}' in Precursor for feature '{unmangled_feature_name}': expected {arg_type}, got {
                    arg.expr_type}", location=precursor_call.location)

    real_feature = TFeatureCall(value_type, precursor_name, arguments, None)
    return real_feature


def annotate_create_expr(
        create_expr: CreateExpr,
        context_method_name: str,
        symtab: ClassSymbolTable,
        hierarchy: ClassHierarchy,
        global_class_table: GlobalClassTable,
        flatten_class_mapping: dict[str, FlattenClass]) -> TCreateExpr:
    object_type = create_expr.object_type
    constructor_call = create_expr.constructor_call

    if not isinstance(object_type, ClassType):
        raise CompilerError("Concrete class types are only supported",
                            location=create_expr.location)

    expr_type = type_of_class_decl_type(object_type)
    if expr_type.name not in hierarchy:
        raise CompilerError(f"Unknown type '{expr_type.name}'",
                            location=create_expr.location)

    if not global_class_table.has_class_table(expr_type.full_name):
        flatten_cls = flatten_class_mapping[expr_type.name]
        # Костыль: из объекта Type (владельница фичи) создаем объект
        # декларации типа, для генерации соответствующей таблицы
        actual_type = class_decl_type_of_type(expr_type)
        create_object_symtab = make_class_symtab(
            actual_type, flatten_cls, hierarchy)
        global_class_table.add_class_table(create_object_symtab)

    create_object_symtab = global_class_table.get_class_table(
        expr_type.full_name)
    constructor_name = constructor_call.feature_name
    arguments = constructor_call.arguments

    if create_object_symtab.is_deferred:
        raise CompilerError(
            f"Cannot call constructor feature '{constructor_name}' of deferred class '{
                create_object_symtab.type_of.full_name}'",
            location=create_expr.location)

    constructor_name_mangled = mangle_name(
        constructor_name, class_name=create_object_symtab.type_of.full_name)
    if not create_object_symtab.has_feature(constructor_name_mangled):
        raise CompilerError(
            f"No constructor feature '{constructor_name}' found",
            location=create_expr.location)
    if not create_object_symtab.is_constructor(constructor_name_mangled):
        raise CompilerError(
            f"Feature '{constructor_name}' is not a constructor",
            location=create_expr.location)

    if not create_object_symtab.can_be_called(
            constructor_name_mangled, hierarchy, symtab.type_of):
        raise CompilerError(
            f"Objects of class '{symtab.type_of.full_name}' are \
not allowed to call constructor feature '{constructor_name}' of class '{create_object_symtab.type_of.full_name}'"
        )

    arguments = [
        annotate_expr_with_types(
            arg,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping,
            context_method_name=context_method_name)
        for arg in arguments
    ]

    signature = create_object_symtab.get_feature_signature(
        constructor_name_mangled)
    if len(arguments) != len(signature):
        feature_node = create_object_symtab.get_feature_node(
            constructor_name_mangled)
        raise CompilerError(
            f"Wrong number of arguments given to constructor feature '{constructor_name}', expected {
                len(signature)}, got {
                len(arguments)}. See definition at {
                feature_node.location}",
            location=create_expr.location)

    for arg, (arg_name, arg_type) in zip(arguments, signature):
        if not arg.expr_type.conforms_to(arg_type, hierarchy):
            printable_arg_name = unmangle_name(arg_name, is_local=True)
            raise CompilerError(
                f"Type mismatch for argument '{printable_arg_name}' in Precursor for feature '{constructor_name}': expected {arg_type}, got {
                    arg.expr_type}", location=create_expr.location)

    return TCreateExpr(expr_type, constructor_name_mangled, arguments)


def annotate_binary_op(bin_op: BinaryOp,
                       context_method_name: str,
                       symtab: ClassSymbolTable,
                       hierarchy: ClassHierarchy,
                       global_class_table: GlobalClassTable,
                       flatten_class_mapping: dict[str, FlattenClass]):
    left, right = bin_op.left, bin_op.right
    typed_left = annotate_expr_with_types(
        left,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping,
        context_method_name=context_method_name)
    typed_right = annotate_expr_with_types(
        right,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping,
        context_method_name=context_method_name)

    operator_name = ""
    match bin_op:
        case AndOp():
            operator_name = "and"
        case OrOp():
            operator_name = "or"
        case AndThenOp():
            operator_name = "and then"
        case OrElseOp():
            operator_name = "or else"
        case XorOp():
            operator_name = "xor"
        case ImpliesOp():
            operator_name = "implies"
        case _: assert False

    if typed_left.expr_type.name != "BOOLEAN":
        raise CompilerError(
            f"Left operand of '{operator_name}' must be BOOLEAN, got {
                typed_left.expr_type.name}",
            location=left.location)
    if typed_right.expr_type.name != "BOOLEAN":
        raise CompilerError(
            f"Right operand of '{operator_name}' must be BOOLEAN, got {
                typed_right.expr_type.name}",
            location=right.location)

    expr_type = typed_left.expr_type

    # Преобразуем импликацию в эквивалентную формулу
    if operator_name == "implies":
        return TBinaryOp(
            expr_type=expr_type,
            operator_name="and then",
            left=TUnaryOp(
                expr_type=expr_type,
                operator_name="not",
                argument=typed_left),
            right=typed_right)

    return TBinaryOp(expr_type=expr_type,
                     operator_name=operator_name,
                     left=typed_left,
                     right=typed_right)


def annotate_unary_op(un_op: NotOp,
                      context_method_name: str,
                      symtab: ClassSymbolTable,
                      hierarchy: ClassHierarchy,
                      global_class_table: GlobalClassTable,
                      flatten_class_mapping: dict[str, FlattenClass]):
    assert isinstance(
        un_op, NotOp), "Only 'not' is supported as unary operator"

    operand = un_op.argument
    typed_operand = annotate_expr_with_types(
        operand,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping,
        context_method_name=context_method_name)

    if typed_operand.expr_type.name != "BOOLEAN":
        raise CompilerError(
            f"Operand of 'not' must be BOOLEAN, got {
                typed_operand.expr_type.name}",
            location=operand.location)

    return TUnaryOp(expr_type=Type("BOOLEAN"),
                    operator_name="not",
                    argument=typed_operand)


def annotate_expr_with_types(
        expr: Expr,
        symtab: ClassSymbolTable,
        hierarchy: ClassHierarchy,
        global_class_table: GlobalClassTable,
        flatten_class_mapping: dict[str, FlattenClass],
        context_method_name: str | None = None) -> TExpr:
    if not isinstance(expr, ConstantValue) and context_method_name is None:
        assert False, "Given expr is not ConstantValue, but context_method_name is None"

    match expr:
        case ConstantValue():
            return annotate_constant_expr(expr)
        case FeatureCall() as feature_call:
            return annotate_feature_call(
                feature_call,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case PrecursorCall() as precursor_call:
            return annotate_precursor_call(
                precursor_call,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case CreateExpr() as create_expr:
            return annotate_create_expr(
                create_expr,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case BinaryOp() as binary_op:
            return annotate_binary_op(
                binary_op,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case UnaryOp() as unary_op:
            return annotate_unary_op(
                unary_op,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case ResultConst() as result_const:
            feature_value_type = symtab.type_of_feature(
                context_method_name, self_called=True)
            if feature_value_type.full_name == "<VOID>":
                method_name = unmangle_name(context_method_name)
                raise CompilerError(
                    f"Invalid use of 'Result': feature '{method_name}' is a procedure and cannot yield a \
result. Use 'Result' only within functions that return a value",
                    location=result_const.location)
            return TVariable(feature_value_type, mangle_name("Result"))
        case _:
            raise CompilerError(
                f"Unsupported expression type: {expr}",
                location=expr.location)


def annotate_assignment(assignment: Assignment,
                        context_method_name: str,
                        symtab: ClassSymbolTable,
                        hierarchy: ClassHierarchy,
                        global_class_table: GlobalClassTable,
                        flatten_class_mapping: dict[str, FlattenClass]):
    if isinstance(assignment.target, str):
        local_name = mangle_name(assignment.target)

        if symtab.has_local(context_method_name, local_name):
            variable_type = symtab.type_of_local(
                context_method_name, local_name)
            left = TVariable(variable_type, local_name)
        else:
            feature_name = mangle_name(
                assignment.target,
                class_name=symtab.full_type_name)
            if not symtab.has_feature(feature_name):
                raise CompilerError(
                    f"Unknown feature or variable '{assignment.target}'",
                    location=assignment.location)

            if not symtab.is_field(feature_name):
                raise CompilerError(
                    f"Left side of assignment is not writable -- must be either field or local variable",
                    location=assignment.location)

            field_type = symtab.type_of_feature(feature_name)
            left = TField(field_type, feature_name)
    elif isinstance(assignment.target, Expr):
        left = annotate_expr_with_types(
            assignment.target,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping,
            context_method_name=context_method_name)
    else:
        assert False, f"Type of target is unknown: {assignment.target}"

    right = annotate_expr_with_types(
        assignment.value,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping,
        context_method_name=context_method_name
    )

    # Специальный случай, когда мы пытаетмся присвоить INTEGER в REAL,
    # компилятор автоматически вставляет функцию преобразования типа
    if right.expr_type.full_name == "INTEGER" and left.expr_type.full_name == "REAL":
        right = TFeatureCall(
            expr_type=Type("REAL"),
            feature_name=mangle_name("to_real", class_name=right.expr_type.full_name),
            arguments=[],
            owner=right)

    if not right.expr_type.conforms_to(left.expr_type, hierarchy):
        raise CompilerError(
            f"Type mismatch in assignment: cannot assign {
                right.expr_type} to {
                left.expr_type}",
            location=assignment.location)

    return TAssignment(lvalue=left, rvalue=right)


def annotate_create_stmt(create_stmt: CreateStmt,
                         context_method_name: str,
                         symtab: ClassSymbolTable,
                         hierarchy: ClassHierarchy,
                         global_class_table: GlobalClassTable,
                         flatten_class_mapping: dict[str, FlattenClass]):
    constructor_call = create_stmt.constructor_call

    if create_stmt.object_type is None:
        local_name = mangle_name(constructor_call.object_name)
        if symtab.has_local(context_method_name, local_name):
            create_object_type = symtab.type_of_local(
                context_method_name, local_name)
        else:
            feature_name = mangle_name(
                constructor_call.object_name,
                class_name=symtab.full_type_name)
            create_object_type = symtab.type_of_feature(
                feature_name, self_called=True) # Почему True? Не знаю, на всякий случай...
            
            if not symtab.is_field(feature_name, self_called=True):
                raise CompilerError(
                    f"Ensure '{constructor_call.object_name}' is correctly declared as a local variable or "
                    f"class field in '{symtab.full_type_name}'"
                )

        if not global_class_table.has_class_table(
                create_object_type.full_name):
            flatten_cls = flatten_class_mapping[create_object_type.name]
            # Костыль: из объекта Type (владельница фичи) создаем объект
            # декларации типа, для генерации соответствующей таблицы
            actual_type = class_decl_type_of_type(create_object_type)
            create_object_symtab = make_class_symtab(
                actual_type, flatten_cls, hierarchy)
            global_class_table.add_class_table(create_object_symtab)

        create_object_symtab = global_class_table.get_class_table(
            create_object_type.full_name)

        if constructor_call.constructor_name is None:
            constructor_name = "default_create"
        else:
            constructor_name = constructor_call.constructor_name

        mangled_constructor_name = mangle_name(
            constructor_name, class_name=create_object_type.full_name)
        if not create_object_symtab.has_feature(mangled_constructor_name):
            raise CompilerError(
                f"Unknown constructor feature '{constructor_name}'",
                location=create_stmt.location)
    else:
        create_object_type = type_of_class_decl_type(create_stmt.object_type)

    # Здесь нет проверки на то, существует ли object_type
    # реально в иерархии классов, т.к. данная проверка и
    # соответствующее создание класса (в случае дженерик-класса)
    # произойдет в annotate_create_expr

    target = constructor_call.object_name

    create_expr = CreateExpr(
        location=create_stmt.location,
        object_type=class_decl_type_of_type(create_object_type),
        constructor_call=FeatureCall(
            location=constructor_call.location,
            feature_name=constructor_call.constructor_name,
            arguments=constructor_call.arguments))
    assignment = Assignment(
        location=create_stmt.location,
        target=target,
        value=create_expr)

    return annotate_assignment(
        assignment,
        context_method_name,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping)


def annotate_if_stmt(if_stmt: IfStmt,
                     context_method_name: str,
                     symtab: ClassSymbolTable,
                     hierarchy: ClassHierarchy,
                     global_class_table: GlobalClassTable,
                     flatten_class_mapping: dict[str,
                                                 FlattenClass]) -> TIfStmt:
    typed_condition = annotate_expr_with_types(
        if_stmt.condition,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping,
        context_method_name=context_method_name)
    if typed_condition.expr_type.name != "BOOLEAN":
        raise CompilerError(
            f"If condition must be BOOLEAN, got {typed_condition.expr_type}",
            location=if_stmt.condition.location)

    typed_then = [
        annotate_statement(
            stmt,
            context_method_name,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping) for stmt in if_stmt.then_branch]
    typed_else = [
        annotate_statement(
            stmt,
            context_method_name,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping) for stmt in if_stmt.else_branch]

    typed_elseif = []
    for elseif in if_stmt.elseif_branches:
        typed_elseif_cond = annotate_expr_with_types(
            elseif.condition,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping,
            context_method_name=context_method_name)
        if typed_elseif_cond.expr_type.name != "BOOLEAN":
            raise CompilerError(
                f"Elseif condition must be BOOLEAN, got {
                    typed_elseif_cond.expr_type}",
                location=elseif.condition.location)
        typed_elseif_body = [
            annotate_statement(
                stmt,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping) for stmt in elseif.body]
        typed_elseif.append((typed_elseif_cond, typed_elseif_body))

    return TIfStmt(
        condition=typed_condition,
        then_branch=typed_then,
        else_branch=typed_else,
        elseif_branches=typed_elseif)


def annotate_loop(loop_stmt: LoopStmt,
                  context_method_name: str,
                  symtab: ClassSymbolTable,
                  hierarchy: ClassHierarchy,
                  global_class_table: GlobalClassTable,
                  flatten_class_mapping: dict[str, FlattenClass]) -> TLoopStmt:
    typed_init = [
        annotate_statement(
            stmt,
            context_method_name,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping) for stmt in loop_stmt.init_stmts]

    typed_until = annotate_expr_with_types(
        loop_stmt.until_cond,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping,
        context_method_name=context_method_name)
    if typed_until.expr_type.name != "BOOLEAN":
        raise CompilerError(
            f"Loop 'until' condition must be BOOLEAN, got {
                typed_until.expr_type}",
            location=loop_stmt.until_cond.location)

    typed_body = [
        annotate_statement(
            stmt,
            context_method_name,
            symtab,
            hierarchy,
            global_class_table,
            flatten_class_mapping) for stmt in loop_stmt.body]

    return TLoopStmt(
        init_stmts=typed_init,
        until_cond=typed_until,
        body=typed_body)


def annotate_routine(routine_call: RoutineCall,
                     context_method_name: str,
                     symtab: ClassSymbolTable,
                     hierarchy: ClassHierarchy,
                     global_class_table: GlobalClassTable,
                     flatten_class_mapping: dict[str, FlattenClass]):
    feature_call = annotate_feature_call(
        routine_call.feature_call,
        context_method_name,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping)
    if isinstance(feature_call, TField) or isinstance(feature_call, TVariable):
        unmangled_name = unmangle_name(
            feature_call.name,
            is_local=isinstance(feature_call, TVariable))
        raise CompilerError(
            f"Attempted to invoke subroutine '{unmangled_name}' on a variable or field.")
    return TRoutineCall(feature_call)


def annotate_precursor_routine(
        precursor: PrecursorCallStmt,
        context_method_name: str,
        symtab: ClassSymbolTable,
        hierarchy: ClassHierarchy,
        global_class_table: GlobalClassTable,
        flatten_class_mapping: dict[str, FlattenClass]):
    feature_call = annotate_precursor_call(
        precursor.precursor_call,
        context_method_name,
        symtab,
        hierarchy,
        global_class_table,
        flatten_class_mapping)
    if isinstance(feature_call, TField) or isinstance(feature_call, TVariable):
        unmangled_name = unmangle_name(
            feature_call.name,
            is_local=isinstance(feature_call, TVariable))
        raise CompilerError(
            f"Attempted to invoke subroutine '{unmangled_name}' on a variable or field")
    return TRoutineCall(feature_call)


def annotate_statement(stmt: Statement,
                       context_method_name: str,
                       symtab: ClassSymbolTable,
                       hierarchy: ClassHierarchy,
                       global_class_table: GlobalClassTable,
                       flatten_class_mapping: dict[str, FlattenClass]):
    match stmt:
        case Assignment() as assignment:
            return annotate_assignment(
                assignment,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case CreateStmt() as create_stmt:
            return annotate_create_stmt(
                create_stmt,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case IfStmt() as if_stmt:
            return annotate_if_stmt(
                if_stmt,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case LoopStmt() as loop_stmt:
            return annotate_loop(
                loop_stmt,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case RoutineCall() as routine_call:
            return annotate_routine(
                routine_call,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case PrecursorCallStmt() as precursor_call_stmt:
            return annotate_precursor_routine(
                precursor_call_stmt,
                context_method_name,
                symtab,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
        case _:
            raise CompilerError(
                f"Unsupported statement type: {stmt}",
                location=stmt.location)


def make_codegen_class(flatten_cls: FlattenClass,
                       hierarchy: ClassHierarchy,
                       global_class_table: GlobalClassTable,
                       flatten_class_mapping: dict[str, FlattenClass],
                       actual_type: ClassType | None = None) -> TClass:
    # Дикий костыль, необходимый для того, чтобы при любом тексте в
    # в классе NONE отбрасывать все методы и поля
    if flatten_cls.class_name == "NONE":
        return TClass(class_name="NONE", methods=[], fields=[])

    if flatten_cls.class_decl.generics and actual_type is None:
        assert False, (f"Generic class '{
            flatten_cls.class_name}' requires an actual type, but none was provided.")

    if not flatten_cls.class_decl.generics and actual_type is not None:
        assert False, (f"Non-generic class '{
            flatten_cls.class_name}' should not have an actual type provided.")

    # Если переданный класс не найден в таблице всех классов,
    # значит нам необходимо его определить самостоятельно
    if not global_class_table.has_class_table(flatten_cls.class_name):
        actual_type = actual_type or ClassType(
            location=None, name=flatten_cls.class_name)
        class_type = type_of_class_decl_type(actual_type)

        if not global_class_table.has_class_table(class_type.full_name):
            symtab = make_class_symtab(
                actual_type,
                flatten_cls,
                hierarchy)

            global_class_table.add_class_table(symtab)
        else:
            symtab = global_class_table.get_class_table(class_type.full_name)
    # В ином случае, просто получаем уже созданную таблицу класса
    else:
        symtab = global_class_table.get_class_table(flatten_cls.class_name)

    methods = []
    fields = []
    for feature_name, feature_node in symtab.feature_node_map.items():

        if isinstance(feature_node, Field):
            field_type = symtab.type_of_feature(feature_name, self_called=True)
            fields.append(TField(field_type, feature_name))
        elif isinstance(feature_node, Constant):
            if not isinstance(feature_node.constant_value, ConstantValue):
                raise CompilerError(
                    f"Constant '{feature_name}' does not have a valid constant value",
                    location=feature_node.location)

            declared_field_type = symtab.type_of_feature(
                feature_name, self_called=True)
            actual_expr_type = annotate_constant_expr(
                feature_node.constant_value)
            if not actual_expr_type.expr_type.conforms_to(
                    declared_field_type, hierarchy):
                raise CompilerError(
                    f"Type mismatch in constant '{feature_name}': expected {declared_field_type}, got {
                        actual_expr_type.expr_type}", location=feature_node.location)
        elif isinstance(feature_node, BaseMethod):
            is_constructor = symtab.is_constructor(feature_name)

            if isinstance(feature_node, ExternalMethod):
                methods.append(
                    TExternalMethod(
                        feature_name,
                        symtab.get_feature_signature(feature_name),
                        symtab.type_of_feature(feature_name, self_called=True),
                        is_constructor,
                        feature_node.language,
                        feature_node.alias))
            elif isinstance(feature_node, Method):
                body = []
                
                # Нечто похожее на данный код дублируется в preprocess.py,
                # по-хорошему от этого надо избавиться, но сейчас мне все равно...
                return_type = symtab.type_of_feature(
                    feature_name, self_called=True)
                if return_type.full_name != "<VOID>":
                    match return_type.full_name:
                        case "INTEGER":
                            default_value = TIntegerConst(return_type, 0)
                        case "REAL":
                            default_value = TRealConst(return_type, 0)
                        case "STRING":
                            default_value = TStringConst(return_type, "")
                        case "CHARACTER":
                            default_value = TCharacterConst(return_type, "")
                        case "BOOLEAN":
                            default_value = TBoolConst(return_type, False)
                        case _:
                            default_value = TVoidConst(expr_type=Type("NONE"))
                    body.append(
                        TAssignment(
                            TVariable(return_type, "local_Result"),
                            default_value))

                body.extend([
                    annotate_statement(
                        stmt,
                        feature_name,
                        symtab,
                        hierarchy,
                        global_class_table,
                        flatten_class_mapping)
                    for stmt in feature_node.do])
                methods.append(
                    TUserDefinedMethod(
                        feature_name,
                        symtab.get_feature_signature(feature_name),
                        return_type,
                        is_constructor,
                        symtab.get_variables(feature_name),
                        body))
        else:
            assert False, (f"Unexpected feature type '{
                type(feature_node).__name__}' encountered for feature '{feature_name}'")

    return TClass(symtab.full_type_name, methods, fields)


def check_types(
        flatten_classes: list[FlattenClass],
        hierarchy: ClassHierarchy,
        error_collector: ErrorCollector) -> list[TClass]:
    non_generic_classes = [
        fc for fc in flatten_classes if not fc.class_decl.generics]

    flatten_class_mapping = {fcls.class_name: fcls for fcls in flatten_classes}
    global_class_table = GlobalClassTable()

    codegen_classes = []
    for flatten_cls in non_generic_classes:
        try:
            tclass = make_codegen_class(
                flatten_cls,
                hierarchy,
                global_class_table,
                flatten_class_mapping)
            codegen_classes.append(tclass)
        except CompilerError as error:
            error_collector.add_error(error)

    if not error_collector.ok():
        return []

    for class_name, types in GLOBAL_GENERIC_TABLE.items():
        flatten_cls = flatten_class_mapping[class_name]

        for typ in types:
            actual_type = class_decl_type_of_type(typ)
            try:
                tclass = make_codegen_class(
                    flatten_cls,
                    hierarchy,
                    global_class_table,
                    flatten_class_mapping,
                    actual_type=actual_type)
                codegen_classes.append(tclass)
            except CompilerError as error:
                error_collector.add_error(error)

    return codegen_classes

from serpent.semantic_checker.type_check import *

from serpent.codegen.constpool import (
    ConstPool,
    add_package_prefix,
    make_fully_qualifed_name,
    split_package_path,
    PLATFORM_CLASS_NAME,
    ROOT_CLASS_NAME,
    COMPILER_NAME)
from serpent.codegen.bytecommand import *
from serpent.codegen.preprocess import default_value_for
from serpent.errors import CompilerWarning, CompilerError


@dataclass(frozen=True)
class LocalTable:
    variables: list[tuple[str, int]] = field(default_factory=list)
    is_static: bool = False

    @property
    def count(self) -> int:
        if self.is_static:
            return len(self.variables)
        return len(self.variables) + 1

    def __getitem__(self, variable_name: str) -> int:
        index = -1
        for v, i in self.variables:
            if v == variable_name:
                index = i

        if index == -1:
            index = self.count
            self.variables.append((variable_name, index))

        return index


def generate_bytecode_for_integer_const(
        const: TIntegerConst,
        pool: ConstPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("INTEGER")
    class_index = pool.find_class(fq_class_name)
    methodref_index = pool.add_methodref(
        method_name="<init>",
        desc="(I)V",
        fq_class_name=fq_class_name)

    bytecode = [
        New(class_index),
        Dup(),
        Bipush(const.value),
        InvokeSpecial(methodref_index)
    ]

    return bytecode


def generate_bytecode_for_real_const(
        const: TRealConst,
        pool: ConstPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("REAL")
    class_index = pool.find_class(fq_class_name)
    methodref_idx = pool.add_methodref(
        method_name="<init>",
        desc="(F)V",
        fq_class_name=fq_class_name)

    index = pool.add_float(const.value)
    ldc = Ldc(index) if index < 256 else Ldc_w(index)

    bytecode = [
        New(class_index),
        Dup(),
        ldc,
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_bool_const(
        const: TBoolConst,
        pool: ConstPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("BOOLEAN")
    class_index = pool.find_class(fq_class_name)
    methodref_idx = pool.add_methodref(
        method_name="<init>",
        desc="(I)V",
        fq_class_name=fq_class_name)

    if const.value == 0:
        push_command = Iconst_i(0)
    elif const.value == 1:
        push_command = Iconst_i(1)
    else: assert False, f"Weird value for boolean const: {const.value}"

    bytecode = [
        New(class_index),
        Dup(),
        push_command,
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_string_const(
        const: TStringConst,
        pool: ConstPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("STRING")
    class_index = pool.find_class(fq_class_name)
    methodref_idx = pool.add_methodref(
        method_name="<init>",
        desc="(Ljava/lang/String;)V",
        fq_class_name=fq_class_name)
    
    index = pool.add_string(const.value)
    ldc = Ldc(index) if index < 256 else Ldc_w(index)
    bytecode = [
        New(class_index),
        Dup(),
        ldc,
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_character_const(
        const: TCharacterConst,
        pool: ConstPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("CHARACTER")
    class_index = pool.find_class(fq_class_name)
    methodref_idx = pool.add_methodref(
        method_name="<init>",
        desc="(Ljava/lang/String;)V",
        fq_class_name=fq_class_name)

    index = pool.find_string(const.value)
    ldc = Ldc(index) if index < 256 else Ldc_w(index)
    bytecode = [
        New(class_index),
        Dup(),
        ldc,
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_void_const() -> list[ByteCommand]:
    return [Aconst_null()]


def generate_bytecode_for_current_const() -> list[ByteCommand]:
    return [Aload(0)]


def generate_bytecode_for_create_expr(
        tcreate_expr: TCreateExpr,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    create_fq_class_name = add_package_prefix(tcreate_expr.expr_type.full_name)
    class_index = pool.find_class(create_fq_class_name)
    
    bytecode = [New(class_index), Dup(), Dup()]

    init_index = pool.add_methodref(
        method_name="<init>",
        desc="()V",
        fq_class_name=create_fq_class_name)
    bytecode.append(InvokeSpecial(init_index))

    for arg in tcreate_expr.arguments:
        arg_bytecode = generate_bytecode_for_expr(
            arg, fq_class_name, pool, local_table)
        bytecode.extend(arg_bytecode)

    constructor_index = pool.find_methodref(
        method_name=tcreate_expr.constructor_name,
        fq_class_name=add_package_prefix(ROOT_CLASS_NAME))
    bytecode.append(InvokeVirtual(constructor_index))

    return bytecode


def unpack_builtin_type(type_name: str, pool: ConstPool) -> list[ByteCommand]:
    match type_name:
        case "STRING":
            field_index = pool.add_fieldref(
                field_name="raw_string",
                desc="Ljava/lang/String;",
                fq_class_name=add_package_prefix(PLATFORM_CLASS_NAME))
        case "CHARACTER":
            field_index = pool.add_fieldref(
                field_name="raw_string",
                desc="Ljava/lang/String;",
                fq_class_name=add_package_prefix(PLATFORM_CLASS_NAME))
        case "INTEGER":
            field_index = pool.add_fieldref(
                field_name="raw_int",
                desc="I",
                fq_class_name=add_package_prefix(PLATFORM_CLASS_NAME))
        case "REAL":
            field_index = pool.add_fieldref(
                field_name="raw_float",
                desc="F",
                fq_class_name=add_package_prefix(PLATFORM_CLASS_NAME))
        case "BOOLEAN":
            field_index = pool.add_fieldref(
                field_name="raw_int",
                desc="I",
                fq_class_name=add_package_prefix(PLATFORM_CLASS_NAME))
        case _:
            field_index = -1

    if field_index == -1:
        return []
    return [GetField(field_index)]


def generate_bytecode_for_feature_call(
        tfeature_call: TFeatureCall,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []
    
    if tfeature_call.owner is None:
        this = [Aload(0)]
    else:
        this = generate_bytecode_for_expr(
                tfeature_call.owner,
                fq_class_name,
                pool,
                local_table)
    
    bytecode.extend(this)

    for arg in tfeature_call.arguments:
        arg_bytecode = generate_bytecode_for_expr(
            arg, fq_class_name, pool, local_table)
        bytecode.extend(arg_bytecode)

    if tfeature_call.owner is not None:
        fq_class_name = add_package_prefix(
            tfeature_call.owner.expr_type.full_name)
    methoref_idx = pool.find_methodref(
        tfeature_call.feature_name, add_package_prefix(ROOT_CLASS_NAME))
    bytecode.append(InvokeVirtual(methoref_idx))

    return bytecode


def generate_bytecode_for_field(
        tfield: TField,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []
    if tfield.owner is not None:
        fq_class_name = add_package_prefix(tfield.owner.expr_type.full_name)
        bytecode.extend(
            generate_bytecode_for_expr(
                tfield.owner,
                fq_class_name,
                pool,
                local_table))
    else:
        bytecode.append(Aload(0))
    field_index = pool.find_fieldref(tfield.name, fq_class_name)
    return [*bytecode, GetField(field_index)]


def generate_bytecode_for_variable(
        tvariable: TVariable,
        local_table: LocalTable) -> list[ByteCommand]:
    variable_index = local_table[tvariable.name]
    return [Aload(variable_index)]


def unpack_boolean(pool: ConstPool) -> list[ByteCommand]:
    return unpack_builtin_type("BOOLEAN", pool)


def pack_boolean(pool: ConstPool) -> list[ByteCommand]:
    return pack_builtin_type("BOOLEAN", pool)


def generate_bytecode_for_and(left: TExpr,
                              right: TExpr,
                              fq_class_name: str,
                              pool: ConstPool,
                              local_table: LocalTable) -> list[ByteCommand]:
    """
    Нестандартное логическое И без короткого замыкания.
    Вычисляем левый и правый операнды, затем перемножаем их (поскольку 1*1==1, а если хоть один 0, то 0).
    """
    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    bytecode.append(Imul())
    bytecode.extend(pack_boolean(pool))
    return bytecode


def generate_bytecode_for_or(left: TExpr,
                             right: TExpr,
                             fq_class_name: str,
                             pool: ConstPool,
                             local_table: LocalTable) -> list[ByteCommand]:
    """
    Нестандартное логическое ИЛИ без короткого замыкания.
    Вычисляются оба операнда, затем они складываются.
    После этого, если сумма > 0 – результат истина (1), иначе ложь (0).
    При этом выражения перед вычислениями распаковываются,
    а итоговый int (0 или 1) оборачивается в BOOLEAN.
    """
    bytecode = []
    # Вычисляем левый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    # Вычисляем правый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    # Складываем два int
    bytecode.append(Iadd())

    bytecode.append(Ifne(0))
    ifne_index = len(bytecode) - 1

    bytecode.append(Iconst_i(1))

    bytecode.append(Goto(0))
    goto_index = len(bytecode) - 1

    bytecode.append(Iconst_i(0))
    
    bytecode.append(Nop())

    bytecode[ifne_index] = Ifne(bytesize(bytecode[ifne_index:goto_index+1]))
    bytecode[goto_index] = Goto(bytesize(bytecode[goto_index:len(bytecode) - 1]))

    bytecode.extend(pack_boolean(pool))
    return bytecode


def generate_bytecode_for_and_then(left: TExpr,
                                   right: TExpr,
                                   fq_class_name: str,
                                   pool: ConstPool,
                                   local_table: LocalTable) -> list[ByteCommand]:
    """
    Логическое И с коротким замыканием.
    Если левый операнд равен 0 (ложь), то вычисление правого пропускается и результат – ложь.
    Иначе левый отбрасывается, и результатом становится значение правого операнда.
    Выражения распаковываются перед проверками, а итоговый результат оборачивается.
    """
    bytecode = []
    
    # Вычисляем левый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))

    bytecode.append(Ifeq(0))
    ifeq_index1 = len(bytecode) - 1

    # Вычисляем правый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))

    bytecode.append(Ifeq(0))
    ifeq_index2 = len(bytecode) - 1

    bytecode.append(Iconst_i(1))

    bytecode.append(Goto(0))
    goto_index = len(bytecode) - 1

    bytecode.append(Iconst_i(0))
    bytecode.append(Nop())

    bytecode[ifeq_index1] = Ifeq(bytesize(bytecode[ifeq_index1:goto_index+1]))
    bytecode[ifeq_index2] = Ifeq(bytesize(bytecode[ifeq_index2:goto_index+1]))
    bytecode[goto_index] = Goto(bytesize(bytecode[goto_index:len(bytecode)-1]))

    bytecode.extend(pack_boolean(pool))

    return bytecode


def generate_bytecode_for_or_else(left: TExpr, right: TExpr, fq_class_name: str,
                                  pool: ConstPool,
                                  local_table: LocalTable) -> list[ByteCommand]:
    """
    Логическое ИЛИ с коротким замыканием.
    Если левый операнд ненулевой (истина), то вычисление правого пропускается и результат – истина.
    Иначе левый отбрасывается, и результатом становится значение правого операнда.
    Выражения распаковываются перед проверками, а итоговый результат оборачивается.
    """
    bytecode = []
    
    # Вычисляем левый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))

    bytecode.append(Ifne(0))
    ifne_index1 = len(bytecode) - 1

    # Вычисляем правый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))

    bytecode.append(Ifne(0))
    ifne_index2 = len(bytecode) - 1

    bytecode.append(Iconst_i(0))

    bytecode.append(Goto(0))
    goto_index = len(bytecode) - 1

    bytecode.append(Iconst_i(1))
    bytecode.append(Nop())

    bytecode[ifne_index1] = Ifne(bytesize(bytecode[ifne_index1:goto_index+1]))
    bytecode[ifne_index2] = Ifne(bytesize(bytecode[ifne_index2:goto_index+1]))
    bytecode[goto_index] = Goto(bytesize(bytecode[goto_index:len(bytecode)-1]))

    bytecode.extend(pack_boolean(pool))

    return bytecode


def generate_bytecode_for_not(
        texpr: TExpr,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []
    
    # Вычисляем левый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(
        texpr, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))

    bytecode.append(Ifeq(0))
    ifeq_index = len(bytecode) - 1

    bytecode.append(Iconst_i(0))

    bytecode.append(Goto(0))
    goto_index = len(bytecode) - 1

    bytecode.append(Iconst_i(1))
    bytecode.append(Nop())

    bytecode[ifeq_index] = Ifeq(bytesize(bytecode[ifeq_index:goto_index+1]))
    bytecode[goto_index] = Goto(bytesize(bytecode[goto_index:len(bytecode)-1]))

    bytecode.extend(pack_boolean(pool))
    
    return bytecode


def generate_bytecode_for_expr(
        texpr: TExpr,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    match texpr:
        case TIntegerConst():
            return generate_bytecode_for_integer_const(texpr, pool)
        case TRealConst():
            return generate_bytecode_for_real_const(texpr, pool)
        case TBoolConst():
            return generate_bytecode_for_bool_const(texpr, pool)
        case TCharacterConst():
            return generate_bytecode_for_character_const(texpr, pool)
        case TStringConst():
            return generate_bytecode_for_string_const(texpr, pool)
        case TVoidConst():
            return generate_bytecode_for_void_const()
        case TStringConst():
            return generate_bytecode_for_void_const(texpr)
        case TCreateExpr():
            return generate_bytecode_for_create_expr(
                texpr, fq_class_name, pool, local_table)
        case TFeatureCall():
            return generate_bytecode_for_feature_call(
                texpr, fq_class_name, pool, local_table)
        case TField():
            return generate_bytecode_for_field(
                texpr, fq_class_name, pool, local_table)
        case TVariable():
            return generate_bytecode_for_variable(texpr, local_table)
        case TCurrent():
            return generate_bytecode_for_current_const()
        case TBinaryOp(
                operator_name=operator_name,
                left=left,
                right=right):
            match operator_name:
                case "and":
                    return generate_bytecode_for_and(
                        left, right, fq_class_name, pool, local_table)
                case "or":
                    return generate_bytecode_for_or(
                        left, right, fq_class_name, pool, local_table)
                case "and then":
                    return generate_bytecode_for_and_then(
                        left, right, fq_class_name, pool, local_table)
                case "or else":
                    return generate_bytecode_for_or_else(
                        left, right, fq_class_name, pool, local_table)
                case _:
                    raise NotImplementedError(operator_name)
        case TUnaryOp(
                operator_name=operator_name,
                argument=argument):
            match operator_name:
                case "not":
                    return generate_bytecode_for_not(
                        argument, fq_class_name, pool, local_table);
                case _:
                    raise NotImplementedError(operator_name)
        case _:
            raise NotImplementedError(texpr)


def generate_bytecode_for_assignment(
        tassignment: TAssignment,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    lvalue = tassignment.lvalue
    rvalue = tassignment.rvalue

    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(rvalue, fq_class_name, pool, local_table))

    match lvalue:
        case TField(name=field_name):
            field_index = pool.find_fieldref(field_name, fq_class_name)
            bytecode.insert(0, Aload(0))
            bytecode.append(PutField(field_index))
        case TVariable(name=variable_name):
            variable_index = local_table[variable_name]
            bytecode.append(Astore(variable_index))

    return bytecode


def bytesize(commands: list[ByteCommand]) -> int:
    return sum(command.size() for command in commands)


def generate_bytecode_for_ifstmt(
        tifstmt: TIfStmt,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []

    ifeqs = []
    gotos = []

    bytecode.extend(
        generate_bytecode_for_expr(
            tifstmt.condition, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))

    bytecode.append(Ifeq(0))
    ifeqs.append(len(bytecode) - 1)
    
    bytecode.extend(
        generate_bytecode_for_stmts(
            tifstmt.then_branch, fq_class_name, pool, local_table))
    bytecode.append(Goto(0))
    gotos.append(len(bytecode) - 1)

    for (condition, branch) in tifstmt.elseif_branches:
        bytecode.extend(
            generate_bytecode_for_expr(
                condition, fq_class_name, pool, local_table))
        bytecode.append(Ifeq(0))
        ifeqs.append(len(bytecode) - 1)

        bytecode.extend(
            generate_bytecode_for_stmts(
                branch, fq_class_name, pool, local_table))
        bytecode.append(Goto(0))
        gotos.append(len(bytecode) - 1)

    if tifstmt.else_branch:
        bytecode.extend(
            generate_bytecode_for_stmts(
                tifstmt.else_branch, fq_class_name, pool, local_table))
        
    bytecode.append(Nop())

    assert len(ifeqs) == len(gotos)
    for ifeq, goto in zip(ifeqs, gotos):
        ifeq_offset = bytesize(bytecode[ifeq:goto+1])
        bytecode[ifeq] = Ifeq(ifeq_offset)
        goto_offset = bytesize(bytecode[goto:len(bytecode)-1])
        bytecode[goto] = Goto(goto_offset)

    return bytecode


def generate_bytecode_for_loop(
        tloop: TLoopStmt,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []

    bytecode.extend(
        generate_bytecode_for_stmts(
            tloop.init_stmts, fq_class_name, pool, local_table))

    bytecode.extend(
        generate_bytecode_for_expr(
            tloop.until_cond, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    bytecode.append(Ifne(0))
    ifnes1_index = len(bytecode) - 1

    loop_start_index = len(bytecode)
    bytecode.extend(
        generate_bytecode_for_stmts(
            tloop.body, fq_class_name, pool, local_table))
    
    bytecode.extend(
        generate_bytecode_for_expr(
            tloop.until_cond, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    bytecode.append(Ifne(0))
    ifnes2_index = len(bytecode) - 1
    
    bytecode.append(Goto(0))
    goto_index = len(bytecode) - 1

    bytecode.append(Nop())

    bytecode[ifnes1_index] = Ifne(
        bytesize(bytecode[ifnes1_index:goto_index+1]))
    bytecode[ifnes2_index] = Ifne(
        bytesize(bytecode[ifnes2_index:goto_index+1]))
    
    bytecode[goto_index] = Goto(
        -bytesize(bytecode[loop_start_index:goto_index]))
    
    return bytecode


def generate_bytecode_for_routine_call(
        troutine_call: TRoutineCall,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    tfeature_call = troutine_call.feature_call
    bytecode = generate_bytecode_for_feature_call(
        tfeature_call, fq_class_name, pool, local_table)
    if tfeature_call.expr_type.full_name != "<VOID>":
        bytecode.append(Pop())
    return bytecode


def generate_bytecode_for_stmt(
        tstmt: TStatement,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    match tstmt:
        case TAssignment():
            return generate_bytecode_for_assignment(
                tstmt, fq_class_name, pool, local_table)
        case TRoutineCall():
            return generate_bytecode_for_routine_call(
                tstmt, fq_class_name, pool, local_table)
        case TIfStmt():
            return generate_bytecode_for_ifstmt(
                tstmt, fq_class_name, pool, local_table)
        case TLoopStmt():
            return generate_bytecode_for_loop(
                tstmt, fq_class_name, pool, local_table)
        case _: assert False


def generate_bytecode_for_stmts(
        tstmts: list[TStatement],
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []

    for tstmt in tstmts:
        bytecode.extend(
            generate_bytecode_for_stmt(
                tstmt, fq_class_name, pool, local_table))
        
    return bytecode


def pack_builtin_type(type_name: str, pool: ConstPool) -> list[ByteCommand]:
    this = f"L{add_package_prefix(PLATFORM_CLASS_NAME)};"
    desc_mapping = {
        "STRING": f"(Ljava/lang/String;)V",
        "CHARACTER": f"(Ljava/lang/String;)V",
        "INTEGER": f"(I)V",
        "REAL": f"(F)V",
        "BOOLEAN": f"(I)V"
    }

    fq_class_name = add_package_prefix(type_name)
    class_index = pool.find_class(fq_class_name)
    methodref_idx = pool.add_methodref(
        method_name="<init>",
        desc=desc_mapping[type_name],
        fq_class_name=fq_class_name)

    bytecode = [
        New(class_index),
        Dupx1(),
        Swap(),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_method(
        method: TMethod,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable)-> list[ByteCommand]:
    bytecode = []

    match method:
        case TUserDefinedMethod(
                body=body, return_type=return_type, variables=variables):
            for vname, vtype in variables:
                bytecode.extend(
                    generate_bytecode_for_assignment(
                        TAssignment(
                            lvalue=TVariable(vtype, vname),
                            rvalue=default_value_for(vtype)),
                        fq_class_name=fq_class_name,
                        pool=pool,
                        local_table=local_table))

            bytecode.extend(
                generate_bytecode_for_stmts(
                    body,
                    fq_class_name,
                    pool,
                    local_table))
        case TExternalMethod(
                parameters=parameters,
                return_type=return_type,
                alias=alias):
            bytecode.append(Aload(0))
            
            for pname, ptype in parameters:
                bytecode.append(Aload(local_table[pname]))
                if ptype.full_name in ["STRING", "INTEGER", "BOOLEAN", "CHARACTER", "REAL"]:
                    bytecode.extend(
                        unpack_builtin_type(ptype.full_name, pool))

            parts = split_package_path(alias)
            # 1. Получить имя и класс static метода
            #    Тут нет проверок на корректность задания alias,
            #    это должно проверяться на этапе заполнения таблицы констант
            ext_method_name = parts[-1]
            ext_fq_class_name = make_fully_qualifed_name(parts[:-1])
            # 2. Сгенерировать вызов invokestatic
            methodref_index = pool.find_methodref(
                ext_method_name, fq_class_name=ext_fq_class_name)
            bytecode.append(InvokeStatic(methodref_index))
    
    return_type = method.return_type
    is_function = return_type.full_name != "<VOID>"
    if is_function:
        if isinstance(method, TExternalMethod):
            # 3. Взависимости от возвращаемого значения метода,
            #    произвести соотвествующую "распаковку" и "упаковку"
            #    в зависимости от типа возвращаемого значения
            if return_type.full_name != "<VOID>":
                match return_type.full_name:
                    case "STRING":
                        bytecode.extend(pack_builtin_type("STRING", pool))
                    case "CHARACTER":
                        bytecode.extend(pack_builtin_type("CHARACTER", pool))
                    case "INTEGER":
                        bytecode.extend(pack_builtin_type("INTEGER", pool))
                    case "REAL":
                        bytecode.extend(pack_builtin_type("REAL", pool))
                    case "BOOLEAN":
                        bytecode.extend(pack_builtin_type("BOOLEAN", pool))
        else:
            bytecode.append(Aload(local_table["local_Result"]))
        bytecode.append(Areturn())
    else:
        bytecode.append(Return())

    return bytecode

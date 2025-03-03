from serpent.semantic_checker.type_check import *

from serpent.codegen.constpool import (
    ConstPool,
    add_package_prefix,
    PLATFORM_CLASS_NAME)
from serpent.codegen.bytecommand import *


@dataclass(frozen=True)
class LocalTable:
    variables: list[tuple[str, int]] = field(default_factory=list)

    @property
    def count(self) -> int:
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

    bytecode = [
        New(class_index),
        Dup(),
        Bipush(const.value),
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
    
    string_index = pool.find_string(const.value)
    bytecode = [
        New(class_index),
        Dup(),
        Ldc(string_index),
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

    string_index = pool.find_string(const.value)
    bytecode = [
        New(class_index),
        Dup(),
        Ldc(string_index),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_void_const() -> list[ByteCommand]:
    return [Aconst_null()]


def generate_bytecode_for_create_expr(
        tcreate_expr: TCreateExpr,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    create_fq_class_name = add_package_prefix(tcreate_expr.expr_type.full_name)
    class_index = pool.find_class(create_fq_class_name)
    
    bytecode = [New(class_index), Dup()]

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
        fq_class_name=create_fq_class_name)
    bytecode.append(InvokeVirtual(constructor_index))

    return bytecode


def generate_bytecode_for_feature_call(
        tfeature_call: TFeatureCall,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []
    
    if tfeature_call.owner is None:
        bytecode.append(Aload(0))
    else:
        bytecode.extend(
            generate_bytecode_for_expr(
                tfeature_call.owner,
                fq_class_name,
                pool,
                local_table))

    for arg in tfeature_call.arguments:
        arg_bytecode = generate_bytecode_for_expr(
            arg, fq_class_name, pool, local_table)
        bytecode.extend(arg_bytecode)

    if tfeature_call.owner is not None:
        fq_class_name = add_package_prefix(tfeature_call.owner.expr_type.full_name)
    methoref_idx = pool.find_methodref(tfeature_call.feature_name, fq_class_name)
        
    bytecode.append(InvokeVirtual(methoref_idx))
    return bytecode


def generate_bytecode_for_field(
        tfield: TField,
        fq_class_name: str,
        pool: ConstPool) -> list[ByteCommand]:
    field_index = pool.find_fieldref(tfield.name, fq_class_name)
    return [GetField(field_index)]


def generate_bytecode_for_variable(
        tvariable: TVariable,
        local_table: LocalTable) -> list[ByteCommand]:
    variable_index = local_table[tvariable.name]
    return [Aload(variable_index)]


def unpack_boolean(pool: ConstPool) -> list[ByteCommand]:
    field_index = pool.add_fieldref(
        field_name="raw_int",
        desc="I",
        fq_class_name=add_package_prefix(PLATFORM_CLASS_NAME))
    return [GetField(field_index)]


def pack_boolean(pool: ConstPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("BOOLEAN")
    class_index = pool.find_class(fq_class_name)
    methodref_idx = pool.add_methodref(
        method_name="<init>",
        desc="(I)V",
        fq_class_name=fq_class_name)

    bytecode = [
        New(class_index),
        Dupx1(),
        Swap(),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


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
    
    # Ветвящаяся последовательность:
    # 1. Dup – дублируем сумму
    # 2. Ifgt (placeholder): если значение > 0, переходим к ветке, где будет Bipush(1)
    # 3. Pop – удаляем оставшуюся копию суммы
    # 4. Bipush(0) – результат false
    # 5. Goto (placeholder) – переход к завершению
    # 6. Bipush(1) – ветка, возвращающая true
    bytecode.append(Dup())
    index_ifgt = len(bytecode)
    bytecode.append(Ifgt(0))  # placeholder
    bytecode.append(Pop())
    index_false = len(bytecode)
    bytecode.append(Bipush(0))
    index_goto = len(bytecode)
    bytecode.append(Goto(0))  # placeholder
    index_true = len(bytecode)
    bytecode.append(Bipush(1))
    # Патчинг переходов (вычисление смещений)
    positions = []
    current_offset = 0
    for instr in bytecode:
        positions.append(current_offset)
        current_offset += instr.size()
    total_size = current_offset
    # Патчим Ifgt: цель – инструкция Bipush(1) (индекс index_true)
    target_offset = positions[index_true]
    current_instr_offset = positions[index_ifgt]
    jump_instr_size = bytecode[index_ifgt].size()
    relative_offset = target_offset - (current_instr_offset + jump_instr_size)
    bytecode[index_ifgt] = Ifgt(relative_offset)
    # Патчим Goto: цель – конец ветвящейся последовательности (total_size)
    current_instr_offset = positions[index_goto]
    jump_instr_size = bytecode[index_goto].size()
    relative_offset = total_size - (current_instr_offset + jump_instr_size)
    bytecode[index_goto] = Goto(relative_offset)
    
    # Итоговый результат – int (0 или 1). Оборачиваем его в BOOLEAN.
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
    bytecode.append(Dup())
    index_ifeq = len(bytecode)
    bytecode.append(Ifeq(0))  # placeholder
    bytecode.append(Pop())
    # Вычисляем правый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    index_goto = len(bytecode)
    bytecode.append(Goto(0))  # placeholder
    label_false_index = len(bytecode)
    bytecode.append(Bipush(0))
    end_index = len(bytecode)
    # Патчинг переходов
    positions = []
    current_offset = 0
    for instr in bytecode:
        positions.append(current_offset)
        current_offset += instr.size()
    # Патчим Ifeq: цель – переход к метке L_false (label_false_index)
    target_offset = positions[label_false_index]
    current_instr_offset = positions[index_ifeq]
    jump_instr_size = bytecode[index_ifeq].size()
    relative_offset = target_offset - (current_instr_offset + jump_instr_size)
    bytecode[index_ifeq] = Ifeq(relative_offset)
    # Патчим Goto: цель – конец блока (end_index)
    target_offset = positions[end_index]
    current_instr_offset = positions[index_goto]
    jump_instr_size = bytecode[index_goto].size()
    relative_offset = target_offset - (current_instr_offset + jump_instr_size)
    bytecode[index_goto] = Goto(relative_offset)
    
    # Результат – int, оборачиваем его в BOOLEAN.
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
    bytecode.append(Dup())
    index_ifne = len(bytecode)
    bytecode.append(Ifne(0))  # placeholder
    bytecode.append(Pop())
    # Вычисляем правый операнд и распаковываем
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, pool, local_table))
    bytecode.extend(unpack_boolean(pool))
    index_goto = len(bytecode)
    bytecode.append(Goto(0))  # placeholder
    label_true_index = len(bytecode)
    bytecode.append(Bipush(1))
    end_index = len(bytecode)
    # Патчинг переходов
    positions = []
    current_offset = 0
    for instr in bytecode:
        positions.append(current_offset)
        current_offset += instr.size()
    # Патчим Ifne: цель – переход к метке L_true (label_true_index)
    target_offset = positions[label_true_index]
    current_instr_offset = positions[index_ifne]
    jump_instr_size = bytecode[index_ifne].size()
    relative_offset = target_offset - (current_instr_offset + jump_instr_size)
    bytecode[index_ifne] = Ifne(relative_offset)
    # Патчим Goto: цель – конец блока (end_index)
    target_offset = positions[end_index]
    current_instr_offset = positions[index_goto]
    jump_instr_size = bytecode[index_goto].size()
    relative_offset = target_offset - (current_instr_offset + jump_instr_size)
    bytecode[index_goto] = Goto(relative_offset)
    
    # Результат – int, его нужно обернуть в BOOLEAN.
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
        case TStringConst():
            return generate_bytecode_for_void_const(texpr)
        case TCreateExpr():
            return generate_bytecode_for_create_expr(
                texpr, fq_class_name, pool, local_table)
        case TFeatureCall():
            return generate_bytecode_for_feature_call(
                texpr, fq_class_name, pool, local_table)
        case TField():
            return generate_bytecode_for_field(texpr, fq_class_name, pool)
        case TVariable():
            return generate_bytecode_for_variable(texpr, local_table)
        case _:
            raise NotImplementedError


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
    """
    Генерирует байт-код для цикла until.

    Структура TLoopStmt:
      - init_stmts: инструкции инициализации (выполняются один раз до входа в цикл)
      - until_cond: условие завершения цикла; цикл повторяется, пока условие ложно
      - body: инструкции, повторяющиеся в цикле

    Алгоритм:
      1. Выполнить инициализацию (init_stmts).
      2. Отметить начало цикла (loop_start).
      3. Выполнить тело цикла (body).
      4. Вычислить условие until_cond.
      5. Если until_cond == 0 (ложь), с помощью инструкции Ifeq перейти к началу цикла.
         Если условие истинно, выполнение продолжается после цикла.
    """
    instrs = []
    
    # Генерируем код для инициализационных инструкций
    for init_stmt in tloop.init_stmts:
        init_code = generate_bytecode_for_stmt(init_stmt, fq_class_name, pool, local_table)
        instrs.extend(init_code)
    
    # Отмечаем начало цикла
    loop_start_index = len(instrs)
    
    # Генерируем код для тела цикла
    for stmt in tloop.body:
        body_code = generate_bytecode_for_stmt(stmt, fq_class_name, pool, local_table)
        instrs.extend(body_code)
    
    # Генерируем код для вычисления условия until
    cond_code = generate_bytecode_for_expr(tloop.until_cond, fq_class_name, pool, local_table)
    cond_code.extend(unpack_boolean(pool))
    instrs.extend(cond_code)
    
    # Добавляем инструкцию Ifeq с placeholder-смещением.
    # Если значение условия (на вершине стека) равно 0, переходим к началу цикла.
    patch_index = len(instrs)
    instrs.append(Ifeq(0))  # placeholder для смещения
    
    # Второй проход: вычисляем байтовые позиции каждой инструкции для патчинга перехода.
    positions = []
    current_offset = 0
    for instr in instrs:
        positions.append(current_offset)
        current_offset += instr.size()
    
    # Целевая позиция – начало цикла (loop_start_index)
    target_offset = positions[loop_start_index]
    current_instr_offset = positions[patch_index]
    jump_instr_size = instrs[patch_index].size()
    relative_offset = target_offset - (current_instr_offset + jump_instr_size)
    
    # Обновляем инструкцию перехода с корректным относительным смещением.
    instrs[patch_index] = Ifeq(relative_offset)
    
    return instrs


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


def generate_bytecode_for_method(
        method: TMethod,
        fq_class_name: str,
        pool: ConstPool,
        local_table: LocalTable)-> list[ByteCommand]:
    bytecode = []

    if isinstance(method, TUserDefinedMethod):
        bytecode.extend(
            generate_bytecode_for_stmts(
                method.body,
                fq_class_name,
                pool,
                local_table))

        is_function = method.return_type.full_name != "<VOID>"
        if is_function:
            bytecode.append(Aload(local_table["local_Result"]))
            bytecode.append(Areturn())
        else:
            bytecode.append(Return())
    else:
        ...
    
    return bytecode

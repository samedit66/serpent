from serpent.semantic_checker.type_check import *

from serpent.codegen.constant_pool import (
    ConstantPool,
    add_package_prefix,
    get_type_descriptor)
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


def bytecode_size(bytecode: list[ByteCommand]) -> int:
    return sum(bc.size() for bc in bytecode)


def generate_bytecode_for_integer_const(
        const: TIntegerConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("INTEGER")
    integer_class_idx = constant_pool.add_constant_class(fq_class_name)
    methodref_idx = constant_pool.add_methodref(
        fq_class_name,
        method_name="<init>",
        method_desc="(I)V")

    bytecode = [
        New(integer_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_real_const(
        const: TRealConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("REAL")
    real_class_idx = constant_pool.add_constant_class(fq_class_name)
    methodref_idx = constant_pool.add_methodref(
        fq_class_name,
        method_name="<init>",
        method_desc="(F)V")

    bytecode = [
        New(real_class_idx),
        Bipush(const.value),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_bool_const(
        const: TBoolConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("BOOLEAN")
    bool_class_idx = constant_pool.add_constant_class(fq_class_name)
    methodref_idx = constant_pool.add_methodref(
        fq_class_name,
        method_name="<init>",
        method_desc="(I)V")

    bytecode = [
        New(bool_class_idx),
        Bipush(int(const.value)),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_string_const(
        const: TStringConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("STRING")
    string_class_idx = constant_pool.add_constant_class(fq_class_name)
    methodref_idx = constant_pool.add_methodref(
        fq_class_name,
        method_name="<init>",
        method_desc="(Ljava/lang/String;)V")

    string_index = constant_pool.find_constant_string_index(const.value)
    assert string_index != -1

    bytecode = [
        New(string_class_idx),
        Ldc(string_index),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_character_const(
        const: TCharacterConst,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    fq_class_name = add_package_prefix("CHARACTER")
    char_class_idx = constant_pool.add_constant_class(fq_class_name)
    methodref_idx = constant_pool.add_methodref(
        fq_class_name,
        method_name="<init>",
        method_desc="(Ljava/lang/String;)V")

    string_index = constant_pool.find_constant_string_index(const.value)
    assert string_index != -1

    bytecode = [
        New(char_class_idx),
        Ldc(string_index),
        InvokeSpecial(methodref_idx)
    ]

    return bytecode


def generate_bytecode_for_void_const() -> list[ByteCommand]:
    return [Aconst_null()]


def generate_bytecode_for_create_expr(
        tcreate_expr: TCreateExpr,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    create_fq_class_name = add_package_prefix(tcreate_expr.expr_type.full_name)
    class_index = constant_pool.add_constant_class(create_fq_class_name)
    
    bytecode = [
        New(class_index),
        Dup()
    ]

    init_idx = constant_pool.add_methodref(
        fq_class_name=create_fq_class_name,
        method_name="<init>",
        method_desc="()V")
    bytecode.extend(
        [InvokeSpecial(init_idx), Dup()])

    for arg in tcreate_expr.arguments:
        arg_bytecode = generate_bytecode_for_expr(arg, fq_class_name, constant_pool, local_table)
        bytecode.extend(arg_bytecode)

    constructor_desc = "".join(get_type_descriptor(arg.expr_type) for arg in tcreate_expr.arguments)
    constructor_idx = constant_pool.add_methodref(
        fq_class_name=create_fq_class_name,
        method_name=tcreate_expr.constructor_name,
        method_desc=f"({constructor_desc})V")
    bytecode.append(InvokeVirtual(constructor_idx))

    return bytecode


def generate_bytecode_for_feature_call(
        tfeature_call: TFeatureCall,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []
    
    if tfeature_call.owner is None:
        bytecode.append(Aload(0))
    else:
        bytecode.extend(
            generate_bytecode_for_expr(
                tfeature_call.owner,
                fq_class_name,
                constant_pool,
                local_table))

    for arg in tfeature_call.arguments:
        arg_bytecode = generate_bytecode_for_expr(
            arg, fq_class_name, constant_pool, local_table)
        bytecode.extend(arg_bytecode)

    if tfeature_call.owner is None:
        methoref_idx = constant_pool.find_constant_methodref(
            fq_class_name, tfeature_call.feature_name)
    else:
        owner_fq_class_name = add_package_prefix(tfeature_call.owner.expr_type.full_name)
        methoref_idx = constant_pool.find_constant_methodref(
            owner_fq_class_name, tfeature_call.feature_name)
        
    assert methoref_idx != -1
    bytecode.append(InvokeVirtual(methoref_idx))

    return bytecode


def generate_bytecode_for_field(
        tfield: TField,
        fq_class_name: str,
        constant_pool: ConstantPool) -> list[ByteCommand]:
    field_index = constant_pool.add_field(fq_class_name, tfield)
    return [GetField(field_index)]


def generate_bytecode_for_variable(
        tvariable: TVariable,
        local_table: LocalTable) -> list[ByteCommand]:
    variable_index = local_table[tvariable.name]
    return [Aload(variable_index)]


def generate_bytecode_for_and(left: TExpr, right: TExpr, fq_class_name: str,
                              constant_pool: ConstantPool,
                              local_table: LocalTable) -> list[ByteCommand]:
    """
    Нестандартное логическое И без короткого замыкания.
    Вычисляем левый и правый операнды, затем перемножаем их (поскольку 1*1==1, а если хоть один 0, то 0).
    """
    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, constant_pool, local_table))
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, constant_pool, local_table))
    bytecode.append(Imul())
    return bytecode


def generate_bytecode_for_or(left: TExpr, right: TExpr, fq_class_name: str,
                             constant_pool: ConstantPool,
                             local_table: LocalTable) -> list[ByteCommand]:
    """
    Нестандартное логическое ИЛИ без короткого замыкания.
    Вычисляются оба операнда, затем они складываются.
    После этого, если сумма > 0 – результат истина (1), иначе ложь (0).
    Для этого формируется ветвящаяся последовательность, которая патчится после вычисления байтовых позиций.
    """
    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, constant_pool, local_table))
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, constant_pool, local_table))
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
    # Патчинг переходов
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
    return bytecode


def generate_bytecode_for_and_then(left: TExpr, right: TExpr, fq_class_name: str,
                                   constant_pool: ConstantPool,
                                   local_table: LocalTable) -> list[ByteCommand]:
    """
    Логическое И с коротким замыканием.
    Если левый операнд равен 0 (ложь), то вычисление правого пропускается и результат – ложь.
    Иначе левый отбрасывается, и результатом становится значение правого операнда.
    
    Структура:
      - Вычисляем left
      - Dup
      - Ifeq (placeholder) – если left == 0, переход к метке L_false
      - Pop – отбрасываем left (она равна истине)
      - Вычисляем right
      - Goto (placeholder) – переход к завершению (L_end)
      - L_false: Bipush(0)
      - L_end:
    """
    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, constant_pool, local_table))
    bytecode.append(Dup())
    index_ifeq = len(bytecode)
    bytecode.append(Ifeq(0))  # placeholder
    bytecode.append(Pop())
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, constant_pool, local_table))
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
    total_size = current_offset
    # Патчим Ifeq: цель – метка L_false (label_false_index)
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
    return bytecode


def generate_bytecode_for_or_else(left: TExpr, right: TExpr, fq_class_name: str,
                                  constant_pool: ConstantPool,
                                  local_table: LocalTable) -> list[ByteCommand]:
    """
    Логическое ИЛИ с коротким замыканием.
    Если левый операнд ненулевой (истина), то вычисление правого пропускается и результат – истина.
    Иначе левый отбрасывается, и результатом становится значение правого операнда.
    
    Структура:
      - Вычисляем left
      - Dup
      - Ifne (placeholder) – если left != 0, переход к метке L_true
      - Pop – отбрасываем left (она ложна)
      - Вычисляем right
      - Goto (placeholder) – переход к завершению (L_end)
      - L_true: Bipush(1)
      - L_end:
    """
    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(left, fq_class_name, constant_pool, local_table))
    bytecode.append(Dup())
    index_ifne = len(bytecode)
    bytecode.append(Ifne(0))  # placeholder
    bytecode.append(Pop())
    bytecode.extend(generate_bytecode_for_expr(right, fq_class_name, constant_pool, local_table))
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
    total_size = current_offset
    # Патчим Ifne: цель – метка L_true (label_true_index)
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
    return bytecode


def generate_bytecode_for_expr(
        texpr: TExpr,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    match texpr:
        case TIntegerConst():
            return generate_bytecode_for_integer_const(texpr, constant_pool)
        case TRealConst():
            return generate_bytecode_for_real_const(texpr, constant_pool)
        case TBoolConst():
            return generate_bytecode_for_bool_const(texpr, constant_pool)
        case TCharacterConst():
            return generate_bytecode_for_character_const(texpr, constant_pool)
        case TStringConst():
            return generate_bytecode_for_string_const(texpr, constant_pool)
        case TStringConst():
            return generate_bytecode_for_void_const(texpr)
        case TCreateExpr():
            return generate_bytecode_for_create_expr(
                texpr, fq_class_name, constant_pool, local_table)
        case TFeatureCall():
            return generate_bytecode_for_feature_call(
                texpr, fq_class_name, constant_pool, local_table)
        case TField():
            return generate_bytecode_for_field(texpr, fq_class_name, constant_pool)
        case TVariable():
            return generate_bytecode_for_variable(texpr, local_table)
        case _:
            raise NotImplementedError


def generate_bytecode_for_assignment(
        tassignment: TAssignment,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    lvalue = tassignment.lvalue
    rvalue = tassignment.rvalue

    bytecode = []
    bytecode.extend(generate_bytecode_for_expr(lvalue, fq_class_name, constant_pool, local_table))
    bytecode.extend(generate_bytecode_for_expr(rvalue, fq_class_name, constant_pool, local_table))

    match lvalue:
        case TField() as tfield:
            field_index = constant_pool.add_field(fq_class_name, tfield)
            bytecode.append(PutField(field_index))
        case TVariable() as tvariable:
            variable_index = local_table[tvariable.name]
            bytecode.append(Astore(variable_index))

    return bytecode


def generate_bytecode_for_ifstmt(
        tifstmt: TIfStmt,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    """
    Генерирует последовательность байт-кодов для оператора if.
    Структура TIfStmt предполагает наличие:
      - основного условия и then-ветки,
      - списка elseif-веток в виде пар (условие, список инструкций),
      - ветки else (список инструкций).
    
    Алгоритм:
      1. Для каждой условной ветки (if и elseif):
         - генерируется код для вычисления условия;
         - вставляется инструкция Ifeq с отложенным смещением,
           которое в случае ложного условия переходит к следующей ветке.
      2. Для каждой ветки генерируется код для набора инструкций тела.
      3. Для всех веток, кроме последней, в конец добавляется инструкция Goto,
         чтобы при выполнении выбранной ветки перейти к завершению конструкции.
      4. После формирования полной последовательности производится второй проход,
         где вычисляются байтовые позиции и исправляются смещения в переходах.
    """
    # Формируем список веток: каждая ветка представлена кортежем
    # (тип_ветки, условие, список_инструкций)
    branches = []
    # Основная ветка if
    branches.append(('if', tifstmt.condition, tifstmt.then_branch))
    # elseif-ветки
    for cond, stmts in tifstmt.elseif_branches:
        branches.append(('elseif', cond, stmts))
    # Ветка else
    branches.append(('else', None, tifstmt.else_branch))
    
    n = len(branches)
    instrs = []  # итоговый список байт-команд
    # branch_start_instr_index[i] – индекс в списке instrs, с которого начинается тело i-ой ветки
    branch_start_instr_index = []
    # Списки для фиксации мест, где необходимо патчить инструкции переходов
    patch_cond = []  # для условных переходов (Ifeq)
    patch_goto = []  # для безусловных переходов (Goto)
    
    for i, (branch_type, cond, stmts) in enumerate(branches):
        if branch_type in ('if', 'elseif'):
            # Генерируем код для вычисления условия
            cond_code = generate_bytecode_for_expr(cond, fq_class_name, constant_pool, local_table)
            instrs.extend(cond_code)
            # Вставляем условный переход: если условие ложно, перейти к следующей ветке
            cond_jump_index = len(instrs)
            instrs.append(Ifeq(0))  # смещение пока placeholder
            patch_cond.append(cond_jump_index)
            # Тело ветки начнётся после условного перехода
            branch_start_instr_index.append(len(instrs))
        else:
            # Для ветки else условие отсутствует – тело начинается сразу
            branch_start_instr_index.append(len(instrs))
        
        # Генерируем код для инструкций тела ветки
        for stmt in stmts:
            stmt_code = generate_bytecode_for_stmt(stmt, fq_class_name, constant_pool, local_table)
            instrs.extend(stmt_code)
        
        # Для всех веток, кроме последней, добавляем безусловный переход к концу конструкции
        if i < n - 1:
            goto_index = len(instrs)
            instrs.append(Goto(0))  # placeholder
            patch_goto.append(goto_index)
    
    # Первый проход: вычисляем байтовые смещения для каждой инструкции
    positions = []
    current_offset = 0
    for instr in instrs:
        positions.append(current_offset)
        current_offset += instr.size()
    total_size = current_offset  # общий размер блока if в байтах
    
    # Патчим условные переходы: для каждой условной ветки смещение должно указывать
    # на начало тела следующей ветки (то есть branch_start_instr_index[i+1])
    for i, cond_jump_index in enumerate(patch_cond):
        target_instr_index = branch_start_instr_index[i + 1]
        target_byte_offset = positions[target_instr_index]
        current_instr_offset = positions[cond_jump_index]
        jump_instr_size = instrs[cond_jump_index].size()
        relative_offset = target_byte_offset - (current_instr_offset + jump_instr_size)
        instrs[cond_jump_index] = Ifeq(relative_offset)
    
    # Патчим безусловные переходы: они должны переводить выполнение в конец блока if
    for goto_index in patch_goto:
        current_instr_offset = positions[goto_index]
        jump_instr_size = instrs[goto_index].size()
        relative_offset = total_size - (current_instr_offset + jump_instr_size)
        instrs[goto_index] = Goto(relative_offset)
    
    return instrs


def generate_bytecode_for_loop(
        tloop: TLoopStmt,
        fq_class_name: str,
        constant_pool: ConstantPool,
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
        init_code = generate_bytecode_for_stmt(init_stmt, fq_class_name, constant_pool, local_table)
        instrs.extend(init_code)
    
    # Отмечаем начало цикла
    loop_start_index = len(instrs)
    
    # Генерируем код для тела цикла
    for stmt in tloop.body:
        body_code = generate_bytecode_for_stmt(stmt, fq_class_name, constant_pool, local_table)
        instrs.extend(body_code)
    
    # Генерируем код для вычисления условия until
    cond_code = generate_bytecode_for_expr(tloop.until_cond, fq_class_name, constant_pool, local_table)
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
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    tfeature_call = troutine_call.feature_call
    bytecode = generate_bytecode_for_feature_call(
        tfeature_call, fq_class_name, constant_pool, local_table)
    if tfeature_call.expr_type.full_name != "<VOID>":
        bytecode.append(Pop())
    return bytecode


def generate_bytecode_for_stmt(
        tstmt: TStatement,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    match tstmt:
        case TAssignment():
            return generate_bytecode_for_assignment(
                tstmt, fq_class_name, constant_pool, local_table)
        case TRoutineCall():
            return generate_bytecode_for_routine_call(
                tstmt, fq_class_name, constant_pool, local_table)
        case TIfStmt():
            return generate_bytecode_for_ifstmt(
                tstmt, fq_class_name, constant_pool, local_table)
        case TLoopStmt():
            return generate_bytecode_for_loop(
                tstmt, fq_class_name, constant_pool, local_table)
        case _: assert False


def generate_bytecode_for_stmts(
        tstmts: list[TStatement],
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable) -> list[ByteCommand]:
    bytecode = []

    for tstmt in tstmts:
        bytecode.extend(
            generate_bytecode_for_stmt(
                tstmt, fq_class_name, constant_pool, local_table))
        
    return bytecode


def generate_bytecode_for_method(
        method: TMethod,
        fq_class_name: str,
        constant_pool: ConstantPool,
        local_table: LocalTable)-> list[ByteCommand]:
    bytecode = []

    if isinstance(method, TUserDefinedMethod):
        bytecode.extend(
            generate_bytecode_for_stmts(
                method.body,
                fq_class_name,
                constant_pool,
                local_table))

        if method.return_type.full_name != "<VOID>":
            bytecode.append(Aload(local_table["local_Result"]))
            bytecode.append(Areturn())
        else:
            bytecode.append(Return())
    else:
        ...
    
    return bytecode

import json
import sys

from serpent.tree import make_ast
from serpent.parser_adapter import parse
from serpent.errors import *
from serpent.semantic_checker.examine_system import examine_system
from serpent.semantic_checker.analyze_inheritance import analyze_inheritance
from serpent.semantic_checker.symtab import make_class_symtab, ClassHierarchy

eiffel_code = """class ANY
feature
    default_create do end

    print (s: STRING)
        external "Java"
        alias "com.eiffel.PLATFORM.print"
    end
end

class STRING end

class REAL end

class BOOLEAN end

class NONE end

class APPLICATION
create make
feature
    make do
        do_shit ("HELLO", "WORLD")
    end

    do_shit (a, b: STRING)
    local
        c: STRING
    do
        print (a)
        c := "HELLO"
        print (b)

    end
end
"""


json_ast, stderr = parse(eiffel_code, "build/eiffelp.exe")
if stderr:
    print(stderr, file=sys.stderr)
    sys.exit(1)

dict_ast = json.loads(json_ast)

ast = make_ast(dict_ast)

error_collector = ErrorCollector()
examine_system(ast, error_collector)
if not error_collector.ok():
    error_collector.show()
    sys.exit(0)

flatten_classes = analyze_inheritance(ast, error_collector)
if not error_collector.ok():
    error_collector.show()
    sys.exit(0)

hierarchy = ClassHierarchy(ast)

from serpent.tree.type_decl import ClassType
from serpent.semantic_checker.symtab import GlobalClassTable, make_class_symtab
from serpent.semantic_checker.type_check import make_codegen_class, check_types
from serpent.semantic_checker.utils import pretty_print_node
from serpent.codegen.constpool import make_const_pool, add_package_prefix
from serpent.codegen.preprocess import make_general_class
from serpent.codegen.class_file import make_class_file
from serpent.codegen.genbytecode import generate_bytecode_for_stmts


def pretty_print_program(commands: list, const_pool = None) -> None:
    """
    Выводит ассемблерное представление программы (список объектов ByteCommand)
    с адресами, мнемониками, операндами и шестнадцатеричным представлением байтов.
    
    Если задана таблица констант (const_pool), то для команд, содержащих поле `index`,
    выводится в комментарии строковое представление константы из таблицы.
    
    :param commands: Список объектов, наследующих ByteCommand.
    :param const_pool: Объект ConstPool, содержащий константы для расшифровки.
    """
    offset = 0
    for command in commands:
        # Получаем байтовое представление команды
        code_bytes = command.to_bytes()
        # Форматируем смещение в виде 4-значного hex-числа
        offset_str = f"{offset:04x}:"
        # Используем имя класса в качестве мнемоники
        mnemonic = command.__class__.__name__
        
        # Собираем операнды из полей dataclass (если они заданы)
        operands = []
        for field_name, field_def in getattr(command, '__dataclass_fields__', {}).items():
            # Пропускаем служебное поле, если требуется (например, если tag вычисляется через cached_property)
            value = getattr(command, field_name)
            operands.append(f"{field_name}={value}")
        operand_str = " " + ", ".join(operands) if operands else ""
        
        # Если команда имеет атрибут "index" и задана таблица констант,
        # получаем соответствующую константу для вывода комментария.
        comment = ""
        if const_pool is not None and hasattr(command, "index"):
            idx = getattr(command, "index")
            # Предполагается, что константный pool нумеруется с 1, а список – с 0.
            try:
                constant = const_pool.get_by_index(idx - 1)
                comment = f" ; {constant!r}"
            except IndexError:
                comment = " ; <не найдено в ConstPool>"
        
        # Формируем строку шестнадцатеричных байт
        bytes_hex = " ".join(f"{b:02x}" for b in code_bytes)
        # Вывод строки: смещение, мнемоника с операндами, байты и комментарий (если есть)
        print(f"{offset_str} {mnemonic}{operand_str}    // {bytes_hex}{comment}")
        
        # Обновляем смещение для следующей команды
        offset += len(code_bytes)


flatten_class_mapping = {fcls.class_name: fcls for fcls in flatten_classes}

tclasses = check_types(flatten_classes, hierarchy, error_collector)
if not error_collector.ok():
    error_collector.show()
    sys.exit(1)

from serpent.codegen.constpool import *


main_class_name = "APPLICATION"
main_routine = mangle_name(feature_name="make", class_name=main_class_name)

general_class = make_general_class(tclasses)

all_classes = [general_class, *tclasses]
for i in range(len(all_classes)):
    current = all_classes[i]
    rest = [cls for cls in all_classes if cls.class_name != current.class_name]

    entry_method_name = (
        None
        if current.class_name != main_class_name
        else main_routine)
    class_file = make_class_file(
        current,
        rest,
        entry_point_method=entry_method_name)

    class_file_code = class_file.to_bytes()
    with open(f"{current.class_name}.class", mode="wb") as f:
        f.write(class_file_code)

    if current.class_name == main_class_name:
        with open(f"{current.class_name}.class", "rb") as f:
            print(f.read().hex())


import os
import shutil

def move_class_files(src_dir, dst_dir):
    # Создаем папку назначения, если она не существует
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    # Перебираем все файлы в исходной директории
    for filename in os.listdir(src_dir):
        if filename.endswith('.class'):
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, filename)
            
            # Если файл с таким именем уже есть в папке назначения, удаляем его
            if os.path.exists(dst_path):
                os.remove(dst_path)
            
            # Перемещаем файл
            shutil.move(src_path, dst_path)
            print(f"Перемещен файл: {filename}")

if __name__ == "__main__":
    source_directory = "."  # Текущая директория
    destination_directory = os.path.join(source_directory, "com/eiffel")
    move_class_files(source_directory, destination_directory)

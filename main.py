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

    to_string, out: STRING
    -- Строковое представление объекта.
    -- По умолчанию возвращает строку с описанием местоположения
    -- объекта в памяти.
    external "Java"
    alias "com.eiffel.Any.out"
    end
end

class TEST
feature
    t: INTEGER
    local
        x: INTEGER
        y: ARRAY[INTEGER]
    do
        x := (2 + 2) - (4 * 7) / 10
    end
end

class Y end

class ARRAY [E]
feature
    some: E
    item (index: INTEGER): E do end
    put (element: E; index: INTEGER) do end
end

class INTEGER
feature
    plus (other: like Current): like Current do end

    minus (other: like Current): like Current do end

    product (other: like Current): like Current do end

    division (other: like Current): like Current do end

    is_less (other: like Current): BOOLEAN do end

    is_equal (other: like Current): BOOLEAN do end
end

class PERSON
create
    make
feature
    age: INTEGER
    name: STRING
feature
    fuck do end

    make (a_name: STRING; a_age: INTEGER)
    do
        age := a_age
        name := a_name
    end

    java_method (a, b: INTEGER): INTEGER
        external "Java"
        alias "com.eiffel.PERSON_UTILS.method"
    end

    calculate (a, b: INTEGER): INTEGER
    local
        i: INTEGER
        flag: BOOLEAN
    do
        i := java_method (1, 10)
    end
end

class STRING feature plus (other: like Current): like Current do end end

class REAL end

class BOOLEAN end

class NONE end
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

general_class = make_general_class(tclasses)

tc = tclasses[0]
rest_classes = tclasses[1:]

class_file = make_class_file(general_class, tclasses, entry_point_method=mangle_name("fuck", class_name="PERSON"))
pretty_print_const_pool(class_file.constant_pool)

#for i in range(1000):
#    pretty_print_program(class_file.methods_table.methods[i].code.bytecode, class_file.constant_pool)

class_file_code = class_file.to_bytes()
with open("PERSON.class", mode="wb") as f:
    f.write(class_file_code)

with open("PERSON.class", "rb") as f:
    print(f.read().hex())
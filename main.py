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
    alias "com.eiffel.base.Any.out"
    end
end

class TEST
feature
    t: INTEGER
    local
        x: INTEGER
    do
        x := (2 + 2) - (4 * 7) / 10
    end
end


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
    make (a_name: STRING; a_age: INTEGER)
    do
        age := a_age
        name := a_name
    end

    calculate: INTEGER
    do
        Result := 1 + 2 - 10 + Result

        if Result < 10 then
            Result := 4
        elseif Result = 254 then
            Result := 8 + 1
        else
            Result := 10
        end
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
from serpent.codegen.constant_pool import make_constant_pool, add_package_prefix
from serpent.codegen.preprocess import make_general_class
from serpent.codegen.class_file import make_class_file
from serpent.codegen.genbytecode import generate_bytecode_for_stmts


flatten_class_mapping = {fcls.class_name: fcls for fcls in flatten_classes}

tclasses = check_types(flatten_classes, hierarchy, error_collector)
if not error_collector.ok():
    error_collector.show()
    sys.exit(1)

from serpent.codegen.constant_pool import *

general_class = make_general_class(tclasses)

tc = tclasses[3]
rest_classes = tclasses[:3] + tclasses[4:]

class_file = make_class_file(tc, rest_classes)
pretty_print_constant_pool(class_file.constant_pool)

class_file_code = class_file.to_bytes()
with open("PERSON.class", mode="wb") as f:
    f.write(class_file_code)

with open("PERSON.class", "rb") as f:
    print(f.read().hex())
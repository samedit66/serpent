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
    Name: STRING = "Дмитрий"

    print (s: STRING) do end

    t do
        print (Name)
    end

    x: ARRAY[INTEGER]
end

class ARRAY [E]
feature
    some: E
    item (index: INTEGER): E do end
end

class INTEGER end

class STRING feature plus (other: like Current): like Current do end end

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
from serpent.codegen.constant_pool import make_constant_pool
from serpent.codegen.general_class import make_general_class
from serpent.codegen.tables import create_class_file

flatten_class_mapping = {fcls.class_name: fcls for fcls in flatten_classes}

tclasses = check_types(flatten_classes, hierarchy, error_collector)
if not error_collector.ok():
    error_collector.show()
    sys.exit(1)

from serpent.codegen.constant_pool import *

general_class = make_general_class(tclasses)
print(pretty_print_node(general_class))

constant_pool0 = make_constant_pool(tclasses[0])
class_file = create_class_file(tclasses[0], constant_pool0, general_class)
print(class_file)

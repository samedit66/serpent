import json
import sys

from serpent.tree import make_ast
from serpent.parser_adapter import parse
from serpent.errors import *
from serpent.semantic_checker.examine_system import examine_system
from serpent.semantic_checker.analyze_inheritance import analyze_inheritance
from serpent.semantic_checker.symtab import make_class_symtab, ClassHierarchy

eiffel_code = """
class ANY
feature
    default_create do print (10) end

    print (x: INTEGER): ARRAY[STRING] do end

    out: STRING

    to_string: like out

    to_s: like to_string

    twin: like Current
    local
        x: INTEGER
        y: ARRAY[ANY]
    do
    end
end

class ARRAY [G]
feature
    item (i: INTEGER): G do end

    test
    do
        x := create {ARRAY[INTEGER]}.default_create
    end
end

class INTEGER
inherit ANY
    redefine out end
feature
    out: STRING do print (10) end
feature
    plus (other: like Current): like Current do end
feature
    test
    local
        x: STRING
        y: INTEGER
        z: BASE
    do
        x := Void
        create z.make
    end
end

class REAL
feature
    plus (other: like Current): like Current
        external "Java"
        alias "ss"
    end
end

class STRING end

class BASE
inherit ANY redefine out end
create make
feature
    make do end
    b: like a
    a: STRING
    out: STRING
    c: like b
end

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
from serpent.semantic_checker.type_check import make_codegen_class
from serpent.semantic_checker.utils import pretty_print_node

flatten_class_mapping = {fcls.class_name: fcls for fcls in flatten_classes}

global_class_table = GlobalClassTable()
tclass = make_codegen_class(
    flatten_classes[2],
    hierarchy,
    global_class_table,
    flatten_class_mapping)

#symtab = make_class_symtab(
#    ClassType(location=None, name="ANY"),
#    flatten_classes[0],
#    hierarchy)
print(pretty_print_node(tclass))

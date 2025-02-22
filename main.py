import json
import sys

from serpent.tree import make_ast
from serpent.parser_adapter import parse
from serpent.errors import *
from serpent.semantic_checker.examine_system import examine_system
from serpent.semantic_checker.analyze_inheritance import analyze_inheritance
from serpent.semantic_checker.type_check import make_class_symtab, ClassHierarchy

eiffel_code = """
class ANY
feature
    default_create do end

    out: STRING

    to_string: like out

    to_s: like to_string

    twin: like Current
end

class ARRAY [G] feature item (i: INTEGER): G do end end

class INTEGER feature f: ARRAY[INTEGER] do end end

class STRING end

class BASE
inherit ANY redefine out end
feature
    b: like a
    a: STRING
    out: STRING
    c: like b
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
symtab = make_class_symtab(ClassType(location=None, name="ARRAY", generics=[ClassType(location=None, name="INTEGER")]), flatten_classes[1], hierarchy)
print(symtab)

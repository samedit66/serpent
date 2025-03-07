from serpent.build import build


build(
    eiffel_source_dirs=["stdlib", "app"],
    java_source_dirs=["rtl"],
    parser_path="build/eiffelp",
    build_dir="output")

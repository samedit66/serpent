from pathlib import Path
import json
import os
import subprocess
import sys

from serpent.parser_adapter import parse_files
from serpent.errors import ErrorCollector, CompilerError

from serpent.tree import make_ast
from serpent.parser_adapter import parse_files
from serpent.errors import *
from serpent.semantic_checker.examine_system import examine_system
from serpent.semantic_checker.analyze_inheritance import analyze_inheritance
from serpent.semantic_checker.symtab import ClassHierarchy
from serpent.semantic_checker.type_check import TClass, check_types
from serpent.semantic_checker.symtab import mangle_name
from serpent.codegen.preprocess import make_general_class
from serpent.codegen.class_file import make_class_file


def run(classpath: str,
        error_collector: ErrorCollector,
        main_class_name: str,
        eiffel_package: str) -> None:
    fq_main_class = f"{eiffel_package}.{main_class_name}"
    # В модуле codegen отсутствует генерация stack map frames,
    # поэтому запускаем JVM с флагом компиляции -noverify
    javac_cmd = [
        "java",
        "-noverify",
        "-classpath", classpath,
        fq_main_class
    ]

    try:
        result = subprocess.run(
            javac_cmd,
            stdout=sys.stdout,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            error_collector.add_error(
                CompilerError(f"Runtime error: {result.stderr}", source="serpent")
            )
    except Exception as e:
        error_collector.add_error(
            CompilerError(f"Java compilation failed: {e}", source="serpent")
        )


def make_jar(build_dir: str,
             error_collector: ErrorCollector,
             main_class_name: str,
             eiffel_package: str,
             jar_name: str,
             output_dir: Path) -> None:
    """
    Создает jar-файл из всех файлов, содержащихся в каталоге build_dir.
    Jar-файл включает всю структуру директорий, начиная с build_dir.
    
    :param build_dir: Каталог сборки, содержащий скомпилированные файлы.
    :param jar_name: Имя jar-файла (по умолчанию "app.jar").
    :param output_dir: Каталог, куда будет помещен jar-файл (по умолчанию текущая папка).
    :param error_collector: Объект для сбора ошибок, если требуется.
    """
    build_dir = Path(build_dir)
    jar_path = Path(output_dir) / jar_name
    manifest_dir = build_dir / "META-INF"
    manifest_path = manifest_dir / "MANIFEST.MF"

    # Создаем папку META-INF для манифеста
    manifest_dir.mkdir(parents=True, exist_ok=True)
    # Записываем файл манифеста
    with open(manifest_path, "w") as manifest_file:
        manifest_file.write("Manifest-Version: 1.0\n")
        fq_main_class_name = f"{eiffel_package}.{main_class_name}"
        manifest_file.write(f"Main-Class: {fq_main_class_name}\n")
        manifest_file.write("\n")  # Пустая строка в конце файла обязательна

    # Команда для создания JAR-файла
    jar_cmd = [
        "jar",
        "cfm",  # 'c' - создать JAR, 'f' - указать имя, 'm' - добавить манифест
        str(jar_path),
        str(manifest_path),
        "-C",
        str(build_dir),
        "."
    ]

    try:
        result = subprocess.run(
            jar_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            error_collector.add_error(
                CompilerError(f"Jar creation error: {result.stderr}", source="serpent"))
    except OSError as e:
        error_collector.add_error(
            CompilerError(f"Jar creation failed: {e}", source="serpent"))


def build_class_files(
        eiffel_source_dirs: list[str],
        java_source_dirs: list[str],
        parser_path: str,
        error_collector: ErrorCollector,
        java_version: int,
        build_dir: str,
        main_class_name: str,
        main_routine_name: str,
        eiffel_package: str,
        verbose: bool) -> None:
    """
    Автоматизирует процесс сборки проекта:
      - Парсит и компилирует исходные файлы Eiffel, генерируя .class файлы,
        которые затем перемещаются в папку build_dir/com/eiffel.
      - Компилирует исходные файлы Java, сохраняя исходную структуру директорий,
        и размещает их в build_dir.

    Параметры:
      eiffel_source_dirs: Список директорий с исходниками Eiffel.
      java_source_dirs: Список директорий с исходниками Java.
      parser_path: Путь к исполняемому файлу парсера Eiffel.
      build_dir: Каталог для размещения скомпилированных файлов.
      java_version: Версия Java для компиляции (по умолчанию 9).
      verbose: Показывать ли прогресс-бар компиляции классов?
    """
    # Создаем каталог сборки, если его нет.
    build_dir = Path(build_dir)
    make_build_dir(build_dir)

    # 1. Парсинг исходников Eiffel.
    json_ast = parse(eiffel_source_dirs, parser_path, error_collector)
    if not error_collector.ok():
        return

    # Создаем AST из полученного словаря.
    ast = make_ast(json_ast)

    # 2. Семантическая проверка и анализ.
    examine_system(ast, error_collector)
    if not error_collector.ok():
        return

    flatten_classes = analyze_inheritance(ast, error_collector)
    if not error_collector.ok():
        return

    hierarchy = ClassHierarchy(ast)
    classes = check_types(flatten_classes, hierarchy, error_collector)
    if not error_collector.ok():
        return

    # 3. Генерация .class файлов для Eiffel.
    # Определяем главный класс и входной метод.
    eiffel_package_dir = build_dir / eiffel_package.replace(".", "/")
    make_build_dir(eiffel_package_dir)

    try:
        major, minor  = map_java_version(java_version)
    except CompilerError as err:
        error_collector.add_error(err)
    if not error_collector.ok():
        return

    compile_eiffel_classes(
        classes,
        error_collector,
        eiffel_package_dir,
        main_class_name=main_class_name,
        main_routine_name=main_routine_name,
        minor_version=minor,
        major_version=major,
        verbose=verbose)
    if not error_collector.ok():
        return

    # 4. Компиляция Java исходников.
    compile_java_files(java_source_dirs, error_collector, build_dir, java_version)
    if not error_collector.ok():
        return


def map_java_version(java_version: int) -> tuple[int, int]:
    if 5 <= java_version <= 16:
        return (java_version + 44, 0)
    raise CompilerError(
        f"Java version '{java_version}' is not supported")


def compile_eiffel_classes(
        classes: list[TClass],
        error_collector: ErrorCollector,
        build_dir: str,
        main_class_name: str,
        main_routine_name: str,
        minor_version: int,
        major_version: int,
        verbose: bool = False) -> None:
    main_class = next(
        (cls for cls in classes if cls.class_name == main_class_name), None)
    if main_class is None:
        error_collector.add_error(
            CompilerError(f"Main class '{main_class_name}' not found", source="serpent"))
        return

    if not any(method for method in main_class.methods):
        error_collector.add_error(
            CompilerError(
                f"Main feature '{main_routine_name}' of class '{main_class_name}' not found",
                source="serpent"))
        return

    main_routine = mangle_name(
        feature_name=main_routine_name,
        class_name=main_class_name)

    general_class = make_general_class(classes)
    all_classes = [general_class] + classes

    build_dir = Path(build_dir)

    if verbose and is_tqdm_installed():
        from tqdm import tqdm
        progress_bar = tqdm(all_classes, desc="Compiling classes")
    else:
        progress_bar = all_classes

    for current in progress_bar:
        rest = [cls for cls in all_classes if cls.class_name != current.class_name]
        entry_method_name = main_routine if current.class_name == main_class_name else None

        try:
            class_file = make_class_file(
                current,
                rest,
                minor_version=minor_version,
                major_version=major_version,
                entry_point_method=entry_method_name)
        except CompilerError as err:
            error_collector.add_error(err)
            continue

        class_file_code = class_file.to_bytes()
        class_filename = build_dir / f"{current.class_name}.class"

        try:
            with open(class_filename, "wb") as f:
                f.write(class_file_code)
        except OSError as e:
            error_collector.add_error(
                CompilerError(f"Error writing file {class_filename}: {e}", source="serpent")
            )
            return


def is_tqdm_installed() -> bool:
    try:
        import tqdm
        return True
    except ImportError:
        return False


def compile_java_files(
        java_source_dirs,
        error_collector: ErrorCollector,
        build_dir: Path,
        java_version) -> None:
    make_build_dir(build_dir)

    java_files = []
    for java_dir in java_source_dirs:
        try:
            java_files.extend(
                str(file)
                for file in collect_files(java_dir, ext="java", recursive=True))
        except CompilerError as err:
            error_collector.add_error(err)

    if not error_collector.ok():
        return

    if not java_files:
        error_collector.add_error(
            CompilerError("No Java source files found", source="serpent")
        )
        return

    javac_cmd = [
        "javac",
        "-d", str(build_dir),
        "--release", str(java_version)
    ] + java_files

    try:
        result = subprocess.run(
            javac_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            error_collector.add_error(
                CompilerError(f"Java compilation error: {result.stderr}", source="serpent")
            )
    except Exception as e:
        error_collector.add_error(
            CompilerError(f"Java compilation failed: {e}", source="serpent")
        )


def make_build_dir(build_dir) -> None:
    Path(build_dir).mkdir(parents=True, exist_ok=True)


def parse(
        eiffel_source_dirs,
        parser_path,
        error_collector: ErrorCollector) -> dict | None:
    eiffel_files = []
    for eiffel_dir in eiffel_source_dirs:
        try:
            eiffel_files.extend(
                collect_files(eiffel_dir, ext="e", recursive=True))
        except CompilerError as err:
            error_collector.add_error(err)

    if not error_collector.ok():
        return None

    stdout, stderr = parse_files(eiffel_files, parser_path)
    if stderr:
        error_collector.add_error(
            CompilerError(f"Parser error: {stderr}")
        )
        return None

    try:
        json_ast = json.loads(stdout)
        return json_ast
    except json.JSONDecodeError as err:
        error_collector.add_error(
            CompilerError(f"Failed to load JSON AST: invalid JSON output: {err}")
        )
    
    return None


def collect_files(
        path_to_dir,
        ext: str | None = None,
        recursive: bool = False) -> list[Path]:
    path = Path(path_to_dir)
    if not path.exists():
        raise CompilerError(f"Directory not found: {path}", source="serpent")

    if path.is_file():
        raise CompilerError(f"Expected directory, but found file: {path}", source="serpent")
    
    if not ext.startswith("."):
        ext = "." + ext

    collected = []
    for x in path.iterdir():
        if recursive and x.is_dir():
            collected.extend(collect_files(x, ext))
        elif x.is_file() and (ext is None or x.suffix == ext):
            collected.append(x)

    return collected

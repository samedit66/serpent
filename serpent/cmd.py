import argparse
from pathlib import Path
import sys

from serpent.errors import ErrorCollector, CompilerError
from serpent.build import build_class_files, run, make_jar
from serpent.resources import get_resource_path


def init_project(name: str, error_collector: ErrorCollector) -> None:
    app_dir = Path(name)
    app_file = app_dir / "app.e"

    if app_dir.exists():
        error_collector.add_error(
            CompilerError(f"Directory {app_dir} already exists", source="serpent")
        )
        return

    app_dir.mkdir(parents=True)
    try:
        with open(app_file, "w") as f:
            f.write(
"""class
    APPLICATION

create
    make
    
feature
                    
    make
    do
        print ("Hello, world!%N")
    end

end
""")
    except OSError as e:
        error_collector.add_error(
            CompilerError(f"Error creating file {app_file}: {e}", source="serpent")
        )
        return


def main() -> None:
    parser = argparse.ArgumentParser(prog="serpent", description="Serpent Eiffel Compiler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `init` command
    init_parser = subparsers.add_parser("init", help="Create a minimal Eiffel project.")
    init_parser.add_argument("name", nargs="?", default="app", help="Project name (default: app)")

    # `build` command
    build_parser = subparsers.add_parser("build", help="Compile an Eiffel project.")
    build_parser.add_argument("source", nargs="?", default=".", help="Source folder (default: current directory).")
    build_parser.add_argument("-m", "--mainclass", default="APPLICATION", help="Main class (default: APPLICATION).")
    build_parser.add_argument("-r", "--mainroutine", default="make", help="Main method (default: make).")
    build_parser.add_argument("-j", "--javaversion", type=int, default=8, help="Java version (default: 8).")
    build_parser.add_argument("-d", "--outputdir", default="classes", help="Build folder (default: classes).")
    build_parser.add_argument("-v", "--verbose", action="store_true", help="Show a progress bar of class compiling.")

    # `run` command
    run_parser = subparsers.add_parser("run", help="Run compiled class files.")
    run_parser.add_argument(
        "-c", "--classpath",
        default="classes",
        help="Folder with class files (default: classes)."
    )
    run_parser.add_argument(
        "-m", "--mainclass",
        default="APPLICATION",
        help="Main class (default: APPLICATION)."
    )

    # `exec` command
    exec_parser = subparsers.add_parser("exec", help="Compile an Eiffel project and run compiled class files.")
    exec_parser.add_argument("-s", "--source", default=".", help="Source folder (default: current directory).")
    exec_parser.add_argument("-m", "--mainclass", default="APPLICATION", help="Main class (default: APPLICATION).")
    exec_parser.add_argument("-r", "--mainroutine", default="make", help="Main method (default: make).")
    exec_parser.add_argument("-j", "--javaversion", type=int, default=8, help="Java version (default: 8).")
    exec_parser.add_argument("-d", "--outputdir", default="classes", help="Build folder (default: classes).")
    exec_parser.add_argument("-v", "--verbose", action="store_true", help="Show a progress bar of class compiling.")

    # `jar` command
    jar_parser = subparsers.add_parser("jar", help="Create a JAR file.")
    jar_parser.add_argument("classpath", nargs="?", default="classes", help="Folder with class files (default: classes).")
    jar_parser.add_argument("-m", "--mainclass", default="APPLICATION", help="Main class (default: APPLICATION).")
    jar_parser.add_argument("-d", "--outputdir", default=".", help="Output folder for the JAR file (default: current directory).")
    jar_parser.add_argument("-n", "--jarname", default="app.jar", help="Jar name (default: app.jar).")

    args, unknown = parser.parse_known_args()

    error_collector = ErrorCollector()
    stdlib = get_resource_path("stdlib")
    rtldir = get_resource_path("rtl")
    parser_path = get_resource_path("build") / "eiffelp"

    if args.command == "init":
        init_project(args.name, error_collector)
    elif args.command == "build":
        build_class_files(
            eiffel_source_dirs=[stdlib, args.source],
            java_source_dirs=[rtldir],
            parser_path=parser_path,
            error_collector=error_collector,
            build_dir=args.outputdir,
            java_version=args.javaversion,
            main_class_name=args.mainclass,
            main_routine_name=args.mainroutine,
            eiffel_package="com.eiffel",
            verbose=args.verbose,
        )
    elif args.command == "run":
        run(
            args.classpath,
            error_collector,
            args.mainclass,
            eiffel_package="com.eiffel",
            cmd_args=unknown,
        )
    elif args.command == "exec":
        build_class_files(
            eiffel_source_dirs=[stdlib, args.source],
            java_source_dirs=[rtldir],
            parser_path=parser_path,
            error_collector=error_collector,
            build_dir=args.outputdir,
            java_version=args.javaversion,
            main_class_name=args.mainclass,
            main_routine_name=args.mainroutine,
            eiffel_package="com.eiffel",
            verbose=args.verbose,
        )
        if not error_collector.ok():
            error_collector.show()
            sys.exit(1)

        run(
            args.outputdir,
            error_collector,
            args.mainclass,
            eiffel_package="com.eiffel",
        )
    elif args.command == "jar":
        make_jar(
            build_dir=args.classpath,
            error_collector=error_collector,
            main_class_name=args.mainclass,
            eiffel_package="com.eiffel",
            jar_name=args.jarname,
            output_dir=args.outputdir,
        )

    if not error_collector.ok():
        error_collector.show()


if __name__ == "__main__":
    main()

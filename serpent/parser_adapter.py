import subprocess
import re
from pathlib import Path


def parse_files(files, parser_path):
    files_arg = [str(f) for f in files]
    try:
        output = subprocess.run(
            [parser_path, *files_arg],
            capture_output=True)
    except FileNotFoundError:
        raise RuntimeError(
            f'Couldn\'t find eiffel parser by path "{parser_path}"')
    stdout, stderr = output.stdout.decode(), output.stderr.decode()
    return replace_rn_with_n(stdout), replace_rn_with_n(stderr)


def parse_string(source, parser_path):
    """Возвращает результат работы парсера Eiffel по заданному файлу

    :param program: Текст программы на Eiffel
    :param parser_path: Путь к парсеру, включая имя файла парсера

    :return: кортеж из двух строк: stdout и stderr
    """
    try:
        output = subprocess.run(
            [parser_path],
            input=source.encode(),
            capture_output=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f'Couldn\'t find eiffel parser by path "{parser_path}"')
    stdout, stderr = output.stdout.decode(), output.stderr.decode()
    return replace_rn_with_n(stdout), replace_rn_with_n(stderr)


def replace_rn_with_n(s):
    return "\n".join(s.splitlines())


def make_error_message(stderr):
    """Считывает все сообщения об ошибках из stderr

    :param stderr: сообщения из stderr потока

    :return: сообщение об ошибках
    """
    errors = re.findall(r'error: .*\n?', stderr)
    return '\n'.join(errors)

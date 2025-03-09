from abc import ABC, abstractmethod, abstractproperty
from .tree.abstract_node import Location


class CompilerDiagnostic(ABC, Exception):
    BOLD_COLOR = "\033[1m"
    RESET_COLOR = "\x1B[0m"

    def __init__(
            self,
            desc: str,
            location: Location | None = None,
            source: str | None = None) -> None:
        """
        :param desc: Описание проблемы.
        :param location: Опционально, позиция (или диапазон) в исходном коде.
        :param source: Альтернативный источник ошибки (например, имя файла), если ошибка не привязана к позиции.
        """
        self.desc = desc
        self.location = location
        self.source = source

    @property
    @abstractmethod
    def severity(self) -> str:
        """Строка, обозначающая тип проблемы (например, 'error' или 'warning')."""

    @property
    @abstractmethod
    def color(self) -> str:
        """Цветовое выделение для типа проблемы."""

    @staticmethod
    def format_source(location: Location | None, source: str | None) -> str:
        if location is not None:
            return f"{location}: "
        elif source is not None:
            return f"{source}: "
        else:
            return ""

    def __str__(self) -> str:
        source_str = self.format_source(self.location, self.source)
        return (f"{self.BOLD_COLOR}{source_str}"
                f"{self.color}{self.severity}: "
                f"{self.RESET_COLOR}{self.desc}")


class CompilerError(CompilerDiagnostic):
    @property
    def severity(self) -> str:
        return "error"

    @property
    def color(self) -> str:
        return "\x1B[31m"  # Красный цвет для ошибок


class CompilerWarning(CompilerDiagnostic):
    @property
    def severity(self) -> str:
        return "warning"

    @property
    def color(self) -> str:
        return "\x1B[33m"  # Желтый цвет для предупреждений


class ErrorCollector:
    LINE_SEPARATOR = "\n\n"

    def __init__(self) -> None:
        self.errors = []

    def __contains__(self, error: CompilerError) -> bool:
        msg = str(error)
        return any(msg == str(error) for error in self.errors)

    def add_error(self, error: CompilerError) -> None:
        if error not in self:
            self.errors.append(error)

    def ok(self) -> bool:
        return len(
            [err
             for err in self.errors
             if isinstance(err, CompilerError)]) == 0

    def show(self) -> None:
        if self.ok():
            return

        for error in self.errors:
            print(error, end=self.LINE_SEPARATOR)

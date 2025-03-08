import importlib.resources as pkg_resources


def get_resource_path(subdir):
    """Возвращает путь к ресурсной папке внутри пакета."""
    return pkg_resources.files(__package__) / subdir

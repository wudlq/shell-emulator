import base64
import binascii
import json
import os
import time


class VfsError(Exception):
    """Ошибка работы с VFS: неверный файл, путь не найден и т.п."""


class File:
    """Файл VFS: двоичное содержимое и время изменения."""

    is_dir = False

    def __init__(self, data=b"", mtime=None):
        """Создаёт файл с содержимым data."""
        self.data = data
        self.mtime = time.time() if mtime is None else mtime


class Directory:
    """Каталог VFS: словарь «имя -> узел»."""

    is_dir = True

    def __init__(self, mtime=None):
        """Создаёт пустой каталог."""
        self.children = {}
        self.mtime = time.time() if mtime is None else mtime


def normalize(path, cwd="/"):
    """Переводит путь в абсолютный вид без «.», «..» и лишних «/»."""
    if not path.startswith("/"):
        path = cwd.rstrip("/") + "/" + path
    parts = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return "/" + "/".join(parts)


def split_path(path):
    """Делит абсолютный нормализованный путь на родителя и имя."""
    parent, _, name = path.rpartition("/")
    return parent or "/", name


class Vfs:
    """VFS в памяти: имя и корневой каталог."""

    def __init__(self, name, root=None):
        """Создаёт VFS; без root получается пустая (минимальная) VFS."""
        self.name = name
        self.root = root if root is not None else Directory()

    def resolve(self, path, cwd="/"):
        """Переводит путь в абсолютный, проверяя каждый шаг, как в UNIX.

        Путь может быть относительным (от cwd) и содержать «.», «..»
        и повторные «/», например home/user/data/../../buddy/././info.
        Перед «.» и «..» проверяется, что пройденная часть пути
        существует и является каталогом. Последнее имя не проверяется,
        чтобы путь подходил и для создания новых файлов и каталогов.
        """
        if not path.startswith("/"):
            path = cwd.rstrip("/") + "/" + path
        parts = []
        for part in path.split("/"):
            if part not in (".", ".."):
                if part:
                    parts.append(part)
                continue
            if not self.get("/" + "/".join(parts)).is_dir:
                raise VfsError("не является каталогом")
            if part == ".." and parts:
                parts.pop()
        return "/" + "/".join(parts)

    def get(self, path):
        """Возвращает узел по абсолютному нормализованному пути."""
        node = self.root
        for part in path.split("/"):
            if not part:
                continue
            if not node.is_dir:
                raise VfsError("не является каталогом")
            node = node.children.get(part)
            if node is None:
                raise VfsError("нет такого файла или каталога")
        return node

    def stats(self):
        """Считает каталоги, файлы и общий размер файлов в байтах."""
        dirs, files, size = 0, 0, 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.is_dir:
                dirs += 1
                stack.extend(node.children.values())
            else:
                files += 1
                size += len(node.data)
        return dirs, files, size


def read_mtime(item):
    """Берёт mtime из описания узла, если оно задано числом."""
    mtime = item.get("mtime")
    if isinstance(mtime, (int, float)) and not isinstance(mtime, bool):
        return mtime
    return None


def build_file(item, path):
    """Создаёт файл из описания JSON, декодируя base64."""
    data = item.get("data", "")
    if isinstance(data, list) and all(isinstance(s, str) for s in data):
        data = "".join(data)
    if not isinstance(data, str):
        raise VfsError(path + ": поле data должно быть строкой")
    try:
        content = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise VfsError(path + ": неверные данные base64") from None
    return File(content, read_mtime(item))


def build_dir(item, path):
    """Создаёт каталог и рекурсивно всё его содержимое."""
    children = item.get("children", {})
    if not isinstance(children, dict):
        raise VfsError(path + ": поле children должно быть объектом")
    node = Directory(read_mtime(item))
    for name, child in children.items():
        if not name or "/" in name or name in (".", ".."):
            raise VfsError(path + ": недопустимое имя " + repr(name))
        node.children[name] = build_node(child, normalize(name, path))
    return node


def build_node(item, path):
    """Создаёт узел VFS (файл или каталог) из описания JSON."""
    if not isinstance(item, dict):
        raise VfsError(path + ": узел должен быть объектом JSON")
    kind = item.get("type")
    if kind == "file":
        return build_file(item, path)
    if kind == "dir":
        return build_dir(item, path)
    raise VfsError(path + ": неизвестный тип узла " + repr(kind))


def load_vfs(path):
    """Загружает VFS из JSON-файла в память."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except OSError as err:
        raise VfsError("не удалось открыть файл VFS: " + str(err)) from None
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise VfsError("файл VFS не является JSON: " + str(err)) from None
    if not isinstance(data, dict) or "root" not in data:
        raise VfsError("в файле VFS нет корневого каталога root")
    root = build_node(data["root"], "/")
    if not root.is_dir:
        raise VfsError("корень VFS должен быть каталогом")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        name = os.path.splitext(os.path.basename(path))[0]
    return Vfs(name, root)

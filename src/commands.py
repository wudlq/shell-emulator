"""Команды эмулятора. Каждая команда — функция (shell, args)."""

import math
import platform
import time

from vfs import VfsError, normalize

HEAD_DEFAULT_LINES = 10
DATE_FORMAT = "%Y-%m-%d %H:%M"
HIDDEN_PREFIX = "."
SIZE_STEP = 1024
SIZE_UNITS = "KMGT"
SIZE_DECIMAL_LIMIT = 10


class ShellError(Exception):
    """Ошибка выполнения команды (неверные аргументы и т.п.)."""


def parse_flags(args, allowed):
    """Отделяет флаги вида -l, -la от остальных аргументов.

    allowed — строка допустимых букв. Аргумент «--» завершает флаги,
    одиночный «-» считается обычным аргументом.
    """
    flags, rest = set(), []
    args = list(args)
    while args:
        arg = args.pop(0)
        if arg == "--":
            rest.extend(args)
            break
        if len(arg) > 1 and arg.startswith("-"):
            for letter in arg[1:]:
                if letter not in allowed:
                    raise ShellError("неизвестный параметр -" + letter)
                flags.add(letter)
        else:
            rest.append(arg)
    return flags, rest


def get_node(shell, path):
    """Находит узел VFS по пути относительно текущего каталога."""
    try:
        return shell.vfs.get(shell.vfs.resolve(path, shell.cwd))
    except VfsError as err:
        raise ShellError(path + ": " + str(err)) from None


def get_file(shell, path):
    """Находит файл; для каталога выдаёт ошибку."""
    node = get_node(shell, path)
    if node.is_dir:
        raise ShellError(path + ": это каталог")
    return node


def as_text(node):
    """Содержимое файла как текст (неверные байты заменяются)."""
    return node.data.decode("utf-8", errors="replace")


def print_text(text):
    """Печатает текст, добавляя перевод строки в конце, если его нет."""
    print(text, end="" if text.endswith("\n") or not text else "\n")


def human_size(size):
    """Размер в удобном виде, как в ls -h: 512, 1.5K, 23K, 4.0M.

    Делит на 1024, пока число не станет меньше 1024. Значение меньше
    10 выводится с одним знаком после точки. Округление вверх.
    """
    value, unit = size, ""
    for next_unit in SIZE_UNITS:
        if value < SIZE_STEP:
            break
        value, unit = value / SIZE_STEP, next_unit
    if not unit:
        return str(size)
    tenths = math.ceil(value * 10) / 10
    if tenths < SIZE_DECIMAL_LIMIT:
        return "{:.1f}{}".format(tenths, unit)
    return "{}{}".format(math.ceil(value), unit)


def long_line(name, node, human):
    """Строка подробного вывода ls -l для одного узла.

    human=True — размер файла в удобном виде (ls -lh).
    Для каталога размер — число элементов в нём.
    """
    mode = "drwxr-xr-x" if node.is_dir else "-rw-r--r--"
    if node.is_dir:
        size = str(len(node.children))
    else:
        size = human_size(len(node.data)) if human else str(len(node.data))
    date = time.strftime(DATE_FORMAT, time.localtime(node.mtime))
    return "{} {:>8} {} {}".format(mode, size, date, name)


def dir_entries(shell, path, node, show_all):
    """Элементы каталога для ls, отсортированные по имени.

    Скрытые (имя начинается с точки) показываются только при
    show_all=True (ls -a), и тогда в начало добавляются «.» и «..».
    """
    items = sorted(
        (name, child) for name, child in node.children.items()
        if show_all or not name.startswith(HIDDEN_PREFIX))
    if show_all:
        parent = shell.vfs.get(shell.vfs.resolve(path + "/..", shell.cwd))
        items = [(".", node), ("..", parent)] + items
    return items


def list_node(shell, path, node, flags):
    """Печатает содержимое каталога или имя файла для ls."""
    if node.is_dir:
        items = dir_entries(shell, path, node, "a" in flags)
    else:
        items = [(path, node)]
    for name, child in items:
        if "l" in flags:
            print(long_line(name, child, "h" in flags))
        else:
            print(name)


def cmd_ls(shell, args):
    """ls [-lha] [путь...] — содержимое каталогов (по умолчанию текущего).

    -l — подробный вывод: тип и права, размер, дата изменения, имя.
    -h — вместе с -l: размер файлов в удобном виде (1.5K, 23K).
    -a — показать скрытые элементы (имя с точки), а также «.» и «..».
    Ключи можно объединять в любом порядке: -lha, -hal, -lh, -la.
    """
    flags, paths = parse_flags(args, "lha")
    paths = paths or ["."]
    errors = []
    found = []
    for path in paths:
        try:
            found.append((path, get_node(shell, path)))
        except ShellError as err:
            errors.append(str(err))
    for message in errors:
        print("ls: " + message)
    for index, (path, node) in enumerate(found):
        if len(paths) > 1 and node.is_dir:
            print(("\n" if index else "") + path + ":")
        list_node(shell, path, node, flags)


def cmd_cd(shell, args):
    """cd [путь] — сменить текущий каталог (без аргумента — корень)."""
    if len(args) > 1:
        raise ShellError("слишком много аргументов")
    path = args[0] if args else "/"
    if not path:
        return
    if not get_node(shell, path).is_dir:
        raise ShellError(path + ": не является каталогом")
    shell.cwd = shell.vfs.resolve(path, shell.cwd)


def cmd_cat(shell, args):
    """cat файл... — вывести содержимое файлов подряд."""
    if not args:
        raise ShellError("не указан файл")
    for path in args:
        try:
            print_text(as_text(get_file(shell, path)))
        except ShellError as err:
            print("cat: " + str(err))


def head_count(value):
    """Проверяет число строк для head и переводит его в int."""
    if not value.isdigit():
        raise ShellError("неверное число строк: " + repr(value))
    return int(value)


def parse_head_args(args):
    """Разбирает аргументы head: -n N, -nN или -N и список файлов."""
    count, files = HEAD_DEFAULT_LINES, []
    args = list(args)
    while args:
        arg = args.pop(0)
        if arg == "-n":
            if not args:
                raise ShellError("параметр -n требует число")
            count = head_count(args.pop(0))
        elif arg.startswith("-n"):
            count = head_count(arg[2:])
        elif arg[1:].isdigit() and arg.startswith("-"):
            count = int(arg[1:])
        elif arg.startswith("-") and len(arg) > 1:
            raise ShellError("неизвестный параметр " + arg)
        else:
            files.append(arg)
    return count, files


def cmd_head(shell, args):
    """head [-n N] файл... — первые N строк файлов (по умолчанию 10)."""
    count, files = parse_head_args(args)
    if not files:
        raise ShellError("не указан файл")
    for index, path in enumerate(files):
        try:
            node = get_file(shell, path)
        except ShellError as err:
            print("head: " + str(err))
            continue
        if len(files) > 1:
            print(("\n" if index else "") + "==> " + path + " <==")
        lines = as_text(node).splitlines(keepends=True)
        print_text("".join(lines[:count]))


def uname_fields(shell):
    """Поля uname по буквам параметров, в порядке вывода для -a."""
    return {
        "s": "Linux",
        "n": shell.vfs.name,
        "r": "6.0-shell-emulator",
        "m": platform.machine() or "unknown",
        "o": "GNU/Linux",
    }


def cmd_uname(shell, args):
    """uname [-a|-s|-n|-r|-m|-o] — сведения о (эмулируемой) системе.

    -s имя ядра (по умолчанию), -n имя узла (имя VFS), -r выпуск,
    -m архитектура реальной машины, -o имя ОС, -a всё сразу.
    """
    flags, rest = parse_flags(args, "asnrmo")
    if rest:
        raise ShellError("лишний аргумент " + repr(rest[0]))
    fields = uname_fields(shell)
    if "a" in flags:
        flags = set(fields)
    flags = flags or {"s"}
    print(" ".join(value for key, value in fields.items() if key in flags))


def change_vfs(shell, name, paths, action, strict=True):
    """Применяет action к каждому пути, печатая ошибки по отдельности.

    Все изменения выполняются только в памяти, файл VFS не меняется.
    strict=False — каталоги на пути заранее не проверяются (нужно для
    mkdir -p, который сам создаёт недостающие каталоги).
    """
    for path in paths:
        if not path:
            print(name + ": пустое имя")
            continue
        try:
            if strict:
                action(shell.vfs.resolve(path, shell.cwd))
            else:
                action(normalize(path, shell.cwd))
        except VfsError as err:
            print(name + ": " + path + ": " + str(err))


def cmd_mkdir(shell, args):
    """mkdir [-p] каталог... — создать каталоги в памяти.

    -p — создать промежуточные каталоги, не ругаться на существующие.
    """
    flags, paths = parse_flags(args, "p")
    if not paths:
        raise ShellError("не указан каталог")
    parents = "p" in flags
    change_vfs(shell, "mkdir", paths,
               lambda path: shell.vfs.mkdir(path, parents), not parents)


def cmd_touch(shell, args):
    """touch файл... — создать пустые файлы или обновить их время."""
    if not args:
        raise ShellError("не указан файл")
    change_vfs(shell, "touch", args, shell.vfs.touch)


def cmd_exit(shell, args):
    """Завершает работу эмулятора."""
    if args:
        raise ShellError("лишние аргументы")
    shell.running = False


def cmd_vfs_info(shell, args):
    """Служебная команда: сведения о загруженной VFS."""
    if args:
        raise ShellError("лишние аргументы")
    dirs, files, size = shell.vfs.stats()
    print("имя VFS:", shell.vfs.name)
    print("каталогов:", dirs)
    print("файлов:", files)
    print("размер файлов, байт:", size)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "cat": cmd_cat,
    "head": cmd_head,
    "uname": cmd_uname,
    "mkdir": cmd_mkdir,
    "touch": cmd_touch,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}

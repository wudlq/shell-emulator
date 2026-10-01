"""Эмулятор командной оболочки ОС: точка входа."""

import argparse
import sys

from shell import Shell
from vfs import Vfs, VfsError, load_vfs

DEFAULT_VFS_NAME = "vfs"


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор командной оболочки ОС")
    parser.add_argument("--vfs", help="путь к JSON-файлу VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def open_vfs(path):
    """Загружает VFS из файла; без пути создаёт пустую VFS."""
    if not path:
        return Vfs(DEFAULT_VFS_NAME)
    return load_vfs(path)


def main():
    """Запускает эмулятор с заданными параметрами."""
    args = parse_args()
    print("[debug] vfs =", args.vfs)
    print("[debug] script =", args.script)
    try:
        vfs = open_vfs(args.vfs)
    except VfsError as err:
        print("ошибка загрузки VFS:", err)
        sys.exit(1)
    shell = Shell(vfs)
    if args.script and not shell.run_script(args.script):
        sys.exit(1)
    shell.run()


if __name__ == "__main__":
    main()

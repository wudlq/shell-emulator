"""Эмулятор командной оболочки ОС."""

import argparse
import os
import sys

QUOTES = "'\""
COMMENT = "#"
DEFAULT_VFS_NAME = "vfs"


class ParseError(Exception):
    """Ошибка разбора строки, например незакрытая кавычка."""


class ShellError(Exception):
    """Ошибка выполнения команды (неверные аргументы и т.п.)."""


class Splitter:
    """Посимвольный разбор строки на слова."""

    def __init__(self):
        """Начальное состояние: слов нет, кавычка не открыта."""
        self.words = []
        self.current = None
        self.quote = None

    def end_word(self):
        """Завершает текущее слово, если оно начато."""
        if self.current is not None:
            self.words.append(self.current)
        self.current = None

    def feed(self, ch):
        """Обрабатывает символ. Возвращает False, если начался комментарий."""
        if self.quote:
            if ch == self.quote:
                self.quote = None
            else:
                self.current += ch
        elif ch in QUOTES:
            self.quote = ch
            self.current = self.current or ""
        elif ch == COMMENT and self.current is None:
            return False
        elif ch.isspace():
            self.end_word()
        else:
            self.current = (self.current or "") + ch
        return True


def split_line(line):
    """Делит строку на слова с учётом кавычек и комментариев.

    Текст внутри одинарных или двойных кавычек считается одним
    словом, даже если в нём есть пробелы. Сами кавычки в результат
    не попадают. Пустые кавычки дают пустой аргумент.
    Символ # в начале слова (вне кавычек) начинает комментарий,
    всё после него до конца строки игнорируется.
    """
    splitter = Splitter()
    for ch in line:
        if not splitter.feed(ch):
            break
    if splitter.quote:
        raise ParseError("незакрытая кавычка " + splitter.quote)
    splitter.end_word()
    return splitter.words


class Shell:
    """Эмулятор командной оболочки."""

    def __init__(self, vfs_name):
        """Создаёт оболочку, работающую с VFS по имени vfs_name."""
        self.vfs_name = vfs_name
        self.running = True
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    def prompt(self):
        """Возвращает строку приглашения к вводу."""
        return self.vfs_name + ":/$ "

    def execute(self, line):
        """Разбирает и выполняет одну строку ввода."""
        try:
            words = split_line(line)
        except ParseError as err:
            print("ошибка разбора:", err)
            return
        if not words:
            return
        name, args = words[0], words[1:]
        command = self.commands.get(name)
        if command is None:
            print(name + ": команда не найдена")
            return
        try:
            command(args)
        except ShellError as err:
            print(name + ": " + str(err))

    def run(self):
        """Интерактивный режим: читает команды, пока не будет exit."""
        while self.running:
            try:
                line = input(self.prompt())
            except EOFError:
                print()
                break
            self.execute(line)

    def run_script(self, path):
        """Выполняет стартовый скрипт, показывая ввод и вывод.

        Пустые строки и строки-комментарии пропускаются.
        Возвращает False, если файл скрипта не удалось прочитать.
        """
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except OSError as err:
            print("ошибка чтения скрипта:", err)
            return False
        for line in lines:
            text = line.strip()
            if not text or text.startswith(COMMENT):
                continue
            print(self.prompt() + text)
            self.execute(text)
            if not self.running:
                break
        return True

    def cmd_ls(self, args):
        """Заглушка команды ls: печатает имя и аргументы."""
        print("ls", args)

    def cmd_cd(self, args):
        """Заглушка команды cd: печатает имя и аргументы."""
        print("cd", args)

    def cmd_exit(self, args):
        """Завершает работу эмулятора."""
        if args:
            raise ShellError("лишние аргументы")
        self.running = False


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор командной оболочки ОС")
    parser.add_argument("--vfs", help="путь к файлу VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def get_vfs_name(path):
    """Имя VFS для приглашения — имя файла без расширения."""
    if not path:
        return DEFAULT_VFS_NAME
    return os.path.splitext(os.path.basename(path))[0]


def main():
    """Запускает эмулятор с заданными параметрами."""
    args = parse_args()
    print("[debug] vfs =", args.vfs)
    print("[debug] script =", args.script)
    shell = Shell(get_vfs_name(args.vfs))
    if args.script and not shell.run_script(args.script):
        sys.exit(1)
    shell.run()


if __name__ == "__main__":
    main()

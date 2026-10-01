"""Цикл работы эмулятора: интерактивный режим и стартовый скрипт."""

from commands import COMMANDS, ShellError
from lexer import COMMENT, ParseError, split_line
from vfs import VfsError


class Shell:
    """Эмулятор командной оболочки, работающий с VFS в памяти."""

    def __init__(self, vfs):
        """Создаёт оболочку; текущий каталог — корень VFS."""
        self.vfs = vfs
        self.cwd = "/"
        self.running = True
        self.commands = COMMANDS

    def prompt(self):
        """Возвращает приглашение: имя VFS и текущий каталог."""
        return self.vfs.name + ":" + self.cwd + "$ "

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
            command(self, args)
        except (ShellError, VfsError) as err:
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

"""Эмулятор командной оболочки ОС."""

QUOTES = "'\""
VFS_NAME = "vfs"


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
        """Обрабатывает очередной символ строки."""
        if self.quote:
            if ch == self.quote:
                self.quote = None
            else:
                self.current += ch
        elif ch in QUOTES:
            self.quote = ch
            self.current = self.current or ""
        elif ch.isspace():
            self.end_word()
        else:
            self.current = (self.current or "") + ch


def split_line(line):
    """Делит строку на слова с учётом кавычек.

    Текст внутри одинарных или двойных кавычек считается одним
    словом, даже если в нём есть пробелы. Сами кавычки в результат
    не попадают. Пустые кавычки дают пустой аргумент.
    """
    splitter = Splitter()
    for ch in line:
        splitter.feed(ch)
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


def main():
    """Запускает эмулятор в интерактивном режиме."""
    Shell(VFS_NAME).run()


if __name__ == "__main__":
    main()

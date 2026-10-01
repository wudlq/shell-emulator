"""Разбор строки ввода на слова с учётом кавычек и комментариев."""

QUOTES = "'\""
COMMENT = "#"


class ParseError(Exception):
    """Ошибка разбора строки, например незакрытая кавычка."""


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

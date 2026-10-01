"""Команды эмулятора. Каждая команда — функция (shell, args)."""


class ShellError(Exception):
    """Ошибка выполнения команды (неверные аргументы и т.п.)."""


def cmd_ls(shell, args):
    """Заглушка команды ls: печатает имя и аргументы."""
    print("ls", args)


def cmd_cd(shell, args):
    """Заглушка команды cd: печатает имя и аргументы."""
    print("cd", args)


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
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}

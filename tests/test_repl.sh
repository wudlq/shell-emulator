#!/bin/sh
# Этап 1: проверка REPL через перенаправление ввода.
cd "$(dirname "$0")/.."

printf '%s\n' \
    'ls' \
    'ls -l /home' \
    'cd "my folder"' \
    "cd 'one two' three" \
    'ls ""' \
    'cd "не закрыта' \
    'unknown arg' \
    'exit 1' \
    'exit' | ./run.sh

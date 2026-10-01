#!/bin/sh
# Этапы 4-5: стартовые скрипты с командами эмулятора.
cd "$(dirname "$0")/.."

echo "=== этап 4: ls, cd, cat, head, uname ==="
./run.sh --vfs tests/vfs/deep.json --script tests/scripts/stage4.txt

echo "=== этап 5: mkdir, touch (изменения только в памяти) ==="
before=$(cksum < tests/vfs/deep.json)
./run.sh --vfs tests/vfs/deep.json --script tests/scripts/stage5.txt
after=$(cksum < tests/vfs/deep.json)
if [ "$before" = "$after" ]; then
    echo "файл VFS не изменился"
else
    echo "ОШИБКА: файл VFS изменился"
fi

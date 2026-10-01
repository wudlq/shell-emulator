#!/bin/sh
# Этап 4: стартовый скрипт с командами ls, cd, cat, head, uname.
cd "$(dirname "$0")/.."

echo "=== этап 4: ls, cd, cat, head, uname ==="
./run.sh --vfs tests/vfs/deep.json --script tests/scripts/stage4.txt

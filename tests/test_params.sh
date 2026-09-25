#!/bin/sh
# Этап 2: проверка параметров командной строки.
cd "$(dirname "$0")/.."

echo "=== без параметров ==="
echo exit | ./run.sh

echo "=== только --vfs ==="
echo exit | ./run.sh --vfs myvfs.json

echo "=== только --script ==="
./run.sh --script tests/scripts/stage2.txt

echo "=== --vfs и --script ==="
./run.sh --vfs myvfs.json --script tests/scripts/stage2.txt

echo "=== несуществующий скрипт ==="
./run.sh --script tests/scripts/nope.txt

echo "=== неизвестный параметр ==="
./run.sh --foo

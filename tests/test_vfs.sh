#!/bin/sh
# Этап 3: запуск эмулятора с разными вариантами VFS.
cd "$(dirname "$0")/.."

echo "=== минимальная VFS (пустой корень) ==="
./run.sh --vfs tests/vfs/minimal.json --script tests/scripts/stage3.txt

echo "=== VFS с несколькими файлами (есть двоичный) ==="
./run.sh --vfs tests/vfs/files.json --script tests/scripts/stage3.txt

echo "=== VFS с 3+ уровнями файлов и папок ==="
./run.sh --vfs tests/vfs/deep.json --script tests/scripts/stage3.txt

echo "=== без --vfs: пустая VFS в памяти ==="
echo 'vfs-info' | ./run.sh

echo "=== ошибка: файл VFS не существует ==="
./run.sh --vfs tests/vfs/nope.json

echo "=== ошибка: файл VFS не JSON ==="
./run.sh --vfs tests/vfs/broken.json

echo "=== ошибка: неверный base64 ==="
./run.sh --vfs tests/vfs/bad_base64.json

echo "=== ошибка: корень VFS не каталог ==="
./run.sh --vfs tests/vfs/not_dir.json

#!/bin/bash

for file in *.ui; do
    [ -e "$file" ] || continue

    output="${file%.ui}.py"  # doğru isimlendirme
    echo "Dönüştürülüyor: $file -> $output"
    pyuic5 "$file" -o "$output"
done

echo "Bitti!"
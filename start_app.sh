#!/bin/bash

# .venv var mı kontrol et
if [ ! -d ".venv" ]; then
    echo "❌ Sanal ortam (.venv) bulunamadı."
    exit 1
fi

# Python dosyası var mı kontrol et
if [ ! -f "test/TEST_newGUI.py" ]; then
    echo "❌ test/TEST_newGUI.py dosyası bulunamadı."
    exit 1
fi

# Komutu çalıştır
echo "🚀 test.TEST_newGUI başlatılıyor..."
sudo .venv/bin/python -m test.TEST_newGUI
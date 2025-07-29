#!/bin/bash

# Python sürümünü kontrol et
REQUIRED_PYTHON="3.8"

if ! python3 -V | grep "$REQUIRED_PYTHON" > /dev/null; then
    echo "Python $REQUIRED_PYTHON gerekli. Lütfen uygun sürümü yükleyin."
    exit 1
fi

# Sanal ortam oluştur
python3 -m venv .venv
source .venv/bin/activate

# Gereksinimleri yükle
pip install --upgrade pip
pip install -r requirements.txt

echo "Kurulum tamamlandı ✅"

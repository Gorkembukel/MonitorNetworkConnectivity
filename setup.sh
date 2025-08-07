#!/bin/bash

# Python sürümünü kontrol et


# Sanal ortam oluştur
python3 -m venv .venv
source .venv/bin/activate

# Gereksinimleri yükle
pip install --upgrade pip
pip install -r requirements.txt

echo "Kurulum tamamlandı ✅"

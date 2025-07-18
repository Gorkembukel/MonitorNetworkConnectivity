#!/bin/bash

# Hedef listesi
targets=(
  google.com
  208.67.222.222
  44.208.147.61
  8.8.8.8
  1.1.1.1
  mcdonalds.com
  facebook.com
  invalid.domain.com
  andasis.com
  burgerking.com
  turkiye.gov.tr
  ieee.org
  9.9.9.9
  4.2.2.2
)

# Ping sayısı
PING_COUNT=20000

# Her hedef için ayrı fping başlat
for target in "${targets[@]}"
do
  {
    echo "▶ $target başlatılıyor..."
    fping -c "$PING_COUNT" -p 1 "$target" 2>&1 |
      sed "s/^/[$target] /"
    echo "✅ $target tamamlandı."
    echo
  } &
done

# Tüm işlemleri bekle
wait

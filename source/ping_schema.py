# ping_schema.py

PING_PARAMETERS = {
    "target": {
        "type": str,
        "label": "IP / Hostname",
        "required": True
    },
    "duration": {
        "type": int,
        "label": "Ping Süresi (saniye)",
        "default": 10
    },
    "interval_ms": {
        "type": int,
        "label": "Ping Aralığı (ms)",
        "default": 1000
    },
    "timeout": {
        "type": float,
        "label": "Zaman Aşımı (sn)",
        "default": 1.0
    },
    "size": {
        "type": int,
        "label": "Paket boyutu (byte)",
        "default": 32
    }

}

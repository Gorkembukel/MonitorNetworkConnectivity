#common_fuction.py
import os
def read_targets_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"🚫 File not found: {file_path}")
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

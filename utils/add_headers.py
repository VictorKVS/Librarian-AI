# utils/add_headers.py
import os

def add_header_to_file(path: str, header: str):
    with open(path, "r+", encoding="utf-8") as f:
        content = f.read()
        f.seek(0, 0)
        f.write(header.rstrip("\r\n") + "\n\n" + content)
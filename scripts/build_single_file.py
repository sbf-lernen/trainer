#!/usr/bin/env python3
"""Baut dist/sbf-trainer.html: eine einzelne, verschickbare HTML-Datei
mit eingebetteten Fragen (data.js) und Bildern (Base64).

Aufruf aus dem Projektverzeichnis: python3 scripts/build_single_file.py
"""
import base64
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIME = {".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}

html = open(f"{ROOT}/index.html", encoding="utf-8").read()
data_js = open(f"{ROOT}/data.js", encoding="utf-8").read()

img_data = {}
for fn in sorted(os.listdir(f"{ROOT}/images")):
    ext = os.path.splitext(fn)[1].lower()
    if ext not in MIME:
        continue
    b64 = base64.b64encode(open(f"{ROOT}/images/{fn}", "rb").read()).decode()
    img_data[fn] = f"data:{MIME[ext]};base64,{b64}"

inline = ("<script>\n" + data_js
          + "const IMG_DATA = " + json.dumps(img_data, separators=(",", ":"))
          + ";\n</script>")
out = html.replace('<script src="data.js"></script>', inline, 1)
assert out != html, "data.js-Script-Tag nicht gefunden"

os.makedirs(f"{ROOT}/dist", exist_ok=True)
dest = f"{ROOT}/dist/sbf-trainer.html"
open(dest, "w", encoding="utf-8").write(out)
print(f"{dest}: {os.path.getsize(dest) / 1e6:.1f} MB, {len(img_data)} Bilder eingebettet")

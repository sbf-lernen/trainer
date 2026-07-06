#!/usr/bin/env python3
"""Lädt den amtlichen SBF-Fragenkatalog von elwis.de und erzeugt data.js + images/.

Aufruf aus dem Projektverzeichnis: python3 scripts/update_catalog.py
"""
import hashlib
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine"
PAGES = {
    "basis": f"{BASE}/Fragenkatalog-See/Basisfragen/Basisfragen-node.html",
    "see": f"{BASE}/Fragenkatalog-See/Spezifische-Fragen-See/Spezifische-Fragen-See-node.html",
    "binnen": f"{BASE}/Fragenkatalog-Binnen/Spezifische-Fragen-Binnen/Spezifische-Fragen-Binnen-node.html",
    "segeln": f"{BASE}/Fragenkatalog-Binnen/Spezifische-Fragen-Segeln/Spezifische-Fragen-Segeln-node.html",
}
PREFIX = {"basis": "B", "see": "S", "binnen": "N", "segeln": "G"}
EXPECTED = {"basis": 72, "see": 213, "binnen": 181, "segeln": 47}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


class Extractor(HTMLParser):
    """Sammelt Frage-<p>-Blöcke und Antwort-<ol type=a>-Listen im content-Div."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_content = False
        self.depth = 0
        self.blocks = []
        self.cur = None
        self.cur_imgs = []
        self.in_ol = False
        self.answers = None
        self.li_buf = None
        self.li_imgs = None
        self.p_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.in_content:
            if tag == "div" and a.get("id") == "content":
                self.in_content = True
                self.depth = 1
            return
        if tag == "div":
            self.depth += 1
        if tag == "p" and not self.in_ol:
            # ELWIS verschachtelt <p class="picture"> in Frage-Absätzen
            if self.cur is None:
                self.cur = []
                self.cur_imgs = []
                self.p_depth = 1
            else:
                self.p_depth += 1
        elif tag == "ol" and "elwisOL" in (a.get("class") or ""):
            self.in_ol = True
            self.answers = []
        elif tag == "li" and self.in_ol:
            self.li_buf = []
            self.li_imgs = []
        elif tag == "img":
            img = {"src": a.get("src", ""), "alt": a.get("alt", "") or a.get("title", "")}
            if self.in_ol and self.li_buf is not None:
                self.li_imgs.append(img)
            elif self.cur is not None:
                self.cur_imgs.append(img)

    def handle_endtag(self, tag):
        if not self.in_content:
            return
        if tag == "div":
            self.depth -= 1
            if self.depth <= 0:
                self.in_content = False
            return
        if tag == "p" and self.cur is not None and not self.in_ol:
            self.p_depth -= 1
            if self.p_depth > 0:
                return
            text = re.sub(r"\s+", " ", "".join(self.cur)).strip()
            if text or self.cur_imgs:
                self.blocks.append(("p", {"text": text, "imgs": self.cur_imgs}))
            self.cur = None
        elif tag == "li" and self.in_ol and self.li_buf is not None:
            text = re.sub(r"\s+", " ", "".join(self.li_buf)).strip()
            self.answers.append({"text": text, "imgs": self.li_imgs})
            self.li_buf = None
        elif tag == "ol" and self.in_ol:
            self.in_ol = False
            self.blocks.append(("ol", self.answers))
            self.answers = None

    def handle_data(self, data):
        if not self.in_content:
            return
        if self.in_ol and self.li_buf is not None:
            self.li_buf.append(data)
        elif self.cur is not None:
            self.cur.append(data)


def parse_questions(html):
    ex = Extractor()
    ex.feed(html)
    questions = []
    pending = None
    for kind, data in ex.blocks:
        if kind == "p":
            m = re.match(r"^(\d+)\.\s+(.*)", data["text"])
            if m:
                pending = {"n": int(m.group(1)), "q": m.group(2).strip(), "qimgs": data["imgs"]}
            elif pending and not data["text"] and data["imgs"]:
                pending["qimgs"].extend(data["imgs"])
            elif pending and data["text"]:
                pending["q"] += " " + data["text"]
                pending["qimgs"].extend(data["imgs"])
        elif kind == "ol" and pending is not None:
            pending["answers"] = data
            questions.append(pending)
            pending = None
    return questions


def image_filename(url):
    path = url.split("?")[0]
    base = re.sub(r"[^A-Za-z0-9._-]", "_", "/".join(path.split("/")[-2:]))
    return hashlib.md5(url.encode()).hexdigest()[:6] + "_" + base


def main():
    os.makedirs(f"{ROOT}/images", exist_ok=True)
    data, img_urls = {}, {}
    ok = True
    for key, url in PAGES.items():
        print(f"lade {key} …")
        qs = parse_questions(fetch(url).decode("utf-8"))
        items = []
        for q in qs:
            if len(q.get("answers", [])) != 4:
                print(f"  WARNUNG: Frage {q['n']} hat {len(q.get('answers', []))} Antworten")
                ok = False
            item = {"id": f"{PREFIX[key]}{q['n']}", "n": q["n"], "q": q["q"]}
            qi = []
            for im in q["qimgs"]:
                full = im["src"] if im["src"].startswith("http") else "https://www.elwis.de" + im["src"]
                img_urls[full] = image_filename(full)
                qi.append(img_urls[full])
            if qi:
                item["img"] = qi
            answers = []
            for ans in q["answers"]:
                a = {"t": ans["text"]}
                ai = []
                for im in ans["imgs"]:
                    full = im["src"] if im["src"].startswith("http") else "https://www.elwis.de" + im["src"]
                    img_urls[full] = image_filename(full)
                    ai.append(img_urls[full])
                if ai:
                    a["img"] = ai
                answers.append(a)
            item["a"] = answers  # a[0] ist laut ELWIS immer die richtige
            items.append(item)
        print(f"  {len(items)} Fragen (erwartet {EXPECTED[key]})")
        if len(items) != EXPECTED[key]:
            print("  ABWEICHUNG von erwarteter Anzahl — Katalog geändert oder Parser kaputt?")
            ok = False
        data[key] = items

    print(f"lade {len(img_urls)} Bilder …")
    for url, fn in img_urls.items():
        dest = f"{ROOT}/images/{fn}"
        if not os.path.exists(dest):
            with open(dest, "wb") as f:
                f.write(fetch(url))

    js = "const SBF_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(f"{ROOT}/data.js", "w", encoding="utf-8") as f:
        f.write(js)
    print("data.js geschrieben")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

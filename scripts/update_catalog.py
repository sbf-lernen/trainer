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
}
PREFIX = {"basis": "B", "see": "S", "binnen": "N"}
EXPECTED = {"basis": 72, "see": 213, "binnen": 181}


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


def cell_text(cell_html):
    t = re.sub(r"<br\s*/?>", "\n", cell_html)
    t = re.sub(r"<[^>]+>", "", t)
    t = html_unescape(t)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in t.split("\n")]
    return "\n".join(ln for ln in lines if ln).strip()


def html_unescape(s):
    import html as h
    return h.unescape(s)


def parse_nav_page(html, n):
    content = html[html.find('id="content"'):]
    content = content[:content.find("Stand:")]
    tbl_start = content.find("<table")
    tbl_end = content.find("</table>")
    intro_html = content[:tbl_start]
    intro = [cell_text(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", intro_html, re.S)]
    intro = "\n\n".join(p for p in intro if p)
    tasks = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", content[tbl_start:tbl_end], re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) == 3:
            tasks.append({"q": cell_text(cells[1]), "s": cell_text(cells[2])})
    note_html = content[tbl_end:]
    notes = [cell_text(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", note_html, re.S)]
    note = "\n\n".join(p for p in notes if p)
    item = {"n": n, "intro": intro, "tasks": tasks}
    if note:
        item["note"] = note
    return item


COORD_RE = re.compile(r"(?:([NE])\s*)?(\d{1,3})\s*°\s*(\d{1,2}(?:[.,]\d+)?)\s*'\s*(?:([NE]))?")


def nav_bbox(item):
    """Grober Kartenbereich der Aufgabe aus allen Koordinaten in Text und Lösungen."""
    text = item["intro"] + " " + " ".join(t["q"] + " " + t["s"] for t in item["tasks"])
    lats, lons = [], []
    for m in COORD_RE.finditer(text):
        axis = m.group(1) or m.group(4)
        if not axis:
            continue
        val = int(m.group(2)) + float(m.group(3).replace(",", ".")) / 60
        (lats if axis == "N" else lons).append(round(val, 4))
    if lats and lons:
        return [min(lats), min(lons), max(lats), max(lons)]
    return None


def fetch_nav():
    nav = []
    for i in range(1, 16):
        url = (f"{BASE}/Fragenkatalog-See/Navigationsaufgaben/"
               f"Navigationsaufgabe-{i:02d}/Navigationsaufgabe-{i:02d}-node.html")
        print(f"lade Navigationsaufgabe {i} …")
        item = parse_nav_page(fetch(url).decode("utf-8"), i)
        if len(item["tasks"]) != 9:
            print(f"  WARNUNG: {len(item['tasks'])} statt 9 Teilaufgaben")
        box = nav_bbox(item)
        if box:
            item["box"] = box
        else:
            print("  WARNUNG: keine Koordinaten für Kartenbereich gefunden")
        nav.append(item)
    return nav


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

    data["nav"] = fetch_nav()

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

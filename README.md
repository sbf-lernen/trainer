# SBF Trainer

Lern-Tool für die Theorieprüfung zum Sportbootführerschein **See** und **Binnen**
(mit Antriebsmaschine), basierend auf dem amtlichen Fragen- und Antwortenkatalog
von [ELWIS](https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/)
(Stand: August 2023).

## Starten

Kein Build nötig — einfach einen statischen Server im Projektordner starten:

```
python3 -m http.server 8321
```

und <http://localhost:8321> öffnen. (`index.html` direkt per Doppelklick geht
auch, solange der Browser lokale Bilder lädt.)

## Funktionen

- **Drei Lernstapel**: Basisfragen (72, gelten für See und Binnen gemeinsam),
  spezifische Fragen See (213) und spezifische Fragen Binnen (181).
  Reihenfolge: „Schwächste zuerst" (einfaches Leitner-System), zufällig oder
  der Reihe nach. Sofortiges Feedback.
- **Fehler-Kartei**: eigener Stapel mit allen Fragen, die schon mal falsch
  beantwortet wurden und noch nicht sicher sitzen.
- **Prüfungssimulation** mit amtlichem Zuschnitt: 30 Fragen pro Bogen
  (7 Basisfragen + 23 spezifische), bestanden mit mind. 5 richtigen
  Basisfragen **und** mind. 18 richtigen spezifischen Fragen. Mit
  60-Minuten-Countdown (automatische Abgabe bei Zeitablauf) und Auswertung
  inkl. Review aller falsch beantworteten Fragen.
- **Navigationsaufgaben (See)** *(nur lokal, siehe unten)*: alle 15 amtlichen Aufgaben à 9 Teilaufgaben
  mit den offiziellen Lösungen zum Aufdecken und Selbstbewerten. Die
  Kartenarbeit passiert auf der Übungskarte D49, die man selbst braucht.
  Zur Orientierung lässt sich der betreffende Kartenbereich als eingebettete
  OpenSeaMap anzeigen (benötigt Internet; die D49 selbst ist BSH-Material und
  darf hier nicht eingebettet werden).
- **Knoten (Praxis)** *(nur lokal)*: die 10 Prüfungsknoten als Lernkarten — Bild ansehen,
  Knoten mit der Leine stecken, Verwendungszweck aufsagen, Lösung aufdecken
  und selbst bewerten. Knotenbilder von Wikimedia Commons (Public Domain bzw.
  CC BY/CC BY-SA, Nachweis jeweils unter dem Bild verlinkt).
- **Statistik**: Fortschritt pro Lernstapel, Tagesbilanz mit Lern-Streak,
  Problemfragen, Prüfungshistorie.
- Fortschritt wird lokal im Browser gespeichert (localStorage), keine
  Anmeldung, keine Server-Komponente.

Im amtlichen Katalog ist immer Antwort a die richtige — das Tool mischt die
Antwortpositionen deshalb bei jeder Anzeige neu. Die Alt-Texte der amtlichen
Bilder verraten oft die Lösung und werden darum nicht angezeigt.

**Nicht abgedeckt:** die Manöver der praktischen Prüfung — und das
tatsächliche Binden der Knoten übt man mit einer Leine in der Hand.

## Öffentlich vs. lokal

Die Module Navigationsaufgaben und Knoten erscheinen nur, wenn der Trainer
lokal läuft (`localhost` oder direkt als Datei geöffnet) — auf der
veröffentlichten GitHub-Pages-Seite sind sie ausgeblendet. Damit macht die
öffentliche Seite keinerlei Anfragen an fremde Server (die OpenSeaMap-Karte
der Navigationsaufgaben würde sonst beim Öffnen Leaflet vom CDN und
Kartenkacheln von OpenStreetMap/OpenSeaMap laden).

## Weitergeben

```
python3 scripts/build_single_file.py
```

erzeugt `dist/sbf-trainer.html` — eine einzelne Datei (~1,7 MB) mit allen
Fragen und Bildern eingebettet. Die kann man per Mail/Messenger verschicken;
Empfänger öffnen sie einfach im Browser (auch mobil), kein Server nötig.
Lernfortschritt wird lokal im jeweiligen Browser gespeichert.

## Datenbestand aktualisieren

```
python3 scripts/update_catalog.py
```

lädt die Katalogseiten und Navigationsaufgaben von elwis.de neu, prüft die
erwarteten Fragenzahlen (72 Basis / 213 See / 181 Binnen / 15 Nav-Aufgaben)
und schreibt `data.js` sowie neue Bilder nach `images/`.

## Dateien

- `index.html` — die komplette App (Vanilla JS, keine Abhängigkeiten)
- `data.js` — alle 466 Fragen und 15 Navigationsaufgaben als JS-Objekt; `a[0]` ist jeweils die richtige Antwort
- `images/` — 159 Abbildungen (Schifffahrtszeichen, Schallsignale, Betonnung, Knoten …)
- `scripts/update_catalog.py` — Crawler/Parser für die ELWIS-Seiten
- `scripts/build_single_file.py` — baut die verschickbare Einzeldatei nach `dist/`

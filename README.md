# SBF Trainer

Lern-Tool für die Theorieprüfung zum Sportbootführerschein **See** und **Binnen**
(inkl. Segeln-Fragen für Binnen unter Segel), basierend auf dem amtlichen
Fragen- und Antwortenkatalog von [ELWIS](https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/)
(Stand: August 2023).

## Starten

Kein Build nötig — einfach einen statischen Server im Projektordner starten:

```
python3 -m http.server 8321
```

und <http://localhost:8321> öffnen. (`index.html` direkt per Doppelklick geht
auch, solange der Browser lokale Bilder lädt.)

## Funktionen

- **Lernmodus** pro Katalog (See / Binnen / Segeln), wahlweise nur Basisfragen
  oder nur spezifische Fragen. Reihenfolge: „Schwächste zuerst" (einfaches
  Leitner-System), zufällig oder der Reihe nach. Sofortiges Feedback.
- **Prüfungssimulation** mit amtlichem Zuschnitt: 30 Fragen pro Bogen
  (7 Basisfragen + 23 spezifische), bestanden mit mind. 5 richtigen
  Basisfragen **und** mind. 18 richtigen spezifischen Fragen. Auswertung mit
  Review aller falsch beantworteten Fragen.
- **Statistik**: Lernfortschritt pro Katalog, Problemfragen, Prüfungshistorie.
- Fortschritt wird lokal im Browser gespeichert (localStorage), keine
  Anmeldung, keine Server-Komponente.

Im amtlichen Katalog ist immer Antwort a die richtige — das Tool mischt die
Antwortpositionen deshalb bei jeder Anzeige neu. Die Alt-Texte der amtlichen
Bilder verraten oft die Lösung und werden darum nicht angezeigt.

**Nicht abgedeckt:** die Navigationsaufgaben (Kartenaufgaben, SBF See,
Fragen 286–300), Knoten und die praktische Prüfung.

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

lädt die Katalogseiten von elwis.de neu, prüft die erwarteten Fragenzahlen
(72 Basis / 213 See / 181 Binnen / 47 Segeln) und schreibt `data.js` sowie
neue Bilder nach `images/`.

## Dateien

- `index.html` — die komplette App (Vanilla JS, keine Abhängigkeiten)
- `data.js` — alle 513 Fragen als JS-Objekt; `a[0]` ist jeweils die richtige Antwort
- `images/` — 151 Abbildungen (Schifffahrtszeichen, Schallsignale, Betonnung …)
- `scripts/update_catalog.py` — Crawler/Parser für die ELWIS-Seiten
- `scripts/build_single_file.py` — baut die verschickbare Einzeldatei nach `dist/`

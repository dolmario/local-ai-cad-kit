# Local AI CAD Kit – vom Foto zum gedruckten Teil

**CAD Next, lokaler Releasekandidat:** Die fünf überarbeiteten CAD-Skills, vollständig bemaßten Aufgaben und getrennten Konfigurationen für OpenCode1, OpenCode2, Cline Core, Crush und Hermes stehen in [CAD-NEXT.md](CAD-NEXT.md). Die zusätzliche [Lernanleitung](SKILL-LEARNING.md) beschreibt dauerhafte Projekt-Skills; [Web-Modi](WEB-CAD-TEST.md) ergänzen bei Bedarf Dokumentationsabrufe und Suche. Noch nicht auf GitHub veröffentlicht. Der neue Einstieg heißt START-CAD-NEXT.bat; die folgende Anleitung beschreibt das bisherige Foto-/Markerboard-Kit. Eigene Kit-Dateien stehen unter MIT, siehe LICENSE; Drittprogramme und Gewichte behalten ihre eigenen Lizenzen.

Ein lokales KI-Modell (Qwen3.8 27B) konstruiert für dich druckbare Teile in **FreeCAD**. Es kann dein Teil auch über ein Foto auf einem gedruckten Markerboard vermessen.
Alles läuft auf deinem eigenen PC, ohne Cloud und ohne Konto.

## Schnellstart (5 Schritte)

1. ZIP **komplett entpacken** (Rechtsklick > Alle extrahieren) nach `local-ai-cad-kit`. Nicht aus der ZIP heraus starten, kein Pfad mit Leerzeichen.
2. **START-HERE.bat** doppelklicken. Windows warnt eventuell („Der Computer wurde geschützt“ > *Weitere Informationen* > *Trotzdem ausführen*), und FreeCAD/Node fragen nach Administratorrechten. Die Installation lädt etwa 23 GB und dauert rund eine Stunde. Fenster offen lassen, bis „Setup finished“ steht.
3. **START-CAD.bat** doppelklicken. Es öffnen sich mehrere Fenster (Modellserver minimiert, FreeCAD, opencode). Das ist normal. Der erste Start kann mehrere Minuten dauern, bitte warten.
4. Im opencode-Fenster einen Satz tippen, z. B. `/beschreibung Kabelclip für 6-mm-Kabel, 3 mm Wand, Schraubenloch 3,5 mm`. Fragt opencode nach Erlaubnis für einen Werkzeugaufruf, bestätigen (allow). Fertige Teile liegen als STL und STEP im Ordner `output\`.
5. Fertig? `/exit` tippen, dann **STOP-CAD.bat** doppelklicken. Das gibt Grafikspeicher und Arbeitsspeicher wieder frei.

Du brauchst keinen 3D-Drucker, um es auszuprobieren: `/beschreibung` und `/zeichnung` liefern Dateien, die du am Bildschirm in FreeCAD ansehen kannst. Das Markerboard brauchst du nur für `/kappe` mit Foto. Legst du Fotos oder Zeichnungen in den Kit-Ordner (z. B. `eingabe\`), gehst du Pfadproblemen aus dem Weg; Pfade mit Leerzeichen in Anführungszeichen setzen.

## Was drin ist

- **Druckbares Markerboard.** Schlüssel oder flaches Teil drauflegen, fotografieren, und das Werkzeug rechnet das Foto in Millimeter um.
- **Foto-Mess-MCP.** Misst Kopfdurchmesser, Schulterbreite und Schaftrichtung eines Schlüssels.
- **FreeCAD-MCP** (neka-nat/freecad-mcp, MIT). Die KI baut echte Körper in FreeCAD und exportiert STL und STEP.
- **opencode**, ein Chat im Terminal. Du schreibst, die KI benutzt die Werkzeuge.
- **Skills**, die das Modell selbst lädt: `key-cap` (parametrischer Kappenbauer mit Selbstprüfung, hat unsere gedruckte Kappe auf 0,001 mm³ genau nachgebaut), `drawing-to-part`, `printability`, `photo-vs-caliper`, `freecad-mcp-rules`. Es sind einfache Textdateien in `skills/`: lesen, ändern, eigene dazulegen (Ordner mit einer `SKILL.md`).
- **Die Kappe aus dem Video** (STEP/STL) und unsere Druckhinweise für TPU 95A auf dem Anycubic Kobra X.

## Voraussetzungen

- Windows 10 oder 11 mit winget („App-Installer“).
- Etwa 30 GB freier Speicherplatz.
- Eine Grafikkarte. Der Installer erkennt sie und wählt das Modell:
  - **big** (ab 22 GB Grafikspeicher, z. B. RTX 3090/4090/5090, AMD Strix Halo mit 64 GB oder mehr): Qwen3.8 27B komplett auf der GPU. Von uns getestet auf GMKtec EVO-X2 (Ryzen AI Max+ 395).
  - **medium** (8–22 GB Grafikspeicher **plus mindestens 32 GB RAM**, z. B. RTX 3080 Ti mit 12 GB): Qwen3.6 35B-A3B. Die Aufmerksamkeit rechnet auf der GPU, die Experten liegen im Arbeitsspeicher. Langsamer, aber es läuft. Auf einer RTX 3080 Ti getestet: siehe Bekannte Probleme unten.
  - Darunter bricht der Installer mit einer klaren Meldung ab.
  - Profil erzwingen: `START-HERE.bat -ModelProfile medium`.
- NVIDIA bekommt llama.cpp mit CUDA (Treiber für CUDA 12.4 oder neuer), AMD und Intel die Vulkan-Version.
- Internet für die Erstinstallation (etwa 20 GB Download).

## Installation mit einem Klick

1. ZIP in einen Ordner **ohne** Sonderzeichen entpacken, zum Beispiel `local-ai-cad-kit`.
2. **START-HERE.bat** doppelklicken.
   - Installiert FreeCAD, uv, Node.js und opencode, lädt danach llama.cpp und das Modell.
   - Richtet das FreeCAD-MCP-Addon ein und macht einen Selbsttest.
   - Protokoll in `install.log`.
3. **START-CAD.bat** doppelklicken. Startet Modell, FreeCAD und opencode.

Nur anschauen, was passieren würde: `START-HERE.bat -DryRun`.

## Benutzen

1. `markerboard/` drucken (siehe `markerboard/DRUCKEN.md`). Schlüssel in die Mitte legen, senkrecht von oben fotografieren.
2. In opencode einen fertigen Befehl nutzen (Prompts in `prompts/PIPELINE-PROMPTS.md`):
   - `/kappe eingabe\schluessel.jpg` – Schlüsselkappe aus einem Foto
   - `/zeichnung eingabe\halter.png` – Teil aus einer technischen Zeichnung
   - `/beschreibung Kabelclip für 6-mm-Kabel, 3 mm Wand` – Teil aus einer Beschreibung
   - `/pruefen` – offenes Teil vor dem Druck prüfen
3. Die KI zeigt die Fotowerte und fragt nach **Messschieberwerten**. Bitte nachmessen, denn Fotos lesen Breiten etwa 0,2 bis 0,3 mm zu groß.
4. Die KI baut die Kappe in FreeCAD, prüft sie und speichert STL und STEP in `output/`.
5. Die STL prüfen:
   `uv run --project foto-mcp --with trimesh --with networkx python pruefen/stl_pruefen.py output\kappe.stl`
6. Slicen und drucken. Wir: TPU 95A auf dem Anycubic Kobra X.

## Wie genau ist mein Board?

`uv run --project foto-mcp python pruefen/platte_pruefen.py <foto.jpg>` fotografiert-vermisst die kleinen Kreuze auf der Platte (sie gehen nicht in die Entzerrung ein). Bei uns: Median etwa 0,1 bis 0,2 mm auf der Plattenebene. Teile, die höher als die Platte sind, erscheinen von oben größer; dafür Teilhöhe mit dem Messschieber nehmen (2 mm Höhenfehler ≈ 0,2 mm Maßfehler bei 30 mm).

## Ehrliche Grenzen

- Die Fotomessung ist eine Schätzung. Sie braucht eine flache Platte, gleichmäßiges Licht und alle Marken im Bild. Der Messschieber hat immer Vorrang.
- Der Schlüsselmodus braucht einen runden Schlüsselkopf.
- Das Modell kann Fehler machen. In unseren Tests hat es einmal eine Öffnung an die falsche Stelle gebaut und trotzdem „passt“ gesagt. Deshalb prüft das Kit nach, und du solltest das Teil in FreeCAD ansehen.
- Eine Kappe hat nach einem Druck gepasst. Das ist ein funktionierendes Beispiel, keine Garantie für jeden Schlüssel und Drucker.

## Bekannte Probleme und Tipps (aus unseren Testläufen)
- **RAM:** Das Profil medium hält etwa 23 GB Experten-Gewichte im Arbeitsspeicher. 32 GB RAM sind das absolute Minimum; vor START-CAD Browser und andere KI-Programme schließen.
- **FreeCAD-Fenster „Dokument-Wiederherstellung“:** Nach hartem Beenden erscheint es beim nächsten Start. Solange es offen ist, läuft die MCP-Verbindung in Zeitüberschreitung („modal dialog is open“ / „Request timed out“). *Bereinigen* klicken und bestätigen, dann weitermachen.
- **Bilder außerhalb des Kit-Ordners:** `opencode run` lehnt Dateien außerhalb des Kit-Ordners ab. Im normalen Chatfenster bei der Nachfrage „allow“ wählen oder Foto/Zeichnung vorher in den Kit-Ordner kopieren.
- **Zeichnungen sind der schwierige Teil:** Auf dem Profil für die RTX 3080 Ti liest das Modell Zeichnungen manchmal falsch (Bohrung an falscher Stelle, hohl statt voll). Es fragt bei fehlenden Maßen und erfindet keine Zahlen, aber die Tabelle „Zeichnung / Modell“ immer selbst prüfen. Foto zur Kappe und einfache Beschreibungen liefen in unseren Tests.
- **Entpacken so, dass `START-HERE.bat` direkt im Zielordner liegt** (zum Beispiel `local-ai-cad-kit`).
- **Der Modellserver bricht mitten in einer Aufgabe ab** (opencode meldet „Cannot connect to API“): Die Logs liegen in `logs\llama-server.err.log` (die letzten Zeilen nennen den Grund). Wir haben das einmal auf dem EVO-X2 mit dem 27B-Modell gesehen (Windows-Fehler 0xc0000409 = das Programm hat sich selbst beendet). Noch einmal versuchen und andere Programme schließen; passiert es immer wieder, ein kleineres Modell oder eine kleinere Kontextgröße nehmen (siehe Modelltabelle) und uns die beiden Logdateien schicken.

## Modell wählen oder wechseln (kleinere PCs, eigenes Modell)
Der Installer wählt ein Modell passend zur Hardware. Ihr könnt eines erzwingen und mehrere nebeneinander behalten.

| Profil | Modell | Braucht | Stand |
|---|---|---|---|
| `big` | Qwen3.8 27B | ab 22 GB Grafikspeicher | auf dem EVO-X2 getestet |
| `medium` | Qwen3.6 35B-A3B (Experten im RAM) | 8 GB GPU + 32 GB RAM | auf einer RTX 3080 Ti getestet |
| `small` | Qwen3.5 9B | 8 GB GPU + 16 GB RAM | **von uns nicht getestet** |
| `mini` | Qwen3-VL 4B | 4 GB GPU + 16 GB RAM | **von uns nicht getestet**, nur Fotos und einfache Teile |
| `custom` | beliebiges Vision-GGUF von Hugging Face | eure Wahl | selbst testen |

- Profil erzwingen: `START-HERE.bat -ModelProfile small`
- Eigenes Modell: `START-HERE.bat -ModelRepo <user/repo> -ModelFile <name.gguf>` (optional `-Ctx 32768`, bei MoE-Modellen `-CpuMoe 99`). Im Repo muss eine `mmproj-F16.gguf` (Vision) liegen.
- Zwischen installierten Modellen wechseln, ohne neu zu laden: `START-CAD.bat -Profile medium`
- Kleinere Modelle lesen Zeichnungen unsicherer. Das Kit fragt bei fehlenden Maßen nach, aber die Tabelle „Zeichnung / Modell“ immer selbst prüfen.
- Für Teil 2 wollen wir weitere Modelle testen. Schreibt in die Kommentare, welches.

## Ollama oder LM Studio schon da? opencode, FreeCAD, uv schon installiert?
- **Eigenen Modellserver statt unseres nutzen:** `START-HERE.bat -ExternalUrl <URL> -ExternalModel <Modellname>`. Das Kit lädt dann kein Modell und startet kein llama.cpp, es richtet nur FreeCAD, die Werkzeuge und opencode ein.
  - **Ollama:** `-ExternalUrl http://127.0.0.1:11434/v1 -ExternalModel <Name aus "ollama list">`. Ollamas Standard-Kontext ist klein: vor dem Start `OLLAMA_CONTEXT_LENGTH=32768` (oder mehr) setzen.
  - **LM Studio:** lokalen Server starten (Reiter Developer), dann `-ExternalUrl http://127.0.0.1:1234/v1 -ExternalModel <dort angezeigte Modell-ID>`. Modell mit Kontextlänge 32768 oder mehr laden.
  - Das Modell muss **Bilder (Vision)** und **Werkzeugaufrufe (Tool Calling)** können. Ohne Vision können `/kappe` und `/zeichnung` keine Fotos und Zeichnungen lesen.
  - Zurück zu unserem Server jederzeit: `START-CAD.bat -Profile big` (oder das Profil, das ihr vorher installiert hattet).
- **Schon installierte Programme werden erkannt und bleiben:** FreeCAD 1.x, uv, Node.js und opencode werden nur installiert, wenn sie fehlen, und `winget` ist nur dafür nötig. Das Kit startet opencode mit einer eigenen Konfigurationsdatei, eure eigenen opencode-Einstellungen und Modelle bleiben unberührt. Wir haben opencode 1.19.0 und FreeCAD 1.1 getestet; andere Versionen können sich anders verhalten.

## Werbung
Unser Drucker, der Anycubic Kobra X: https://pboost.me/E6KBb0ba (Werbung / Affiliate-Link: Bei qualifizierten Käufen erhalte ich eventuell eine Provision, für dich ändert sich der Preis nicht).

# Dauerhaftes Skill-Lernen im CAD-Kit

Das Kit kann neue Verfahren als echte Skills speichern und vorhandene Skills erweitern.
Beim nächsten Start erscheinen die gespeicherten Skills wieder im Katalog. Das Modell muss
die passende Anleitung tatsächlich lesen und anwenden; die Infrastruktur allein beweist
noch keinen erfolgreichen autonomen Lernvorgang. Modellgewichte werden nicht verändert.

## Ablage und Neustart

`skills/` enthält die mitgelieferte Ausgangsversion. Der Starter legt daraus beim ersten
Start `.cad-learning/skills/` als lokale, veränderbare Arbeitsfassung an. Diese Ablage gilt
für alle fünf Harnesses desselben Kits. Sie bleibt bei einem neuen Runtime-Ordner erhalten.
Ein neues Kit in einem anderen Ordner hat zunächst seine eigene Lernablage.

Das Modell verbessert dort nach einer wiederverwendbaren Erkenntnis den passenden Skill
oder erstellt einen neuen Ordner mit `SKILL.md`. Die Anleitung
`skills/cad-skill-learning/SKILL.md` beschreibt Quellen, ausgeführte Tests, Versionen und die
Unterscheidung zwischen bestätigt und unbestätigt. Speichern ist auch über gewöhnliche
Dateiwerkzeuge möglich. Es gibt kein festes Verzeichnis vorformulierter Fehlermeldungen.

Unveränderte Ausgangsdateien dürfen bei einer späteren Kitaktualisierung erneuert werden.
Lokale Änderungen und bewusst gelöschte Dateien werden erhalten. Wenn eine neue
Ausgangsversion einer lokalen Änderung widerspricht, bleibt die lokale Fassung aktiv;
die andere wird unter `.cad-learning/conflicts/` mit Hash und Herkunft gesichert.
Neue Ausgangsdateien werden ergänzt. Entfernte Ausgangsdateien werden nicht automatisch
aus der lokalen Lernablage gelöscht.

Cline bekommt zusätzlich `.cline/skills/` als Arbeitskopie. Der Starter sammelt Änderungen
beim Verlassen ein. Auch wenn ein vorheriger Lauf unterbrochen wurde, vergleicht der nächste
Start die Kopie mit dem letzten Stand, bevor neue Dateien hineinkopiert werden. Bei
gleichzeitigen widersprüchlichen Änderungen bleiben beide Fassungen in einer Konfliktablage
erhalten; die schon persistierte Fassung bleibt aktiv. Bewusste Löschungen werden nur dann
übernommen, wenn die Gegenseite unverändert ist. Für ein Kit jeweils eine Harness-Sitzung
verwenden; die kurze Dateisynchronisierung hat zusätzlich eine Betriebssystem-Dateisperre.

## Harness-Anbindung

| Harness | Dauerhafte Ablage und Wiederladen |
| --- | --- |
| OpenCode 1.19.6 | `skills: {paths: [skills_dir]}` nach dem lokal geprüften V1-Schema; zusätzlich Sitzungskatalog als Dateifallback. |
| OpenCode 2.3.2 | `skills: [skills_dir]`; normaler Skillkatalog und `skill`-Werkzeug, zusätzlich Sitzungskatalog. |
| Cline Core/SDK 0.2.1 | Projektkopie `.cline/skills`, nativer Skillloader und Sitzungskatalog. Schreiben über Projektdateiwerkzeuge; im synthetischen Startertest tatsächlich ausgeführt. |
| Crush 0.102.0 | `options.skills_paths: [skills_dir]` und Katalog im Startauftrag. Die erzeugte Konfiguration und Dateipersistenz sind geprüft; hieraus folgt kein neuer nativer Crush-Modelllauf. |
| Hermes 0.23.3 | `skills.create_dir: skills_dir`, `skills.external_dirs: [skills_dir]`; native `skill_manage`-Erzeugung und Änderung am Fundort. |

Hermes hat die Präzedenz `project → local → create_dir → external_dirs`. Daher keine
zweite Kopie der CAD-Skills nach `HERMES_HOME/skills` schreiben: Sie würde die dauerhafte
Fassung verschatten. `HERMES_HOME` darf für Sitzungsdaten weiter je Lauf neu sein.
`create_dir` wird selbst durchsucht; der explizite Eintrag in `external_dirs` dokumentiert
die gemeinsame Suchablage und wird von Hermes dedupliziert.

Die normale automatische Entdeckung bleibt eingeschaltet. Bei Harnesses ohne passenden
Loader enthält `learning-instructions.md` Namen, Beschreibungen und tatsächliche Dateipfade.
Das Modell liest nur die relevanten Skilltexte. Ein Katalogeintrag beweist noch nicht,
dass ein Modell den Skill im konkreten Auftrag genutzt hat.

## Im Starter bereits eingebunden

Der normale Start erledigt die Vorbereitung automatisch. `harnesses/configure.py` ruft
`prepare(kit, runtime, harness)` auf, konfiguriert die oben genannten Suchpfade und gibt
den Sitzungskatalog an `start-cad-next.ps1` zurück. Der Starter liest auch seine direkt
eingebetteten CAD-Kernanleitungen aus der dauerhaften Ablage. Damit werden lokale
Verbesserungen beim nächsten Start tatsächlich wieder angeboten.

Im äußeren `finally` sammelt der Starter Änderungen nach dem Harness-Ende ein. Für
eine manuelle Wartung sind dieselben reinen Dateibefehle verfügbar; im normalen Ablauf
müssen Nutzer sie nicht selbst ausführen:

```powershell
& $python (Join-Path $kit 'harnesses\skill_learning.py') prepare $kit $runtime $harness
& $python (Join-Path $kit 'harnesses\skill_learning.py') sync $kit $harness
```

`prepare` liefert `skills_dir`, `cline_skills_dir`, `instructions`, `hermes`, `imported`
und `conflicts`; der Runtime-Pfad muss innerhalb des Kits liegen. Beide Befehle geben
JSON aus. Konflikte und Synchronisierungsfehler bleiben sichtbar. Das nächste `prepare`
kann ungesicherte Cline-Änderungen einsammeln, ersetzt aber keine Fehlermeldung eines
fehlgeschlagenen Abschlusses.

`.cad-learning/` und `.cline/` sind in `.gitignore` ausgeschlossen. Sie können private
lokale Inhalte enthalten und gehören nicht ungeprüft in ein Upload-Paket. Der Lernskill
fordert portable, synthetische Beispiele ohne private CAD-Aufträge, Geheimnisse oder
persönliche Dateipfade. `.gitignore` ist keine Inhaltsprüfung eines separat gebauten ZIPs.

## Geprüfter Umfang am 23.11.2026

### Dateipersistenz und erzeugte Konfiguration

Die Standardbibliothekstests laufen in neu angelegten temporären Kits:

```powershell
py -3.12 tests\skill_learning_test.py
```

Zehn Tests bestanden: neue Skills und Änderungen über frische Runtime-Ordner,
Dateikatalog und Harnesswechsel, Cline-Synchronisierung und Wiederholung ohne Änderungen,
Wiederherstellung nach ausgelassenem Abschluss, Migration einer vorhandenen Cline-Kopie,
Konflikte einschließlich Löschkonflikt, Kitaktualisierung ohne Verlust lokaler Änderungen,
bewusste Löschungen sowie abgewiesene Pfade außerhalb des Kits und unsichere Manifestpfade.

Zusätzlich bestanden alle 15 Konfigurationsfälle: fünf Harnesses × Webmodi `off`, `fetch`
und `search`. Je Fall wurden Text-/Bildprofile und zwei simulierte Dateisitzungen geprüft,
einschließlich neuem Skill, Erweiterung eines vorhandenen Skills, Wiederladen und
unverändertem Ausgangsbestand. Diese Tests starteten keinen Harness, FreeCAD, MCP,
Netzwerkabruf oder Modelllauf. Eine gültige Konfiguration beweist keine autonome Modellnutzung.

### Native Hermes-Bibliotheksfunktionen

Der optionale Hermes-Test benötigt eine bereits installierte Hermes-Python-Umgebung;
er installiert und lädt nichts herunter:

```powershell
& $hermesPython tests\hermes_skill_learning_test.py --hermes-source $hermesSource
```

Mit dem vorhandenen Hermes-Quellstand bestanden native `skill_manage`-Aufrufe für
`create`, `patch`, `write_file`, außerdem `skills_list` und `skill_view`. Ein zweiter
Python-Prozess mit frischem isoliertem `HERMES_HOME` fand dieselbe Datei ausschließlich
über `external_dirs` und änderte sie dort. Anschließend erschien sie im Cline-Dateispiegel
und Sitzungskatalog. Modul-SHA256 binden das Ergebnis an die geprüfte Quelle.
Ein Audit-Guard sperrte Netzwerk, Listener, Prozessstarts und fremde Schreibpfade; die
IPv6-Bindeprobe einer HTTP-Bibliothek wurde schon vor dem Systemaufruf blockiert und
im Ergebnis ausgewiesen. Die eigentlichen Skilloperationen bestanden.

Diese Datei-/Konfigurations- und Bibliotheksprüfungen sind CPU-Infrastrukturtests,
ohne Modellinferenz, FreeCAD, MCP oder beobachtete autonome Skillverbesserung.

### Zwei echte Starter-Sitzungen mit synthetischem Provider

Der spätere `release-starter-cpu-check-v4` bestand zwei vollständige öffentliche
Cline-Core-Starter-Sitzungen mit echtem FreeCAD und MCP. Ein synthetischer Modellprovider
gab die Werkzeugfolge vor. Dabei wurde über den echten Datei-Editor ein Skill geschrieben;
die zweite, frische Runtime lud dieselbe Datei mit unverändertem SHA256 über den nativen
Cline-Skillloader wieder. Auch ein realer Dokumentationsabruf über Web-MCP bestand.
Beide Sitzungen boten 17 native FreeCAD-Werkzeuge und forderten tatsächlich 131072
Ausgabetokens mit `ThinkingBudget=-1` im Profil an.

Das belegt die integrierte Speicher-/Wiederladestrecke und verfügbare Werkzeuge. Kein
LLM entschied, was gelernt werden soll, und kein Modell wendete eine selbst gelernte
Methode an. Der kleine FreeCAD-Prüfkörper und der geprüfte Bildtransport dieser Fixture
sind in [CAD-NEXT.md](CAD-NEXT.md) getrennt beschrieben; die Grafik-Viewport-Prüfung
belegt keine GPU-freie Darstellung.

Am 24. November hat auch die aktuelle Windows-Fassung des Starters (V6) diesen Ablauf bestanden. In der ersten Sitzung schrieb der Editor den Skill lokal. In einer frischen Sitzung öffnete Cline dieselbe Fassung mit seinem nativen Skill-Lader. Die zweite Sitzung rief außerdem die FreeCAD-Dokumentation ab. Beide Sitzungen konnten einen Körper mit 70 mm³ über FreeCADCmd messen. Der Test fand mit vorgegebenen Werkzeugaufrufen statt.

Der neue Skill bestand zusätzlich `skill-creator/scripts/quick_validate.py` mit der
bereits vorhandenen Python-3.11-/PyYAML-Umgebung. Das prüft sein Format, nicht sein Verhalten.

## Primärquellen und Versionsgrenzen

- [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills):
  Architektur, dauerhafte Erzeugungsablage und externe Skills. Für die installierte Version
  wurden zusätzlich `agent/skill_utils.py` (`get_skill_create_dir`,
  `get_external_skills_dirs`, `get_skill_search_roots`), `tools/skill_manager_tool.py`
  (`_resolve_skill_dir`, `_find_skill`, `skill_manage`, `SKILL_MANAGE_SCHEMA`) und
  `tools/skills_tool.py` (`skills_list`, `skill_view`) gelesen und direkt geprüft.
- [OpenCode Skills](https://opencode.ai/docs/skills/): aktueller V2-Suchpfad und normale
  Entdeckung. Für V1 wurde das lokal erfasste OpenAPI-Schema der installierten Version
  verwendet; V2-Dokumentation wird nicht auf V1 übertragen. Die 15 Fälle prüfen
  Konfigurationen und Dateien, keine zusätzlichen OpenCode-Modellläufe.
- Installiertes `@cline/core/package.json`: SDK 0.2.1 und offizielles Repository
  [cline/cline](https://github.com/cline/cline). Cline-Datei-Editor und nativer Skillread
  sind zusätzlich im synthetischen Starterlauf beobachtet; native Schreibfunktionen
  von Hermes wurden direkt als Bibliotheksaufrufe geprüft.

Lokales Lernen schreibt die veränderbare Arbeitsfassung; die mitgelieferte
`freecad-mcp-rules`-Ausgangsversion bleibt erhalten. Ungeprüfte API-Vermutungen bleiben
ausdrücklich unbestätigt.

## Früherer echter Hermes-CAD-Lauf

Die Werkzeugspur von `hermes-big-clip-cad` enthält zwei `skill_view`-Aufrufe für
`freecad-mcp-rules` und `printability`, aber keinen `skill_manage`- oder Datei-/Shell-
Schreibaufruf. Die Dateiprüfung fand nur Ausgangsskills und die mitgelieferten CAD-Skills.
Damit ist echte Skillnutzung belegt, keine autonome Erstellung oder Erweiterung.
Geprüft wurden Werkzeugmetadaten und Dateien; Denktexte wurden nicht übernommen.

## Noch offener Modellnachweis

Inkling sollte nach dem Gehäusebau eine Erfahrung als Skill speichern und den Skill in einer frischen Sitzung an einem anderen Maß anwenden. Der Modelllauf endete  mit einem ROCm-Fehler, bevor dieser Versuch begann. Zuvor hatte der Betreuer eine blockierte FreeCAD-Oberfläche wiederhergestellt.

Die fünf gesicherten 120-mm-Dateien enthielten einen funktionsfähigen nativen Zwischenstand. Alle fünf Parameter ließen sich nach dem Öffnen ändern. Daraus entstand später auf der CPU die geprüfte 140-mm-Variante. Diese Erfahrung ist in die redaktionell ergänzte Exportanleitung eingeflossen. [Exportanleitung](tools/EXPORT-NATIVE-LENGTHS.md) · [CAD-Ergebnisse](CAD-NEXT.md) · [Webversuch](WEB-CAD-TEST.md)

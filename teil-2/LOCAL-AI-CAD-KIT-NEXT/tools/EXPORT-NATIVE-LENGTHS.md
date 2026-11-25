# Vorhandene native Längen als Recovery exportieren

`export-native-lengths.py` öffnet eine bestehende FCStd für jede gewünschte Länge
frisch, setzt ihren vorhandenen Tabellenalias und lässt FreeCAD neu berechnen.
Es konstruiert keine Referenzgeometrie und führt keinen Modelllauf aus. Die
Quelldatei wird nicht gespeichert; ihr SHA-256 wird vorher und nachher geprüft.
Alle erzeugten Dateien sind spätere **CPU-derived Exporte**, auch die Variante
mit unverändertem Ausgangsmaß. Ein zuvor fehlgeschlagener Modelllauf bleibt
fehlgeschlagen. Ein Recovery-Export ist kein nachträglicher Benchmark-Pass.

Den Helfer mit dem Python der vorhandenen FreeCAD-Installation aufrufen, das
`FreeCAD`, `Part` und `MeshPart` bereits bereitstellt. Er installiert nichts und
startet weder GUI, MCP noch Modellserver. Beispiel in PowerShell aus dem Kit:

```powershell
$freecadPython = Join-Path $env:LOCALAPPDATA 'Programs\FreeCAD 1.1\bin\python.exe'
& $freecadPython -X utf8 .\tools\export-native-lengths.py `
  '.\CAD\enclosure-original.FCStd' '.\CAD\derived-new' `
  --lengths 120 140 --sheet Spreadsheet --body Body --lid Lid `
  --length-alias LengthMM --manifest
```

Der Zielordner muss **noch fehlen**, sein Elternordner muss existieren. Vorhandene
Ausgaben werden weder überschrieben noch gelöscht; bei Fehlern bleiben Teildateien
und `DERIVATION.json` zur Prüfung erhalten. Für einen weiteren Versuch einen anderen
neuen Ordner wählen. Verknüpfte/Reparse-Pfade werden abgelehnt. Der Prozess muss
frisch sein und darf keine anderen FreeCAD-Dokumente geöffnet haben.

Die Standardwerte sind `--lengths 120 140`, `--sheet Spreadsheet`, `--body Body`,
`--lid Lid` und `--length-alias LengthMM`. Objekt- und Tabellennamen müssen den
**internen Namen** der tatsächlichen Datei entsprechen, nicht nur der sichtbaren
Beschriftung. Diese vorher im vorhandenen Dateibaum bzw. in den
Objekteigenschaften feststellen. Die Tabelle muss `Spreadsheet::Sheet` sein und
den Alias schon enthalten. Body und Lid müssen vorhandene, unterschiedliche
Shape-Objekte sein; Python-Proxies werden abgelehnt. Längen müssen positiv,
endlich und eindeutig sein; `120` und `120.0` zählen als dasselbe Maß.
Der Helfer ist für Gehäuse ausgelegt, deren äußere Länge der X-Ausdehnung beider
Teile entspricht. Nach dem Neuberechnen muss diese tatsächlich dem gewünschten
Maß folgen. Ein vorhandener Alias an einer unveränderlichen Form reicht nicht.

Pro Länge entstehen `enclosure-120-cpu-derived.FCStd`, `body-120.step`,
`body-120.stl`, `lid-120.step`, `lid-120.stl` entsprechend dem gewählten Maß.
Dateinamen werden ausschließlich aus festen Präfixen und den Zahlen erzeugt;
bei Dezimalmaßen steht etwa `120p5` für `120.5` mm. Jede Shape muss gültig sein
und genau einen Solid enthalten. STL wird mit `MeshPart` und 0,01 mm linearer,
0,1 rad Winkelabweichung sowie `Relative=False` vernetzt.

Falls beim Headless-Speichern `GuiDocument.xml` fehlt und die Eingabe eine solche
Datei besitzt, wird **nur dieser XML-Eintrag unverändert** übernommen. Der Beleg
nennt das pro Variante und enthält seinen Eingabehash. Das erzeugt kein neues
Viewport-Bild und keine Kameraanpassung. Beim späteren Öffnen gegebenenfalls
**Fit All / Ansicht einpassen** wählen. Geometrie und sichtbare Darstellung
anschließend gesondert prüfen.

`DERIVATION.json` enthält Eingabehash, Quell-Unverändertheit, Parameter,
Shape-Messungen, FreeCAD-/Helferversion und SHA-256/Bytes aller Artefakte. Der Hash
des Belegs selbst wird auf stdout ausgegeben. `--manifest` ergänzt ein ausdrücklich
abgeleitetes `cad-manifest.json`: für 120/140 mit `document_120`/`document_140`
und tatsächlichen Objektnamen, für beliebige Maße mit
`documents_by_length_mm` und vollständiger Varianten-/Dateizuordnung.

Ein Rückgabecode 0 bedeutet **exportiert, unabhängige Prüfungen ausstehend**.
Shape-Gültigkeit und ein Solid ersetzen weder vollständige Maße-/Funktionsprüfung
noch STEP/STL-Abgleich, unabhängiges natives Reopen, Druck oder Passprobe. Originale
Modellexporte und diese Ableitungen in Ergebnisberichten getrennt ausweisen.

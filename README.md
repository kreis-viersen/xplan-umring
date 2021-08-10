# umringpolygon-zu-xplanung
Umringpolygon eines Bebauungsplans aus QGIS nach XPlanGML konvertieren

Bei Fragen, Anmerkungen, etc. erreichen Sie uns auch per E-Mail unter [open@kreis-viersen.de]( mailto:open@kreis-viersen.de?subject=umringpolygon-zu-xplanung ).

## Es wird benötigt:
1. QGIS mit QGIS Modell [`umringpolygon-zu-xplanung.model3`](https://github.com/kreis-viersen/umringpolygon-zu-xplanung/releases/download/v0.4.0/umringpolygon-zu-xplanung_v0_4_0.zip).
2. Das Browserkonvertierungstool unter https://kreis-viersen.github.io/umringpolygon-zu-xplanung

Eine offline Verwendung des Browserkonvertierungstool ist möglich. Hierzu einfach die ebenfalls in der [`.zip`-Datei](https://github.com/kreis-viersen/umringpolygon-zu-xplanung/releases/download/v0.4.0/umringpolygon-zu-xplanung_v0_4_0.zip) enthaltene `.html`-Datei lokal im Browser öffnen.<br>Die aktuelle Online-Version ist immer unter https://kreis-viersen.github.io/umringpolygon-zu-xplanung zu finden.

## Workflow

1. Bebauungsplanumring in QGIS digitalisieren oder vorhandenen Umring laden.<br>Wichtig: Der Vektorlayer darf nur ein Objekt (= den Umring) vom Typ Polygon beinhalten.
2. QGIS Modell `umringpolygon-zu-xplanung.model3` ausführen.<br>Eingabelayer ist der Vektorlayer mit dem Bebauungsplanumring, die übrigen Modelleingaben ensprechend befüllen/auswählen und Speicherort für die `.gml`-Datei festlegen.
3. Die so erzeugte `.gml`-Datei mit dem [Browserkonvertierungstool](https://kreis-viersen.github.io/umringpolygon-zu-xplanung) nach XPlanGML konvertieren, erzeugte `.zip`-Datei speichern.

## Develop (browsertool)

```bash
# clone the repository
git clone https://github.com/kreis-viersen/umringpolygon-zu-xplanung
cd umringpolygon-zu-xplanung
```
Install the deps, start the dev server and open the web browser on `http://localhost:8080/`.

```bash
# install dependencies
npm install
# start dev server
npm start
```

The build process will watch for changes to the filesystem, rebuild and autoreload the browser tool. However note this from the [webpack-dev-server docs](https://webpack.js.org/configuration/dev-server/):

> webpack uses the file system to get notified of file changes. In some cases this does not work. For example, when using Network File System (NFS). Vagrant also has a lot of problems with this. In these cases, use polling. ([snippet source](https://webpack.js.org/configuration/dev-server/#devserverwatchoptions-))

```bash
# build the app
npm run build
```
Once the build is finished, you'll find it at `dist/`.

```bash
# publish files to a gh-pages branch on GitHub
npm run deploy
```

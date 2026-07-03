# Synthetic Data Studio

A portable Windows app for generating synthetic data with [Faker](https://faker.readthedocs.io/).
No installation, no Python or Node required on the end user's machine.

## How it works

- `app.py` starts a small Flask server bound to `127.0.0.1` on a random free port,
  then opens the UI in a chromeless Edge window (falls back to your default browser
  if Edge isn't found).
- The browser page pings the server every 8 seconds. If you close the window and
  the pings stop, the server shuts itself down within ~20 seconds -- no lingering
  background process, no tray icon needed.
- `faker_api.py` introspects the installed Faker library to build the field-type
  picker, so every locale's full provider list shows up automatically -- nothing
  is hardcoded.
- Your last-used schema is saved to `settings.json` next to the exe and reloaded
  next time you open the app.

## Run it during development

Requires Python 3.10+ on your dev machine only (end users won't need it).

```
run_dev.bat
```

or manually:

```
pip install -r requirements.txt
python app.py
```

## Build the portable Windows app

```
build.bat
```

This runs PyInstaller in `--onedir` mode and produces:

```
dist\SyntheticDataStudio\
├── SyntheticDataStudio.exe
├── _internal\           (Python runtime, Flask, Faker, etc.)
└── static\              (the UI)
```

That entire `dist\SyntheticDataStudio\` folder **is** the app. Zip it, copy it to
a USB stick, or drop it in any folder -- double-clicking the exe is the whole
install process. `settings.json` will appear next to the exe on first run and
travels with the folder.

Notes on the build:

- `--onedir` (not `--onefile`) is used deliberately: `--onefile` silently
  self-extracts to a temp folder on the host's C: drive on every launch, which
  defeats the point of a portable app and slows startup. `--onedir` runs in place.
- The spec bundles Faker's locale data files explicitly via `collect_data_files`,
  since PyInstaller doesn't always find package data automatically.
- The exe is unsigned, so Windows SmartScreen may show a warning on first run on
  an unfamiliar machine ("Windows protected your PC" -> "More info" -> "Run
  anyway"). Code-signing removes this but requires a paid certificate.
- The app assumes Microsoft Edge (present on all Windows 10/11 machines by
  default) or any default browser for rendering the UI -- no WebView2 runtime
  bundling needed.

## Project layout

```
synth_data_studio/
├── app.py              Flask server + launcher + lifecycle management
├── faker_api.py         Faker introspection + row generation
├── static/
│   ├── index.html       Schema builder UI
│   ├── style.css
│   └── app.js            Fetch calls, live preview, exports, heartbeat
├── build.spec           PyInstaller config (portable --onedir)
├── build.bat             Runs the PyInstaller build
├── run_dev.bat            Runs from source for development
└── requirements.txt
```

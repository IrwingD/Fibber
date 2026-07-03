# Fibber

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
- Your last-used schema and theme are saved to `settings.json` next to the exe
  and reloaded next time you open the app.

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

## Build the app

```
build.bat
```

This runs PyInstaller in `--onefile` mode and produces a single file:

```
dist\Fibber.exe
```

That one file **is** the app -- nothing else needs to travel with it. Every launch
it briefly self-extracts to a temp folder before running (adds ~1-3 seconds of
startup), which is the tradeoff for shipping one file instead of a folder.

Notes on the build:

- The spec bundles Faker's locale data files explicitly via `collect_data_files`,
  since PyInstaller doesn't always find package data automatically.
- The exe is unsigned, so Windows SmartScreen may show a warning on first run on
  an unfamiliar machine ("Windows protected your PC" -> "More info" -> "Run
  anyway"). Code-signing removes this but requires a paid certificate.
- The app assumes Microsoft Edge (present on all Windows 10/11 machines by
  default) or any default browser for rendering the UI -- no WebView2 runtime
  bundling needed.

## Distributing it

**Don't commit `Fibber.exe` into the repo** -- `dist\` is gitignored on purpose.
Binaries don't belong in git history (no diffing, repo bloat, and GitHub soft-blocks
files over 100MB anyway).

Instead, build locally and attach `Fibber.exe` to a [GitHub Release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
Anyone visiting the repo gets a clean download link on the Releases page --
no digging through folders required.

## Project layout

```
Fibber/
├── app.py              Flask server + launcher + lifecycle management
├── faker_api.py         Faker introspection + row generation
├── static/
│   ├── index.html       Schema builder UI
│   ├── style.css
│   └── app.js            Fetch calls, live preview, exports, heartbeat
├── build.spec           PyInstaller config (onefile)
├── build.bat             Runs the PyInstaller build
├── run_dev.bat            Runs from source for development
└── requirements.txt
```

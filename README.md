# CSV Variable Plotter (Desktop)

A native desktop app (Tkinter + Matplotlib) for plotting two variables from a CSV file with X-period data slicing.

## Features
- Open any `.csv` file from your computer.
- Choose `X` and `Y` variables.
- Choose `X period` as a data slice (not a date):
  - `All`
  - `First 10%`
  - `First 25%`
  - `Middle 50%`
  - `Last 25%`
  - `Last 10%`
- Or choose `Manual Range` and enter `Start X` / `End X`.
  - If Start/End values are not exact matches in CSV, the app rounds to the nearest existing X values.
- Plot a 2D line chart inside the app window.
- Line mode supports smoothing (`Smooth line` + window size).
- Supports one-click export via `Export Plot PNG` with configurable `Export DPI`.
- Controls are on the left sidebar.
- On macOS, when no plot is shown, the right side uses native frosted glass (`NSVisualEffectView`).

## Setup
```bash
cd /Users/lin/Desktop/CSV_Processing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python3 app.py
```

## Notes
- `Tkinter` is part of standard Python on most macOS installs.
- X-period now slices the loaded rows by position, not by specific date values.
- For native macOS frosted glass, install dependencies from `requirements.txt` (includes `pyobjc-framework-Cocoa` on macOS).
- Numeric `Time` columns are kept numeric (to avoid accidental `1970` epoch axis conversion).

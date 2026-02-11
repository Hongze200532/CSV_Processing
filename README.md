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
- Plot a 2D line or scatter chart inside the app window.
- Controls are on the left sidebar; the non-control area uses a blur-style overlay.

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

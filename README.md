# CSV Variable Plotter (Desktop)

A native desktop app (Tkinter + Matplotlib) for plotting two variables from a CSV file with optional time-period filtering.

## Features
- Open any `.csv` file from your computer.
- Choose `X` and `Y` variables.
- Optionally choose a datetime-like period column.
- Set start and end dates (`YYYY-MM-DD`) to filter rows.
- Plot a 2D line or scatter chart inside the app window.

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
- If date filtering is enabled, use date format `YYYY-MM-DD`.

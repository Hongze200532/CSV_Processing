# CSV Variable Plotter (Desktop)

A native desktop app (Tkinter + Matplotlib) for plotting two variables from a CSV file with optional X-variable period filtering.

## Features
- Open any `.csv` file from your computer.
- Choose `X` and `Y` variables.
- Choose `X period`: `All`, `Last 7 Days`, `Last 30 Days`, `Last 90 Days`, `Last 365 Days`.
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
- X-period filtering requires the selected X variable to be datetime-like.

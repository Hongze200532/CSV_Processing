# CSV Variable Plotter 

A native desktop application built with **Tkinter + Matplotlib** for loading CSV data, selecting variables, and generating 2D comparison plots.

This project is **not** a Streamlit/web app. Run `app.py` directly.

## Download APP
- [Download Latest APP (macOS .zip)](https://github.com/Hongze200532/CSV_Processing/releases/latest/download/CSV-Variable-Plotter-macOS.zip)
- [All Releases](https://github.com/Hongze200532/CSV_Processing/releases)

## What This App Is For
The app is designed for test/experiment workflows where you need to:
- compare multiple CSV sources quickly,
- switch X/Y variables interactively,
- focus on specific parts of the data,
- export high-quality figures for reports.

## Key Features
- Create multiple **Platforms** (logical source groups).
- Add multiple CSV files under each platform.
- Plot across all loaded sources in:
  - `Overlay (One Chart)` mode, or
  - `Separate Subplots` mode.
- Choose `X variable` and `Y variable` from shared columns.
- Slice data by X-period:
  - `All`
  - `First 10%`
  - `First 25%`
  - `Middle 50%`
  - `Last 25%`
  - `Last 10%`
  - `Manual Range`
- Manual range supports nearest-value snapping when exact input is not present.
- Optional line smoothing with configurable window size.
- Plot display size control via numeric input (`Display size (%)`).
- PNG export with configurable DPI (`Export DPI`).

## Current UI Layout
The left side is a floating shell with **two parallel control columns**:

- Source column:
  - `Platforms`
  - `Choose CSV`
- Main control column:
  - `Variables & Mode`
  - `X Period`
  - `Render & Export`

The right side is the chart display area.

Note: data preview is currently removed.

## How To Use
1. In `Platforms`, enter a platform name and click `Add Platform`.
2. Select the target item in `Current platform`.
3. Click `Choose CSV(s)` and add one or more files to that platform.
4. Select `X variable` and `Y variable`.
5. Select plot mode:
   - `Overlay (One Chart)`
   - `Separate Subplots`
6. Select `X period` (or use `Manual Range` with Start/End X).
7. (Optional) Enable smoothing and set smoothing window.
8. Enter `Display size (%)` (example: `85`) and press Enter.
9. Click `Plot`.
10. Set `Export DPI` and click `Export Plot PNG` when needed.

## Parameter Notes
- `X period` percentage modes slice by row position.
- `Manual Range` behavior:
  - numeric X: nearest numeric values are used,
  - datetime-like X: nearest timestamps are used.
- `Display size (%)` changes on-screen chart size only, not export quality.
- `Export DPI` controls output image clarity.

## Data Organization Rules
- Internal structure: `Platform -> multiple CSV files`.
- The app validates common columns across all loaded sources.
- At least 2 shared columns are required for X/Y plotting.
- If adding new CSV files breaks compatibility, the add operation is rejected with a `Column mismatch` warning.
- Duplicate file names in the same platform are auto-renamed (e.g., `file (2).csv`).

## Installation
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

## Dependencies
- `pandas>=2.0.0`
- `matplotlib>=3.8.0`
- `pyobjc-framework-Cocoa>=10.0` (macOS only, for native frosted-glass effects)

## FAQ
### Why do I get `Column mismatch` when adding files?
The new files do not share enough common columns with already loaded sources.

### Why does the chart look too large/small?
Adjust `Display size (%)` and press Enter.

### Is this a browser app?
No. It is a native desktop app.

## Project Files
- `app.py`: main desktop application
- `requirements.txt`: Python dependencies
- `README.md`: project documentation

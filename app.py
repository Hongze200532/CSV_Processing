import io
import math
from pathlib import Path
import sys
import importlib.util
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd

if "seaborn-v0_8-whitegrid" in plt.style.available:
    plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.dpi"] = 160
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.size"] = 4.5
plt.rcParams["axes.titlesize"] = 5
plt.rcParams["axes.labelsize"] = 4.5
plt.rcParams["xtick.labelsize"] = 4
plt.rcParams["ytick.labelsize"] = 4
plt.rcParams["lines.antialiased"] = True
plt.rcParams["path.simplify"] = True
plt.rcParams["path.simplify_threshold"] = 0.2

HAS_COCOA = sys.platform == "darwin" and importlib.util.find_spec("AppKit") is not None

if HAS_COCOA:
    from AppKit import (
        NSApp,
        NSMakeRect,
        NSViewHeightSizable,
        NSViewWidthSizable,
        NSVisualEffectBlendingModeBehindWindow,
        NSVisualEffectMaterialSidebar,
        NSVisualEffectStateActive,
        NSVisualEffectView,
    )


class CSVPlotterApp(tk.Tk):
    PERIOD_TO_SLICE = {
        "First 10%": (0.00, 0.10),
        "First 25%": (0.00, 0.25),
        "Middle 50%": (0.25, 0.75),
        "Last 25%": (0.75, 1.00),
        "Last 10%": (0.90, 1.00),
    }
    X_PERIOD_OPTIONS = ["All", *PERIOD_TO_SLICE.keys(), "Manual Range"]

    def __init__(self) -> None:
        super().__init__()
        self.title("CSV Variable Plotter (Desktop)")
        self.geometry("1400x860")

        self.data_frames: dict[str, pd.DataFrame] = {}
        self.has_plot = False
        self.controls_panel: ttk.Frame | None = None
        self.right_panel: tk.Frame | None = None
        self.native_blur_view = None

        self.file_path_var = tk.StringVar(value="No file selected")
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.x_period_var = tk.StringVar(value="All")
        self.plot_mode_var = tk.StringVar(value="Overlay (One Chart)")
        self.manual_start_var = tk.StringVar()
        self.manual_end_var = tk.StringVar()
        self.smooth_line_var = tk.BooleanVar(value=True)
        self.smooth_window_var = tk.StringVar(value="7")
        self.export_dpi_var = tk.StringVar(value="300")
        self.status_var = tk.StringVar(value="Select a CSV file to begin.")
        self.hover_point_var = tk.StringVar(value="X: -- | Y: --")
        self.peak_max_var = tk.StringVar(value="Max: --")
        self.peak_min_var = tk.StringVar(value="Min: --")

        self.current_plot_x_col = ""
        self.current_plot_y_col = ""
        self.current_plot_sources: list[str] = []
        self.current_plot_x_values: list = []
        self.current_plot_y_values: list = []
        self.current_plot_xy_pixels: np.ndarray | None = None
        self.hover_snap_px = 14.0

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(main, padding=(0, 0, 12, 0), width=300)
        controls.pack(side=tk.LEFT, fill=tk.Y)
        controls.pack_propagate(False)
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_rowconfigure(30, weight=1)
        self.controls_panel = controls

        ttk.Button(controls, text="Choose CSV(s)", command=self.load_csv).grid(
            row=0, column=0, sticky="ew", pady=(0, 10)
        )
        ttk.Label(controls, text="File").grid(row=1, column=0, sticky="w")
        ttk.Label(
            controls,
            textvariable=self.file_path_var,
            wraplength=260,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(2, 10))

        ttk.Label(controls, text="X variable").grid(row=3, column=0, sticky="w")
        self.x_combo = ttk.Combobox(controls, textvariable=self.x_var, state="readonly")
        self.x_combo.grid(row=4, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(controls, text="Y variable").grid(row=5, column=0, sticky="w")
        self.y_combo = ttk.Combobox(controls, textvariable=self.y_var, state="readonly")
        self.y_combo.grid(row=6, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(controls, text="X period").grid(row=7, column=0, sticky="w")
        self.x_period_combo = ttk.Combobox(
            controls,
            textvariable=self.x_period_var,
            state="readonly",
            values=self.X_PERIOD_OPTIONS,
        )
        self.x_period_combo.grid(row=8, column=0, sticky="ew", pady=(2, 10))
        self.x_period_combo.bind("<<ComboboxSelected>>", self.on_x_period_change)

        ttk.Label(controls, text="Start X (manual)").grid(row=9, column=0, sticky="w")
        self.manual_start_entry = ttk.Entry(controls, textvariable=self.manual_start_var, state="disabled")
        self.manual_start_entry.grid(row=10, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(controls, text="End X (manual)").grid(row=11, column=0, sticky="w")
        self.manual_end_entry = ttk.Entry(controls, textvariable=self.manual_end_var, state="disabled")
        self.manual_end_entry.grid(row=12, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(controls, text="Plot mode").grid(row=13, column=0, sticky="w")
        self.plot_mode_combo = ttk.Combobox(
            controls,
            textvariable=self.plot_mode_var,
            state="readonly",
            values=["Overlay (One Chart)", "Separate Subplots"],
        )
        self.plot_mode_combo.grid(row=14, column=0, sticky="ew", pady=(2, 10))

        ttk.Checkbutton(
            controls,
            text="Smooth line",
            variable=self.smooth_line_var,
        ).grid(row=15, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.smooth_window_var).grid(
            row=16, column=0, sticky="ew", pady=(2, 10)
        )

        ttk.Label(controls, text="Export DPI").grid(row=17, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.export_dpi_var).grid(
            row=18, column=0, sticky="ew", pady=(2, 10)
        )

        ttk.Button(controls, text="Plot", command=self.plot_data).grid(
            row=19, column=0, sticky="ew", pady=(6, 6)
        )
        ttk.Button(controls, text="Export Plot PNG", command=self.export_plot).grid(
            row=20, column=0, sticky="ew", pady=(0, 10)
        )

        ttk.Label(controls, textvariable=self.status_var, wraplength=260, justify="left").grid(
            row=22, column=0, sticky="sw"
        )
        ttk.Label(controls, text="Hover Point").grid(row=23, column=0, sticky="w", pady=(8, 0))
        ttk.Label(controls, textvariable=self.hover_point_var, wraplength=260, justify="left").grid(
            row=24, column=0, sticky="w"
        )
        ttk.Label(controls, text="Peaks").grid(row=25, column=0, sticky="w", pady=(8, 0))
        ttk.Label(controls, textvariable=self.peak_max_var, wraplength=260, justify="left").grid(
            row=26, column=0, sticky="w"
        )
        ttk.Label(controls, textvariable=self.peak_min_var, wraplength=260, justify="left").grid(
            row=27, column=0, sticky="w"
        )

        self.right_panel = tk.Frame(main, bg="#efefef")
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content = ttk.Panedwindow(self.right_panel, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True)

        preview_frame = ttk.Frame(content, padding=(0, 8, 8, 8))
        chart_frame = ttk.Frame(content, padding=(8, 8, 0, 8))
        content.add(preview_frame, weight=1)
        content.add(chart_frame, weight=2)

        ttk.Label(preview_frame, text="Data Preview (first 20 rows)").pack(anchor="w")
        self.preview_text = tk.Text(preview_frame, wrap=tk.NONE, height=28)
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.fig, self.ax = plt.subplots(figsize=(11.5, 7.2), dpi=180, constrained_layout=True)
        self.fig.patch.set_facecolor("#f8fafc")
        self.ax.set_facecolor("#ffffff")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_plot_hover)

        if HAS_COCOA:
            self.bind("<Configure>", self._sync_blur_overlay)
            self.controls_panel.bind("<Configure>", self._sync_blur_overlay)
            self.after(120, self._ensure_native_blur_overlay)
            self.show_blur_overlay()

    def show_blur_overlay(self) -> None:
        if HAS_COCOA:
            self._ensure_native_blur_overlay()
            if self.native_blur_view is not None:
                self.native_blur_view.setHidden_(False)
                self._sync_blur_overlay()
        return

    def hide_blur_overlay(self) -> None:
        # Left sidebar frosted glass should always stay visible.
        self.show_blur_overlay()

    def _ensure_native_blur_overlay(self) -> None:
        if not HAS_COCOA or self.native_blur_view is not None or self.controls_panel is None:
            return

        app = NSApp()
        if app is None:
            self.after(120, self._ensure_native_blur_overlay)
            return

        window = app.mainWindow()
        if window is None:
            windows = app.windows()
            if windows and len(windows) > 0:
                window = windows[0]
        if window is None:
            self.after(120, self._ensure_native_blur_overlay)
            return

        content_view = window.contentView()
        self.native_blur_view = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, 10, 10))
        self.native_blur_view.setMaterial_(NSVisualEffectMaterialSidebar)
        self.native_blur_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        self.native_blur_view.setState_(NSVisualEffectStateActive)
        if hasattr(self.native_blur_view, "setIgnoresMouseEvents_"):
            self.native_blur_view.setIgnoresMouseEvents_(True)
        self.native_blur_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        content_view.addSubview_(self.native_blur_view)
        self._sync_blur_overlay()

    def _sync_blur_overlay(self, _event: tk.Event | None = None) -> None:
        if not HAS_COCOA or self.native_blur_view is None or self.controls_panel is None:
            return

        self.update_idletasks()
        x = self.controls_panel.winfo_x()
        y_top = self.controls_panel.winfo_y()
        width = max(1, self.controls_panel.winfo_width())
        height = max(1, self.controls_panel.winfo_height())
        root_height = max(1, self.winfo_height())
        cocoa_y = max(0, root_height - y_top - height)
        self.native_blur_view.setFrame_(NSMakeRect(x, cocoa_y, width, height))

    def on_x_period_change(self, _event: tk.Event | None = None) -> None:
        manual_mode = self.x_period_var.get() == "Manual Range"
        entry_state = "normal" if manual_mode else "disabled"
        self.manual_start_entry.configure(state=entry_state)
        self.manual_end_entry.configure(state=entry_state)
        if not manual_mode:
            self.manual_start_var.set("")
            self.manual_end_var.set("")

    def _nearest_numeric(self, values: pd.Series, target: float) -> float:
        nearest_idx = (values - target).abs().idxmin()
        return float(values.loc[nearest_idx])

    def _nearest_datetime(self, values: pd.Series, target: pd.Timestamp) -> pd.Timestamp:
        nearest_idx = (values - target).abs().idxmin()
        return pd.Timestamp(values.loc[nearest_idx])

    def _apply_manual_x_range(self, data: pd.DataFrame, x_col: str) -> tuple[pd.DataFrame, str]:
        start_raw = self.manual_start_var.get().strip()
        end_raw = self.manual_end_var.get().strip()
        if not start_raw or not end_raw:
            raise ValueError("Manual Range requires both Start X and End X.")

        x_series = data[x_col]

        # Prefer numeric interpretation when feasible.
        x_numeric = pd.to_numeric(x_series, errors="coerce")
        numeric_ratio = x_numeric.notna().mean() if len(x_numeric) else 0.0
        if numeric_ratio >= 0.8:
            start_num = pd.to_numeric(pd.Series([start_raw.replace(",", "")]), errors="coerce").iloc[0]
            end_num = pd.to_numeric(pd.Series([end_raw.replace(",", "")]), errors="coerce").iloc[0]
            if pd.isna(start_num) or pd.isna(end_num):
                raise ValueError("X is numeric. Please input numeric Start X and End X.")

            valid_numeric = x_numeric.dropna()
            if valid_numeric.empty:
                raise ValueError("Selected X variable has no numeric values.")

            start_nearest = self._nearest_numeric(valid_numeric, float(start_num))
            end_nearest = self._nearest_numeric(valid_numeric, float(end_num))
            low, high = sorted((start_nearest, end_nearest))
            filtered = data.loc[x_numeric.between(low, high)].copy()
            return filtered, f"X period: Manual [{low:g}, {high:g}]"

        x_datetime = pd.to_datetime(x_series, errors="coerce")
        datetime_ratio = x_datetime.notna().mean() if len(x_datetime) else 0.0
        if datetime_ratio >= 0.8:
            start_dt = pd.to_datetime(start_raw, errors="coerce")
            end_dt = pd.to_datetime(end_raw, errors="coerce")
            if pd.isna(start_dt) or pd.isna(end_dt):
                raise ValueError("X is datetime-like. Please use parseable date/time input.")

            valid_datetime = x_datetime.dropna()
            if valid_datetime.empty:
                raise ValueError("Selected X variable has no datetime values.")

            start_nearest = self._nearest_datetime(valid_datetime, pd.Timestamp(start_dt))
            end_nearest = self._nearest_datetime(valid_datetime, pd.Timestamp(end_dt))
            low_dt, high_dt = sorted((start_nearest, end_nearest))
            filtered = data.loc[x_datetime.between(low_dt, high_dt)].copy()
            return (
                filtered,
                f"X period: Manual [{low_dt.strftime('%Y-%m-%d %H:%M:%S')}, {high_dt.strftime('%Y-%m-%d %H:%M:%S')}]",
            )

        raise ValueError("Manual Range supports numeric or datetime-like X variable only.")

    def _should_parse_x_as_datetime(self, series: pd.Series) -> bool:
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        if pd.api.types.is_numeric_dtype(series):
            return False

        sample = series.dropna().astype(str).head(120)
        if sample.empty:
            return False

        numeric_like_ratio = sample.str.fullmatch(r"[+-]?\d+(?:\.\d+)?").fillna(False).mean()
        if numeric_like_ratio >= 0.8:
            return False

        datetime_hint_ratio = sample.str.contains(r"[-/:T]").fillna(False).mean()
        return bool(datetime_hint_ratio >= 0.35)

    def _get_smooth_window(self, data_len: int) -> int:
        raw = self.smooth_window_var.get().strip()
        num = pd.to_numeric(pd.Series([raw]), errors="coerce").iloc[0]
        if pd.isna(num):
            return min(7, max(1, data_len))
        window = int(max(1, round(float(num))))
        return min(window, max(1, data_len))

    def _clear_plot_insights(self) -> None:
        self.hover_point_var.set("X: -- | Y: --")
        self.peak_max_var.set("Max: --")
        self.peak_min_var.set("Min: --")
        self.current_plot_x_col = ""
        self.current_plot_y_col = ""
        self.current_plot_sources = []
        self.current_plot_x_values = []
        self.current_plot_y_values = []
        self.current_plot_xy_pixels = None

    def _format_axis_value(self, value) -> str:
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d %H:%M:%S").rstrip()
        if hasattr(value, "item"):
            try:
                value = value.item()
            except Exception:
                pass
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value)

    def _update_peak_info_multi(self, plotted_series: list[dict], x_col: str, y_col: str) -> None:
        max_info = None
        min_info = None
        for item in plotted_series:
            x_series = item["x"]
            y_series = item["y"]
            source = item["source"]
            y_numeric = pd.to_numeric(y_series, errors="coerce")
            valid = y_numeric.notna()
            if valid.sum() == 0:
                continue

            x_valid = x_series.loc[valid].reset_index(drop=True)
            y_valid = y_numeric.loc[valid].reset_index(drop=True)
            local_max_idx = int(y_valid.idxmax())
            local_min_idx = int(y_valid.idxmin())

            local_max = (float(y_valid.iloc[local_max_idx]), source, x_valid.iloc[local_max_idx], y_valid.iloc[local_max_idx])
            local_min = (float(y_valid.iloc[local_min_idx]), source, x_valid.iloc[local_min_idx], y_valid.iloc[local_min_idx])
            if max_info is None or local_max[0] > max_info[0]:
                max_info = local_max
            if min_info is None or local_min[0] < min_info[0]:
                min_info = local_min

        if max_info is None or min_info is None:
            self.peak_max_var.set("Max: --")
            self.peak_min_var.set("Min: --")
            return

        self.peak_max_var.set(
            f"Max[{max_info[1]}]: {x_col}={self._format_axis_value(max_info[2])}, {y_col}={self._format_axis_value(max_info[3])}"
        )
        self.peak_min_var.set(
            f"Min[{min_info[1]}]: {x_col}={self._format_axis_value(min_info[2])}, {y_col}={self._format_axis_value(min_info[3])}"
        )

    def _update_hover_cache(
        self,
        x_series: pd.Series,
        y_series: pd.Series,
        x_col: str,
        y_col: str,
        source_values: list[str] | None = None,
    ) -> None:
        x_num = pd.to_numeric(x_series, errors="coerce")
        if x_num.notna().mean() < 0.8:
            x_dt = pd.to_datetime(x_series, errors="coerce")
            if x_dt.notna().mean() >= 0.8:
                x_num = pd.Series(mdates.date2num(x_dt.dt.to_pydatetime()), index=x_series.index)

        y_num = pd.to_numeric(y_series, errors="coerce")
        valid = x_num.notna() & y_num.notna()
        if valid.sum() == 0:
            self.current_plot_xy_pixels = None
            self.current_plot_sources = []
            self.current_plot_x_values = []
            self.current_plot_y_values = []
            return

        x_valid_num = x_num.loc[valid].to_numpy(dtype=float)
        y_valid_num = y_num.loc[valid].to_numpy(dtype=float)
        xy = np.column_stack([x_valid_num, y_valid_num])
        self.current_plot_xy_pixels = self.ax.transData.transform(xy)
        self.current_plot_x_values = list(x_series.loc[valid].reset_index(drop=True))
        self.current_plot_y_values = list(y_series.loc[valid].reset_index(drop=True))
        if source_values is None:
            self.current_plot_sources = [""] * len(self.current_plot_x_values)
        else:
            source_arr = pd.Series(source_values)
            self.current_plot_sources = list(source_arr.loc[valid].reset_index(drop=True).astype(str))
        self.current_plot_x_col = x_col
        self.current_plot_y_col = y_col

    def _on_plot_hover(self, event) -> None:
        if (
            event is None
            or event.inaxes != self.ax
            or self.current_plot_xy_pixels is None
            or not self.current_plot_x_values
            or not self.current_plot_y_values
            or event.x is None
            or event.y is None
        ):
            self.hover_point_var.set("X: -- | Y: --")
            return

        delta = self.current_plot_xy_pixels - np.array([event.x, event.y])
        dist2 = np.einsum("ij,ij->i", delta, delta)
        nearest_i = int(np.argmin(dist2))
        if float(np.sqrt(dist2[nearest_i])) > self.hover_snap_px:
            self.hover_point_var.set("X: -- | Y: --")
            return

        x_value = self.current_plot_x_values[nearest_i]
        y_value = self.current_plot_y_values[nearest_i]
        source = self.current_plot_sources[nearest_i] if nearest_i < len(self.current_plot_sources) else ""
        src_prefix = f"[{source}] " if source else ""
        self.hover_point_var.set(
            f"{src_prefix}{self.current_plot_x_col}: {self._format_axis_value(x_value)} | "
            f"{self.current_plot_y_col}: {self._format_axis_value(y_value)}"
        )

    def _get_export_dpi(self) -> int:
        raw = self.export_dpi_var.get().strip()
        num = pd.to_numeric(pd.Series([raw]), errors="coerce").iloc[0]
        if pd.isna(num):
            return 300
        return int(min(1200, max(72, round(float(num)))))

    def export_plot(self) -> None:
        if not self.has_plot:
            messagebox.showinfo("No plot", "Please plot data before exporting.")
            return

        x_name = self.x_var.get().strip() or "x"
        y_name = self.y_var.get().strip() or "y"
        safe_x = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in x_name)
        safe_y = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in y_name)
        default_name = f"{safe_y}_vs_{safe_x}.png"

        out_path = filedialog.asksaveasfilename(
            title="Export plot as PNG",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG image", "*.png")],
        )
        if not out_path:
            return

        dpi = self._get_export_dpi()
        self.fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor=self.fig.get_facecolor())
        self.status_var.set(f"Saved plot: {out_path} (DPI: {dpi})")

    def load_csv(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="Select CSV file(s)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_paths:
            return

        loaded_frames: dict[str, pd.DataFrame] = {}
        failed_files: list[str] = []
        for file_path in file_paths:
            path_obj = Path(file_path)
            if not path_obj.exists() or path_obj.stat().st_size == 0:
                failed_files.append(path_obj.name)
                continue

            raw_bytes = path_obj.read_bytes()
            if not raw_bytes.strip():
                failed_files.append(path_obj.name)
                continue

            csv_text = raw_bytes.decode("utf-8", errors="replace")
            df = pd.read_csv(io.StringIO(csv_text), on_bad_lines="skip")
            if df.empty:
                failed_files.append(path_obj.name)
                continue

            df.columns = [str(col).strip() for col in df.columns]
            loaded_frames[path_obj.name] = df

        if not loaded_frames:
            messagebox.showwarning("No data", "No valid CSV files were loaded.")
            return

        self.data_frames = loaded_frames
        first_name = next(iter(self.data_frames))
        first_df = self.data_frames[first_name]
        common_cols = set(first_df.columns)
        for frame in self.data_frames.values():
            common_cols &= set(frame.columns)

        columns = [c for c in first_df.columns if c in common_cols]
        if len(columns) < 2:
            messagebox.showwarning(
                "Column mismatch",
                "Loaded files do not share enough common columns for X/Y plotting.",
            )
            return

        self.x_combo["values"] = columns
        self.y_combo["values"] = columns

        self.x_var.set(columns[0] if self.x_var.get() not in columns else self.x_var.get())
        self.y_var.set(columns[1] if self.y_var.get() not in columns and len(columns) > 1 else (self.y_var.get() or columns[0]))
        if self.y_var.get() not in columns:
            self.y_var.set(columns[1] if len(columns) > 1 else columns[0])
        self.x_period_var.set("All")
        self.manual_start_var.set("")
        self.manual_end_var.set("")
        self.on_x_period_change()
        self.has_plot = False
        self._clear_plot_insights()
        self.show_blur_overlay()

        if len(self.data_frames) == 1:
            self.file_path_var.set(next(iter(self.data_frames)))
        else:
            head_names = list(self.data_frames.keys())[:3]
            suffix = f" ... (+{len(self.data_frames)-3} more)" if len(self.data_frames) > 3 else ""
            self.file_path_var.set(f"{len(self.data_frames)} files: {', '.join(head_names)}{suffix}")

        self._update_preview(first_df.head(20))
        failed_note = f" | skipped: {', '.join(failed_files)}" if failed_files else ""
        self.status_var.set(
            f"Loaded {len(self.data_frames)} file(s), common columns: {len(columns)}{failed_note}"
        )

    def plot_data(self) -> None:
        if not self.data_frames:
            messagebox.showinfo("No data", "Load CSV file(s) first.")
            return

        x_col = self.x_var.get().strip()
        y_col = self.y_var.get().strip()
        if not x_col or not y_col:
            messagebox.showwarning("Missing selection", "Choose X and Y variables.")
            return

        x_period = self.x_period_var.get()
        prepared: list[dict] = []
        skipped_sources: list[str] = []

        for source, frame in self.data_frames.items():
            if x_col not in frame.columns or y_col not in frame.columns:
                skipped_sources.append(source)
                continue

            filtered_df = frame.copy()
            if x_period in self.PERIOD_TO_SLICE:
                total_rows = len(filtered_df)
                start_ratio, end_ratio = self.PERIOD_TO_SLICE[x_period]
                start_idx = int(total_rows * start_ratio)
                end_idx = int(total_rows * end_ratio)
                if end_idx <= start_idx:
                    end_idx = start_idx + 1
                end_idx = min(end_idx, total_rows)
                filtered_df = filtered_df.iloc[start_idx:end_idx].copy()
            elif x_period == "Manual Range":
                try:
                    filtered_df, _ = self._apply_manual_x_range(filtered_df, x_col)
                except ValueError:
                    skipped_sources.append(source)
                    continue

            if filtered_df.empty:
                skipped_sources.append(source)
                continue

            filtered_df[y_col] = pd.to_numeric(filtered_df[y_col], errors="coerce")
            if self._should_parse_x_as_datetime(filtered_df[x_col]):
                parsed_x = pd.to_datetime(filtered_df[x_col], errors="coerce")
                if parsed_x.notna().mean() >= 0.8:
                    filtered_df[x_col] = parsed_x
            else:
                x_numeric = pd.to_numeric(filtered_df[x_col], errors="coerce")
                if x_numeric.notna().mean() >= 0.8:
                    filtered_df[x_col] = x_numeric

            plot_df = filtered_df[[x_col, y_col]].dropna()
            if plot_df.empty:
                skipped_sources.append(source)
                continue

            plot_df = plot_df.sort_values(x_col).reset_index(drop=True)
            y_plot = plot_df[y_col].copy()
            if self.smooth_line_var.get() and len(plot_df) >= 3:
                smooth_window = self._get_smooth_window(len(plot_df))
                if smooth_window >= 2:
                    y_plot = y_plot.rolling(window=smooth_window, center=True, min_periods=1).mean()

            prepared.append(
                {
                    "source": source,
                    "x": plot_df[x_col].reset_index(drop=True),
                    "y": y_plot.reset_index(drop=True),
                    "rows": len(plot_df),
                    "preview": filtered_df.head(20),
                }
            )

        if not prepared:
            messagebox.showwarning("No valid data", "No plot-ready data found for selected variables.")
            return

        self.fig.clf()
        mode = self.plot_mode_var.get()
        colors = plt.cm.tab20(np.linspace(0, 1, max(len(prepared), 2)))
        total_points = int(sum(item["rows"] for item in prepared))

        if mode == "Separate Subplots":
            cols = 2 if len(prepared) > 1 else 1
            rows = math.ceil(len(prepared) / cols)
            axes = self.fig.subplots(rows, cols, squeeze=False)
            flat_axes = [ax for row_axes in axes for ax in row_axes]
            for i, item in enumerate(prepared):
                ax_i = flat_axes[i]
                ax_i.plot(
                    item["x"],
                    item["y"],
                    linewidth=0.75,
                    antialiased=True,
                    color=colors[i % len(colors)],
                    solid_capstyle="round",
                    solid_joinstyle="round",
                )
                ax_i.set_title(item["source"], fontsize=5)
                ax_i.set_xlabel(x_col, fontsize=4.5)
                ax_i.set_ylabel(y_col, fontsize=4.5)
                ax_i.tick_params(axis="both", labelsize=4)
                ax_i.grid(True, alpha=0.28, linestyle="-", linewidth=0.6)
                ax_i.margins(x=0.02, y=0.08)
            for j in range(len(prepared), len(flat_axes)):
                flat_axes[j].set_visible(False)
            self.ax = flat_axes[0]
            self.canvas.draw()
            self._clear_plot_insights()
            self.hover_point_var.set("Hover data: available in Overlay mode")
        else:
            self.ax = self.fig.add_subplot(111)
            hover_x_list: list[pd.Series] = []
            hover_y_list: list[pd.Series] = []
            hover_src_list: list[str] = []
            for i, item in enumerate(prepared):
                self.ax.plot(
                    item["x"],
                    item["y"],
                    linewidth=0.75,
                    antialiased=True,
                    color=colors[i % len(colors)],
                    solid_capstyle="round",
                    solid_joinstyle="round",
                    label=item["source"],
                )
                hover_x_list.append(item["x"])
                hover_y_list.append(item["y"])
                hover_src_list.extend([item["source"]] * len(item["x"]))

            self.ax.set_xlabel(x_col, fontsize=4.5)
            self.ax.set_ylabel(y_col, fontsize=4.5)
            self.ax.set_title(f"{y_col} vs {x_col}", fontsize=5)
            self.ax.tick_params(axis="both", labelsize=4)
            self.ax.grid(True, alpha=0.28, linestyle="-", linewidth=0.7)
            self.ax.margins(x=0.02, y=0.08)
            if len(prepared) > 1:
                self.ax.legend(loc="best", fontsize=4, title="Source", title_fontsize=4.2)
            self.fig.autofmt_xdate()
            self.canvas.draw()
            self._update_hover_cache(
                pd.concat(hover_x_list, ignore_index=True),
                pd.concat(hover_y_list, ignore_index=True),
                x_col,
                y_col,
                source_values=hover_src_list,
            )

        self._update_peak_info_multi(prepared, x_col, y_col)
        self.has_plot = True
        self.hide_blur_overlay()

        self._update_preview(prepared[0]["preview"])
        skipped_note = f" | skipped: {len(skipped_sources)}" if skipped_sources else ""
        self.status_var.set(
            f"Mode: {mode} | files plotted: {len(prepared)} | points: {total_points}{skipped_note} | X period: {x_period}"
        )

    def _update_preview(self, df_head: pd.DataFrame) -> None:
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, df_head.to_string(index=False))


if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()

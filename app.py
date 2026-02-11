import io
from pathlib import Path
import sys
import importlib.util
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

if "seaborn-v0_8-whitegrid" in plt.style.available:
    plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.dpi"] = 160
plt.rcParams["savefig.dpi"] = 300
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
        self.geometry("1200x760")

        self.df: pd.DataFrame | None = None
        self.blur_overlay: tk.Canvas | None = None
        self.has_plot = False
        self.right_panel: tk.Frame | None = None
        self.native_blur_view = None

        self.file_path_var = tk.StringVar(value="No file selected")
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.x_period_var = tk.StringVar(value="All")
        self.manual_start_var = tk.StringVar()
        self.manual_end_var = tk.StringVar()
        self.smooth_line_var = tk.BooleanVar(value=True)
        self.smooth_window_var = tk.StringVar(value="7")
        self.export_dpi_var = tk.StringVar(value="300")
        self.chart_type_var = tk.StringVar(value="Line")
        self.status_var = tk.StringVar(value="Select a CSV file to begin.")

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(main, padding=(0, 0, 12, 0), width=300)
        controls.pack(side=tk.LEFT, fill=tk.Y)
        controls.pack_propagate(False)
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_rowconfigure(22, weight=1)

        ttk.Button(controls, text="Choose CSV", command=self.load_csv).grid(
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

        ttk.Label(controls, text="Chart").grid(row=13, column=0, sticky="w")
        self.chart_combo = ttk.Combobox(
            controls,
            textvariable=self.chart_type_var,
            state="readonly",
            values=["Line", "Scatter"],
        )
        self.chart_combo.grid(row=14, column=0, sticky="ew", pady=(2, 10))

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

        self.fig, self.ax = plt.subplots(figsize=(8.6, 5.8), dpi=180, constrained_layout=True)
        self.fig.patch.set_facecolor("#f8fafc")
        self.ax.set_facecolor("#ffffff")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        if HAS_COCOA:
            self.bind("<Configure>", self._sync_blur_overlay)
            self.right_panel.bind("<Configure>", self._sync_blur_overlay)
            self.after(120, self._ensure_native_blur_overlay)
        else:
            # Fallback blur-like layer for non-macOS environments.
            self.blur_overlay = tk.Canvas(
                self.right_panel,
                highlightthickness=0,
                bd=0,
                bg="#d9d9d9",
            )
            self.blur_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.blur_overlay.bind("<Configure>", self._redraw_blur_overlay)
            self._redraw_blur_overlay()
        self.show_blur_overlay()

    def show_blur_overlay(self) -> None:
        if HAS_COCOA:
            self._ensure_native_blur_overlay()
            if self.native_blur_view is not None:
                self.native_blur_view.setHidden_(False)
                self._sync_blur_overlay()
            return
        if self.blur_overlay is not None:
            self.blur_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.blur_overlay.lift()

    def hide_blur_overlay(self) -> None:
        if HAS_COCOA:
            if self.native_blur_view is not None:
                self.native_blur_view.setHidden_(True)
            return
        if self.blur_overlay is not None:
            self.blur_overlay.place_forget()

    def _ensure_native_blur_overlay(self) -> None:
        if not HAS_COCOA or self.native_blur_view is not None or self.right_panel is None:
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
        self.native_blur_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        content_view.addSubview_(self.native_blur_view)
        self._sync_blur_overlay()

    def _sync_blur_overlay(self, _event: tk.Event | None = None) -> None:
        if not HAS_COCOA or self.native_blur_view is None or self.right_panel is None:
            return

        self.update_idletasks()
        x = self.right_panel.winfo_x()
        y_top = self.right_panel.winfo_y()
        width = max(1, self.right_panel.winfo_width())
        height = max(1, self.right_panel.winfo_height())
        root_height = max(1, self.winfo_height())
        cocoa_y = max(0, root_height - y_top - height)
        self.native_blur_view.setFrame_(NSMakeRect(x, cocoa_y, width, height))

    def _redraw_blur_overlay(self, _event: tk.Event | None = None) -> None:
        if self.blur_overlay is None:
            return
        width = max(1, self.blur_overlay.winfo_width())
        height = max(1, self.blur_overlay.winfo_height())
        self.blur_overlay.delete("all")
        self.blur_overlay.create_rectangle(
            0,
            0,
            width,
            height,
            fill="#f3f3f3",
            outline="",
            stipple="gray50",
        )
        self.blur_overlay.create_rectangle(
            0,
            0,
            width,
            height,
            fill="#ffffff",
            outline="",
            stipple="gray25",
        )

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
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return

        path_obj = Path(file_path)
        if not path_obj.exists() or path_obj.stat().st_size == 0:
            messagebox.showwarning("Invalid file", "Selected file is empty or unavailable.")
            return

        raw_bytes = path_obj.read_bytes()
        if not raw_bytes.strip():
            messagebox.showwarning("Invalid file", "Selected file has no content.")
            return

        csv_text = raw_bytes.decode("utf-8", errors="replace")
        df = pd.read_csv(io.StringIO(csv_text), on_bad_lines="skip")

        if df.empty:
            messagebox.showwarning("No data", "CSV contains no readable rows.")
            return

        df.columns = [str(col).strip() for col in df.columns]
        self.df = df

        columns = self.df.columns.tolist()
        self.x_combo["values"] = columns
        self.y_combo["values"] = columns

        self.x_var.set(columns[0])
        self.y_var.set(columns[1] if len(columns) > 1 else columns[0])
        self.x_period_var.set("All")
        self.manual_start_var.set("")
        self.manual_end_var.set("")
        self.on_x_period_change()
        self.has_plot = False
        self.show_blur_overlay()

        self.file_path_var.set(file_path)
        self._update_preview(self.df.head(20))
        self.status_var.set(f"Loaded {len(self.df)} rows and {len(columns)} columns.")

    def plot_data(self) -> None:
        if self.df is None:
            messagebox.showinfo("No data", "Load a CSV file first.")
            return

        x_col = self.x_var.get().strip()
        y_col = self.y_var.get().strip()
        if not x_col or not y_col:
            messagebox.showwarning("Missing selection", "Choose X and Y variables.")
            return

        filtered_df = self.df.copy()
        x_period = self.x_period_var.get()
        period_note = f"X period: {x_period}"
        if x_period in self.PERIOD_TO_SLICE:
            total_rows = len(filtered_df)
            start_ratio, end_ratio = self.PERIOD_TO_SLICE[x_period]
            start_idx = int(total_rows * start_ratio)
            end_idx = int(total_rows * end_ratio)
            if end_idx <= start_idx:
                end_idx = start_idx + 1
            end_idx = min(end_idx, total_rows)

            filtered_df = filtered_df.iloc[start_idx:end_idx].copy()
            if filtered_df.empty:
                messagebox.showwarning("No rows", "Selected X period slice has no data.")
                return
        elif x_period == "Manual Range":
            try:
                filtered_df, period_note = self._apply_manual_x_range(filtered_df, x_col)
            except ValueError as exc:
                messagebox.showwarning("Invalid manual range", str(exc))
                return

        if filtered_df.empty:
            messagebox.showwarning("No rows", "No rows match the selected X period.")
            return

        filtered_df[y_col] = pd.to_numeric(filtered_df[y_col], errors="coerce")
        if self._should_parse_x_as_datetime(filtered_df[x_col]):
            parsed_x = pd.to_datetime(filtered_df[x_col], errors="coerce")
            x_parse_ratio = parsed_x.notna().mean() if len(parsed_x) else 0.0
            if x_parse_ratio >= 0.8:
                filtered_df[x_col] = parsed_x
        else:
            x_numeric = pd.to_numeric(filtered_df[x_col], errors="coerce")
            x_numeric_ratio = x_numeric.notna().mean() if len(x_numeric) else 0.0
            if x_numeric_ratio >= 0.8:
                filtered_df[x_col] = x_numeric

        plot_df = filtered_df[[x_col, y_col]].dropna()
        if plot_df.empty:
            messagebox.showwarning(
                "No valid data",
                "No valid points remain after filtering and numeric conversion.",
            )
            return

        self.ax.clear()
        if self.chart_type_var.get() == "Line":
            plot_df = plot_df.sort_values(x_col).reset_index(drop=True)
            y_plot = plot_df[y_col].copy()
            if self.smooth_line_var.get() and len(plot_df) >= 3:
                smooth_window = self._get_smooth_window(len(plot_df))
                if smooth_window >= 2:
                    y_plot = y_plot.rolling(window=smooth_window, center=True, min_periods=1).mean()

            self.ax.plot(
                plot_df[x_col],
                y_plot,
                linewidth=2.0,
                antialiased=True,
                color="#1f77b4",
                solid_capstyle="round",
                solid_joinstyle="round",
            )
        else:
            self.ax.scatter(
                plot_df[x_col],
                plot_df[y_col],
                s=22,
                alpha=0.85,
                color="#1f77b4",
                edgecolors="white",
                linewidths=0.4,
            )

        self.ax.set_xlabel(x_col)
        self.ax.set_ylabel(y_col)
        self.ax.set_title(f"{y_col} vs {x_col}")
        self.ax.grid(True, alpha=0.28, linestyle="-", linewidth=0.7)
        self.ax.margins(x=0.02, y=0.08)
        self.fig.autofmt_xdate()
        self.canvas.draw_idle()
        self.has_plot = True
        self.hide_blur_overlay()

        self._update_preview(filtered_df.head(20))
        self.status_var.set(
            f"Plotted {len(plot_df)} points from {len(filtered_df)} rows ({period_note})."
        )

    def _update_preview(self, df_head: pd.DataFrame) -> None:
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, df_head.to_string(index=False))


if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()

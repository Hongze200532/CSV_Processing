import io
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd


class CSVPlotterApp(tk.Tk):
    PERIOD_TO_DAYS = {
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "Last 90 Days": 90,
        "Last 365 Days": 365,
    }
    X_PERIOD_OPTIONS = ["All", *PERIOD_TO_DAYS.keys()]

    def __init__(self) -> None:
        super().__init__()
        self.title("CSV Variable Plotter (Desktop)")
        self.geometry("1200x760")

        self.df: pd.DataFrame | None = None

        self.file_path_var = tk.StringVar(value="No file selected")
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.x_period_var = tk.StringVar(value="All")
        self.chart_type_var = tk.StringVar(value="Line")
        self.status_var = tk.StringVar(value="Select a CSV file to begin.")

        self._build_ui()

    def _build_ui(self) -> None:
        controls = ttk.Frame(self, padding=12)
        controls.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(controls, text="Choose CSV", command=self.load_csv).grid(
            row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="w"
        )
        ttk.Label(controls, textvariable=self.file_path_var).grid(
            row=0, column=1, columnspan=8, sticky="w", pady=(0, 8)
        )

        ttk.Label(controls, text="X variable").grid(row=1, column=0, sticky="w")
        self.x_combo = ttk.Combobox(controls, textvariable=self.x_var, state="readonly", width=20)
        self.x_combo.grid(row=1, column=1, padx=(0, 12), sticky="w")
        self.x_combo.bind("<<ComboboxSelected>>", self.on_x_variable_change)

        ttk.Label(controls, text="Y variable").grid(row=1, column=2, sticky="w")
        self.y_combo = ttk.Combobox(controls, textvariable=self.y_var, state="readonly", width=20)
        self.y_combo.grid(row=1, column=3, padx=(0, 12), sticky="w")

        ttk.Label(controls, text="X period").grid(row=1, column=4, sticky="w")
        self.x_period_combo = ttk.Combobox(
            controls,
            textvariable=self.x_period_var,
            state="readonly",
            width=16,
            values=self.X_PERIOD_OPTIONS,
        )
        self.x_period_combo.grid(row=1, column=5, padx=(0, 12), sticky="w")

        ttk.Label(controls, text="Chart").grid(row=1, column=6, sticky="w")
        self.chart_combo = ttk.Combobox(
            controls,
            textvariable=self.chart_type_var,
            state="readonly",
            width=12,
            values=["Line", "Scatter"],
        )
        self.chart_combo.grid(row=1, column=7, padx=(0, 12), sticky="w")

        ttk.Button(controls, text="Plot", command=self.plot_data).grid(row=1, column=8, sticky="w")

        ttk.Label(controls, textvariable=self.status_var).grid(
            row=2, column=0, columnspan=9, sticky="w", pady=(10, 0)
        )

        content = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        preview_frame = ttk.Frame(content, padding=(0, 8, 8, 8))
        chart_frame = ttk.Frame(content, padding=(8, 8, 0, 8))
        content.add(preview_frame, weight=1)
        content.add(chart_frame, weight=2)

        ttk.Label(preview_frame, text="Data Preview (first 20 rows)").pack(anchor="w")
        self.preview_text = tk.Text(preview_frame, wrap=tk.NONE, height=28)
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.fig, self.ax = plt.subplots(figsize=(7.5, 5.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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

        self.file_path_var.set(file_path)
        self._update_preview(self.df.head(20))
        self.status_var.set(f"Loaded {len(self.df)} rows and {len(columns)} columns.")

    def on_x_variable_change(self, _event: tk.Event) -> None:
        if self.df is None:
            return

        x_col = self.x_var.get().strip()
        if not x_col:
            return

        parsed_x = pd.to_datetime(self.df[x_col], errors="coerce")
        x_parse_ratio = parsed_x.notna().mean() if len(parsed_x) else 0.0
        if x_parse_ratio < 0.5 and self.x_period_var.get() != "All":
            self.x_period_var.set("All")
            messagebox.showinfo(
                "X period reset",
                "Selected X variable is not datetime-like. X period was reset to 'All'.",
            )

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
        parsed_x = pd.to_datetime(filtered_df[x_col], errors="coerce")
        x_parse_ratio = parsed_x.notna().mean() if len(parsed_x) else 0.0

        x_period = self.x_period_var.get()
        if x_period != "All":
            if x_parse_ratio < 0.5:
                messagebox.showwarning(
                    "Invalid X period",
                    "X period filtering requires X variable to be datetime-like.",
                )
                return

            valid_dates = parsed_x.dropna()
            if valid_dates.empty:
                messagebox.showwarning("No datetime values", "Selected X variable has no valid datetime values.")
                return

            days = self.PERIOD_TO_DAYS[x_period]
            end_ts = valid_dates.max()
            start_ts = end_ts - pd.Timedelta(days=days)
            mask = parsed_x.between(start_ts, end_ts)
            filtered_df = filtered_df.loc[mask].copy()
            parsed_x = parsed_x.loc[mask]

        if filtered_df.empty:
            messagebox.showwarning("No rows", "No rows match the selected X period.")
            return

        filtered_df[y_col] = pd.to_numeric(filtered_df[y_col], errors="coerce")
        if x_parse_ratio >= 0.8:
            filtered_df[x_col] = parsed_x

        plot_df = filtered_df[[x_col, y_col]].dropna()
        if plot_df.empty:
            messagebox.showwarning(
                "No valid data",
                "No valid points remain after filtering and numeric conversion.",
            )
            return

        self.ax.clear()
        if self.chart_type_var.get() == "Line":
            self.ax.plot(plot_df[x_col], plot_df[y_col], linewidth=1.5)
        else:
            self.ax.scatter(plot_df[x_col], plot_df[y_col], s=18)

        self.ax.set_xlabel(x_col)
        self.ax.set_ylabel(y_col)
        self.ax.set_title(f"{y_col} vs {x_col}")
        self.ax.grid(True, alpha=0.35)
        self.fig.autofmt_xdate()
        self.canvas.draw_idle()

        self._update_preview(filtered_df.head(20))
        self.status_var.set(
            f"Plotted {len(plot_df)} points from {len(filtered_df)} rows (X period: {x_period})."
        )

    def _update_preview(self, df_head: pd.DataFrame) -> None:
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, df_head.to_string(index=False))


if __name__ == "__main__":
    app = CSVPlotterApp()
    app.mainloop()

import io
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd


class CSVPlotterApp(tk.Tk):
    PERIOD_TO_SLICE = {
        "First 10%": (0.00, 0.10),
        "First 25%": (0.00, 0.25),
        "Middle 50%": (0.25, 0.75),
        "Last 25%": (0.75, 1.00),
        "Last 10%": (0.90, 1.00),
    }
    X_PERIOD_OPTIONS = ["All", *PERIOD_TO_SLICE.keys()]

    def __init__(self) -> None:
        super().__init__()
        self.title("CSV Variable Plotter (Desktop)")
        self.geometry("1200x760")

        self.df: pd.DataFrame | None = None
        self.blur_overlay: tk.Canvas | None = None

        self.file_path_var = tk.StringVar(value="No file selected")
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.x_period_var = tk.StringVar(value="All")
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
        controls.grid_rowconfigure(10, weight=1)

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

        ttk.Label(controls, text="Chart").grid(row=9, column=0, sticky="w")
        self.chart_combo = ttk.Combobox(
            controls,
            textvariable=self.chart_type_var,
            state="readonly",
            values=["Line", "Scatter"],
        )
        self.chart_combo.grid(row=10, column=0, sticky="ew", pady=(2, 10))

        ttk.Button(controls, text="Plot", command=self.plot_data).grid(
            row=11, column=0, sticky="ew", pady=(6, 10)
        )

        ttk.Label(controls, textvariable=self.status_var, wraplength=260, justify="left").grid(
            row=12, column=0, sticky="sw"
        )

        right_panel = tk.Frame(main, bg="#efefef")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content = ttk.Panedwindow(right_panel, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True)

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

        # Simulated blur layer on the non-control area.
        self.blur_overlay = tk.Canvas(
            right_panel,
            highlightthickness=0,
            bd=0,
            bg="#d9d9d9",
        )
        self.blur_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.blur_overlay.bind("<Configure>", self._redraw_blur_overlay)
        self._redraw_blur_overlay()

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
            fill="#d8d8d8",
            outline="",
            stipple="gray50",
        )
        self.blur_overlay.create_rectangle(
            0,
            0,
            width,
            height,
            fill="#eeeeee",
            outline="",
            stipple="gray25",
        )
        self.blur_overlay.create_text(
            width // 2,
            height // 2,
            text="Blurred Area",
            fill="#666666",
            font=("Helvetica", 16, "bold"),
        )

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
        if x_period != "All":
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

        if filtered_df.empty:
            messagebox.showwarning("No rows", "No rows match the selected X period.")
            return

        parsed_x = pd.to_datetime(filtered_df[x_col], errors="coerce")
        x_parse_ratio = parsed_x.notna().mean() if len(parsed_x) else 0.0
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

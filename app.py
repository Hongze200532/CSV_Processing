import io
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

# If someone runs `python app.py`, exit early with a clear command.
if __name__ == "__main__" and "streamlit" not in (sys.argv[0] or "").lower():
    print("This is a Streamlit app. Run it with: streamlit run app.py")
    raise SystemExit(0)

st.set_page_config(page_title="CSV Variable Plotter", layout="wide")


def try_parse_datetime(series: pd.Series) -> tuple[pd.Series, float]:
    parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
    ratio = parsed.notna().mean() if len(series) else 0.0
    return parsed, float(ratio)


def stop_app(code: int = 0) -> None:
    """Stop in Streamlit mode and also exit cleanly in bare Python mode."""
    st.stop()
    raise SystemExit(code)


st.title("CSV Variable Plotter")
st.caption(
    "Upload a CSV file, choose two variables, optionally filter by a time period, and generate a 2D plot."
)

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file to begin.")
    stop_app()

raw_bytes = uploaded_file.getvalue()
if not raw_bytes.strip():
    st.warning("The uploaded file is empty.")
    stop_app()

# Decode safely and skip malformed rows so this path doesn't rely on try/except.
csv_text = raw_bytes.decode("utf-8", errors="replace")
df = pd.read_csv(io.StringIO(csv_text), on_bad_lines="skip")

if df.empty:
    st.warning("The uploaded CSV file is empty.")
    stop_app()

# Clean column names for easier selection in UI.
df.columns = [str(col).strip() for col in df.columns]
columns = df.columns.tolist()

st.subheader("Data Preview")
st.dataframe(df.head(50), use_container_width=True)

with st.sidebar:
    st.header("Plot Settings")
    x_col = st.selectbox("X variable", columns, index=0)
    y_col = st.selectbox("Y variable", columns, index=1 if len(columns) > 1 else 0)

    # Let users pick a column representing period/time for filtering.
    filter_col = st.selectbox("Period filter column (optional)", ["(None)"] + columns)

    parsed_filter_dates = None
    if filter_col != "(None)":
        parsed_filter_dates, parse_ratio = try_parse_datetime(df[filter_col])
        if parse_ratio < 0.5:
            st.warning(
                "Selected period column does not look like datetime values. "
                "Choose a datetime-like column for time-period filtering."
            )
            parsed_filter_dates = None

    start_ts = end_ts = None
    if parsed_filter_dates is not None:
        valid_dates = parsed_filter_dates.dropna()
        if valid_dates.empty:
            st.warning("No valid datetime values found in selected period column.")
        else:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_range = st.date_input(
                "Select time period",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_ts = pd.Timestamp(date_range[0])
                end_ts = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    chart_type = st.radio("Chart type", ["Line", "Scatter"], horizontal=True)

filtered_df = df.copy()

if parsed_filter_dates is not None and start_ts is not None and end_ts is not None:
    mask = parsed_filter_dates.between(start_ts, end_ts)
    filtered_df = filtered_df.loc[mask].copy()

if filtered_df.empty:
    st.warning("No rows match the selected time period.")
    stop_app()

# Convert Y to numeric for mathematical-style 2D plots.
filtered_df[y_col] = pd.to_numeric(filtered_df[y_col], errors="coerce")

# If X can be parsed as datetime, use datetime to improve axis formatting.
parsed_x_dates, x_parse_ratio = try_parse_datetime(filtered_df[x_col])
if x_parse_ratio >= 0.8:
    filtered_df[x_col] = parsed_x_dates

plot_df = filtered_df[[x_col, y_col]].dropna()

if plot_df.empty:
    st.warning("No valid data points remain after filtering and type conversion.")
    stop_app()

st.subheader("2D Plot")
if chart_type == "Line":
    fig = px.line(plot_df, x=x_col, y=y_col)
else:
    fig = px.scatter(plot_df, x=x_col, y=y_col)

fig.update_layout(
    xaxis_title=x_col,
    yaxis_title=y_col,
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)
st.caption(f"Showing {len(plot_df)} points from {len(filtered_df)} filtered rows.")

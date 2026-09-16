"""
Electricity Consumption Forecasting — Streamlit prototype

A single-file dashboard that ingests a CSV time-series of electricity
consumption, auto-detects the datetime + target columns, engineers
calendar/lag features, trains three regression models (Linear Regression,
Random Forest, XGBoost), compares them, and produces a future forecast.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import io
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Electricity Consumption Forecasting",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCENT_BLUE = "#00B4FF"
ACCENT_AMBER = "#FFB703"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def detect_datetime_column(df: pd.DataFrame) -> str | None:
    """Return the first column that looks like a datetime, else None."""
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
        # Try parsing as datetime on a small sample.
        sample = df[col].dropna().astype(str).head(20)
        if len(sample) == 0:
            continue
        try:
            pd.to_datetime(sample, errors="raise")
            return col
        except (ValueError, TypeError):
            continue
    # Name-based fallback.
    for col in df.columns:
        lname = col.lower()
        if any(k in lname for k in ("date", "time", "datetime", "timestamp")):
            return col
    return None


def detect_target_column(df: pd.DataFrame, datetime_col: str | None) -> str | None:
    """Return the best numeric column candidate for the consumption target."""
    numeric = df.select_dtypes(include="number").columns.tolist()
    if datetime_col and datetime_col in numeric:
        numeric.remove(datetime_col)
    if not numeric:
        return None
    # Prefer a column whose name hints at consumption/load/energy.
    for col in numeric:
        lname = col.lower()
        if any(k in lname for k in ("consum", "load", "energy", "power", "usage", "kwh", "mw")):
            return col
    return numeric[0]


def infer_freq(df: pd.DataFrame, datetime_col: str) -> str:
    """Infer 'H' (hourly) or 'D' (daily) from the median time delta."""
    if len(df) < 3:
        return "D"
    deltas = df[datetime_col].sort_values().diff().dropna()
    if deltas.empty:
        return "D"
    median_minutes = deltas.median().total_seconds() / 60.0
    if median_minutes <= 90:
        return "H"
    return "D"


@st.cache_data(show_spinner="Cleaning and engineering features…")
def load_and_prepare(uploaded_bytes: bytes, datetime_col: str, target_col: str) -> dict:
    """Parse CSV, clean, engineer features, and split chronologically.

    Returns a dict with the prepared DataFrame, train/test splits, feature
    lists, inferred frequency, and missing-value handling report.
    """
    df = pd.read_csv(io.BytesIO(uploaded_bytes))

    # --- Datetime parsing & chronological sort ---
    df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce")
    df = df.dropna(subset=[datetime_col]).sort_values(datetime_col).reset_index(drop=True)

    # --- Keep only target + datetime for the series, then handle missing ---
    df = df[[datetime_col, target_col]].copy()
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce")

    missing_before = int(df[target_col].isna().sum())
    # Forward-fill, then interpolate any remaining leading gaps.
    df[target_col] = df[target_col].ffill().interpolate()
    # Drop any residual NaNs at the very edges.
    df = df.dropna(subset=[target_col]).reset_index(drop=True)
    missing_after = int(df[target_col].isna().sum())

    # --- Frequency inference ---
    freq = infer_freq(df, datetime_col)

    # --- Feature engineering ---
    dt = df[datetime_col]
    df["hour"] = dt.dt.hour
    df["dayofweek"] = dt.dt.dayofweek
    df["month"] = dt.dt.month
    df["is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)

    if freq == "H":
        df["lag_1"] = df[target_col].shift(1)
        df["lag_24"] = df[target_col].shift(24)
        lag_cols = ["lag_1", "lag_24"]
    else:
        df["lag_1"] = df[target_col].shift(1)
        df["lag_7"] = df[target_col].shift(7)
        lag_cols = ["lag_1", "lag_7"]

    feature_cols = ["hour", "dayofweek", "month", "is_weekend"] + lag_cols

    df = df.dropna(subset=feature_cols).reset_index(drop=True)

    # --- Chronological 80/20 split ---
    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]

    return {
        "df": df,
        "train": train,
        "test": test,
        "feature_cols": feature_cols,
        "target_col": target_col,
        "datetime_col": datetime_col,
        "freq": freq,
        "missing_before": missing_before,
        "missing_after": missing_after,
    }


def _make_model(name: str):
    if name == "Linear Regression":
        return LinearRegression()
    if name == "Random Forest":
        return RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=-1)
    if name == "XGBoost":
        return XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.9,
            random_state=42,
            n_jobs=-1,
        )
    raise ValueError(f"Unknown model: {name}")


@st.cache_resource(show_spinner=False)
def train_all_models(_data: dict) -> dict:
    """Train all three models on the train split and return predictions + metrics.

    Cached with @st.cache_resource so switching views won't retrain.
    The leading underscore on _data signals Streamlit not to hash its contents.
    """
    train, test = _data["train"], _data["test"]
    feature_cols = _data["feature_cols"]
    target_col = _data["target_col"]

    X_train = train[feature_cols]
    y_train = train[target_col]
    X_test = test[feature_cols]
    y_test = test[target_col]

    results: dict = {}
    for name in ("Linear Regression", "Random Forest", "XGBoost"):
        model = _make_model(name)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = r2_score(y_test, preds)
        results[name] = {
            "model": model,
            "preds": preds,
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
        }
    return results


@st.cache_resource(show_spinner=False)
def train_full_and_forecast(_data: dict, model_name: str, horizon: int) -> pd.DataFrame:
    """Train the selected model on the full dataset and forecast `horizon` steps.

    Returns a DataFrame with datetime + forecast columns.
    """
    df = _data["df"]
    feature_cols = _data["feature_cols"]
    target_col = _data["target_col"]
    datetime_col = _data["datetime_col"]
    freq = _data["freq"]

    X = df[feature_cols]
    y = df[target_col]

    model = _make_model(model_name)
    model.fit(X, y)

    last_ts = df[datetime_col].iloc[-1]
    step = pd.Timedelta(hours=1) if freq == "H" else pd.Timedelta(days=1)

    future_rows = []
    cur_ts = last_ts + step
    # Keep a rolling view of recent target values for lag construction.
    recent = df[target_col].tolist()

    for _ in range(horizon):
        hour = cur_ts.hour
        dow = cur_ts.dayofweek
        month = cur_ts.month
        is_weekend = int(dow >= 5)

        if freq == "H":
            lag_1 = recent[-1]
            lag_24 = recent[-24] if len(recent) >= 24 else recent[-1]
            row = [hour, dow, month, is_weekend, lag_1, lag_24]
        else:
            lag_1 = recent[-1]
            lag_7 = recent[-7] if len(recent) >= 7 else recent[-1]
            row = [hour, dow, month, is_weekend, lag_1, lag_7]

        pred = float(model.predict([row])[0])
        future_rows.append({datetime_col: cur_ts, "forecast": pred})
        recent.append(pred)
        cur_ts += step

    return pd.DataFrame(future_rows)


def kpi_card(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)


# ---------------------------------------------------------------------------
# App header
# ---------------------------------------------------------------------------
st.title("⚡ Electricity Consumption Forecasting")
st.caption(
    "Upload a time-series CSV, compare three models, and forecast future "
    "consumption. Auto-detects the datetime and target columns."
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded is None:
        st.info("No file uploaded yet. Add a CSV to begin.")
    else:
        st.success(f"Loaded: {uploaded.name}")

    st.divider()
    model_choice = st.selectbox(
        "Model",
        ["Linear Regression", "Random Forest", "XGBoost"],
        index=2,
    )
    horizon = st.number_input(
        "Forecast horizon (future steps)",
        min_value=1,
        max_value=336,
        value=24,
        help="Number of future hours (if hourly data) or days (if daily) to predict.",
    )
    forecast_btn = st.button("Generate Forecast", type="primary")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
if uploaded is None:
    st.warning("Please upload a CSV file from the sidebar to get started.")
    st.stop()

# Read bytes once (cached downstream).
raw_bytes = uploaded.getvalue()

# Peek to auto-detect columns.
try:
    peek = pd.read_csv(io.BytesIO(raw_bytes), nrows=50)
except Exception as exc:
    st.error(f"Could not read the CSV: {exc}")
    st.stop()

auto_dt = detect_datetime_column(peek)
auto_target = detect_target_column(peek, auto_dt)

with st.sidebar:
    st.divider()
    st.subheader("Columns")
    dt_col = st.selectbox(
        "Datetime column",
        peek.columns.tolist(),
        index=peek.columns.get_loc(auto_dt) if auto_dt else 0,
    )
    target_col = st.selectbox(
        "Target column (consumption)",
        peek.select_dtypes(include="number").columns.tolist() or peek.columns.tolist(),
        index=(
            peek.select_dtypes(include="number").columns.get_loc(auto_target)
            if auto_target and auto_target in peek.select_dtypes(include="number").columns
            else 0
        ),
    )
    if st.button("Re-run detection"):
        auto_dt = detect_datetime_column(peek)
        auto_target = detect_target_column(peek, auto_dt)
        st.rerun()

if dt_col is None or target_col is None:
    st.error("Could not determine datetime or target column. Please select them in the sidebar.")
    st.stop()

# Prepare data.
with st.spinner("Cleaning data and engineering features…"):
    data = load_and_prepare(raw_bytes, dt_col, target_col)

df = data["df"]
freq_label = "hourly" if data["freq"] == "H" else "daily"

# Friendly missing-value note.
m_before = data["missing_before"]
if m_before > 0:
    st.info(
        f"Filled **{m_before}** missing target values (forward-fill + interpolation). "
        f"Remaining missing: {data['missing_after']}."
    )

# Train all models (cached).
with st.spinner("Training Linear Regression, Random Forest, and XGBoost…"):
    results = train_all_models(data)

# Best model by R².
best_name = max(results, key=lambda k: results[k]["r2"])
best_r2 = results[best_name]["r2"]

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
st.subheader("Overview")
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Total records", f"{len(df):,}")
with k2:
    kpi_card("Date range", f"{df[dt_col].iloc[0]:%Y-%m-%d} → {df[dt_col].iloc[-1]:%Y-%m-%d}")
with k3:
    kpi_card("Avg. consumption", f"{df[target_col].mean():,.2f}")
with k4:
    kpi_card("Best model (R²)", f"{best_name}", delta=f"R² = {best_r2:.3f}")

st.write("")

# ---------------------------------------------------------------------------
# Tabs: Comparison | Actual vs Predicted | Forecast
# ---------------------------------------------------------------------------
tab_compare, tab_actual, tab_forecast = st.tabs(
    ["Model Comparison", "Actual vs Predicted", "Forecast"]
)

# --- Tab 1: Model comparison ----------------------------------------------
with tab_compare:
    st.subheader("Model Comparison")

    metrics_df = pd.DataFrame(
        {
            "Model": list(results.keys()),
            "MAE": [results[m]["mae"] for m in results],
            "RMSE": [results[m]["rmse"] for m in results],
            "R²": [results[m]["r2"] for m in results],
        }
    ).set_index("Model")

    st.dataframe(
        metrics_df.style.format({"MAE": "{:.3f}", "RMSE": "{:.3f}", "R²": "{:.3f}"}),
        use_container_width=True,
    )

    # Grouped bar chart of metrics.
    fig = go.Figure()
    for metric in ("MAE", "RMSE", "R²"):
        fig.add_trace(
            go.Bar(
                x=metrics_df.index,
                y=metrics_df[metric],
                name=metric,
                text=metrics_df[metric].round(3),
                textposition="outside",
            )
        )
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="#0A1A2F",
        plot_bgcolor="#0A1A2F",
        font=dict(color="#E6EEF8"),
        title="MAE, RMSE and R² across models",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 2: Actual vs Predicted -------------------------------------------
with tab_actual:
    st.subheader(f"Actual vs Predicted — {model_choice}")
    test = data["test"]
    preds = results[model_choice]["preds"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=test[dt_col],
            y=test[target_col],
            mode="lines",
            name="Actual",
            line=dict(color=ACCENT_BLUE, width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=test[dt_col],
            y=preds,
            mode="lines",
            name=f"Predicted ({model_choice})",
            line=dict(color=ACCENT_AMBER, width=2, dash="dash"),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0A1A2F",
        plot_bgcolor="#0A1A2F",
        font=dict(color="#E6EEF8"),
        xaxis_title="Time",
        yaxis_title="Consumption",
        hovermode="x unified",
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    m = results[model_choice]
    c1, c2, c3 = st.columns(3)
    c1.metric("MAE", f"{m['mae']:.3f}")
    c2.metric("RMSE", f"{m['rmse']:.3f}")
    c3.metric("R²", f"{m['r2']:.3f}")

# --- Tab 3: Forecast ------------------------------------------------------
with tab_forecast:
    st.subheader("Forecast")

    if forecast_btn:
        with st.spinner(f"Training {model_choice} on full data and forecasting {horizon} {freq_label} steps…"):
            future = train_full_and_forecast(data, model_choice, int(horizon))

        st.success(f"Forecasted {len(future)} future {freq_label} steps.")

        # Combine actual + forecast with a vertical marker at the boundary.
        actual = df[[dt_col, target_col]].rename(columns={target_col: "actual"})
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=actual[dt_col],
                y=actual["actual"],
                mode="lines",
                name="Actual",
                line=dict(color=ACCENT_BLUE, width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=future[dt_col],
                y=future["forecast"],
                mode="lines",
                name="Forecast",
                line=dict(color=ACCENT_AMBER, width=2, dash="dash"),
            )
        )
        # Vertical marker at "today" (last actual timestamp).
        fig.add_vline(
            x=actual[dt_col].iloc[-1],
            line_dash="dot",
            line_color="#FF6B6B",
            annotation_text="today",
            annotation_position="top left",
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A1A2F",
            plot_bgcolor="#0A1A2F",
            font=dict(color="#E6EEF8"),
            xaxis_title="Time",
            yaxis_title="Consumption",
            hovermode="x unified",
            height=480,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(future.rename(columns={"forecast": "Forecast"}), use_container_width=True)
    else:
        st.info(
            f"Set a horizon in the sidebar and click **Generate Forecast** to "
            f"see the next {int(horizon)} {freq_label} steps."
        )

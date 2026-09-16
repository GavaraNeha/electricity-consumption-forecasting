# ⚡ Electricity Consumption Forecasting

A Streamlit web app that ingests an electricity/energy consumption time-series CSV, auto-detects the datetime and target columns, engineers features, trains three regression models, compares them, and forecasts future consumption.

Built as a college Machine Learning project demo.

---

## Features

- **CSV upload & auto-detection** — Upload any time-series CSV through the app. The datetime and consumption columns are auto-detected by type and name, with manual override via dropdowns.
- **Data cleaning** — Parses the datetime column, sorts chronologically, and handles missing values via forward-fill + interpolation (reports how many rows were affected).
- **Feature engineering** — Creates calendar features (hour, day-of-week, month, is_weekend) and lag features (`lag_1`, `lag_24` for hourly data; `lag_1`, `lag_7` for daily data).
- **Chronological split** — 80% train / 20% test with no shuffling, preserving time order.
- **Three models trained & compared:**
  - Linear Regression
  - Random Forest Regressor
  - XGBoost Regressor
- **Metrics** — MAE, RMSE, and R² computed for each model on the test set.
- **Caching** — Trained models are cached with `@st.cache_resource` so switching views doesn't retrain from scratch.
- **Interactive Plotly charts** — Model comparison bar chart, actual-vs-predicted line chart with hover tooltips, and a forecast chart with a dashed future extension and a "today" vertical marker.
- **Custom dark theme** — Dark navy background with electric-blue and amber accents (energy/electricity feel) via `.streamlit/config.toml`.

---

## Dashboard Layout

1. **Sidebar** — CSV uploader, column selectors, model selector, and forecast horizon input.
2. **KPI cards** — Total records, date range, average consumption, and best-performing model with its R².
3. **Model Comparison tab** — Bar chart comparing MAE, RMSE, and R² across all three models, plus a metrics table.
4. **Actual vs Predicted tab** — Interactive line chart overlaying actual test-period values and the selected model's predictions.
5. **Forecast tab** — Trains the selected model on the full dataset and plots forecasted future values as a dashed-line extension with a "today" marker.

---

## Tech Stack

| Component       | Library           |
|-----------------|-------------------|
| Web framework   | Streamlit         |
| Data handling   | pandas, numpy     |
| ML models       | scikit-learn, xgboost |
| Charts          | Plotly            |

---

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

Then upload your CSV through the sidebar and explore the dashboard.

---

## Expected CSV Format

Any time-series CSV with at minimum:

- A **datetime column** (e.g., `timestamp`, `date`, `datetime`) — auto-detected
- A **numeric consumption column** (e.g., `consumption_kwh`, `load_mw`, `energy`) — auto-detected

Optional columns (e.g., temperature, weather) are ignored by the pipeline but won't cause errors.

**Example:**

| timestamp            | consumption_kwh |
|----------------------|-----------------|
| 2024-01-01 00:00:00  | 512.3           |
| 2024-01-01 01:00:00  | 498.7           |
| 2024-01-01 02:00:00  | 475.1           |

---

## Project Structure

```
.
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Custom dark theme
└── README.md
```

---

## License

For educational use — college ML project demo.

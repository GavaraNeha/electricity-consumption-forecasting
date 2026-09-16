"""
Cyber-Eco Smart Grid theme for Streamlit.

Usage in app.py:
    from cyber_eco_theme import inject_custom_css, render_kpi_card, render_model_badge

    st.set_page_config(page_title="Ecolectric Smart City", layout="wide")
    inject_custom_css()

    # Replace your KPI st.metric() calls with:
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi_card("Total Records", "260,616")
    with c2: render_kpi_card("Date Range", "2007-01-01 → Present")
    with c3: render_kpi_card("Avg. Consumption", "1.16 kWh")
    with c4: render_model_badge("Linear Regression", 0.828)
"""

import streamlit as st


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

        :root{
            --bg-deep:#0B132B;
            --bg-panel:#1C2541;
            --cyan:#00F5D4;
            --blue:#00BBF9;
            --green:#38B000;
            --green-light:#70E000;
            --amber:#FFB100;
            --glass-bg:rgba(30,41,59,0.55);
            --glass-bg-strong:rgba(15,23,42,0.65);
            --glass-border:rgba(0,245,212,0.20);
        }

        /* ---------- Base canvas ---------- */
        html, body, [data-testid="stAppViewContainer"]{
            background:
                radial-gradient(circle at 15% 10%, rgba(0,245,212,0.10), transparent 40%),
                radial-gradient(circle at 85% 0%, rgba(0,187,249,0.10), transparent 45%),
                radial-gradient(circle at 50% 100%, rgba(56,176,0,0.08), transparent 50%),
                repeating-linear-gradient(0deg, rgba(0,245,212,0.035) 0px, rgba(0,245,212,0.035) 1px, transparent 1px, transparent 42px),
                repeating-linear-gradient(90deg, rgba(0,245,212,0.035) 0px, rgba(0,245,212,0.035) 1px, transparent 1px, transparent 42px),
                var(--bg-deep) !important;
            font-family:'Inter', sans-serif;
        }

        h1, h2, h3 {
            font-family:'Plus Jakarta Sans', sans-serif !important;
            font-weight:800 !important;
            color:#EAF6FF !important;
            text-shadow: 0 0 18px rgba(0,245,212,0.35);
            letter-spacing:0.3px;
        }

        /* ---------- Sidebar: glass panel ---------- */
        section[data-testid="stSidebar"] > div{
            background:var(--glass-bg-strong) !important;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-right:1px solid var(--glass-border);
        }
        section[data-testid="stSidebar"] * { color:#DCEFFF !important; }
        section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3{
            text-shadow:none !important;
        }

        /* ---------- File uploader dropzone ---------- */
        [data-testid="stFileUploaderDropzone"]{
            background:var(--glass-bg) !important;
            border:1.5px dashed var(--cyan) !important;
            border-radius:14px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        }

        /* ---------- Buttons: neon gradient glow ---------- */
        .stButton>button, .stDownloadButton>button{
            background: linear-gradient(135deg, var(--cyan), var(--blue)) !important;
            color:#03141C !important;
            font-weight:700 !important;
            border:none !important;
            border-radius:12px !important;
            padding:0.6em 1.4em !important;
            box-shadow: 0 0 18px rgba(0,245,212,0.45), 0 0 2px rgba(0,245,212,0.9);
            transition: all 0.25s ease;
        }
        .stButton>button:hover, .stDownloadButton>button:hover{
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 0 28px rgba(0,245,212,0.75), 0 0 6px rgba(0,245,212,1);
        }

        /* ---------- Tabs ---------- */
        [data-baseweb="tab-list"]{ gap:6px; }
        [data-baseweb="tab"]{
            background:var(--glass-bg) !important;
            border:1px solid var(--glass-border) !important;
            border-radius:10px 10px 0 0 !important;
            color:#B9D9E8 !important;
        }
        [aria-selected="true"][data-baseweb="tab"]{
            color:#03141C !important;
            background: linear-gradient(135deg, var(--cyan), var(--blue)) !important;
            box-shadow:0 0 16px rgba(0,245,212,0.5);
        }

        /* ---------- Dataframes / tables ---------- */
        [data-testid="stDataFrame"], [data-testid="stTable"]{
            background:var(--glass-bg) !important;
            border:1px solid var(--glass-border) !important;
            border-radius:14px !important;
            backdrop-filter: blur(14px);
        }

        /* ---------- Alerts (info/success boxes) ---------- */
        div[data-testid="stAlert"]{
            background:var(--glass-bg) !important;
            border:1px solid var(--glass-border) !important;
            border-radius:12px !important;
            backdrop-filter: blur(14px);
        }

        /* ---------- Floating HUD cards ---------- */
        @keyframes floatY {
            0%   { transform: translateY(0px); }
            50%  { transform: translateY(-6px); }
            100% { transform: translateY(0px); }
        }
        .hud-card{
            background:var(--glass-bg);
            border:1px solid var(--glass-border);
            border-radius:16px;
            padding:18px 20px;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.10),
                0 8px 30px rgba(0,0,0,0.35);
            animation: floatY 5s ease-in-out infinite;
            transition: box-shadow 0.25s ease, transform 0.25s ease;
        }
        .hud-card:hover{
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.15),
                0 0 26px rgba(0,245,212,0.35),
                0 10px 34px rgba(0,0,0,0.4);
        }
        .hud-label{
            font-size:0.78rem; text-transform:uppercase; letter-spacing:1.4px;
            color:#8FB6C9; margin-bottom:6px; font-weight:600;
        }
        .hud-value{
            font-family:'JetBrains Mono', monospace;
            font-size:1.6rem; font-weight:700; color:#EAF6FF;
        }
        .hud-value.accent-green{ color:var(--green-light); text-shadow:0 0 12px rgba(112,224,0,0.5); }
        .hud-value.accent-cyan{ color:var(--cyan); text-shadow:0 0 12px rgba(0,245,212,0.5); }
        .hud-value.accent-amber{ color:var(--amber); text-shadow:0 0 12px rgba(255,177,0,0.5); }

        /* ---------- Model performance pill ---------- */
        .model-pill{
            display:inline-block; padding:4px 12px; border-radius:999px;
            background:rgba(56,176,0,0.18); border:1px solid rgba(112,224,0,0.45);
            color:var(--green-light); font-family:'JetBrains Mono', monospace;
            font-weight:700; font-size:0.85rem; margin-top:8px;
        }

        /* ---------- App header banner ---------- */
        .eco-header{
            display:flex; align-items:center; gap:14px;
            padding:22px 26px; border-radius:18px; margin-bottom:22px;
            background:linear-gradient(120deg, rgba(0,245,212,0.10), rgba(0,187,249,0.06), rgba(56,176,0,0.08));
            border:1px solid var(--glass-border);
            backdrop-filter: blur(16px);
        }
        .eco-header .leaf{ font-size:2.2rem; filter: drop-shadow(0 0 10px rgba(112,224,0,0.7)); }
        .eco-header h1{ margin:0 !important; font-size:1.9rem !important; }
        .eco-header p{ margin:2px 0 0 0; color:#9FC6D8; font-size:0.95rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title="Ecolectric Smart City", subtitle="Sustainable Power Consumption Forecasting"):
    st.markdown(
        f"""
        <div class="eco-header">
            <div class="leaf">⚡🌿</div>
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, accent: str = "cyan"):
    """accent: 'cyan' | 'green' | 'amber' | '' (plain white)"""
    accent_class = f"accent-{accent}" if accent else ""
    st.markdown(
        f"""
        <div class="hud-card">
            <div class="hud-label">{label}</div>
            <div class="hud-value {accent_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_badge(model_name: str, r2: float):
    st.markdown(
        f"""
        <div class="hud-card">
            <div class="hud-label">Best Model (R²)</div>
            <div class="hud-value accent-green">{model_name}</div>
            <div class="model-pill">↑ R² = {r2:.3f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

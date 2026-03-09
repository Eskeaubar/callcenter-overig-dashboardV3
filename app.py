import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, date
import re

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="KCC Categorie Overige",
    layout="wide"
)

# ------------------------------------------------
# VWE STYLE
# ------------------------------------------------

st.markdown("""
<style>

.main-header {
background:#2fb463;
padding:20px;
border-radius:10px;
display:flex;
align-items:center;
gap:20px;
}

.main-title {
font-size:32px;
font-weight:700;
color:white;
}

.sub-title {
font-size:16px;
color:white;
}

.podium-card{
background:#d9f2e3;
border-radius:12px;
padding:25px;
text-align:center;
height:260px;
display:flex;
flex-direction:column;
justify-content:center;
box-shadow:0 6px 18px rgba(0,0,0,0.2);
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# HEADER MET LOGO
# ------------------------------------------------

col1, col2 = st.columns([1,6])

with col1:
    st.image("logo_vwe.png", width=120)

with col2:
    st.markdown("""
    <div class="main-header">
        <div>
            <div class="main-title">KCC Categorie Overige</div>
            <div class="sub-title">Analyse dashboard</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------

uploaded_file = st.file_uploader("Upload CRM Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = ["Onderwerp","Beschrijving","Gemaakt op","Gemaakt door"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom ontbreekt: {col}")
            st.stop()

    # ------------------------------------------------
    # DATA PREP
    # ------------------------------------------------

    df["Beschrijving"] = df["Beschrijving"].astype(str).str.lower()
    df["Gemaakt op"] = pd.to_datetime(df["Gemaakt op"], dayfirst=True)
    df = df.dropna(subset=["Gemaakt op"])

    df["datum"] = df["Gemaakt op"].dt.date

    # alleen werkdagen
    df["weekday"] = pd.to_datetime(df["datum"]).dt.weekday
    df = df[df["weekday"] < 5]

    dataset_start = df["datum"].min()
    dataset_end = df["datum"].max()

    df["Overig_flag"] = df["Onderwerp"].str.lower().str.contains("overig")

    # ------------------------------------------------
    # FILTERS
    # ------------------------------------------------

    st.sidebar.header("Filters")

    filter_optie = st.sidebar.selectbox(
        "Periode",
        [
            "Alles",
            "Gisteren",
            "Afgelopen week",
            "Afgelopen maand",
            "Afgelopen kalender maand",
            "Aangepaste periode"
        ]
    )

    max_date = dataset_end
    min_date = dataset_start

    if filter_optie == "Gisteren":
        start = max_date - timedelta(days=1)
        end = max_date

    elif filter_optie == "Afgelopen week":
        start = max_date - timedelta(days=7)
        end = max_date

    elif filter_optie == "Afgelopen maand":
        start = max_date - timedelta(days=30)
        end = max_date

    elif filter_optie == "Afgelopen kalender maand":

        first_day_current_month = date(max_date.year, max_date.month, 1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)

        start = date(last_day_previous_month.year, last_day_previous_month.month, 1)
        end = last_day_previous_month

    elif filter_optie == "Aangepaste periode":

        start = st.sidebar.date_input("Startdatum", min_date)
        end = st.sidebar.date_input("Einddatum", max_date)

    else:

        start = min_date
        end = max_date

    df = df[(df["datum"] >= start) & (df["datum"] <= end)]

    # ------------------------------------------------
    # KPI
    # ------------------------------------------------

    total_calls = len(df)
    overig_calls = df["Overig_flag"].sum()

    st.header("📊 KPI Overzicht")

    st.info(
        f"Analyseperiode dataset: {dataset_start.strftime('%d-%m-%Y')} t/m {dataset_end.strftime('%d-%m-%Y')}"
    )

    st.info(
        f"Gekozen periode filter: {start.strftime('%d-%m-%Y')} t/m {end.strftime('%d-%m-%Y')}"
    )

    col1,col2,col3 = st.columns(3)

    col1.metric("Totaal calls", total_calls)
    col2.metric("Overig calls", overig_calls)

    overig_pct = round(overig_calls/total_calls*100,2) if total_calls>0 else 0

    col3.metric("Overig %", overig_pct)

    # ------------------------------------------------
    # MEDEWERKER ANALYSE
    # ------------------------------------------------

    st.header("👨‍💼 Overig per medewerker")

    agent_stats = df.groupby("Gemaakt door").agg(
        totaal_calls=("Onderwerp","count"),
        overig_calls=("Overig_flag","sum")
    ).reset_index()

    agent_stats["overig_percentage"] = (
        agent_stats["overig_calls"] /
        agent_stats["totaal_calls"] * 100
    ).round(2)

    st.dataframe(agent_stats.sort_values("overig_percentage",ascending=False))

    # ------------------------------------------------
    # PODIUM
    # ------------------------------------------------

    st.header("🏆 Podium – Beste categorisatie")

    best_pct = agent_stats.sort_values("overig_percentage").head(3)

    col1,col2,col3 = st.columns(3)

    if len(best_pct) > 1:
        col1.markdown(f"""
        <div class="podium-card">
        <h1>🥈</h1>
        <b>{best_pct.iloc[1]['Gemaakt door']}</b><br>
        Overig %: {best_pct.iloc[1]['overig_percentage']}%<br>
        Calls: {best_pct.iloc[1]['overig_calls']}
        </div>
        """, unsafe_allow_html=True)

    if len(best_pct) > 0:
        col2.markdown(f"""
        <div class="podium-card">
        <h1>🥇</h1>
        <b>{best_pct.iloc[0]['Gemaakt door']}</b><br>
        Overig %: {best_pct.iloc[0]['overig_percentage']}%<br>
        Calls: {best_pct.iloc[0]['overig_calls']}
        </div>
        """, unsafe_allow_html=True)

    if len(best_pct) > 2:
        col3.markdown(f"""
        <div class="podium-card">
        <h1>🥉</h1>
        <b>{best_pct.iloc[2]['Gemaakt door']}</b><br>
        Overig %: {best_pct.iloc[2]['overig_percentage']}%<br>
        Calls: {best_pct.iloc[2]['overig_calls']}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(
        """
        <div style="text-align:center">
        <h2>🎆 Einde dashboard bereikt 🎆</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.balloons()

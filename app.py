import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, date
import re

st.set_page_config(page_title="KCC Categorie Overige", layout="wide")

st.title("📞 KCC Categorie Overige Dashboard")

# ------------------------------------------------
# MUZIEK
# ------------------------------------------------

play_music = st.sidebar.checkbox("🎵 Achtergrondmuziek", value=False)

if play_music:
    audio_file = open("background_music.mp3", "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3")

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

    df["Beschrijving"] = df["Beschrijving"].astype(str).str.lower()

    df["Gemaakt op"] = pd.to_datetime(df["Gemaakt op"], dayfirst=True)

    df = df.dropna(subset=["Gemaakt op"])

    df["datum"] = df["Gemaakt op"].dt.date

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

    # medewerker filter

    medewerkers = ["Alle medewerkers"] + sorted(df["Gemaakt door"].unique())

    medewerker_filter = st.sidebar.selectbox("Medewerker", medewerkers)

    if medewerker_filter != "Alle medewerkers":
        df = df[df["Gemaakt door"] == medewerker_filter]

    # ------------------------------------------------
    # KPI
    # ------------------------------------------------

    total_calls = len(df)
    overig_calls = df["Overig_flag"].sum()

    st.header("📊 KPI Overzicht")

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

    periode_dagen = (end - start).days

    if medewerker_filter != "Alle medewerkers":

        st.info("Podium verborgen omdat een medewerkerfilter actief is.")

    elif periode_dagen < 7:

        st.warning("Te weinig calls voor een eerlijk podium.")

    else:

        if periode_dagen >= 30:
            min_calls = 100
        else:
            min_calls = 50

        podium_data = agent_stats[agent_stats["totaal_calls"] >= min_calls]

        podium_data = podium_data.sort_values("overig_percentage").head(3)

        col1,col2,col3 = st.columns(3)

        if len(podium_data) > 1:
            col1.success(f"🥈 {podium_data.iloc[1]['Gemaakt door']}")

        if len(podium_data) > 0:
            col2.success(f"🥇 {podium_data.iloc[0]['Gemaakt door']}")

        if len(podium_data) > 2:
            col3.success(f"🥉 {podium_data.iloc[2]['Gemaakt door']}")

    # ------------------------------------------------
    # OVERIG ANALYSE
    # ------------------------------------------------

    overig_df = df[df["Overig_flag"]].copy()

    rules = {
        "Inloggen":"login|inlog|wachtwoord|2fa",
        "Factuur":"factuur|betaling|invoice|tarief",
        "Account":"account|profiel|gegevens",
        "Website":"website|portal|pagina",
        "Advertentie":"advert|campagne",
        "Export":"export|douane|document"
    }

    def suggest_category(text):

        for cat,pattern in rules.items():

            if re.search(pattern,text):
                return cat

        return "Onbekend"

    overig_df["Voorgestelde categorie"] = overig_df["Beschrijving"].apply(suggest_category)

    # ------------------------------------------------
    # DRIVER TRENDS
    # ------------------------------------------------

    st.header("📈 Driver Trends")

    calls_per_day = df.groupby("datum").size().reset_index(name="calls")

    overig_trend = overig_df.groupby("datum").size().reset_index(name="overig_calls")

    hercat = len(overig_df[overig_df["Voorgestelde categorie"]!="Onbekend"])

    total_overig = len(overig_df)

    factor = (total_overig - hercat)/total_overig if total_overig>0 else 1

    overig_trend["overig_na_hercategorisatie"] = overig_trend["overig_calls"] * factor

    fig = px.line(
        overig_trend,
        x="datum",
        y=["overig_calls","overig_na_hercategorisatie"],
        title="Trend Overig calls (huidig vs na hercategorisatie)"
    )

    st.plotly_chart(fig,use_container_width=True)

    st.markdown("---")

    st.markdown("### 🎆 Einde dashboard bereikt")

    st.balloons()

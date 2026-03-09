import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter
from datetime import timedelta, date
import calendar

st.set_page_config(page_title="Callcenter Overig Intelligence", layout="wide")

st.title("📞 Callcenter Overig Intelligence Dashboard")

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

    dataset_start = df["datum"].min()
    dataset_end = df["datum"].max()

    df["Overig_flag"] = df["Onderwerp"].str.lower().str.contains("overig")

    # =========================
    # PERIODE FILTER
    # =========================

    st.sidebar.header("Periode filter")

    filter_optie = st.sidebar.selectbox(
        "Selecteer periode",
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

    # =========================
    # KPI
    # =========================

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

    overig_pct = round(overig_calls/total_calls*100,2) if total_calls > 0 else 0

    col3.metric("Overig %", overig_pct)

    # =========================
    # MEDEWERKER ANALYSE
    # =========================

    st.header("👨‍💼 Overig per medewerker")

    agent_stats = df.groupby("Gemaakt door").agg(
        totaal_calls=("Onderwerp","count"),
        overig_calls=("Overig_flag","sum")
    ).reset_index()

    agent_stats["overig_percentage"] = (
        agent_stats["overig_calls"] /
        agent_stats["totaal_calls"] * 100
    ).round(2)

    ranking_pct = agent_stats.sort_values("overig_percentage",ascending=False)

    st.subheader("Ranking op % Overig")

    st.dataframe(ranking_pct,use_container_width=True)

    ranking_count = agent_stats.sort_values("overig_calls",ascending=False)

    st.subheader("Ranking op aantal Overig")

    st.dataframe(ranking_count,use_container_width=True)

    # =========================
    # VISUALISATIES
    # =========================

    st.header("📈 Visualisaties")

    fig1 = px.bar(
        ranking_pct,
        x="Gemaakt door",
        y="overig_percentage",
        title="Percentage Overig per medewerker"
    )

    st.plotly_chart(fig1,use_container_width=True)

    fig2 = px.bar(
        ranking_count,
        x="Gemaakt door",
        y="overig_calls",
        title="Aantal Overig per medewerker"
    )

    st.plotly_chart(fig2,use_container_width=True)

    # =========================
    # AI CATEGORISATIE
    # =========================

    st.header("🤖 Voorgestelde categorie voor Overig calls")

    overig_df = df[df["Overig_flag"]].copy()

    rules = {
        "Inloggen":"login|inlog|wachtwoord|2fa|auth",
        "Factuur":"factuur|betaling|invoice|prijs|tarief",
        "Account":"account|profiel|gegevens|email",
        "Website":"website|portal|pagina|link|formulier",
        "Advertentie":"advert|advertentie|campagne",
        "Export":"export|document|douane"
    }

    def suggest_category(text):

        for category,pattern in rules.items():

            if re.search(pattern,text):

                return category

        return "Onbekend"

    overig_df["Voorgestelde categorie"] = overig_df["Beschrijving"].apply(suggest_category)

    summary = overig_df["Voorgestelde categorie"].value_counts().reset_index()

    summary.columns = ["categorie","aantal"]

    st.dataframe(summary)

    fig3 = px.bar(summary,x="categorie",y="aantal",title="Voorgestelde categorieën binnen Overig")

    st.plotly_chart(fig3,use_container_width=True)

    # =========================
    # OVERIG REDUCTION SIMULATOR
    # =========================

    st.header("🧮 Overig Reduction Simulator")

    hercat = len(overig_df[overig_df["Voorgestelde categorie"]!="Onbekend"])

    total_overig = len(overig_df)

    if total_overig > 0:

        new_overig = total_overig - hercat

        original_pct = round(total_overig / total_calls * 100,2)

        new_pct = round(new_overig / total_calls * 100,2)

        call_reduction = total_overig - new_overig

        pct_reduction = round(original_pct - new_pct,2)

        st.success(
            f"Als deze categorieën worden toegevoegd kan Overig dalen van "
            f"{total_overig} ({original_pct}%) naar {new_overig} ({new_pct}%). "
            f"Dat is een verlaging van {call_reduction} calls en {pct_reduction} procentpunt."
        )

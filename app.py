import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter
from datetime import timedelta, date

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
    # SIDEBAR FILTERS
    # =========================

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

    medewerker_filter = st.sidebar.selectbox(
        "Medewerker filter",
        medewerkers
    )

    if medewerker_filter != "Alle medewerkers":
        df = df[df["Gemaakt door"] == medewerker_filter]

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
    # PODIUM BESTE CATEGORISATIE
    # =========================

    st.header("🏆 Podium – Beste categorisatie")

    podium_data = agent_stats[agent_stats["totaal_calls"] >= 20]

    best_pct = podium_data.sort_values("overig_percentage").head(3)
    best_count = podium_data.sort_values("overig_calls").head(3)

    col1, col2, col3 = st.columns(3)

    podium = [col1, col2, col3]

    for i in range(3):

        if i < len(best_pct):

            medewerker = best_pct.iloc[i]

            podium[i].markdown(
                f"""
                **Plek {i+1}**

                {medewerker['Gemaakt door']}

                Overig %: {medewerker['overig_percentage']}%

                Overig calls: {int(medewerker['overig_calls'])}
                """
            )

        else:
            podium[i].markdown(f"**Plek {i+1}**\n\n—")

    st.header("🏆 Podium – Minste Overig calls")

    col1, col2, col3 = st.columns(3)

    podium = [col1, col2, col3]

    for i in range(3):

        if i < len(best_count):

            medewerker = best_count.iloc[i]

            podium[i].markdown(
                f"""
                **Plek {i+1}**

                {medewerker['Gemaakt door']}

                Overig %: {medewerker['overig_percentage']}%

                Overig calls: {int(medewerker['overig_calls'])}
                """
            )

        else:
            podium[i].markdown(f"**Plek {i+1}**\n\n—")

    # =========================
    # DRIVER TRENDS
    # =========================

    st.header("📈 Driver Trends")

    calls_per_day = df.groupby("datum").size().reset_index(name="calls")

    fig_calls = px.line(
        calls_per_day,
        x="datum",
        y="calls",
        title="Trend totaal aantal calls per dag"
    )

    st.plotly_chart(fig_calls,use_container_width=True)

    overig_df = df[df["Overig_flag"]]

    overig_trend = overig_df.groupby("datum").size().reset_index(name="overig_calls")

    fig_overig = px.line(
        overig_trend,
        x="datum",
        y="overig_calls",
        title="Trend Overig calls per dag"
    )

    st.plotly_chart(fig_overig,use_container_width=True)

    combined = calls_per_day.merge(overig_trend,on="datum",how="left").fillna(0)

    fig_combined = px.line(
        combined,
        x="datum",
        y=["calls","overig_calls"],
        title="Totaal calls vs Overig calls"
    )

    st.plotly_chart(fig_combined,use_container_width=True)

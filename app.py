import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter

st.set_page_config(page_title="Callcenter Overig Dashboard", layout="wide")

st.title("📞 Callcenter Overig Analyse Dashboard")

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

    # Overig detectie
    df["Overig_flag"] = df["Onderwerp"].str.lower().str.contains("overig")

    # Periode bepalen
    periode_van = df["Gemaakt op"].min()
    periode_tot = df["Gemaakt op"].max()

    # KPI
    total_calls = len(df)
    overig_calls = df["Overig_flag"].sum()

    st.header("📊 KPI Overzicht")

    st.info(
        f"Analyseperiode: {periode_van.strftime('%d-%m-%Y')} t/m {periode_tot.strftime('%d-%m-%Y')}"
    )

    col1,col2,col3 = st.columns(3)

    col1.metric("Totaal calls", total_calls)
    col2.metric("Overig calls", overig_calls)

    overig_pct = round(overig_calls / total_calls * 100,2)

    col3.metric("Overig %", overig_pct)

    # ====================
    # MEDEWERKER ANALYSE
    # ====================

    st.header("👨‍💼 Overig per medewerker")

    agent_stats = df.groupby("Gemaakt door").agg(

        totaal_calls=("Onderwerp","count"),
        overig_calls=("Overig_flag","sum")

    ).reset_index()

    agent_stats["overig_percentage"] = (

        agent_stats["overig_calls"] /
        agent_stats["totaal_calls"] * 100

    ).round(2)

    st.subheader("Ranking op percentage Overig")

    ranking_pct = agent_stats.sort_values(
        "overig_percentage",
        ascending=False
    )

    st.dataframe(ranking_pct,use_container_width=True)

    st.subheader("Ranking op aantal Overig calls")

    ranking_count = agent_stats.sort_values(
        "overig_calls",
        ascending=False
    )

    st.dataframe(ranking_count,use_container_width=True)

    # ====================
    # VISUALISATIES
    # ====================

    st.header("📈 Grafieken")

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
        title="Aantal Overig calls per medewerker"
    )

    st.plotly_chart(fig2,use_container_width=True)

    # ====================
    # OVERIG INHOUD
    # ====================

    st.header("📂 Wat zit er in Overig")

    overig_df = df[df["Overig_flag"]]

    top_overig = overig_df["Onderwerp"].value_counts().head(10)

    fig3 = px.bar(
        top_overig,
        title="Top onderwerpen binnen Overig"
    )

    st.plotly_chart(fig3,use_container_width=True)

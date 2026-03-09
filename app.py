import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter

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

    # Overig detectie
    df["Overig_flag"] = df["Onderwerp"].str.lower().str.contains("overig")

    # PERIODE FILTER
    min_date = df["datum"].min()
    max_date = df["datum"].max()

    st.sidebar.header("Periode selectie")

    start = st.sidebar.date_input("Startdatum", min_date)
    end = st.sidebar.date_input("Einddatum", max_date)

    df = df[(df["datum"] >= start) & (df["datum"] <= end)]

    # KPI
    total_calls = len(df)
    overig_calls = df["Overig_flag"].sum()

    st.header("📊 KPI Overzicht")

    st.info(f"Analyseperiode: {start} t/m {end}")

    col1,col2,col3 = st.columns(3)

    col1.metric("Totaal calls", total_calls)
    col2.metric("Overig calls", overig_calls)

    overig_pct = round(overig_calls/total_calls*100,2) if total_calls > 0 else 0

    col3.metric("Overig %", overig_pct)

    # ======================
    # MEDEWERKER ANALYSE
    # ======================

    st.header("👨‍💼 Overig per medewerker")

    agent_stats = df.groupby("Gemaakt door").agg(

        totaal_calls=("Onderwerp","count"),
        overig_calls=("Overig_flag","sum")

    ).reset_index()

    agent_stats["overig_percentage"] = (

        agent_stats["overig_calls"] /

        agent_stats["totaal_calls"] * 100

    ).round(2)

    ranking_pct = agent_stats.sort_values(
        "overig_percentage",
        ascending=False
    )

    st.subheader("Ranking op % Overig")

    st.dataframe(ranking_pct,use_container_width=True)

    ranking_count = agent_stats.sort_values(
        "overig_calls",
        ascending=False
    )

    st.subheader("Ranking op aantal Overig")

    st.dataframe(ranking_count,use_container_width=True)

    # ======================
    # VISUALISATIES
    # ======================

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

    # ======================
    # AI CATEGORISATIE
    # ======================

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

    fig3 = px.bar(
        summary,
        x="categorie",
        y="aantal",
        title="Voorgestelde categorieën binnen Overig"
    )

    st.plotly_chart(fig3,use_container_width=True)

    # ======================
    # CALL DRIVER DISCOVERY
    # ======================

    st.header("🔎 Call Driver Discovery")

    text = " ".join(overig_df["Beschrijving"].dropna())

    words = re.findall(r"\b[a-z]{4,}\b", text)

    stopwords = ["klant","probleem","vraag","help","graag"]

    words = [w for w in words if w not in stopwords]

    word_freq = Counter(words).most_common(15)

    word_df = pd.DataFrame(word_freq,columns=["woord","frequentie"])

    fig_words = px.bar(
        word_df,
        x="woord",
        y="frequentie",
        title="Meest voorkomende woorden in Overig calls"
    )

    st.plotly_chart(fig_words,use_container_width=True)

    # ======================
    # DRIVER TRENDS
    # ======================

    st.header("📈 Driver Trends")

    driver_trend = overig_df.groupby("datum").size().reset_index(name="overig_calls")

    fig_trend = px.line(
        driver_trend,
        x="datum",
        y="overig_calls",
        title="Trend van Overig calls per dag"
    )

    st.plotly_chart(fig_trend,use_container_width=True)

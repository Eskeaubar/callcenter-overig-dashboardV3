import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, date
import re

st.set_page_config(page_title="KCC Overige calls", layout="wide")

st.title("📞 KCC Overige calls")

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

    # =========================
    # WERKDAGEN FILTER
    # =========================

    df["weekday"] = pd.to_datetime(df["datum"]).dt.weekday

    df = df[df["weekday"] < 5]

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

    # =========================
    # KPI OVERZICHT
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

    overig_pct = round(overig_calls/total_calls*100,2) if total_calls>0 else 0

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

    st.subheader("Ranking op % Overig")

    st.dataframe(agent_stats.sort_values("overig_percentage",ascending=False))

    st.subheader("Ranking op aantal Overig")

    st.dataframe(agent_stats.sort_values("overig_calls",ascending=False))

    # =========================
    # VOORGESTELDE CATEGORIEËN
    # =========================

    st.header("🤖 Voorgestelde categorie voor Overig")

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

    summary = overig_df["Voorgestelde categorie"].value_counts().reset_index()

    summary.columns=["Categorie","Aantal"]

    st.dataframe(summary)

    fig_cat = px.bar(summary,x="Categorie",y="Aantal",title="Voorgestelde categorieën")

    st.plotly_chart(fig_cat,use_container_width=True)

    # =========================
    # CATEGORIE PER MEDEWERKER
    # =========================

    st.header("📊 Onderwerpen per medewerker")

    cat_agent = df.groupby(["Gemaakt door","Onderwerp"]).size().reset_index(name="Aantal")

    st.dataframe(cat_agent)

    fig_agent_cat = px.bar(
        cat_agent,
        x="Gemaakt door",
        y="Aantal",
        color="Onderwerp",
        title="Onderwerpen per medewerker"
    )

    st.plotly_chart(fig_agent_cat,use_container_width=True)

    # =========================
    # TRENDS
    # =========================

    st.header("📈 Driver Trends")

    calls_per_day = df.groupby("datum").size().reset_index(name="calls")

    fig_calls = px.line(
        calls_per_day,
        x="datum",
        y="calls",
        title="Trend totaal aantal calls per werkdag"
    )

    st.plotly_chart(fig_calls,use_container_width=True)

    overig_trend = overig_df.groupby("datum").size().reset_index(name="overig_calls")

    fig_overig = px.line(
        overig_trend,
        x="datum",
        y="overig_calls",
        title="Trend Overig calls per werkdag"
    )

    st.plotly_chart(fig_overig,use_container_width=True)

    combined = calls_per_day.merge(overig_trend,on="datum",how="left").fillna(0)

    fig_combined = px.line(
        combined,
        x="datum",
        y=["calls","overig_calls"],
        title="Totaal calls vs Overig calls (werkdagen)"
    )

    st.plotly_chart(fig_combined,use_container_width=True)

    # =========================
    # EINDE DASHBOARD
    # =========================

    st.markdown("---")

    st.markdown(
        """
        <div style="text-align:center">

        # 🎆 Einde dashboard bereikt 🎆

        Scroll omhoog om analyses opnieuw te bekijken.

        </div>
        """,
        unsafe_allow_html=True
    )

    st.balloons()

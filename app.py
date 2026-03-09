# ========================
# AI CATEGORISATIE VOOR OVERIG
# ========================

st.header("🤖 AI Herclassificatie van Overig Calls")

overig_df = df[df["Overig_flag"]].copy()

rules = {

"Inloggen":"login|inlog|wachtwoord|2fa|verific",

"Factuur":"factuur|betaling|invoice|prijs|tarief|btw",

"Account":"account|profiel|gegevens|email|gebruiker",

"Website":"website|portal|pagina|link|formulier|knop",

"Advertentie":"advert|advertentie|campagne|plaatsing",

"Export":"export|document|douane|kfz|eur1"

}

def suggest_category(text):

    for category,pattern in rules.items():

        if pd.notna(text) and re.search(pattern,text):

            return category

    return "Onbekend"

overig_df["Voorgestelde categorie"] = overig_df["Beschrijving"].apply(suggest_category)

# samenvatting

cat_summary = overig_df["Voorgestelde categorie"].value_counts().reset_index()

cat_summary.columns = ["categorie","aantal"]

st.subheader("📊 Voorgestelde categorieën")

st.dataframe(cat_summary)

# grafiek

fig_cat = px.bar(
    cat_summary,
    x="categorie",
    y="aantal",
    title="Voorgestelde categorieën voor Overig calls"
)

st.plotly_chart(fig_cat,use_container_width=True)

# hercategoriseerbaar percentage

hercat = len(overig_df[overig_df["Voorgestelde categorie"]!="Onbekend"])

total_overig = len(overig_df)

if total_overig > 0:

    pct = round(hercat/total_overig*100,2)

else:

    pct = 0

st.info(

    f"{hercat} van {total_overig} Overig calls ({pct}%) kunnen mogelijk hergecategoriseerd worden"

)

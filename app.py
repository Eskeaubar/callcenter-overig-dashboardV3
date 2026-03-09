# =========================
# PODIUM BESTE CATEGORISATIE
# =========================

st.header("🏆 Podium – Beste categorisatie")

periode_dagen = (end - start).days

if periode_dagen < 7:

    st.warning("Te weinig calls voor een eerlijk podium. Selecteer minimaal een week.")

else:

    if periode_dagen >= 30:
        min_calls = 100
    else:
        min_calls = 50

    podium_data = agent_stats[agent_stats["totaal_calls"] >= min_calls]

    best_pct = podium_data.sort_values("overig_percentage").head(3)
    best_count = podium_data.sort_values("overig_calls").head(3)

    medals = ["🥇","🥈","🥉"]

    cols = st.columns(3)

    for i in range(3):

        if i < len(best_pct):

            row = best_pct.iloc[i]

            cols[i].markdown(
                f"""
                ## {medals[i]}

                **{row['Gemaakt door']}**

                Overig %: **{row['overig_percentage']}%**

                Overig calls: **{int(row['overig_calls'])}**

                Totaal calls: {int(row['totaal_calls'])}
                """
            )

        else:

            cols[i].markdown(f"## {medals[i]}\n\n—")

st.header("🏆 Podium – Minste Overig calls")

cols = st.columns(3)

for i in range(3):

    if i < len(best_count):

        row = best_count.iloc[i]

        cols[i].markdown(
            f"""
            ## {medals[i]}

            **{row['Gemaakt door']}**

            Overig %: **{row['overig_percentage']}%**

            Overig calls: **{int(row['overig_calls'])}**

            Totaal calls: {int(row['totaal_calls'])}
            """
        )

    else:

        cols[i].markdown(f"## {medals[i]}\n\n—")

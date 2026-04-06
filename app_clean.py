import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# --------------------------------------------------
# CONFIG PAGE
# --------------------------------------------------
st.set_page_config(
    page_title="CityFlow Analytics - Velib Dashboard",
    layout="wide"
)

# --------------------------------------------------
# STYLE
# --------------------------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #F7FAFC;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: #12344D;
        font-weight: 700;
    }

    [data-testid="stMetricValue"] {
        color: #12344D;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #4F6B7A;
    }

    .hero-box {
        background: linear-gradient(135deg, #12344D 0%, #1D5C7A 55%, #2CA58D 100%);
        padding: 28px 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 6px 20px rgba(18, 52, 77, 0.18);
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 10px;
    }

    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.95;
        margin-bottom: 6px;
    }

    .hero-caption {
        font-size: 0.95rem;
        opacity: 0.9;
    }

    .mini-card {
        background: white;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 14px rgba(18, 52, 77, 0.08);
        border: 1px solid #E7EEF4;
        margin-bottom: 10px;
    }

    .mini-card-title {
        color: #4F6B7A;
        font-size: 0.9rem;
        margin-bottom: 4px;
    }

    .mini-card-value {
        color: #12344D;
        font-size: 1.1rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# HEADER + LOGO
# --------------------------------------------------
logo_path = "cityflow_logo.png"

hero_left, hero_right = st.columns([1, 4])

with hero_left:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

with hero_right:
    st.markdown(
        """
        <div class="hero-box">
            <div class="hero-title">CityFlow Analytics<br>Velib Operational Dashboard</div>
            <div class="hero-subtitle"><strong>Client :</strong> Ville de Paris</div>
            <div class="hero-caption">
                Mission : identifier les zones et stations les plus en tension afin d'eclairer
                le pilotage du reseau Velib et d'orienter les priorites operationnelles.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">Perimetre</div>
            <div class="mini-card-value">Stations Velib en temps reel</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with summary_col2:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">Usage du dashboard</div>
            <div class="mini-card-value">Pilotage et priorisation</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with summary_col3:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">Lecture principale</div>
            <div class="mini-card-value">Zones et stations sous tension</div>
        </div>
        """,
        unsafe_allow_html=True
    )

CSV_PATH = "velib-disponibilite-en-temps-reel.csv"

try:
    # --------------------------------------------------
    # CHARGEMENT
    # --------------------------------------------------
    df = pd.read_csv(CSV_PATH, sep=";")
    df.columns = [col.strip() for col in df.columns]

    # --------------------------------------------------
    # CONVERSIONS
    # --------------------------------------------------
    numeric_cols = [
        "Capacité de la station",
        "Nombre bornettes libres",
        "Nombre total vélos disponibles",
        "Vélos mécaniques disponibles",
        "Vélos électriques disponibles",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    yes_no_cols = [
        "Station en fonctionnement",
        "Borne de paiement disponible",
        "Retour vélib possible"
    ]

    for col in yes_no_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    if "Actualisation de la donnée" in df.columns:
        df["Actualisation de la donnée"] = pd.to_datetime(
            df["Actualisation de la donnée"],
            errors="coerce",
            utc=True
        )

    # --------------------------------------------------
    # COORDONNEES
    # --------------------------------------------------
    if "Coordonnées géographiques" in df.columns:
        coords = df["Coordonnées géographiques"].astype(str).str.split(",", expand=True)

        if coords.shape[1] >= 2:
            df["latitude"] = pd.to_numeric(coords[0].str.strip(), errors="coerce")
            df["longitude"] = pd.to_numeric(coords[1].str.strip(), errors="coerce")
        else:
            df["latitude"] = np.nan
            df["longitude"] = np.nan
    else:
        df["latitude"] = np.nan
        df["longitude"] = np.nan

    # --------------------------------------------------
    # INDICATEURS
    # --------------------------------------------------
    cap = df["Capacité de la station"].replace(0, np.nan)

    df["Taux disponibilite velos"] = (df["Nombre total vélos disponibles"] / cap) * 100
    df["Taux bornettes libres"] = (df["Nombre bornettes libres"] / cap) * 100

    df["Part velos electriques"] = np.where(
        df["Nombre total vélos disponibles"] > 0,
        (df["Vélos électriques disponibles"] / df["Nombre total vélos disponibles"]) * 100,
        np.nan
    )

    df["Manque velos"] = df["Capacité de la station"] - df["Nombre total vélos disponibles"]

    # --------------------------------------------------
    # FILTRES SIDEBAR
    # --------------------------------------------------
    st.sidebar.header("Filtres")

    communes = sorted(df["Nom communes équipées"].dropna().unique().tolist())
    communes_selectionnees = st.sidebar.multiselect(
        "Choisir une ou plusieurs communes",
        options=communes,
        default=communes
    )

    statut_ouverture = st.sidebar.selectbox(
        "Station en fonctionnement",
        options=["Toutes", "Oui uniquement", "Non uniquement"]
    )

    retour_possible = st.sidebar.selectbox(
        "Retour Velib",
        options=["Tous", "Oui uniquement", "Non uniquement"]
    )

    capacite_min = int(df["Capacité de la station"].fillna(0).min())
    capacite_max = int(df["Capacité de la station"].fillna(0).max())

    capacite_range = st.sidebar.slider(
        "Capacite de la station",
        min_value=capacite_min,
        max_value=capacite_max,
        value=(capacite_min, capacite_max)
    )

    # --------------------------------------------------
    # APPLICATION DES FILTRES
    # --------------------------------------------------
    filtered_df = df.copy()

    filtered_df = filtered_df[
        filtered_df["Nom communes équipées"].isin(communes_selectionnees)
    ]

    filtered_df = filtered_df[
        (filtered_df["Capacité de la station"] >= capacite_range[0]) &
        (filtered_df["Capacité de la station"] <= capacite_range[1])
    ]

    if statut_ouverture == "Oui uniquement":
        filtered_df = filtered_df[filtered_df["Station en fonctionnement"] == "OUI"]
    elif statut_ouverture == "Non uniquement":
        filtered_df = filtered_df[filtered_df["Station en fonctionnement"] == "NON"]

    if retour_possible == "Oui uniquement":
        filtered_df = filtered_df[filtered_df["Retour vélib possible"] == "OUI"]
    elif retour_possible == "Non uniquement":
        filtered_df = filtered_df[filtered_df["Retour vélib possible"] == "NON"]

    if filtered_df.empty:
        st.warning("Aucune donnee apres application des filtres.")
        st.stop()

    # --------------------------------------------------
    # KPIs
    # --------------------------------------------------
    nb_stations = len(filtered_df)
    nb_ouvertes = (filtered_df["Station en fonctionnement"] == "OUI").sum()
    tx_ouverture = (nb_ouvertes / nb_stations) * 100 if nb_stations > 0 else 0

    capacite_totale = filtered_df["Capacité de la station"].sum(skipna=True)
    velos_total = filtered_df["Nombre total vélos disponibles"].sum(skipna=True)
    velos_meca = filtered_df["Vélos mécaniques disponibles"].sum(skipna=True)
    velos_elec = filtered_df["Vélos électriques disponibles"].sum(skipna=True)

    tx_global_dispo = (velos_total / capacite_totale) * 100 if capacite_totale > 0 else 0
    part_elec = (velos_elec / velos_total) * 100 if velos_total > 0 else 0

    date_max = filtered_df["Actualisation de la donnée"].max() if "Actualisation de la donnée" in filtered_df.columns else None

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Stations analysees", f"{nb_stations}")
    col2.metric("Stations ouvertes", f"{nb_ouvertes}", f"{tx_ouverture:.1f}%")
    col3.metric("Capacite totale", f"{int(capacite_totale):,}".replace(",", " "))
    col4.metric("Velos disponibles", f"{int(velos_total):,}".replace(",", " "), f"{tx_global_dispo:.1f}%")
    col5.metric("Part velos electriques", f"{part_elec:.1f}%")

    if pd.notna(date_max):
        st.caption(f"Derniere actualisation observee : {date_max}")

    # --------------------------------------------------
    # INSIGHTS CLES
    # --------------------------------------------------
    st.subheader("Synthèse exécutive")

    commune_stats_global = (
        filtered_df.groupby("Nom communes équipées", as_index=False)
        .agg(
            nb_stations=("Identifiant station", "count"),
            capacite_totale=("Capacité de la station", "sum"),
            velos_total=("Nombre total vélos disponibles", "sum")
        )
    )

    commune_stats_global["Taux moyen disponibilite"] = np.where(
        commune_stats_global["capacite_totale"] > 0,
        (commune_stats_global["velos_total"] / commune_stats_global["capacite_totale"]) * 100,
        np.nan
    )

    commune_critique = None
    if not commune_stats_global.empty:
        commune_critique_df = commune_stats_global.sort_values("Taux moyen disponibilite", ascending=True)
        if len(commune_critique_df) > 0:
            commune_critique = commune_critique_df.iloc[0]["Nom communes équipées"]

    stations_crit = filtered_df.dropna(subset=["Taux disponibilite velos"]).copy()
    stations_crit = stations_crit.sort_values("Taux disponibilite velos", ascending=True)

    station_critique = None
    if not stations_crit.empty:
        station_critique = stations_crit.iloc[0]["Nom station"]

    ins1, ins2, ins3 = st.columns(3)

    ins1.info(f"Taux global de disponibilite : **{tx_global_dispo:.1f}%**")
    ins2.warning(f"Commune la plus en tension : **{commune_critique}**" if commune_critique else "Pas de commune critique")
    ins3.error(f"Station la plus en tension : **{station_critique}**" if station_critique else "Pas de station critique")

    # --------------------------------------------------
    # CARTE EN PLEINE LARGEUR
    # --------------------------------------------------
    st.subheader("Vue géographique du réseau")

    map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()

    if map_df.empty:
        st.info("Pas de coordonnees geographiques disponibles.")
    else:
        fig_map = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="Taux disponibilite velos",
            size="Nombre total vélos disponibles",
            hover_name="Nom station",
            hover_data={
                "Nom communes équipées": True,
                "Nombre total vélos disponibles": True,
                "Capacité de la station": True,
                "Taux disponibilite velos": ':.1f'
            },
            zoom=10,
            height=820,
            color_continuous_scale=[
                [0.0, "#D64550"],
                [0.5, "#F4B942"],
                [1.0, "#2CA58D"]
            ],
            title="Stations colorees selon le taux de disponibilite en velos"
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=50, b=0)
        )

        st.plotly_chart(fig_map, use_container_width=True)

    # --------------------------------------------------
    # COMMUNES SOUS TENSION
    # --------------------------------------------------
    st.subheader("Communes sous tension")

    commune_stats = (
        filtered_df.groupby("Nom communes équipées", as_index=False)
        .agg(
            nb_stations=("Identifiant station", "count"),
            capacite_totale=("Capacité de la station", "sum"),
            velos_total=("Nombre total vélos disponibles", "sum")
        )
    )

    commune_stats["Taux moyen disponibilite"] = np.where(
        commune_stats["capacite_totale"] > 0,
        (commune_stats["velos_total"] / commune_stats["capacite_totale"]) * 100,
        np.nan
    )

    min_stations = st.number_input(
        "Nombre minimum de stations par commune",
        min_value=1,
        max_value=50,
        value=5,
        step=1
    )

    commune_rank = commune_stats[commune_stats["nb_stations"] >= min_stations].copy()
    commune_rank = commune_rank.sort_values("Taux moyen disponibilite", ascending=True).head(10)

    if commune_rank.empty:
        st.info("Pas assez de communes pour ce seuil.")
    else:
        fig_communes = px.bar(
            commune_rank,
            x="Taux moyen disponibilite",
            y="Nom communes équipées",
            orientation="h",
            text="Taux moyen disponibilite",
            title="Top 10 des communes au plus faible taux moyen",
            color_discrete_sequence=["#E76F51"]
        )

        fig_communes.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_communes.update_layout(
            yaxis_title="Commune",
            xaxis_title="Taux moyen de disponibilite (%)",
            height=500
        )

        st.plotly_chart(fig_communes, use_container_width=True)

    # --------------------------------------------------
    # LIGNE 2 : HISTOGRAMME + CAMEMBERT
    # --------------------------------------------------
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribution des niveaux de disponibilite")

        hist_df = filtered_df.dropna(subset=["Taux disponibilite velos"]).copy()

        fig_hist = px.histogram(
            hist_df,
            x="Taux disponibilite velos",
            nbins=30,
            title="Distribution des stations selon leur taux de disponibilite",
            color_discrete_sequence=["#457B9D"]
        )

        fig_hist.update_layout(
            xaxis_title="Taux de disponibilite (%)",
            yaxis_title="Nombre de stations",
            height=450
        )

        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        st.subheader("Mix de l'offre disponible")

        pie_df = pd.DataFrame({
            "Type de velo": ["Mecaniques", "Electriques"],
            "Nombre": [velos_meca, velos_elec]
        })

        fig_pie = px.pie(
            pie_df,
            names="Type de velo",
            values="Nombre",
            title="Repartition des velos disponibles",
            color="Type de velo",
            color_discrete_map={
                "Mecaniques": "#1D3557",
                "Electriques": "#2A9D8F"
            }
        )

        fig_pie.update_layout(height=450)

        st.plotly_chart(fig_pie, use_container_width=True)

    # --------------------------------------------------
    # GRAPHE STATIONS CRITIQUES
    # --------------------------------------------------
    st.subheader("Stations prioritaires")

    top_tension = filtered_df.copy()
    top_tension = top_tension.dropna(subset=["Capacité de la station", "Nombre total vélos disponibles"]).copy()
    top_tension = top_tension[top_tension["Capacité de la station"] >= 20]

    top_tension = top_tension.sort_values(
        by=["Manque velos", "Taux disponibilite velos"],
        ascending=[False, True]
    ).head(15)

    if not top_tension.empty:
        top_tension = top_tension.sort_values("Manque velos", ascending=True)

        fig_tension = px.bar(
            top_tension,
            x="Manque velos",
            y="Nom station",
            orientation="h",
            text="Manque velos",
            title="15 stations avec le plus grand manque de velos",
            color_discrete_sequence=["#D64550"],
            hover_data={
                "Nom communes équipées": True,
                "Nombre total vélos disponibles": True,
                "Capacité de la station": True,
                "Taux disponibilite velos": ':.1f'
            }
        )

        fig_tension.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig_tension.update_layout(
            xaxis_title="Nombre de velos manquants par rapport a la capacite",
            yaxis_title="Station",
            height=650
        )

        st.plotly_chart(fig_tension, use_container_width=True)
    else:
        st.info("Pas assez de stations avec une capacite significative pour afficher ce graphique.")

    # --------------------------------------------------
    # TABLEAU DETAILLE
    # --------------------------------------------------
    st.subheader("Détail des stations critiques")

    stations_tension = filtered_df.copy()
    stations_tension = stations_tension.dropna(subset=["Taux disponibilite velos"])
    stations_tension = stations_tension.sort_values(
        by=["Manque velos", "Taux disponibilite velos"],
        ascending=[False, True]
    )

    display_cols = [
        "Nom station",
        "Nom communes équipées",
        "Station en fonctionnement",
        "Capacité de la station",
        "Nombre total vélos disponibles",
        "Manque velos",
        "Nombre bornettes libres",
        "Vélos mécaniques disponibles",
        "Vélos électriques disponibles",
        "Taux disponibilite velos",
        "Taux bornettes libres",
        "Part velos electriques",
        "Actualisation de la donnée"
    ]

    existing_cols = [col for col in display_cols if col in stations_tension.columns]
    stations_display = stations_tension[existing_cols].head(20).copy()

    for col in ["Manque velos", "Taux disponibilite velos", "Taux bornettes libres", "Part velos electriques"]:
        if col in stations_display.columns:
            stations_display[col] = stations_display[col].round(1)

    st.dataframe(stations_display, use_container_width=True)

    # --------------------------------------------------
    # EXPORT CSV
    # --------------------------------------------------
    st.subheader("Exporter les donnees filtrees")

    csv_export = filtered_df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        label="Telecharger les donnees filtrees en CSV",
        data=csv_export,
        file_name="velib_dashboard_filtre.csv",
        mime="text/csv"
    )

    # --------------------------------------------------
    # NOTE METHODO
    # --------------------------------------------------
    st.markdown("---")
    st.markdown(
        """
        ### Note methodologique
        - Les donnees correspondent a un **instant T**.
        - Les taux sont calcules a partir de la **capacite de la station**.
        - Les stations de capacite nulle sont exclues des calculs de ratio.
        - Le graphique des stations critiques repose sur le **manque de velos** par rapport a la capacite totale.
        - Ce dashboard a ete concu par **CityFlow Analytics** comme support d'aide a la decision pour la Ville de Paris.
        """
    )

except Exception as e:
    st.error("Erreur pendant le traitement des donnees")
    st.code(str(e))

import requests
import time
import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="Restrictions eau Arkema", page_icon="💧", layout="wide")
st.title("💧 Restrictions d'eau — Sites Arkema")
st.caption("France (VigiEau) et Espagne (ACA Catalogne).")

# ═══════════════════════════════════════════════════════════════════════════
# FRANCE — Adresses + noms de sites
# ═══════════════════════════════════════════════════════════════════════════

ADRESSES_DEFAULT = """70 Rue de Lille, 59710 Avelin
Route de Carling, 57500 Saint-Avold
3 Allée de Chandaire, 36000 Châteauroux
RD319, 77170 Coubert
Avenue de l'Hermitage, 62223 Saint-Laurent-Blangy
35 Rue Ampère, 69730 Genay
Avenue du Président Duchesne, 14600 Honfleur
N85 BP 16, 38560 Jarrie
Chemin des Brouves, 73130 La Chambre
6 Rue de l'Avenir, 85700 Sèvremont
1 Route Départementale 817, 64170 Lacq
998 Route des Usines, 65300 Lannemezan
6 Rue Guy Pellerin, 33114 Le Barp
Rue du Buisson du Roi, 60880 Le Meux
220 Route de L'Usine, 40400 Lesgor
123 Boulevard de la Millière, 13011 Marseille
122 Route des Pyrénées, 64300 Mont
Avenue du Bourg, 64150 Mourenx
4 Chemin Henri Moissan, 69310 Pierre-Bénite
ZI MONTIFAUT 34 RUE RENE TRUHAUT, 85700 Pouzauges
160 Chemin de Saint-Claire, 07000 Privas
Rue de Bailly, 60170 Ribécourt-Dreslincourt
209 Avenue Charles Despiau, 40370 Rion-des-Landes
Avenue du Jas, 04600 Château-Arnoux-Saint-Auban
27 Rue de la Porte de Dourdan, 28700 Sainville
Centre de production Route du Rilsan, 27470 Serquigny
218 Rue Frédéric Kuhlmann, 60870 Villers-Saint-Paul"""

NOMS_SITES = {
    "70 Rue de Lille, 59710 Avelin":                             "Avelin",
    "Route de Carling, 57500 Saint-Avold":                       "Carling",
    "3 Allée de Chandaire, 36000 Châteauroux":                   "Châteauroux",
    "RD319, 77170 Coubert":                                      "Coubert",
    "Avenue de l'Hermitage, 62223 Saint-Laurent-Blangy":         "Feuchy",
    "35 Rue Ampère, 69730 Genay":                                "Genay",
    "Avenue du Président Duchesne, 14600 Honfleur":              "Honfleur",
    "N85 BP 16, 38560 Jarrie":                                   "Jarrie",
    "Chemin des Brouves, 73130 La Chambre":                      "La Chambre",
    "6 Rue de l'Avenir, 85700 Sèvremont":                        "La Flocellière",
    "1 Route Départementale 817, 64170 Lacq":                    "Lacq",
    "998 Route des Usines, 65300 Lannemezan":                    "Lannemezan",
    "6 Rue Guy Pellerin, 33114 Le Barp":                         "Le Barp",
    "Rue du Buisson du Roi, 60880 Le Meux":                      "Le Meux",
    "220 Route de L'Usine, 40400 Lesgor":                        "Lesgor",
    "123 Boulevard de la Millière, 13011 Marseille":             "Marseille",
    "122 Route des Pyrénées, 64300 Mont":                        "Mont",
    "Avenue du Bourg, 64150 Mourenx":                            "Mourenx",
    "4 Chemin Henri Moissan, 69310 Pierre-Bénite":               "Pierre-Bénite",
    "ZI MONTIFAUT 34 RUE RENE TRUHAUT, 85700 Pouzauges":         "Pouzauges",
    "160 Chemin de Saint-Claire, 07000 Privas":                  "Privas",
    "Rue de Bailly, 60170 Ribécourt-Dreslincourt":               "Ribécourt",
    "209 Avenue Charles Despiau, 40370 Rion-des-Landes":         "Rion",
    "Avenue du Jas, 04600 Château-Arnoux-Saint-Auban":           "Saint-Auban",
    "27 Rue de la Porte de Dourdan, 28700 Sainville":            "Sainville",
    "Centre de production Route du Rilsan, 27470 Serquigny":    "Serquigny",
    "218 Rue Frédéric Kuhlmann, 60870 Villers-Saint-Paul":       "Villers-Saint-Paul",
}

# ═══════════════════════════════════════════════════════════════════════════
# ESPAGNE — Sites (code municipi officiel, plus fiable que le nom accentué)
# ═══════════════════════════════════════════════════════════════════════════

SITES_ESPAGNE = [
    ("Mollet del Vallès", "081249"),
    ("Sant Celoni",       "082021"),
]

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG APIs (⚠️ chaînes simples, pas de liens markdown)
# ═══════════════════════════════════════════════════════════════════════════

API_ADRESSE = "https://api-adresse.data.gouv.fr/search/"
API_VIGIEAU = "https://api.vigieau.gouv.fr/api/zones"
PROFIL      = "entreprise"

API_ACA = "https://analisi.transparenciacatalunya.cat/resource/i5n8-43cw.json"

GRAVITE_LABEL = {
    "vigilance":        "Vigilance",
    "alerte":           "Alerte",
    "alerte_renforcee": "Alerte renforcée",
    "crise":            "Crise",
}
GRAVITE_COLOR = {
    "Vigilance":        "#FFFB8A",
    "Alerte":           "#FFD04C",
    "Alerte renforcée": "#FF944C",
    "Crise":            "#FF4C4C",
}

ETAT_LABEL_ES = {
    "NORMALITAT":      "Normalitat",
    "PREALERTA":       "Prealerta",
    "ALERTA":          "Alerta",
    "EXCEPCIONALITAT": "Excepcionalitat",
    "PREEMERGÈNCIA":   "Preemergència",
    "EMERGÈNCIA":      "Emergència",
    "EMERGÈNCIA I":    "Emergència fase I",
}
ETAT_COLOR_ES = {
    "Normalitat":        "#D4F4DD",
    "Prealerta":         "#FFFB8A",
    "Alerta":            "#FFD04C",
    "Excepcionalitat":   "#FF944C",
    "Preemergència":     "#FF6B4C",
    "Emergència":        "#FF4C4C",
    "Emergència fase I": "#FF4C4C",
}

def dedup(lst):
    unique = list(dict.fromkeys([v for v in lst if v]))
    return " / ".join(unique) if unique else ""

# ═══════════════════════════════════════════════════════════════════════════
# ONGLETS
# ═══════════════════════════════════════════════════════════════════════════

tab_fr, tab_es = st.tabs(["🇫🇷 France (VigiEau)", "🇪🇸 Espagne (ACA Catalogne)"])

# ─────────────────────────────────────────────────────────────────────────
# ONGLET FRANCE
# ─────────────────────────────────────────────────────────────────────────
with tab_fr:
    with st.expander("✏️ Modifier la liste des adresses", expanded=False):
        adresses_txt = st.text_area("Une adresse par ligne", value=ADRESSES_DEFAULT, height=300)

    adresses = [a.strip() for a in adresses_txt.strip().splitlines() if a.strip()]
    st.info(f"**{len(adresses)} sites** chargés. Cliquez sur le bouton pour lancer l'analyse.")

    if st.button("🔍 Lancer l'analyse VigiEau", type="primary", use_container_width=True):
        rows     = []
        progress = st.progress(0, text="Démarrage...")

        for i, adresse in enumerate(adresses):
            progress.progress((i + 1) / len(adresses), text=f"⏳ {adresse}")
            row = {
                "Nom du site":        NOMS_SITES.get(adresse, ""),
                "Adresse":            adresse,
                "Niveau de gravité":  "NA",
                "Types d'eau":        "",
                "Arrêté — début":     "",
                "Arrêté — fin":       "",
                "Arrêté — PDF":       "",
            }

            # ── Géocodage ─────────────────────────────────────────────────
            try:
                geo      = requests.get(API_ADRESSE, params={"q": adresse, "limit": 1}, timeout=10).json()
                features = geo.get("features", [])
                if not features:
                    row["Niveau de gravité"] = "⚠️ Adresse non trouvée"
                    rows.append(row)
                    continue
                lon, lat = features[0]["geometry"]["coordinates"]
            except Exception:
                row["Niveau de gravité"] = "⚠️ Erreur géocodage"
                rows.append(row)
                continue

            # ── VigiEau ───────────────────────────────────────────────────
            try:
                resp = requests.get(
                    API_VIGIEAU,
                    params={"lon": lon, "lat": lat, "profil": PROFIL},
                    timeout=10
                )

                if resp.status_code == 404:
                    pass
                elif resp.status_code == 409:
                    row["Niveau de gravité"] = "⚠️ Zones multiples"
                elif resp.status_code == 200:
                    data  = resp.json()
                    zones = data if isinstance(data, list) else [data]

                    gravites_raw = [
                        (GRAVITE_LABEL.get(z.get("niveauGravite",""), z.get("niveauGravite","")), z.get("type",""))
                        for z in zones if z.get("niveauGravite")
                    ]
                    niveaux_uniques = set(g[0] for g in gravites_raw)
                    if len(niveaux_uniques) == 1 and niveaux_uniques:
                        row["Niveau de gravité"] = niveaux_uniques.pop()
                    elif gravites_raw:
                        row["Niveau de gravité"] = " / ".join(f"{g[0]} ({g[1]})" for g in gravites_raw)

                    types = [z.get("type","") for z in zones if z.get("type")]
                    row["Types d'eau"] = ", ".join(sorted(set(types)))

                    row["Arrêté — début"] = dedup([z.get("arrete",{}).get("dateDebutValidite","") for z in zones])
                    row["Arrêté — fin"]   = dedup([z.get("arrete",{}).get("dateFinValidite","")   for z in zones])
                    row["Arrêté — PDF"]   = dedup([z.get("arrete",{}).get("cheminFichier","")     for z in zones])
                else:
                    row["Niveau de gravité"] = f"⚠️ HTTP {resp.status_code}"
            except Exception:
                row["Niveau de gravité"] = "⚠️ Erreur VigiEau"

            rows.append(row)
            time.sleep(0.3)

        progress.empty()

        df = pd.DataFrame(rows, columns=[
            "Nom du site", "Adresse", "Niveau de gravité", "Types d'eau",
            "Arrêté — début", "Arrêté — fin", "Arrêté — PDF"
        ])

        nb_restr = df[
            ~df["Niveau de gravité"].isin(["NA", ""])
            & ~df["Niveau de gravité"].str.startswith("⚠️", na=False)
        ].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Sites analysés", len(df))
        col2.metric("Avec restriction", nb_restr)
        col3.metric("Sans restriction", len(df) - nb_restr)

        def colorize_row(row):
            niveau = row["Niveau de gravité"]
            for label, color in GRAVITE_COLOR.items():
                if label in niveau:
                    return [f"background-color: {color}"] * len(row)
            return [""] * len(row)

        st.dataframe(df.style.apply(colorize_row, axis=1), use_container_width=True, height=700)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="France")
        st.download_button(
            label="📥 Télécharger France (Excel)",
            data=buffer.getvalue(),
            file_name="vigieau_france.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ─────────────────────────────────────────────────────────────────────────
# ONGLET ESPAGNE
# ─────────────────────────────────────────────────────────────────────────
with tab_es:
    st.info(f"**{len(SITES_ESPAGNE)} sites** en Espagne (Catalogne). Cliquez pour lancer l'analyse.")

    if st.button("🔍 Lancer l'analyse ACA (Espagne)", type="primary", use_container_width=True):
        rows_es = []

        for nom, codi_municipi in SITES_ESPAGNE:
            row = {
                "Nom du site":                     nom,
                "Code municipi":                    codi_municipi,
                "État sécheresse (hidrològic)":     "NA",
                "État sécheresse (pluviomètric)":   "NA",
                "Date du dernier changement":       "",
            }
            try:
                resp = requests.get(
                    API_ACA,
                    params={
                        "codi_municipi": codi_municipi,
                        "$order": "data_canvi_estat_sequera DESC",
                        "$limit": 1,
                    },
                    timeout=15,
                )
                data = resp.json()
                if data:
                    d = data[0]
                    estat_hidro  = d.get("estat_sequera_hidrol_gic", "")
                    estat_pluvio = d.get("estat_sequera_pluviom_tric", "")
                    row["État sécheresse (hidrològic)"]   = ETAT_LABEL_ES.get(estat_hidro, estat_hidro)
                    row["État sécheresse (pluviomètric)"] = ETAT_LABEL_ES.get(estat_pluvio, estat_pluvio)
                    row["Date du dernier changement"]     = d.get("data_canvi_estat_sequera", "")[:10]
                else:
                    row["État sécheresse (hidrològic)"] = "⚠️ Commune non trouvée"
            except Exception as e:
                row["État sécheresse (hidrològic)"] = f"⚠️ Erreur : {e}"

            rows_es.append(row)
            time.sleep(0.3)

        df_es = pd.DataFrame(rows_es)

        def colorize_es(row):
            for label, color in ETAT_COLOR_ES.items():
                if label in str(row["État sécheresse (hidrològic)"]):
                    return [f"background-color: {color}"] * len(row)
            return [""] * len(row)

        st.dataframe(df_es.style.apply(colorize_es, axis=1), use_container_width=True)

        buffer_es = BytesIO()
        with pd.ExcelWriter(buffer_es, engine="openpyxl") as writer:
            df_es.to_excel(writer, index=False, sheet_name="Espagne")
        st.download_button(
            label="📥 Télécharger Espagne (Excel)",
            data=buffer_es.getvalue(),
            file_name="aca_espagne.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.caption("Source : Agència Catalana de l'Aigua (ACA) — dataset officiel des Conques Internes de Catalunya.")

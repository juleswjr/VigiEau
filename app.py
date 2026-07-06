import requests
import time
import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="VigiEau Arkema", page_icon="💧", layout="wide")
st.title("💧 VigiEau — Restrictions d'eau Arkema")
st.caption("Vérifie le niveau de restriction d'eau en vigueur pour chaque site Arkema.")

ADRESSES_DEFAULT = """AVELIN, 70 Rue de Lille, 59710 Avelin
CARLING, Route de Carling, 57500 Saint-Avold
CHATEAUROUX, 3 Allée de Chandaire, 36000 Châteauroux
COUBERT, RD319, 77170 Coubert
FEUCHY, Avenue de l'Hermitage, 62223 Saint-Laurent-Blangy
GENAY, 35 Rue Ampère, 69730 Genay
HONFLEUR, Avenue du Président Duchesne, 14600 Honfleur
JARRIE, N85 BP 16, 38560 Jarrie
LA CHAMBRE, Chemin des Brouves, 73130 La Chambre
LA FLOCELLIERE, 6 Rue de l'Avenir, 85700 Sèvremont
LACQ, 1 Route Départementale 817 64170 Lacq
LANNEMEZAN, 998 Route des Usines, 65300 Lannemezan
LE BARP, 6 Rue Guy Pellerin, 33114 Le Barp
LE MEUX, Rue du Buisson du Roi, 60880 Le Meux
LESGOR, 220 Route de L'Usine, 40400 Lesgor
MARSEILLE, 123 Boulevard de la Millière, 13011 Marseille
MONT, 122 Route des Pyrénées, 64300 Mont
MOURENX, Avenue du Bourg, 64150 Mourenx
PIERRE BENITE, 4 Chemin Henri Moissan, 69310 Pierre-Bénite
POUZAUGE, ZI MONTIFAUT 34 RUE RENE TRUHAUT, 85700 Pouzauges
PRIVAS, 160 Chemin de Saint-Claire, 07000 Privas
RIBECOURT, Rue de Bailly, 60170 Ribécourt-Dreslincourt
RION, 209 Avenue Charles Despiau, 40370 Rion-des-Landes
SAINT AUBAN, Avenue du Jas, 04600 Château-Arnoux-Saint-Auban
SAINVILLE, 27 Rue de la Porte de Dourdan, 28700 Sainville
SERQUINY, Centre de production Route du Rilsan, 27470 Serquigny
VILLERS ST PAUL, 218 Rue Frédéric Kuhlmann, 60870 Villers-Saint-Paul"""

API_ADRESSE = "https://api-adresse.data.gouv.fr/search/"
API_VIGIEAU = "https://api.vigieau.gouv.fr/api/zones"
PROFIL      = "entreprise"

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

def dedup(lst):
    unique = list(dict.fromkeys([v for v in lst if v]))
    return " / ".join(unique) if unique else ""

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
            "Adresse":          adresse,
            "Niveau de gravité": "NA",
            "Types d'eau":      "",
            "Arrêté — début":   "",
            "Arrêté — fin":     "",
            "Arrêté — PDF":     "",
        }

        # ── Géocodage ─────────────────────────────────────────────────────
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

        # ── VigiEau ───────────────────────────────────────────────────────
        try:
            resp = requests.get(
                API_VIGIEAU,
                params={"lon": lon, "lat": lat, "profil": PROFIL},
                timeout=10
            )

            if resp.status_code == 404:
                pass  # NA par défaut

            elif resp.status_code == 409:
                row["Niveau de gravité"] = "⚠️ Zones multiples"

            elif resp.status_code == 200:
                data  = resp.json()
                zones = data if isinstance(data, list) else [data]

                # Niveau de gravité
                gravites_raw = [
                    (GRAVITE_LABEL.get(z.get("niveauGravite",""), z.get("niveauGravite","")), z.get("type",""))
                    for z in zones if z.get("niveauGravite")
                ]
                niveaux_uniques = set(g[0] for g in gravites_raw)
                if len(niveaux_uniques) == 1:
                    row["Niveau de gravité"] = niveaux_uniques.pop()
                elif gravites_raw:
                    row["Niveau de gravité"] = " / ".join(f"{g[0]} ({g[1]})" for g in gravites_raw)

                # Types d'eau
                types = [z.get("type","") for z in zones if z.get("type")]
                row["Types d'eau"] = ", ".join(sorted(set(types)))

                # Arrêté
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
        "Adresse", "Niveau de gravité", "Types d'eau",
        "Arrêté — début", "Arrêté — fin", "Arrêté — PDF"
    ])

    # ── Résumé ────────────────────────────────────────────────────────────
    nb_restr = df[
        ~df["Niveau de gravité"].isin(["NA", ""])
        & ~df["Niveau de gravité"].str.startswith("⚠️", na=False)
    ].shape[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Sites analysés", len(df))
    col2.metric("Avec restriction", nb_restr)
    col3.metric("Sans restriction", len(df) - nb_restr)

    # ── Tableau coloré ────────────────────────────────────────────────────
    def colorize_row(row):
        niveau = row["Niveau de gravité"]
        for label, color in GRAVITE_COLOR.items():
            if label in niveau:
                return [f"background-color: {color}"] * len(row)
        return [""] * len(row)

    # Colonne PDF cliquable
    df_display = df.copy()
    df_display["Arrêté — PDF"] = df_display["Arrêté — PDF"].apply(
        lambda x: f'<a href="{x}" target="_blank">📄 Voir</a>' if x else ""
    )

    st.write(df.style.apply(colorize_row, axis=1).to_html(escape=False), unsafe_allow_html=True)

    # ── Export Excel ──────────────────────────────────────────────────────
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="VigiEau")
    st.download_button(
        label="📥 Télécharger en Excel",
        data=buffer.getvalue(),
        file_name="vigieau_arkema.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

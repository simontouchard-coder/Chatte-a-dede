import streamlit as st
import pandas as pd
import gspread
import time
from datetime import datetime, timedelta
from uuid import uuid4
import pytz

# --- CONFIGURATION ---
st.set_page_config(page_title="La chatte à Dédé 🐱", page_icon="🏆", layout="wide")
st.title("🏆 La chatte à Dédé 🐱")

ID_DU_SHEETS = "1IgtyJJDNGbRlJqztpGqyntstGsQVe0ojwshwDdmNqqA"

# --- EMOJIS DRAPEAUX ---
DRAPEAUX = {
    "France": "🇫🇷", "Allemagne": "🇩🇪", "Espagne": "🇪🇸", "Portugal": "🇵🇹",
    "Italie": "🇮🇹", "Angleterre": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Belgique": "🇧🇪", "Pays-Bas": "🇳🇱",
    "Croatie": "🇭🇷", "Danemark": "🇩🇰", "Suisse": "🇨🇭", "Autriche": "🇦🇹",
    "Pologne": "🇵🇱", "Suède": "🇸🇪", "Norvège": "🇳🇴", "Finlande": "🇫🇮",
    "République Tchèque": "🇨🇿", "Slovaquie": "🇸🇰", "Hongrie": "🇭🇺", "Roumanie": "🇷🇴",
    "Serbie": "🇷🇸", "Ukraine": "🇺🇦", "Turquie": "🇹🇷", "Grèce": "🇬🇷",
    "Ecosse": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Pays de Galles": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Irlande": "🇮🇪", "Irlande du Nord": "🇬🇧",
    "Russie": "🇷🇺", "Slovénie": "🇸🇮", "Albanie": "🇦🇱", "Géorgie": "🇬🇪",
    "Islande": "🇮🇸", "Luxembourg": "🇱🇺", "Kosovo": "🇽🇰", "Macédoine": "🇲🇰",
    "Monténégro": "🇲🇪", "Bosnie": "🇧🇦", "Bulgarie": "🇧🇬", "Lituanie": "🇱🇹",
    "Lettonie": "🇱🇻", "Estonie": "🇪🇪", "Biélorussie": "🇧🇾", "Moldavie": "🇲🇩",
    "Arménie": "🇦🇲", "Azerbaïdjan": "🇦🇿", "Kazakhstan": "🇰🇿", "Chypre": "🇨🇾",
    "Malte": "🇲🇹", "Andorre": "🇦🇩", "Gibraltar": "🇬🇮", "Liechtenstein": "🇱🇮",
    "Saint-Marin": "🇸🇲", "Faroe": "🇫🇴", "Maroc": "🇲🇦", "Sénégal": "🇸🇳",
    "Cameroun": "🇨🇲", "Ghana": "🇬🇭", "Nigeria": "🇳🇬", "Tunisie": "🇹🇳",
    "Algérie": "🇩🇿", "Egypte": "🇪🇬", "Côte d'Ivoire": "🇨🇮", "Mali": "🇲🇱",
    "Brésil": "🇧🇷", "Argentine": "🇦🇷", "Uruguay": "🇺🇾", "Colombie": "🇨🇴",
    "Chili": "🇨🇱", "Pérou": "🇵🇪", "Mexique": "🇲🇽", "États-Unis": "🇺🇸",
    "Canada": "🇨🇦", "Japon": "🇯🇵", "Corée du Sud": "🇰🇷", "Australie": "🇦🇺",
    "Iran": "🇮🇷", "Arabie Saoudite": "🇸🇦", "Qatar": "🇶🇦", "Chine": "🇨🇳",
    "Équateur": "🇪🇨", "Venezuela": "🇻🇪", "Vietnam": "🇻🇳",
}

def drapeau(equipe):
    return DRAPEAUX.get(equipe.strip(), "🏳️")

def equipe_avec_drapeau(equipe):
    return f"{drapeau(equipe)} {equipe}"

LISTE_EQUIPES_48 = [
    "Afrique du Sud", "Algérie", "Allemagne", "Angleterre", "Arabie saoudite",
    "Argentine", "Australie", "Autriche", "Belgique", "Bosnie-Herzégovine",
    "Brésil", "Cap-Vert", "Canada", "Colombie", "Corée du Sud", "Croatie",
    "Curaçao", "Côte d'Ivoire", "Danemark", "Espagne", "États-Unis", "France",
    "Ghana", "Haïti", "Irak", "Iran", "Japon", "Jordanie", "Maroc",
    "Norvège", "Nouvelle-Zélande", "Ouzbékistan", "Panama", "Paraguay",
    "Pays-Bas", "Portugal", "Qatar", "RD Congo", "République tchèque",
    "Sénégal", "Suède", "Suisse", "Tunisie", "Turquie", "Uruguay",
    "Écosse", "Égypte", "Équateur"
]

# --- TIMEZONE FRANCE ---
TZ_FRANCE = pytz.timezone("Europe/Paris")

def now_france():
    """Heure actuelle en heure française."""
    return datetime.now(TZ_FRANCE).replace(tzinfo=None)

# --- CONNEXION GOOGLE SHEETS ---
@st.cache_resource
def get_sheets():
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key("1IgtyJJDNGbRlJqztpGqyntstGsQVe0ojwshwDdmNqqA")
    return (
        sh,
        sh.worksheet("Calendrier"),
        sh.worksheet("Joueurs"),
        sh.worksheet("Pronostics"),
        sh.worksheet("Messages"),
        sh.worksheet("Vainqueurs"),
    )

sh, sheet_cal, sheet_joueurs, sheet_pro, sheet_msg, sheet_vainq = get_sheets()

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=5)
def charger_donnees():
    data = {}
    for nom, obj in [
        ("Calendrier", sheet_cal),
        ("Joueurs", sheet_joueurs),
        ("Pronostics", sheet_pro),
        ("Messages", sheet_msg),
    ]:
        v = obj.get_all_values()
        if len(v) > 1:
            df = pd.DataFrame(v[1:], columns=v[0])
        else:
            df = pd.DataFrame(columns=v[0])
        data[nom] = df
    return data

data = charger_donnees()
df_cal = data["Calendrier"]
df_joueurs = data["Joueurs"]
df_pro = data["Pronostics"]
df_msg = data["Messages"]

if not df_cal.empty:
    df_cal["Date_Heure_dt"] = pd.to_datetime(df_cal["Date_Heure"], dayfirst=True, errors="coerce")

# --- FONCTION DE CALCUL DES POINTS ---
def calculer_points(row_match, p_s1, p_s2):
    try:
        r_s1 = int(str(row_match["Score_1_Reel"]).strip())
        r_s2 = int(str(row_match["Score_2_Reel"]).strip())
        p_s1 = int(str(p_s1).strip())
        p_s2 = int(str(p_s2).strip())
    except Exception:
        return 0

    groupe = str(row_match.get("Groupe", "")).strip()

    if "Poule" in groupe:
        if p_s1 == 5 and p_s2 == 0 and r_s1 == 5 and r_s2 == 0:
            return 7
        if p_s1 == r_s1 and p_s2 == r_s2:
            return 3
        if (
            (p_s1 > p_s2 and r_s1 > r_s2)
            or (p_s1 < p_s2 and r_s1 < r_s2)
            or (p_s1 == p_s2 and r_s1 == r_s2)
        ):
            return 1
        return 0

    elif groupe in ["Seizième", "Huitième", "Quart", "Demi"]:
        bon_qualifie = (p_s1 > p_s2 and r_s1 > r_s2) or (p_s1 < p_s2 and r_s1 < r_s2)
        if not bon_qualifie:
            return 0
        if p_s1 == r_s1 and p_s2 == r_s2:
            return 5
        return 2

    elif groupe == "Petite Finale":
        bon_gagnant = (p_s1 > p_s2 and r_s1 > r_s2) or (p_s1 < p_s2 and r_s1 < r_s2)
        if not bon_gagnant:
            return 0
        if p_s1 == r_s1 and p_s2 == r_s2:
            return 8
        return 3

    elif groupe == "Finale":
        bon_vainqueur = (p_s1 > p_s2 and r_s1 > r_s2) or (p_s1 < p_s2 and r_s1 < r_s2)
        if not bon_vainqueur:
            return 0
        if p_s1 == r_s1 and p_s2 == r_s2:
            return 10
        return 4

    return 0

# --- RÉSULTAT VISUEL D'UN PRONO ---
def statut_prono(row_match, p_s1, p_s2):
    try:
        r_s1 = int(str(row_match["Score_1_Reel"]).strip())
        r_s2 = int(str(row_match["Score_2_Reel"]).strip())
        ps1 = int(str(p_s1).strip())
        ps2 = int(str(p_s2).strip())
    except Exception:
        return ""
    if ps1 == r_s1 and ps2 == r_s2:
        return "🎯"
    bon = (
        (ps1 > ps2 and r_s1 > r_s2)
        or (ps1 < ps2 and r_s1 < r_s2)
        or (ps1 == ps2 and r_s1 == r_s2)
    )
    return "✅" if bon else "❌"

# --- CALCUL DU CLASSEMENT ---
def get_classement():
    if df_cal.empty or df_pro.empty:
        return pd.DataFrame()

    df_pro_saisis = df_pro[
        (df_pro["Prono_Score_1"].astype(str).str.strip() != "")
        & (df_pro["Prono_Score_2"].astype(str).str.strip() != "")
    ].copy()

    if df_pro_saisis.empty:
        return pd.DataFrame()

    df_cal_scores = df_cal[
        (df_cal["Score_1_Reel"].astype(str).str.strip() != "")
        & (df_cal["Score_2_Reel"].astype(str).str.strip() != "")
    ].copy()

    if df_cal_scores.empty:
        return pd.DataFrame()

    df_merge = pd.merge(
        df_pro_saisis,
        df_cal_scores,
        on="ID_Match",
        how="inner",
        suffixes=("_pro", "_cal"),
    )

    df_merge["Points"] = df_merge.apply(
        lambda r: calculer_points(r, r["Prono_Score_1"], r["Prono_Score_2"]),
        axis=1,
    )

    # --- Bon vainqueur (sans score exact) ---
    def est_bon_vainqueur(r):
        try:
            r_s1 = int(str(r["Score_1_Reel"]).strip())
            r_s2 = int(str(r["Score_2_Reel"]).strip())
            p_s1 = int(str(r["Prono_Score_1"]).strip())
            p_s2 = int(str(r["Prono_Score_2"]).strip())
        except Exception:
            return False
        score_exact = (p_s1 == r_s1 and p_s2 == r_s2)
        bon = (
            (p_s1 > p_s2 and r_s1 > r_s2)
            or (p_s1 < p_s2 and r_s1 < r_s2)
            or (p_s1 == p_s2 and r_s1 == r_s2)
        )
        return bon and not score_exact

    def est_score_exact(r):
        try:
            r_s1 = int(str(r["Score_1_Reel"]).strip())
            r_s2 = int(str(r["Score_2_Reel"]).strip())
            p_s1 = int(str(r["Prono_Score_1"]).strip())
            p_s2 = int(str(r["Prono_Score_2"]).strip())
        except Exception:
            return False
        return p_s1 == r_s1 and p_s2 == r_s2

    df_merge["Bon_Vainqueur"] = df_merge.apply(est_bon_vainqueur, axis=1).astype(int)
    df_merge["Score_Exact"] = df_merge.apply(est_score_exact, axis=1).astype(int)

    classement = df_merge.groupby("Joueur", as_index=False).agg(
        Points=("Points", "sum"),
        Bons_pronos=("Bon_Vainqueur", "sum"),
        Scores_exacts=("Score_Exact", "sum"),
    )

    # BONUS VAINQUEUR FINAL
    match_finale = df_cal[df_cal["Groupe"] == "Finale"]
    if not match_finale.empty:
        f = match_finale.iloc[0]
        s1_str = str(f["Score_1_Reel"]).strip()
        s2_str = str(f["Score_2_Reel"]).strip()
        if s1_str.isdigit() and s2_str.isdigit():
            s1, s2 = int(s1_str), int(s2_str)
            if s1 != s2:
                vainqueur_final = f["Equipe_1"] if s1 > s2 else f["Equipe_2"]
                df_vainqueurs = pd.DataFrame(
                    sheet_vainq.get_all_values()[1:],
                    columns=["Joueur", "Equipe_Pariée"]
                )
                for _, row in df_vainqueurs.iterrows():
                    if row["Equipe_Pariée"] == vainqueur_final:
                        if row["Joueur"] in classement["Joueur"].values:
                            classement.loc[classement["Joueur"] == row["Joueur"], "Points"] += 10
                        else:
                            new_row = pd.DataFrame({"Joueur": [row["Joueur"]], "Points": [10], "Bons_pronos": [0], "Scores_exacts": [0]})
                            classement = pd.concat([classement, new_row], ignore_index=True)

    classement = classement.sort_values("Points", ascending=False).reset_index(drop=True)
    classement.index += 1
    return classement

# --- NAVIGATION ---
tab_accueil, tab_pronos, tab_classement, tab_forum, tab_regles, tab_admin = st.tabs(
    ["🏠 Accueil", "⚽ Pronos", "📊 Classement", "💬 Forum", "📖 Règles", "⚙️ Admin"]
)

# ---------------------------------------------------------------
# ACCUEIL
# ---------------------------------------------------------------
with tab_accueil:
    col_auth, col_info = st.columns([1, 2])

    with col_auth:
        st.subheader("Authentification")
        if not st.session_state.get("auth_ok"):
            if df_joueurs.empty:
                st.warning("Aucun joueur enregistré. Ajoute-en via l'onglet Admin.")
            else:
                joueurs_liste = df_joueurs["Joueur"].dropna().unique().tolist()
                joueur = st.selectbox("Qui êtes-vous ?", ["Choisir..."] + joueurs_liste)
                if joueur != "Choisir...":
                    mdp = st.text_input("Mot de passe :", type="password")
                    if st.button("Connexion"):
                        j_info = df_joueurs[df_joueurs["Joueur"] == joueur].iloc[0]
                        if mdp == str(j_info["Mot_de_Passe"]):
                            st.session_state["joueur_actif"] = joueur
                            st.session_state["auth_ok"] = True
                            st.rerun()
                        else:
                            st.error("Code erroné.")
        else:
            st.success(f"Connecté : {st.session_state['joueur_actif']}")
            if st.button("Déconnexion"):
                st.session_state.clear()
                st.rerun()

    with col_info:
        st.subheader("📅 Matchs du jour")
        now = now_france()
        aujourd_hui = now.date()

        if not df_cal.empty:
            matchs_jour = df_cal[df_cal["Date_Heure_dt"].dt.date == aujourd_hui].copy()
            if matchs_jour.empty:
                st.info("Aucun match aujourd'hui.")
            else:
                for _, m in matchs_jour.iterrows():
                    heure = m["Date_Heure_dt"].strftime("%H:%M")
                    e1 = equipe_avec_drapeau(m["Equipe_1"])
                    e2 = equipe_avec_drapeau(m["Equipe_2"])
                    s1 = str(m["Score_1_Reel"]).strip()
                    s2 = str(m["Score_2_Reel"]).strip()
                    score_txt = f"**{s1} – {s2}** ✅" if s1 and s2 else f"*{heure}*"
                    st.markdown(
                        f"🕐 `{heure}` &nbsp;|&nbsp; {e1} **vs** {e2} "
                        f"&nbsp;|&nbsp; {score_txt} &nbsp;|&nbsp; _{m['Groupe']}_"
                    )
        else:
            st.info("Calendrier vide.")

        st.divider()

        st.subheader("🏆 Top 5")
        classement = get_classement()
        if classement.empty:
            st.info("Pas encore de scores calculés.")
        else:
            medailles = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, (_, row) in enumerate(classement.head(5).iterrows()):
                st.markdown(f"{medailles[i]} &nbsp; **{row['Joueur']}** &nbsp;—&nbsp; {int(row['Points'])} pts")

# ---------------------------------------------------------------
# PRONOS
# ---------------------------------------------------------------
with tab_pronos:
    if not st.session_state.get("auth_ok"):
        st.warning("Authentification requise (onglet Accueil).")
    else:
        joueur_actif = st.session_state["joueur_actif"]
        now = now_france()

        # --- PARI VAINQUEUR FINAL ---
        st.subheader("🏆 Pari Vainqueur Final")
        date_limite_vainqueur = datetime(2026, 6, 11, 23, 59, 59)
        est_verrouille_vainqueur = now > date_limite_vainqueur

        df_vainq = pd.DataFrame(
            sheet_vainq.get_all_values()[1:],
            columns=["Joueur", "Equipe_Pariée"]
        )
        pari = df_vainq[df_vainq["Joueur"] == joueur_actif]

        if est_verrouille_vainqueur:
            if not pari.empty:
                st.info(f"🔒 Ton vainqueur final est verrouillé : **{equipe_avec_drapeau(pari.iloc[0]['Equipe_Pariée'])}**")
            else:
                st.warning("Date limite dépassée : aucun pari vainqueur enregistré.")
        else:
            valeur_actuelle = pari.iloc[0]["Equipe_Pariée"] if not pari.empty else LISTE_EQUIPES_48[0]
            idx_defaut = LISTE_EQUIPES_48.index(valeur_actuelle) if valeur_actuelle in LISTE_EQUIPES_48 else 0
            with st.form("form_vainqueur"):
                choix = st.selectbox(
                    "Qui gagnera la Coupe du Monde ?",
                    [equipe_avec_drapeau(e) for e in LISTE_EQUIPES_48],
                    index=idx_defaut
                )
                if st.form_submit_button("Valider mon choix"):
                    nom_choix = LISTE_EQUIPES_48[[equipe_avec_drapeau(e) for e in LISTE_EQUIPES_48].index(choix)]
                    if not pari.empty:
                        sheet_vainq.update_cell(pari.index[0] + 2, 2, nom_choix)
                    else:
                        sheet_vainq.append_row([joueur_actif, nom_choix])
                    st.success(f"Pari enregistré : {choix} !")
                    st.rerun()

        st.divider()

        # --- PRONOSTICS MATCHS ---
        st.subheader("Saisie des pronostics")

        if df_cal.empty:
            st.info("Aucun match dans le calendrier.")
        else:
            masquer_passes = st.toggle("Masquer les matchs passés", value=False)

            df_a_venir = df_cal[
                df_cal["Date_Heure_dt"].isna() | (df_cal["Date_Heure_dt"] > now)
            ].copy()
            df_passes = df_cal[
                df_cal["Date_Heure_dt"].notna() & (df_cal["Date_Heure_dt"] <= now)
            ].copy()

            # --- MATCHS À VENIR ---
            st.markdown("#### ⏳ Matchs à venir")
            if df_a_venir.empty:
                st.info("Tous les matchs sont passés.")
            else:
                with st.form("form_pronos"):

                    st.divider()

                    for _, row in df_a_venir.iterrows():
                        m_id = str(row["ID_Match"]).strip()
                        if not m_id:
                            continue

                        prono = df_pro[
                            (df_pro["Joueur"] == joueur_actif)
                            & (df_pro["ID_Match"] == m_id)
                            & (df_pro["Prono_Score_1"].astype(str).str.strip() != "")
                            & (df_pro["Prono_Score_2"].astype(str).str.strip() != "")
                        ]

                        dt_match = pd.to_datetime(row["Date_Heure"], dayfirst=True, errors="coerce")
                        dans_24h = pd.notna(dt_match) and (dt_match - now) < timedelta(hours=24)

                        if not prono.empty:
                            try:
                                v1 = int(str(prono.iloc[0]["Prono_Score_1"]).strip())
                            except Exception:
                                v1 = None
                            try:
                                v2 = int(str(prono.iloc[0]["Prono_Score_2"]).strip())
                            except Exception:
                                v2 = None
                            statut_saisie = "✅"
                        else:
                            v1, v2 = None, None
                            statut_saisie = "⚠️" if dans_24h else "🔲"

                        e1 = equipe_avec_drapeau(row["Equipe_1"])
                        e2 = equipe_avec_drapeau(row["Equipe_2"])

                        c0, c1, c2, c3 = st.columns([0.3, 3.5, 1, 1])
                        c0.write(statut_saisie)
                        c1.write(f"**{row['Groupe']}** — {row['Date_Heure']} — {e1} vs {e2}")
                        c2.number_input(
                            f"score1_{m_id}", 0, 10,
                            value=v1,
                            placeholder="?",
                            label_visibility="collapsed",
                            key=f"i1_{m_id}",
                        )
                        c3.number_input(
                            f"score2_{m_id}", 0, 10,
                            value=v2,
                            placeholder="?",
                            label_visibility="collapsed",
                            key=f"i2_{m_id}",
                        )

                    st.divider()

                    submit_pronos = st.form_submit_button(
                        "💾 Enregistrer les pronos",
                        type="primary",
                        use_container_width=True,
                    )

                if submit_pronos:
                    now_str = now_france().strftime("%Y-%m-%d %H:%M:%S")
                    df_pro_local = charger_donnees()["Pronostics"]
                    for _, row in df_a_venir.iterrows():
                        m_id = str(row["ID_Match"]).strip()
                        if not m_id:
                            continue
                        dt_match = pd.to_datetime(row["Date_Heure"], dayfirst=True, errors="coerce")
                        if pd.notna(dt_match) and now_france() >= dt_match:
                            continue
                        s1 = st.session_state.get(f"i1_{m_id}")
                        s2 = st.session_state.get(f"i2_{m_id}")
                        if s1 is None or s2 is None:
                            continue
                        prono_exist = df_pro_local[
                            (df_pro_local["Joueur"] == joueur_actif)
                            & (df_pro_local["ID_Match"] == m_id)
                            & (df_pro_local["Prono_Score_1"].astype(str).str.strip() != "")
                            & (df_pro_local["Prono_Score_2"].astype(str).str.strip() != "")
                        ]
                        if prono_exist.empty:
                            for attempt in range(3):
                                try:
                                    sheet_pro.append_row([
                                        str(uuid4()), joueur_actif, m_id,
                                        str(s1), str(s2), now_str,
                                    ])
                                    break
                                except Exception:
                                    if attempt < 2:
                                        time.sleep(2 ** attempt)
                        else:
                            row_idx = prono_exist.index[0] + 2
                            for attempt in range(3):
                                try:
                                    sheet_pro.update(f"D{row_idx}:F{row_idx}", [[str(s1), str(s2), now_str]])
                                    break
                                except Exception:
                                    if attempt < 2:
                                        time.sleep(2 ** attempt)
                    st.success("Pronostics enregistrés !")
                    st.cache_data.clear()
                    st.rerun()

            # --- MATCHS PASSÉS ---
            if not masquer_passes and not df_passes.empty:
                st.markdown("#### 🔒 Matchs passés — Résultats de tes pronos")
                for _, row in df_passes.sort_values("Date_Heure_dt", ascending=False).iterrows():
                    m_id = str(row["ID_Match"]).strip()
                    if not m_id:
                        continue
                    prono = df_pro[
                        (df_pro["Joueur"] == joueur_actif)
                        & (df_pro["ID_Match"] == m_id)
                        & (df_pro["Prono_Score_1"].astype(str).str.strip() != "")
                        & (df_pro["Prono_Score_2"].astype(str).str.strip() != "")
                    ]
                    e1 = equipe_avec_drapeau(row["Equipe_1"])
                    e2 = equipe_avec_drapeau(row["Equipe_2"])
                    s1_reel = str(row["Score_1_Reel"]).strip()
                    s2_reel = str(row["Score_2_Reel"]).strip()
                    score_reel = f"{s1_reel}–{s2_reel}" if s1_reel and s2_reel else "Score non renseigné"
                    if not prono.empty:
                        ps1 = prono.iloc[0]["Prono_Score_1"]
                        ps2 = prono.iloc[0]["Prono_Score_2"]
                        icone = statut_prono(row, ps1, ps2)
                        pts = calculer_points(row, ps1, ps2)
                        prono_txt = f"Ton prono : **{ps1}–{ps2}** {icone} ({pts} pt{'s' if pts > 1 else ''})"
                    else:
                        prono_txt = "⚠️ Pas de prono enregistré"
                    st.markdown(
                        f"**{row['Groupe']}** — {row['Date_Heure']} &nbsp;|&nbsp; "
                        f"{e1} **vs** {e2} &nbsp;|&nbsp; Score réel : **{score_reel}** "
                        f"&nbsp;|&nbsp; {prono_txt}"
                    )

# ---------------------------------------------------------------
# CLASSEMENT COMPLET
# ---------------------------------------------------------------
with tab_classement:
    st.subheader("📊 Classement complet")
    classement = get_classement()
    if classement.empty:
        st.info("Pas encore de scores calculés (aucun match terminé ou pronostics vides).")
    else:
        medailles = ["🥇", "🥈", "🥉"]
        classement["🏅"] = [
            medailles[i] if i < 3 else str(i + 1)
            for i in range(len(classement))
        ]
        classement = classement[["🏅", "Joueur", "Points", "Bons_pronos", "Scores_exacts"]]
        classement = classement.rename(columns={
            "Bons_pronos": "✅ Bons pronos",
            "Scores_exacts": "🎯 Scores exacts",
        })
        st.dataframe(classement, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------
# FORUM
# ---------------------------------------------------------------
with tab_forum:
    st.subheader("💬 Forum")
    if df_msg.empty:
        st.info("Aucun message pour l'instant.")
    else:
        for _, msg in df_msg.iterrows():
            st.markdown(f"**{msg['Pseudo']}** : {msg['Message']}")

    with st.form("form_forum", clear_on_submit=True):
        pseudo = st.session_state.get("joueur_actif", "Anonyme")
        message = st.text_input("Message :")
        envoyer = st.form_submit_button("Envoyer")
        if envoyer:
            if message.strip():
                sheet_msg.append_row([pseudo, message])
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Message vide.")

# ---------------------------------------------------------------
# RÈGLES
# ---------------------------------------------------------------
with tab_regles:
    st.subheader("📖 Règles du jeu")
    st.markdown("""
    ## 🏆 La chatte à Dédé — Règles complètes

    ### 🔐 Connexion & Pronos
    - 1ère connexion, va dans l'onglet admin, inscris ton nom puis crée ton mot de passe. retourne ensuite sur l'onglet Accueil pour te connecter
    - Connecte-toi via l'onglet **Accueil** avec ton pseudo et ton mot de passe.
    - Tes pronostics sont **verrouillés automatiquement** à l'heure du coup d'envoi de chaque match.
    - Pour une première saisie, cliquez sur le "?" et entrez directement un score.
    - Tu peux modifier un prono tant que le match n'a pas commencé.
    - Un match où tu n'as rien saisi ne compte pas — **seuls les pronos explicitement enregistrés sont pris en compte**.
      Donc n'oublie pas d'appuyer sur le gros bouton rouge en bas

    ---

    ### ✅ Indicateurs de saisie (matchs à venir)
    | Icône | Signification |
    |---|---|
    | ✅ | Prono enregistré pour ce match |
    | ⚠️ | Match dans moins de 24h — tu n'as pas encore pronostiqué ! |
    | 🔲 | Match à venir — prono non saisi |

    ---

    ### 🎯 Résultats de tes pronos (matchs passés)
    | Icône | Signification |
    |---|---|
    | 🎯 | Score exact — maximum de points ! |
    | ✅ | Bon vainqueur ou bon nul — points partiels |
    | ❌ | Mauvais prono — 0 point |
    | ⚠️ | Pas de prono enregistré pour ce match |

    ---

    ### ⚽ Barème des points

    **Phase de poules**
    | Résultat | Points |
    |---|---|
    | Bon vainqueur ou match nul | 1 pt |
    | Score exact | 3 pts |
    | Prono 5–0 sur vrai 5–0 | 7 pts 🎉 |

    **Seizième · Huitième · Quart · Demi-finale**
    | Résultat | Points |
    |---|---|
    | Bonne équipe qualifiée | 2 pts |
    | + Bon score au temps réglementaire | +3 pts (5 pts total) |

    **Petite Finale**
    | Résultat | Points |
    |---|---|
    | Bonne équipe gagnante | 3 pts |
    | + Bon score au temps réglementaire | +5 pts (8 pts total) |

    **Finale**
    | Résultat | Points |
    |---|---|
    | Bon vainqueur | 4 pts |
    | + Bon score au temps réglementaire | +6 pts (10 pts total) |

    ---

    ### 🌍 Pari Vainqueur Final
    - Avant le **11 juin 2026 à 23h59**, tu peux parier sur l'équipe qui remportera la Coupe du Monde.
    - Si ton équipe gagne la finale : **+10 pts bonus** sur ton total !
    - Ce pari est **définitivement verrouillé** après la date limite.

    ---

    ### 💬 Forum
    - L'onglet **Forum** permet à tous les participants de laisser des messages librement.
    - C'est l'endroit pour chambrer, encourager, se plaindre des arbitres ou simplement papoter.
    - Une seule règle : **le respect**. Les messages irrespectueux envers les autres participants ne sont pas tolérés.

    ---

    ### 👁️ Affichage des matchs
    - Dans l'onglet **Pronos**, tu peux masquer/afficher les matchs passés avec le toggle en haut.
    - Les matchs passés affichent automatiquement le score réel et le résultat de ton prono.
    """)

# ---------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------
with tab_admin:
    st.subheader("⚙️ Admin - Gestion des joueurs")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Nom du joueur :")
    with col2:
        new_mdp = st.text_input("Mot de passe :")
    if st.button("Ajouter le joueur"):
        if new_name.strip() and new_mdp.strip():
            if not df_joueurs.empty and (df_joueurs["Joueur"] == new_name).any():
                st.error("Ce joueur existe déjà.")
            else:
                sheet_joueurs.append_row([new_name, new_mdp, "0"])
                st.success(f"Joueur {new_name} ajouté.")
                st.cache_data.clear()
                st.rerun()
        else:
            st.error("Nom et mot de passe obligatoires.")

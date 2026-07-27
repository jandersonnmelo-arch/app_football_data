import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Análise - Football-Data.org", page_icon="📊", layout="wide")
st.title("📊 Análise com Football-Data.org")

# 🔴 COLE SUA CHAVE AQUI
API_KEY = "51d62042229e4f4a9532b6376203e602"
HEADERS = {"X-Auth-Token": API_KEY}

# Códigos das competições gratuitas
COMPETICOES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA",
    "🇫🇷 Ligue 1": "FL1",
    "🏆 Champions League": "CL",
    "🇧🇷 Brasileirão Série A": "BSA"
}

def buscar_jogos(sigla, dias=7):
    url = f"https://api.football-data.org/v4/competitions/{sigla}/matches"
    params = {"status": "SCHEDULED", "limit": 50}
    r = requests.get(url, headers=HEADERS, params=params, timeout=15).json()
    return r.get("matches", [])

def buscar_classificacao(sigla):
    url = f"https://api.football-data.org/v4/competitions/{sigla}/standings"
    r = requests.get(url, headers=HEADERS, timeout=15).json()
    return r.get("standings", [{}])[0].get("table", [])

# Interface
comp = st.selectbox("Escolha a Competição", list(COMPETICOES.keys()))
dias = st.slider("Próximos dias", 1,14,7)

jogos = buscar_jogos(COMPETICOES[comp])
hoje = datetime.utcnow()
filtrado = [j for j in jogos if datetime.fromisoformat(j["utcDate"]) <= hoje + timedelta(days=dias)]

if not filtrado:
    st.warning("Nenhum jogo encontrado no período.")
else:
    st.success(f"{len(filtrado)} jogos encontrados")
    st.subheader("📋 Próximas Partidas")
    df_jogos = pd.DataFrame([{
        "Data (BR)": datetime.fromisoformat(j["utcDate"].replace("Z","-04:00")).strftime("%d/%m %H:%M"),
        "Mandante": j["homeTeam"]["name"],
        "Visitante": j["awayTeam"]["name"]
    } for j in filtrado])
    st.dataframe(df_jogos, use_container_width=True, hide_index=True)

    st.subheader("📈 Tabela de Classificação")
    tab = buscar_classificacao(COMPETICOES[comp])
    if tab:
        df_tab = pd.DataFrame([{
            "Pos": t["position"],
            "Time": t["team"]["name"],
            "Jogos": t["playedGames"],
            "Vitórias": t["won"],
            "Empates": t["draw"],
            "Derrotas": t["lost"],
            "Pts": t["points"]
        } for t in tab])
        st.dataframe(df_tab, use_container_width=True, hide_index=True)

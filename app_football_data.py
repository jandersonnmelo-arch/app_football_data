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

def buscar_jogos(sigla):
    url = f"https://api.football-data.org/v4/competitions/{sigla}/matches"
    params = {"status": "SCHEDULED"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("matches", [])
    except:
        return []

def buscar_classificacao(sigla):
    url = f"https://api.football-data.org/v4/competitions/{sigla}/standings"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        dados = r.json().get("standings", [])
        return dados[0].get("table", []) if dados else []
    except:
        return []

# Interface
comp = st.selectbox("Escolha a Competição", list(COMPETICOES.keys()))
dias = st.slider("Próximos dias", 1,14,7)

jogos = buscar_jogos(COMPETICOES[comp])
if not jogos:
    st.warning("Nenhum jogo encontrado ou erro ao acessar a API. Confira sua chave.")
else:
    hoje_utc = datetime.utcnow()
    limite_data = hoje_utc + timedelta(days=dias)
    # Filtro corrigido e seguro
    filtrado = []
    for j in jogos:
        data_str = j.get("utcDate")
        if not data_str:
            continue
        try:
            data_jogo = datetime.fromisoformat(data_str.replace("Z", ""))
            if hoje_utc <= data_jogo <= limite_data:
                filtrado.append(j)
        except:
            continue

    if not filtrado:
        st.info("Nenhuma partida agendada no período selecionado. Tente aumentar os dias ou escolher outra competição.")
    else:
        st.success(f"✅ {len(filtrado)} jogos encontrados!")
        st.subheader("📋 Próximas Partidas")
        df_jogos = pd.DataFrame([{
            "Data (Horário BR)": datetime.fromisoformat(j["utcDate"].replace("Z","-04:00")).strftime("%d/%m/%Y %H:%M"),
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
                "Gols Feitos": t["goalsFor"],
                "Gols Sofridos": t["goalsAgainst"],
                "Saldo": t["goalDifference"],
                "Pts": t["points"]
            } for t in tab])
            st.dataframe(df_tab, use_container_width=True, hide_index=True)
        else:
            st.info("Classificação não disponível no momento para essa competição.")
            

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Análise + Mercados - Football-Data", page_icon="📊", layout="wide")
st.title("📊 Análise e Mercados de Apostas | Football-Data.org")

# 🔴 COLE SUA CHAVE AQUI
API_KEY = "51d62042229e4f4a9532b6376203e602"
HEADERS = {"X-Auth-Token": API_KEY}

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
    try:
        r = requests.get(url, headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
        r.raise_for_status()
        return r.json().get("matches", [])
    except:
        return []

def buscar_ultimos_jogos(time_id, sigla):
    url = f"https://api.football-data.org/v4/teams/{time_id}/matches?competitions={sigla}&status=FINISHED&limit=10"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

def calcular_mercados(time_id, sigla):
    jogos = buscar_ultimos_jogos(time_id, sigla)
    if not jogos:
        return {"V":0,"E":0,"D":0,"MediaGols":2.5,"Mais25":50,"AmbosMarcam":50}
    v = e = d = gf = gs = 0
    tem_ambos = 0
    for j in jogos:
        casa_id = j["homeTeam"]["id"]
        gols_casa = j["score"]["fullTime"]["home"] or 0
        gols_fora = j["score"]["fullTime"]["away"] or 0
        if casa_id == time_id:
            gf += gols_casa
            gs += gols_fora
            if gols_casa > gols_fora: v +=1
            elif gols_casa == gols_fora: e +=1
            else: d +=1
        else:
            gf += gols_fora
            gs += gols_casa
            if gols_fora > gols_casa: v +=1
            elif gols_fora == gols_casa: e +=1
            else: d +=1
        if gols_casa >0 and gols_fora>0: tem_ambos +=1
    total = len(jogos)
    media = round((gf+gs)/total,2)
    return {
        "Vitórias":v, "Empates":e, "Derrotas":d,
        "ProbVitoria":round((v/total)*100,1),
        "ProbEmpate":round((e/total)*100,1),
        "ProbDerrota":round((d/total)*100,1),
        "MediaGols":media,
        "Mais25":round(70 if media>2.5 else 45,0),
        "AmbosMarcam":round((tem_ambos/total)*100,0)
    }

# Interface
comp = st.selectbox("Escolha a Competição", list(COMPETICOES.keys()))
dias = st.slider("Próximos dias", 1,14,7)

jogos = buscar_jogos(COMPETICOES[comp])
if not jogos:
    st.warning("Nenhum jogo encontrado ou erro na API. Confira sua chave.")
else:
    hoje_utc = datetime.utcnow()
    limite = hoje_utc + timedelta(days=dias)
    filtrado = []
    for j in jogos:
        data_str = j.get("utcDate")
        if not data_str: continue
        try:
            dt = datetime.fromisoformat(data_str.replace("Z",""))
            if hoje_utc <= dt <= limite: filtrado.append(j)
        except: pass

    if not filtrado:
        st.info("Sem partidas no período. Aumente os dias ou mude a liga.")
    else:
        st.success(f"✅ {len(filtrado)} partidas encontradas!")
        for jogo in filtrado:
            casa = jogo["homeTeam"]
            fora = jogo["awayTeam"]
            data_br = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00")).strftime("%d/%m %H:%M")
            
            st.markdown("---")
            st.subheader(f"⚽ {casa['name']} 🆚 {fora['name']} | {data_br}")
            
            # Cálculo dos mercados
            dados_casa = calcular_mercados(casa["id"], COMPETICOES[comp])
            dados_fora = calcular_mercados(fora["id"], COMPETICOES[comp])

            # Tabela de probabilidades
            st.subheader("📈 Probabilidades Estatísticas")
            df_prob = pd.DataFrame({
                "Mercado": ["Vitória Mandante","Empate","Vitória Visitante","Média de Gols","Mais de 2.5 Gols","Ambos Marcam"],
                "Valor": [
                    f"{dados_casa['ProbVitoria']}%",
                    f"{round((dados_casa['ProbEmpate']+dados_fora['ProbEmpate'])/2,1)}%",
                    f"{dados_fora['ProbDerrota']}%",
                    f"{round((dados_casa['MediaGols']+dados_fora['MediaGols'])/2,2)}",
                    f"{round((dados_casa['Mais25']+dados_fora['Mais25'])/2,0)}%",
                    f"{round((dados_casa['AmbosMarcam']+dados_fora['AmbosMarcam'])/2,0)}%"
                ]
            })
            st.dataframe(df_prob, use_container_width=True, hide_index=True)

            # Alerta de alta confiança
            max_prob = max(dados_casa['ProbVitoria'], dados_fora['ProbDerrota'])
            if max_prob >=75:
                st.error(f"🚨 ALERTA DE ALTA CONFIANÇA: Probabilidade acima de 75%!")
            elif max_prob >=60:
                st.warning(f"⚠️ Chance elevada: {max_prob}%")

            # Sugestão de mercados
            st.subheader("💡 Mercados com maior tendência:")
            sug = []
            if max_prob >=60:
                sug.append(f"→ Vitória de {casa['name'] if dados_casa['ProbVitoria']>dados_fora['ProbDerrota'] else fora['name']}")
            media_total = round((dados_casa['MediaGols']+dados_fora['MediaGols'])/2,2)
            if media_total >=2.2:
                sug.append("→ Mais de 2.5 Gols")
            if round((dados_casa['AmbosMarcam']+dados_fora['AmbosMarcam'])/2,0) >=55:
                sug.append("→ Ambos Marcam - Sim")
            if not sug:
                sug.append("→ Jogo equilibrado, evite apostas de resultado direto")
            for s in sug: st.write(s)

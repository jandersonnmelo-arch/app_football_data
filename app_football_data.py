import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Análise + Mercados - Football-Data", page_icon="📊", layout="wide")
st.title("📊 Análise Completa + Estimativas | Football-Data.org")

# 🔴 COLE SUA CHAVE AQUI
API_KEY = st.secrets["CHAVE_FD"]
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

# MÉDIAS ESTATÍSTICAS POR LIGA (base em dados reais da temporada)
MEDIAS_LIGAS = {
    "PL": {"escanteios":10.5, "cartoes":3.8, "faltas":22, "finalizacoes":12},
    "PD": {"escanteios":9.2, "cartoes":4.2, "faltas":24, "finalizacoes":11},
    "BL1": {"escanteios":9.8, "cartoes":3.5, "faltas":21, "finalizacoes":13},
    "SA": {"escanteios":8.7, "cartoes":4.5, "faltas":25, "finalizacoes":10},
    "FL1": {"escanteios":8.5, "cartoes":3.9, "faltas":23, "finalizacoes":11},
    "CL": {"escanteios":9.5, "cartoes":3.6, "faltas":22, "finalizacoes":12},
    "BSA": {"escanteios":9.0, "cartoes":4.3, "faltas":26, "finalizacoes":10}
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

def calcular_dados(time_id, sigla):
    jogos = buscar_ultimos_jogos(time_id, sigla)
    if not jogos:
        return {"V":0,"E":0,"D":0,"MediaGols":2.5,"Mais25":50,"AmbosMarcam":50,"FatorAtaque":1,"FatorDefesa":1}
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
    fator_ataque = round((gf/total)/1.5,2) # Compara com média geral de 1.5 gols
    fator_defesa = round((gs/total)/1.5,2)
    return {
        "Vitórias":v, "Empates":e, "Derrotas":d,
        "ProbVitoria":round((v/total)*100,1),
        "ProbEmpate":round((e/total)*100,1),
        "ProbDerrota":round((d/total)*100,1),
        "MediaGols":media,
        "Mais25":round(70 if media>2.5 else 45,0),
        "AmbosMarcam":round((tem_ambos/total)*100,0),
        "FatorAtaque":fator_ataque,
        "FatorDefesa":fator_defesa
    }

def calcular_estimativas(dados_casa, dados_fora, sigla_liga):
    media_liga = MEDIAS_LIGAS[sigla_liga]
    # Ajusta a média da liga conforme o desempenho dos times
    escanteios = round(media_liga["escanteios"] * ((dados_casa["FatorAtaque"] + dados_fora["FatorAtaque"])/2),1)
    cartoes = round(media_liga["cartoes"] * ((dados_casa["FatorDefesa"] + dados_fora["FatorDefesa"])/2),1)
    faltas = round(media_liga["faltas"] * ((dados_casa["FatorDefesa"] + dados_fora["FatorDefesa"])/2),1)
    finalizacoes = round(media_liga["finalizacoes"] * ((dados_casa["FatorAtaque"] + dados_fora["FatorAtaque"])/2),1)
    return {
        "Escanteios":escanteios,
        "Cartões Totais":cartoes,
        "Faltas":faltas,
        "Finalizações":finalizacoes,
        "Mais 9.5 Escanteios":round(70 if escanteios>9.5 else 45,0),
        "Mais 3.5 Cartões":round(65 if cartoes>3.5 else 40,0),
        "Mais 22.5 Faltas":round(60 if faltas>22.5 else 45,0),
        "Mais 11.5 Finalizações":round(65 if finalizacoes>11.5 else 40,0)
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
            
            # Cálculo dos dados
            dados_casa = calcular_dados(casa["id"], COMPETICOES[comp])
            dados_fora = calcular_dados(fora["id"], COMPETICOES[comp])
            estimativas = calcular_estimativas(dados_casa, dados_fora, COMPETICOES[comp])

            # 1. Probabilidades Principais
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

            # 2. ESTIMATIVAS ADICIONAIS
            st.subheader("📊 Estimativas de Estatísticas do Jogo")
            df_est = pd.DataFrame({
                "Item": ["Escanteios (média estimada)","Cartões Totais","Faltas","Finalizações",
                        "Mais de 9.5 Escanteios","Mais de 3.5 Cartões","Mais de 22.5 Faltas","Mais de 11.5 Finalizações"],
                "Valor Estimado": [
                    f"{estimativas['Escanteios']}",
                    f"{estimativas['Cartões Totais']}",
                    f"{estimativas['Faltas']}",
                    f"{estimativas['Finalizações']}",
                    f"{estimativas['Mais 9.5 Escanteios']}%",
                    f"{estimativas['Mais 3.5 Cartões']}%",
                    f"{estimativas['Mais 22.5 Faltas']}%",
                    f"{estimativas['Mais 11.5 Finalizações']}%"
                ]
            })
            st.dataframe(df_est, use_container_width=True, hide_index=True)

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
            if estimativas['Mais 9.5 Escanteios'] >=60:
                sug.append("→ Mais de 9.5 Escanteios")
            if estimativas['Mais 3.5 Cartões'] >=60:
                sug.append("→ Mais de 3.5 Cartões")
            if not sug:
                sug.append("→ Jogo equilibrado, evite apostas de resultado direto")
            for s in sug: st.write(s)
                

import streamlit as st
import requests
from datetime import datetime, timedelta

# ==============================
# CONFIGURAÇÃO
# ==============================
st.set_page_config(page_title="Análise Completa | Football-Data", page_icon="⚽", layout="wide")
st.title("⚽ Análise + Dupla Chance + Últimos 5 Jogos")

API_KEY = st.secrets["CHAVE_FD"]
HEADERS = {"X-Auth-Token": API_KEY}
TEMPORADA = 2025

# ==============================
# LIGAS E MÉDIAS
# ==============================
LIGAS = {
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏆 Libertadores": "CLI",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA"
}

MEDIAS = {
    "BSA": {"esc":9.0,"car":4.3,"fal":26,"fin":10},
    "BRB": {"esc":8.8,"car":4.5,"fal":27,"fin":9},
    "CLI": {"esc":9.5,"car":3.7,"fal":23,"fin":11},
    "PL": {"esc":10.5,"car":3.8,"fal":22,"fin":12},
    "PD": {"esc":9.2,"car":4.2,"fal":24,"fin":11},
    "BL1": {"esc":9.8,"car":3.5,"fal":21,"fin":13},
    "SA": {"esc":8.7,"car":4.5,"fal":25,"fin":10}
}

# ==============================
# FUNÇÕES PRINCIPAIS
# ==============================
def buscar_jogos(sigla):
    hoje = datetime.utcnow().date()
    try:
        r = requests.get(f"https://api.football-data.org/v4/competitions/{sigla}/matches",
                        headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
        return [j for j in r.json().get("matches",[]) 
                if datetime.fromisoformat(j["utcDate"].replace("Z","")).date() <= hoje + timedelta(days=7)]
    except:
        return []

def ultimos_5_jogos(time_id, sigla):
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"competitions":sigla,"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

def calcular_principais(time_id, sigla):
    jogos = ultimos_5_jogos(time_id, sigla)
    if not jogos:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"fA":1,"fD":1,"resumo":[]}
    v=e=d=gf=gs=amb=0
    resumo = []
    for j in jogos:
        cid = j["homeTeam"]["id"]
        gc = j["score"]["fullTime"]["home"] or 0
        ga = j["score"]["fullTime"]["away"] or 0
        if cid == time_id:
            gf += gc; gs += ga
            if gc>ga: v+=1; resumo.append("✅ Vitória")
            elif gc==ga: e+=1; resumo.append("⚖️ Empate")
            else: d+=1; resumo.append("❌ Derrota")
        else:
            gf += ga; gs += gc
            if ga>gc: v+=1; resumo.append("✅ Vitória")
            elif ga==gc: e+=1; resumo.append("⚖️ Empate")
            else: d+=1; resumo.append("❌ Derrota")
        if gc>0 and ga>0: amb+=1
    t=len(jogos)
    return {
        "pV":round((v/t)*100,1), "pE":round((e/t)*100,1), "pD":round((d/t)*100,1),
        "mg":round((gf+gs)/t,2), "ma25":round(70 if (gf+gs)/t>2.5 else 45,0),
        "amb":round((amb/t)*100,0), "fA":round((gf/t)/1.5,2), "fD":round((gs/t)/1.5,2),
        "resumo":resumo
    }

def dupla_chance(pV,pE,pD):
    return {
        "1X": round(pV + pE,1),
        "X2": round(pE + pD,1),
        "12": round(pV + pD,1)
    }

def estimativas(dc,df,sigla):
    m=MEDIAS[sigla]
    return {
        "esc":round(m["esc"]*((dc["fA"]+df["fA"])/2),1),
        "car":round(m["car"]*((dc["fD"]+df["fD"])/2),1),
        "fal":round(m["fal"]*((dc["fD"]+df["fD"])/2),1),
        "fin":round(m["fin"]*((dc["fA"]+df["fA"])/2),1),
        "fal_jogador_est":round((dc["fal"]+df["fal"])/20,1),
        "fin_jogador_est":round((dc["fin"]+df["fin"])/22,1)
    }

# ==============================
# INTERFACE
# ==============================
escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
sigla = LIGAS[escolha]

jogos = buscar_jogos(sigla)
if not jogos:
    st.warning("ℹ️ Nenhum jogo agendado para os próximos 7 dias na fonte.")
else:
    st.success(f"✅ {len(jogos)} jogos encontrados!")
    for jogo in jogos:
        casa = jogo["homeTeam"]
        fora = jogo["awayTeam"]
        dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
        
        st.markdown("---")
        st.subheader(f"⚽ {casa['name']} 🆚 {fora['name']} | {dt.strftime('%d/%m %H:%M')}")

        dc = calcular_principais(casa["id"], sigla)
        df = calcular_principais(fora["id"], sigla)
        dc_dupla = dupla_chance(dc["pV"],dc["pE"],dc["pD"])
        df_dupla = dupla_chance(df["pV"],df["pE"],df["pD"])
        est = estimativas(dc,df,sigla)

        col1,col2,col3 = st.columns(3)
        with col1:
            st.subheader("📈 Resultado Final")
            st.write(f"✅ {casa['name']}: {dc['pV']}%")
            st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
            st.write(f"✅ {fora['name']}: {df['pD']}%")
            st.divider()
            st.subheader("🔀 Dupla Chance")
            st.write(f"1X (Casa/Empate): {round((dc_dupla['1X']+df_dupla['1X'])/2,1)}%")
            st.write(f"X2 (Empate/Fora): {round((dc_dupla['X2']+df_dupla['X2'])/2,1)}%")
            st.write(f"12 (Casa/Fora): {round((dc_dupla['12']+df_dupla['12'])/2,1)}%")

        with col2:
            st.subheader("📊 Últimos 5 Jogos")
            st.write(f"🟢 {casa['name']}: {' '.join(dc['resumo'])}")
            st.write(f"🔴 {fora['name']}: {' '.join(df['resumo'])}")
            st.divider()
            st.write(f"📊 Média Gols: {round((dc['mg']+df['mg'])/2,2)}")
            st.write(f"🔢 Mais 2.5: {round((dc['ma25']+df['ma25'])/2,0)}%")
            st.write(f"🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%")

        with col3:
            st.subheader("📐 Estimativas Gerais")
            st.write(f"Escanteios: {est['esc']} | Cartões: {est['car']}")
            st.write(f"Faltas: {est['fal']} | Finalizações: {est['fin']}")
            st.divider()
            st.info("ℹ️ Estimativa p/ jogador (plano grátis não tem dado individual):")
            st.write(f"→ Sofre Falta: {est['fal_jogador_est']} por jogo")
            st.write(f"→ Finaliza: {est['fin_jogador_est']} por jogo")

        if max(dc['pV'], df['pD']) >=75:
            st.error("🚨 ALTA CONFIANÇA ACIMA DE 75%!")
    

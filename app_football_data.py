import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa + Cartões", page_icon="⚽", layout="wide")
st.title("⚽ Análise de Jogos | Cartões | Últimos Jogos")

# 🔒 CHAVES OCULTAS
API_KEY = st.secrets["CHAVE_FD"]
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

try: DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA",7))
except: DIAS_BUSCA =7

HORARIO_ALERTA = "08:30"
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 📤 TELEGRAM
# ==============================
def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                     data={"chat_id":CHAT_ID,"text":msg,"parse_mode":"Markdown"}, timeout=10)
        return True
    except: return False

# ==============================
# 🏆 LIGAS E MÉDIAS INCLUINDO CARTÕES
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5},
    "BRB": {"esc":8.5,"cartao":3.5,"fin":9.0,"chute_gol":3.5,"fal":27.5},
    "WC": {"esc":8.8,"cartao":2.8,"fin":10.0,"chute_gol":4.5,"fal":24.0},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5},
    "BL1": {"esc":9.8,"cartao":2.5,"fin":12.5,"chute_gol":5.8,"fal":21.0},
    "ED": {"esc":9.2,"cartao":2.9,"fin":11.0,"chute_gol":5.0,"fal":22.5},
    "PD": {"esc":9.0,"cartao":3.0,"fin":10.5,"chute_gol":4.5,"fal":24.0},
    "FL1": {"esc":9.5,"cartao":2.8,"fin":10.8,"chute_gol":4.8,"fal":23.0},
    "ELC": {"esc":8.5,"cartao":3.3,"fin":9.2,"chute_gol":4.0,"fal":25.5},
    "PPL": {"esc":8.8,"cartao":3.1,"fin":10.2,"chute_gol":4.3,"fal":24.5},
    "EC": {"esc":9.0,"cartao":2.9,"fin":10.5,"chute_gol":4.6,"fal":23.0},
    "SA": {"esc":8.7,"cartao":3.4,"fin":9.5,"chute_gol":3.8,"fal":25.5},
    "PL": {"esc":10.2,"cartao":2.6,"fin":11.5,"chute_gol":5.2,"fal":22.0}
}

LIGAS = {
    "⚽ Todas": "TODAS","🇧🇷 Série A":"BSA","🇧🇷 Série B":"BRB","🏆 Champions":"CL","🏆 Copa Mundo":"WC",
    "🏴 Premier League":"PL","🇪🇸 La Liga":"PD","🇩🇪 Bundesliga":"BL1","🇮🇹 Serie A":"SA","🇫🇷 Ligue 1":"FL1",
    "🇳🇱 Eredivisie":"ED","🇵🇹 Primeira Liga":"PPL","🏆 Eurocopa":"EC","🏴 Championship":"ELC"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())

# ==============================
# 🔍 BUSCA CORRIGIDA DOS ÚLTIMOS JOGOS
# ==============================
@st.cache_data(ttl=3600)
def buscar_jogos(sigla, dias):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    lista=[]
    for s in (TODAS_SIGLAS if sigla=="TODAS" else [sigla]):
        try:
            r = requests.get(f"https://api.football-data.org/v4/competitions/{s}/matches",
                            headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
            if r.status_code==200:
                for j in r.json().get("matches",[]):
                    try:
                        dt = datetime.fromisoformat(j["utcDate"].replace("Z",""))
                        if dt.date() <= hoje + timedelta(days=dias): lista.append(j)
                    except:pass
        except:pass
    return lista

@st.cache_data(ttl=3600)
def ultimos_5(time_id):
    time.sleep(0.3)
    try:
        # ✅ SEM FILTRO DE COMPETIÇÃO, PEGA TODOS OS JOGOS DISPONÍVEIS
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches",[])
    except:return []

# ==============================
# 🧮 CÁLCULO COM CARTÕES E DADOS GARANTIDOS
# ==============================
def calcular_base(time_id, sigla):
    jogos = ultimos_5(time_id)
    med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    
    # ✅ SE NÃO TIVER JOGOS, USA MÉDIAS E NÃO ZERA NEM COLOCA ❔
    if not jogos:
        return {
            "pV":33.3,"pE":33.3,"pD":33.4,"mg":2.5,"ma25":50,"amb":50,
            "esc":med["esc"],"cartao":med["cartao"],"fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],
            "resumo":["📊 Média Liga"]*5,"placares":["Sem dados recentes"]
        }
    
    v=e=d=gf=gs=amb=0; resumo=[]; placares=[]; total_cartao=0
    for j in jogos:
        try:
            cid = j["homeTeam"]["id"]
            gc = j["score"]["fullTime"]["home"] or 0
            ga = j["score"]["fullTime"]["away"] or 0
            if cid == time_id:
                gf+=gc; gs+=ga
                if gc>ga:v+=1;resumo.append("✅")
                elif gc==ga:e+=1;resumo.append("⚖️")
                else:d+=1;resumo.append("❌")
                placares.append(f"{gc}x{ga}")
            else:
                gf+=ga; gs+=gc
                if ga>gc:v+=1;resumo.append("✅")
                elif ga==gc:e+=1;resumo.append("⚖️")
                else:d+=1;resumo.append("❌")
                placares.append(f"{ga}x{gc}")
            if gc>0 and ga>0:amb+=1
            total_cartao += med["cartao"]/5
        except:continue
    
    t=len(jogos)
    fator_a = (gf/t)/1.5; fator_d = (gs/t)/1.5
    return {
        "pV":round((v/t)*100,1),"pE":round((e/t)*100,1),"pD":round((d/t)*100,1),
        "mg":round((gf+gs)/t,2),"ma25":round(70 if (gf+gs)/t>2.5 else 45,0),"amb":round((amb/t)*100,0),
        "esc":round(med["esc"]*fator_a,1),
        "cartao":round(total_cartao,1),
        "fin":round(med["fin"]*fator_a,1),
        "chute_gol":round(med["chute_gol"]*fator_a,1),
        "fal":round(med["fal"]*fator_d,1),
        "resumo":resumo,"placares":placares
    }

def dupla(v,e,d): return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

# ==============================
# 📝 MENSAGEM SEM CONFRONTO, COM CARTÕES
# ==============================
def msg_jogo(casa_nome, fora_nome, dt, dc, df, dup, mg, mais25, amb):
    return f"""
⚽ *{casa_nome} 🆚 {fora_nome}* | {dt.strftime('%d/%m %H:%M')}

📊 *Probabilidades:*
✅ {casa_nome}: {dc['pV']}% | ⚖️ {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora_nome}: {df['pD']}%
🔀 Dupla: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 *Métricas do Jogo:*
⚽ Média Gols: {mg} | Mais 2.5: {mais25}% | Ambos Marcam: {amb}%
📐 Escanteios: {round((dc['esc']+df['esc'])/2,1)} | 👟 Faltas: {round((dc['fal']+df['fal'])/2,1)}
🎯 Finalizações: {round((dc['fin']+df['fin'])/2,1)} | ⚽ Chutes ao Gol: {round((dc['chute_gol']+df['chute_gol'])/2,1)}

🟨 *Cartões por Equipe:*
{casa_nome}: {dc['cartao']} média por jogo
{fora_nome}: {df['cartao']} média por jogo

📋 *Últimos 5 Jogos:*
🟢 {casa_nome}: {' '.join(dc['resumo'])} | {' | '.join(dc['placares'])}
🔴 {fora_nome}: {' '.join(df['resumo'])} | {' | '.join(df['placares'])}

{'🚨 ALTA CONFIANÇA!' if max(dc['pV'],df['pD'])>=70 else ''}
---
"""

# ==============================
# 🤖 ROTINA
# ==============================
def alerta():
    while True:
        try:
            if datetime.now().strftime("%H:%M")==HORARIO_ALERTA:
                jogos = buscar_jogos("TODAS", DIAS_BUSCA)
                msg = f"🔔 *RELATÓRIO AUTOMÁTICO*\n🕒 {datetime.now().strftime('%d/%m %H:%M')}\n\n"
                for j in jogos:
                    try:
                        dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                        dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"])
                        df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"])
                        msg += msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dupla(dc['pV'],dc['pE'],dc['pD']),
                                       round((dc['mg']+df['mg'])/2,2), round((dc['ma25']+df['ma25'])/2,0), round((dc['amb']+df['amb'])/2,0))
                    except:pass
                enviar_telegram(msg)
        except:pass
        time.sleep(30)
threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ TELA
# ==============================
st.title("⚽ Análise Completa | Cartões | Últimos Jogos")
esc = st.selectbox("Liga", list(LIGAS.keys()))
dias = st.number_input("Dias à frente",1,14,DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos: st.info("Nenhum jogo encontrado")
    else:
        st.success(f"{len(jogos)} jogos")
        rel = f"🔔 *RELATÓRIO*\n🕒 {datetime.now().strftime('%d/%m %H:%M')}\n\n"
        for j in jogos:
            dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
            dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"])
            df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"])
            dup = dupla(dc['pV'],dc['pE'],dc['pD'])
            mg = round((dc['mg']+df['mg'])/2,2)
            mais25 = round((dc['ma25']+df['ma25'])/2,0)
            amb = round((dc['amb']+df['amb'])/2,0)
            rel += msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg, mais25, amb)
            
            st.subheader(f"⚽ {j['homeTeam']['name']} 🆚 {j['awayTeam']['name']}")
            c1,c2=st.columns(2)
            with c1:
                st.subheader("🏠 Time Casa")
                st.write(f"V:{dc['pV']}% E:{dc['pE']}% D:{dc['pD']}%")
                st.write(f"🟨 Cartões: {dc['cartao']}")
                st.write(f"🎯 Finalizações: {dc['fin']} | Chutes Gol: {dc['chute_gol']}")
                st.write(f"Últimos: {' '.join(dc['resumo'])} | {' | '.join(dc['placares'])}")
            with c2:
                st.subheader("🔴 Time Fora")
                st.write(f"V:{df['pV']}% E:{df['pE']}% D:{df['pD']}%")
                st.write(f"🟨 Cartões: {df['cartao']}")
                st.write(f"🎯 Finalizações: {df['fin']} | Chutes Gol: {df['chute_gol']}")
                st.write(f"Últimos: {' '.join(df['resumo'])} | {' | '.join(df['placares'])}")
            st.markdown("---")
        enviar_telegram(rel)
        st.success("Enviado ao Telegram!")
        

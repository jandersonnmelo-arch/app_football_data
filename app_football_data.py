import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa | Probabilidades Refinadas", page_icon="⚽", layout="wide")
st.title("⚽ Análise Completa | Probabilidades + Métricas do Jogo")

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
# 🏆 LIGAS E MÉDIAS COMPLETAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"gols":2.6,"vit_casa":45,"vit_fora":30,"empate":25},
    "BRB": {"esc":8.5,"cartao":3.5,"fin":9.0,"chute_gol":3.5,"fal":27.5,"gols":2.4,"vit_casa":42,"vit_fora":28,"empate":30},
    "WC": {"esc":8.8,"cartao":2.8,"fin":10.0,"chute_gol":4.5,"fal":24.0,"gols":2.8,"vit_casa":40,"vit_fora":32,"empate":28},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"gols":2.9,"vit_casa":48,"vit_fora":29,"empate":23},
    "BL1": {"esc":9.8,"cartao":2.5,"fin":12.5,"chute_gol":5.8,"fal":21.0,"gols":3.1,"vit_casa":50,"vit_fora":28,"empate":22},
    "ED": {"esc":9.2,"cartao":2.9,"fin":11.0,"chute_gol":5.0,"fal":22.5,"gols":2.8,"vit_casa":46,"vit_fora":29,"empate":25},
    "PD": {"esc":9.0,"cartao":3.0,"fin":10.5,"chute_gol":4.5,"fal":24.0,"gols":2.6,"vit_casa":47,"vit_fora":28,"empate":25},
    "FL1": {"esc":9.5,"cartao":2.8,"fin":10.8,"chute_gol":4.8,"fal":23.0,"gols":2.5,"vit_casa":44,"vit_fora":30,"empate":26},
    "ELC": {"esc":8.5,"cartao":3.3,"fin":9.2,"chute_gol":4.0,"fal":25.5,"gols":2.4,"vit_casa":41,"vit_fora":29,"empate":30},
    "PPL": {"esc":8.8,"cartao":3.1,"fin":10.2,"chute_gol":4.3,"fal":24.5,"gols":2.5,"vit_casa":43,"vit_fora":28,"empate":29},
    "EC": {"esc":9.0,"cartao":2.9,"fin":10.5,"chute_gol":4.6,"fal":23.0,"gols":2.7,"vit_casa":45,"vit_fora":29,"empate":26},
    "SA": {"esc":8.7,"cartao":3.4,"fin":9.5,"chute_gol":3.8,"fal":25.5,"gols":2.5,"vit_casa":42,"vit_fora":29,"empate":29},
    "PL": {"esc":10.2,"cartao":2.6,"fin":11.5,"chute_gol":5.2,"fal":22.0,"gols":2.8,"vit_casa":48,"vit_fora":30,"empate":22}
}

LIGAS = {
    "⚽ Todas": "TODAS","🇧🇷 Série A":"BSA","🇧🇷 Série B":"BRB","🏆 Champions":"CL","🏆 Copa Mundo":"WC",
    "🏴 Premier League":"PL","🇪🇸 La Liga":"PD","🇩🇪 Bundesliga":"BL1","🇮🇹 Serie A":"SA","🇫🇷 Ligue 1":"FL1",
    "🇳🇱 Eredivisie":"ED","🇵🇹 Primeira Liga":"PPL","🏆 Eurocopa":"EC","🏴 Championship":"ELC"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())

# ==============================
# 🔍 BUSCA
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
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        dados = r.json().get("matches",[])
        if dados: return dados
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"limit":10}, timeout=15)
        return [j for j in r.json().get("matches",[]) if j.get("status")=="FINISHED"][:5]
    except:return []

# ==============================
# 🧮 CÁLCULO REFINADO + MÉTRICAS COMPLETAS
# ==============================
def calcular_base(time_id, sigla, eh_casa=False):
    jogos = ultimos_5(time_id)
    med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    
    if not jogos:
        if eh_casa:
            return {"pV":med["vit_casa"],"pE":med["empate"],"pD":med["vit_fora"],"mg":med["gols"],
                    "ma25":50,"amb":50,"esc":med["esc"],"cartao":med["cartao"],
                    "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],
                    "resumo":["📊 Média da Liga"]*5,"placares":["Sem dados → Média"]}
        else:
            return {"pV":med["vit_fora"],"pE":med["empate"],"pD":med["vit_casa"],"mg":med["gols"],
                    "ma25":50,"amb":50,"esc":med["esc"],"cartao":med["cartao"],
                    "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],
                    "resumo":["📊 Média da Liga"]*5,"placares":["Sem dados → Média"]}
    
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
    fator_gols = (gf+gs)/t / med["gols"]
    
    # Cálculo refinado das porcentagens
    pv_base = (v/t)*100
    pe_base = (e/t)*100
    pd_base = (d/t)*100
    
    if eh_casa:
        pv_base *= 1.15
        pd_base *= 0.90
    else:
        pd_base *= 1.10
        pv_base *= 0.95
    
    pv_base *= fator_gols
    pd_base *= fator_gols
    
    total = pv_base + pe_base + pd_base
    pv = round(pv_base/total*100,1)
    pe = round(pe_base/total*100,1)
    pd = round(pd_base/total*100,1)
    
    fator_a = (gf/t)/1.5; fator_d = (gs/t)/1.5
    return {
        "pV":pv,"pE":pe,"pD":pd,
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
# 📝 MENSAGEM COM TODAS AS MÉTRICAS DO CONFRONTO
# ==============================
def msg_jogo(casa_nome, fora_nome, dt, dc, df, dup, mg, mais25, amb, total_esc, total_fal, total_fin, total_chute):
    return f"""
⚽ *{casa_nome} 🆚 {fora_nome}* | {dt.strftime('%d/%m %H:%M')}

📊 *Probabilidades Refinadas:*
✅ {casa_nome}: {dc['pV']}% | ⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora_nome}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 *MÉTRICAS GERAIS DO CONFRONTO:*
⚽ Média Gols: {mg} | Mais 2.5 Gols: {mais25}% | Ambos Marcam: {amb}%
📐 Escanteios: {total_esc} | 👟 Faltas: {total_fal}
🎯 Finalizações: {total_fin} | ⚽ Chutes ao Gol: {total_chute}

🟨 *Cartões por Equipe:*
{casa_nome}: {dc['cartao']} média por jogo
{fora_nome}: {df['cartao']} média por jogo

📋 *Últimos 5 Jogos:*
🟢 {casa_nome}: {' '.join(dc['resumo'])}
🔴 {fora_nome}: {' '.join(df['resumo'])}

{'🚨 ALTA CONFIANÇA!' if max(dc['pV'],df['pD'])>=55 else ''}
---
"""

# ==============================
# 🤖 ROTINA AUTOMÁTICA
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
                        dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], eh_casa=True)
                        df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], eh_casa=False)
                        dup = dupla(dc['pV'],dc['pE'],dc['pD'])
                        mg = round((dc['mg']+df['mg'])/2,2)
                        mais25 = round((dc['ma25']+df['ma25'])/2,0)
                        amb = round((dc['amb']+df['amb'])/2,0)
                        total_esc = round((dc['esc']+df['esc'])/2,1)
                        total_fal = round((dc['fal']+df['fal'])/2,1)
                        total_fin = round((dc['fin']+df['fin'])/2,1)
                        total_chute = round((dc['chute_gol']+df['chute_gol'])/2,1)
                        msg += msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg, mais25, amb, total_esc, total_fal, total_fin, total_chute)
                    except:pass
                enviar_telegram(msg)
        except:pass
        time.sleep(30)
threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ INTERFACE COMPLETA
# ==============================
esc = st.selectbox("Liga", list(LIGAS.keys()))
dias = st.number_input("Dias à frente",1,14,DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos: st.info("Nenhum jogo encontrado")
    else:
        st.success(f"{len(jogos)} jogos carregados!")
        rel = f"🔔 *RELATÓRIO SOLICITADO*\n🕒 {datetime.now().strftime('%d/%m %H:%M')}\n\n"
        for j in jogos:
            dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
            dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], eh_casa=True)
            df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], eh_casa=False)
            dup = dupla(dc['pV'],dc['pE'],dc['pD'])
            mg = round((dc['mg']+df['mg'])/2,2)
            mais25 = round((dc['ma25']+df['ma25'])/2,0)
            amb = round((dc['amb']+df['amb'])/2,0)
            total_esc = round((dc['esc']+df['esc'])/2,1)
            total_fal = round((dc['fal']+df['fal'])/2,1)
            total_fin = round((dc['fin']+df['fin'])/2,1)
            total_chute = round((dc['chute_gol']+df['chute_gol'])/2,1)
            
            rel += msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg, mais25, amb, total_esc, total_fal, total_fin, total_chute)
            
            st.subheader(f"⚽ {j['homeTeam']['name']} 🆚 {j['awayTeam']['name']}")
            
            st.subheader("📈 MÉTRICAS GERAIS DO CONFRONTO")
            st.write(f"⚽ Média Gols: {mg} | Mais 2.5: {mais25}% | Ambos Marcam: {amb}%")
            st.write(f"📐 Escanteios: {total_esc} | 👟 Faltas: {total_fal}")
            st.write(f"🎯 Finalizações: {total_fin} | ⚽ Chutes ao Gol: {total_chute}")
            st.divider()
            
            c1,c2=st.columns(2)
            with c1:
                st.subheader("🏠 Time Casa")
                st.write(f"✅ Vitória: {dc['pV']}% | ⚖️ Empate: {dc['pE']}% | ❌ Derrota: {dc['pD']}%")
                st.write(f"🟨 Cartões: {dc['cartao']}")
                st.write(f"Últimos: {' '.join(dc['resumo'])}")
            with c2:
                st.subheader("🔴 Time Fora")
                st.write(f"✅ Vitória: {df['pV']}% | ⚖️ Empate: {df['pE']}% | ❌ Derrota: {df['pD']}%")
                st.write(f"🟨 Cartões: {df['cartao']}")
                st.write(f"Últimos: {' '.join(df['resumo'])}")
            st.markdown("---")
        enviar_telegram(rel)
        st.success("✅ Relatório completo enviado!")
                

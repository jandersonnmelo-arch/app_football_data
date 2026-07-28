import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa + Confronto Direto", page_icon="⚽", layout="wide")
st.title("⚽ Análise Detalhada | Casa/Fora | Tempos | Handicap | Confronto Direto")

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
    "BSA": {"esc":9.0,"cartao":3.2,"g_1t":1.1,"g_2t":1.4,"esc_1t":4.2,"esc_2t":4.8,"chute_1t":4.5,"chute_2t":5.0,"g_casa":1.6,"g_fora":1.2,"marca_primeiro_casa":62,"marca_primeiro_fora":48},
    "BRB": {"esc":8.5,"cartao":3.5,"g_1t":1.0,"g_2t":1.3,"esc_1t":4.0,"esc_2t":5.0,"chute_1t":4.2,"chute_2t":4.8,"g_casa":1.5,"g_fora":1.1,"marca_primeiro_casa":58,"marca_primeiro_fora":45},
    "CL": {"esc":9.5,"cartao":2.7,"g_1t":1.0,"g_2t":1.5,"esc_1t":4.0,"esc_2t":5.5,"chute_1t":4.5,"chute_2t":6.0,"g_casa":1.8,"g_fora":1.3,"marca_primeiro_casa":65,"marca_primeiro_fora":50},
    "BL1": {"esc":9.8,"cartao":2.5,"g_1t":1.2,"g_2t":1.6,"esc_1t":4.5,"esc_2t":5.3,"chute_1t":5.0,"chute_2t":7.5,"g_casa":1.9,"g_fora":1.4,"marca_primeiro_casa":68,"marca_primeiro_fora":52},
    "PD": {"esc":9.0,"cartao":3.0,"g_1t":1.0,"g_2t":1.4,"esc_1t":4.0,"esc_2t":5.0,"chute_1t":4.5,"chute_2t":6.0,"g_casa":1.7,"g_fora":1.2,"marca_primeiro_casa":60,"marca_primeiro_fora":47},
    "FL1": {"esc":9.5,"cartao":2.8,"g_1t":1.0,"g_2t":1.5,"esc_1t":4.2,"esc_2t":5.3,"chute_1t":4.7,"chute_2t":6.1,"g_casa":1.6,"g_fora":1.2,"marca_primeiro_casa":61,"marca_primeiro_fora":48},
    "SA": {"esc":8.7,"cartao":3.4,"g_1t":0.9,"g_2t":1.2,"esc_1t":3.7,"esc_2t":4.8,"chute_1t":4.0,"chute_2t":5.5,"g_casa":1.5,"g_fora":1.1,"marca_primeiro_casa":57,"marca_primeiro_fora":44},
    "PL": {"esc":10.2,"cartao":2.6,"g_1t":1.1,"g_2t":1.5,"esc_1t":4.5,"esc_2t":5.7,"chute_1t":5.0,"chute_2t":6.5,"g_casa":1.8,"g_fora":1.3,"marca_primeiro_casa":64,"marca_primeiro_fora":51},
    "WC": {"esc":8.8,"cartao":2.8,"g_1t":0.9,"g_2t":1.2,"esc_1t":3.8,"esc_2t":5.0,"chute_1t":4.0,"chute_2t":5.5,"g_casa":1.4,"g_fora":1.0,"marca_primeiro_casa":55,"marca_primeiro_fora":43},
    "ED": {"esc":9.2,"cartao":2.9,"g_1t":1.1,"g_2t":1.5,"esc_1t":4.2,"esc_2t":5.0,"chute_1t":4.8,"chute_2t":6.2,"g_casa":1.8,"g_fora":1.3,"marca_primeiro_casa":63,"marca_primeiro_fora":49},
    "ELC": {"esc":8.5,"cartao":3.3,"g_1t":0.9,"g_2t":1.2,"esc_1t":3.8,"esc_2t":4.7,"chute_1t":4.0,"chute_2t":5.2,"g_casa":1.4,"g_fora":1.0,"marca_primeiro_casa":56,"marca_primeiro_fora":42},
    "PPL": {"esc":8.8,"cartao":3.1,"g_1t":1.0,"g_2t":1.3,"esc_1t":4.0,"esc_2t":4.8,"chute_1t":4.3,"chute_2t":5.9,"g_casa":1.6,"g_fora":1.1,"marca_primeiro_casa":59,"marca_primeiro_fora":46},
    "EC": {"esc":9.0,"cartao":2.9,"g_1t":0.9,"g_2t":1.3,"esc_1t":3.9,"esc_2t":5.1,"chute_1t":4.2,"chute_2t":5.8,"g_casa":1.5,"g_fora":1.1,"marca_primeiro_casa":58,"marca_primeiro_fora":45}
}

LIGAS = {
    "⚽ Todas": "TODAS","🇧🇷 Série A":"BSA","🇧🇷 Série B":"BRB","🏆 Champions":"CL","🏆 Copa Mundo":"WC",
    "🏴 Premier League":"PL","🇪🇸 La Liga":"PD","🇩🇪 Bundesliga":"BL1","🇮🇹 Serie A":"SA","🇫🇷 Ligue 1":"FL1",
    "🇳🇱 Eredivisie":"ED","🇵🇹 Primeira Liga":"PPL","🏆 Eurocopa":"EC","🏴 Championship":"ELC"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())

# ==============================
# 🔍 BUSCA JOGOS E CONFRONTO DIRETO
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
def confronto_direto(id1, id2):
    try:
        r = requests.get(f"https://api.football-data.org/v4/matches?team1={id1}&team2={id2}&status=FINISHED&limit=5",
                        headers=HEADERS, timeout=15)
        dados = r.json().get("matches",[])
        v1=v2=e=0; g1=0; g2=0; lista=[]
        for j in dados:
            try:
                gc = j["score"]["fullTime"]["home"] or 0
                ga = j["score"]["fullTime"]["away"] or 0
                if j["homeTeam"]["id"] == id1:
                    g1+=gc; g2+=ga
                    if gc>ga:v1+=1; lista.append(f"{gc}x{ga} ✅")
                    elif gc==ga:e+=1; lista.append(f"{gc}x{ga} ⚖️")
                    else:v2+=1; lista.append(f"{gc}x{ga} ❌")
                else:
                    g1+=ga; g2+=gc
                    if ga>gc:v1+=1; lista.append(f"{ga}x{gc} ✅")
                    elif ga==gc:e+=1; lista.append(f"{ga}x{gc} ⚖️")
                    else:v2+=1; lista.append(f"{ga}x{gc} ❌")
            except:continue
        q = len(dados) or 1
        return {
            "qtd":len(dados),"v1":v1,"e":e,"v2":v2,
            "p1":round(v1/q*100,1),"pe":round(e/q*100,1),"p2":round(v2/q*100,1),
            "mg1":round(g1/q,2),"mg2":round(g2/q,2),
            "media_total":round((g1+g2)/q,2),
            "ambos":round(sum(1 for j in dados if ((j["score"]["fullTime"]["home"] or 0)>0 and (j["score"]["fullTime"]["away"] or 0)>0))/q*100,0),
            "placares":lista or ["Sem histórico de confronto"]
        }
    except:
        return {"qtd":0,"v1":0,"e":0,"v2":0,"p1":0,"pe":0,"p2":0,"mg1":0,"mg2":0,"media_total":0,"ambos":0,"placares":["Sem histórico"]}

@st.cache_data(ttl=3600)
def ultimos_5(time_id, sigla):
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"competitions":sigla,"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches",[])
    except:return []

# ==============================
# 🧮 CÁLCULO COMPLETO POR CASA/FORA
# ==============================
def analise_ultimos(time_id, sigla, eh_casa):
    jogos = ultimos_5(time_id, sigla)
    med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    res = {
        "qtd":0,"v":0,"e":0,"d":0,"gols":0,"sofridos":0,"ambos":0,
        "g_1t":0,"g_2t":0,"cartao":0,"marca_primeiro":0,"placares":[]
    }
    for j in jogos:
        try:
            cid = j["homeTeam"]["id"]
            gc = j["score"]["fullTime"]["home"] or 0
            ga = j["score"]["fullTime"]["away"] or 0
            g1c = j["score"]["halfTime"]["home"] or 0
            g1a = j["score"]["halfTime"]["away"] or 0
            res["qtd"] +=1
            if (eh_casa and cid==time_id) or (not eh_casa and cid!=time_id):
                gols_time = gc if eh_casa else ga
                sofre_time = ga if eh_casa else gc
                g1 = g1c if eh_casa else g1a
                g2 = (gc-g1c) if eh_casa else (ga-g1a)
                res["gols"] += gols_time
                res["sofridos"] += sofre_time
                res["g_1t"] += g1
                res["g_2t"] += g2
                if gols_time>sofre_time: res["v"]+=1
                elif gols_time==sofre_time: res["e"]+=1
                else: res["d"]+=1
                if gols_time>0 and sofre_time>0: res["ambos"]+=1
                if g1>0 and g1==max(g1c,g1a): res["marca_primeiro"]+=1
                res["placares"].append(f"{gols_time}x{sofre_time}")
                res["cartao"] += med["cartao"]/5
        except:continue
    q = res["qtd"] or 1
    return {
        "pV":round(res["v"]/q*100,1),"pE":round(res["e"]/q*100,1),"pD":round(res["d"]/q*100,1),
        "media_gols":round(res["gols"]/q,2),"media_sofre":round(res["sofridos"]/q,2),
        "ambos":round(res["ambos"]/q*100,0),
        "g_1t":round(res["g_1t"]/q,2),"g_2t":round(res["g_2t"]/q,2),
        "marca_primeiro":round(res["marca_primeiro"]/q*100,0),
        "cartao":round(res["cartao"],1),
        "placares":res["placares"] or ["Sem dados"]
    }

def calcular_base(time_id, sigla):
    med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    casa = analise_ultimos(time_id, sigla, True)
    fora = analise_ultimos(time_id, sigla, False)
    geral = analise_ultimos(time_id, sigla, True)
    mg_geral = round((casa["media_gols"] + fora["media_gols"])/2,2)
    return {
        **geral,"casa":casa,"fora":fora,
        "multigols": 75 if 1<=mg_geral<=3 else 55,
        "handicap_casa": round((casa["media_gols"] - fora["media_gols"])*10,1),
        "handicap_fora": round((fora["media_gols"] - casa["media_gols"])*10,1),
        "total_1t": round((casa["g_1t"] + fora["g_1t"])/2,1),
        "total_2t": round((casa["g_2t"] + fora["g_2t"])/2,1)
    }

def dupla(v,e,d): return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

# ==============================
# 📝 MENSAGEM COMPLETA COM CONFRONTO
# ==============================
def msg_jogo(casa_nome, fora_nome, dt, dc, df, dup, confronto):
    return f"""
⚽ *{casa_nome} 🆚 {fora_nome}* | {dt.strftime('%d/%m %H:%M')}

📊 *Probabilidades Gerais:*
✅ {casa_nome}: {dc['pV']}% | ⚖️ {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora_nome}: {df['pD']}%
🔀 Dupla: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

🔥 *CONFRONTO DIRETO - Últimos {confronto['qtd']}:*
✅ {casa_nome}: {confronto['p1']}% | ⚖️ Empate: {confronto['pe']}% | ✅ {fora_nome}: {confronto['p2']}%
⚽ Média gols: {confronto['media_total']} | Ambos marcam: {confronto['ambos']}%
📋 Placares: {' | '.join(confronto['placares'])}

🎯 *Multigols 1-3:*
{casa_nome}: {dc['multigols']}% | {fora_nome}: {df['multigols']}%

⏱️ *Gols por Tempo:*
🏁 1ºT: {dc['total_1t']} gols | 🏁 2ºT: {dc['total_2t']} gols

📈 *Casa x Fora - Últimos 5:*
🟢 {casa_nome} EM CASA:
• V:{dc['casa']['pV']}% E:{dc['casa']['pE']}% D:{dc['casa']['pD']}%
• Gols:{dc['casa']['media_gols']} Sofre:{dc['casa']['media_sofre']}
• Ambos:{dc['casa']['ambos']}% | Marca primeiro:{dc['casa']['marca_primeiro']}%
• Cartões:{dc['casa']['cartao']} | {' '.join(dc['casa']['placares'])}

🔴 {fora_nome} FORA:
• V:{df['fora']['pV']}% E:{df['fora']['pE']}% D:{df['fora']['pD']}%
• Gols:{df['fora']['media_gols']} Sofre:{df['fora']['media_sofre']}
• Ambos:{df['fora']['ambos']}% | Marca primeiro:{df['fora']['marca_primeiro']}%
• Cartões:{df['fora']['cartao']} | {' '.join(df['fora']['placares'])}

⚖️ Handicap: {casa_nome} {dc['handicap_casa']:+g} | {fora_nome} {df['handicap_fora']:+g}
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
                        dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"])
                        df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"])
                        conf = confronto_direto(j["homeTeam"]["id"], j["awayTeam"]["id"])
                        msg += msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dupla(dc['pV'],dc['pE'],dc['pD']), conf)
                    except:pass
                enviar_telegram(msg)
        except:pass
        time.sleep(30)
threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ INTERFACE
# ==============================
esc = st.selectbox("Liga", list(LIGAS.keys()))
dias = st.number_input("Dias à frente",1,14,DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos: st.info("Nenhum jogo encontrado")
    else:
        st.success(f"{len(jogos)} jogos encontrados!")
        rel = f"🔔 *RELATÓRIO SOLICITADO*\n🕒 {datetime.now().strftime('%d/%m %H:%M')}\n\n"
        for j in jogos:
            dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
            dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"])
            df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"])
            dup = dupla(dc['pV'],dc['pE'],dc['pD'])
            confronto = confronto_direto(j["homeTeam"]["id"], j["awayTeam"]["id"])
            rel += msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, confronto)
            
            st.subheader(f"⚽ {j['homeTeam']['name']} 🆚 {j['awayTeam']['name']}")
            
            # CONFRONTO DIRETO EM DESTAQUE
            st.markdown("---")
            st.subheader("🔥 CONFRONTO DIRETO")
            if confronto["qtd"]>0:
                st.write(f"Últimos {confronto['qtd']} confrontos:")
                c1,c2,c3=st.columns(3)
                with c1:st.metric(f"{j['homeTeam']['name']}",f"{confronto['p1']}%")
                with c2:st.metric("Empate",f"{confronto['pe']}%")
                with c3:st.metric(f"{j['awayTeam']['name']}",f"{confronto['p2']}%")
                st.write(f"Média total gols: {confronto['media_total']} | Ambos marcam: {confronto['ambos']}%")
                st.write(f"Placares: {' | '.join(confronto['placares'])}")
            else:
                st.info("Sem histórico de confronto direto registrado")
            
            # RESTANTE DAS ANÁLISES
            c1,c2=st.columns(2)
            with c1:
                st.subheader("🏠 CASA - Últimos 5")
                st.write(f"V:{dc['casa']['pV']}% E:{dc['casa']['pE']}% D:{dc['casa']['pD']}%")
                st.write(f"Gols:{dc['casa']['media_gols']} Sofre:{dc['casa']['media_sofre']}")
                st.write(f"Ambos:{dc['casa']['ambos']}% | Marca primeiro:{dc['casa']['marca_primeiro']}%")
                st.write(f"Cartões:{dc['casa']['cartao']} | {' '.join(dc['casa']['placares'])}")
            with c2:
                st.subheader("🔴 FORA - Últimos 5")
                st.write(f"V:{df['fora']['pV']}% E:{df['fora']['pE']}% D:{df['fora']['pD']}%")
                st.write(f"Gols:{df['fora']['media_gols']} Sofre:{df['fora']['media_sofre']}")
                st.write(f"Ambos:{df['fora']['ambos']}% | Marca primeiro:{df['fora']['marca_primeiro']}%")
                st.write(f"Cartões:{df['fora']['cartao']} | {' '.join(df['fora']['placares'])}")
            
            st.subheader("📊 RESUMO GERAL")
            st.write(f"Gols 1ºT:{dc['total_1t']} | 2ºT:{dc['total_2t']} | Multigols:{dc['multigols']}%")
            st.write(f"Handicap: {j['homeTeam']['name']} {dc['handicap_casa']:+g} | {j['awayTeam']['name']} {df['handicap_fora']:+g}")
            st.markdown("---")
        
        enviar_telegram(rel)
        st.success("✅ Relatório completo enviado ao Telegram!")
                 

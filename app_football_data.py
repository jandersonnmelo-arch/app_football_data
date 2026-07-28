import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa", page_icon="⚽", layout="wide")
st.title("⚽ Análise de Jogos + Envio Telegram")

# 🔒 CHAVES OCULTAS
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves! Erro: {e}")
    st.stop()

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

# ⏰ ALERTA ÀS 07:00 MANAUS
HORARIO_ALERTA = "07:00"
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 📤 FUNÇÃO ENVIO TELEGRAM
# ==============================
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": str(CHAT_ID),
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        r = requests.post(url, data=payload, timeout=20)
        return (True, "✅ Enviado") if r.status_code == 200 else (False, f"❌ Erro {r.status_code}")
    except Exception as e:
        return False, f"❌ Falha: {str(e)}"

# ==============================
# 🏆 MÉDIAS DAS LIGAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
            "vit_casa":45,"vit_fora":30,"empate":25,
            "mais15":75,"menos15":25,"mais25":55,"menos25":45,"menos35":82},
    "BRB": {"esc":8.5,"cartao":3.5,"fin":9.0,"chute_gol":3.5,"fal":27.5,"defesa_gk":4.5,"gols":2.4,
            "vit_casa":42,"vit_fora":28,"empate":30,
            "mais15":72,"menos15":28,"mais25":52,"menos25":48,"menos35":85},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "vit_casa":48,"vit_fora":29,"empate":23,
           "mais15":80,"menos15":20,"mais25":62,"menos25":38,"menos35":75},
    "PL": {"esc":10.2,"cartao":2.6,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa_gk":3.4,"gols":2.8,
           "vit_casa":48,"vit_fora":30,"empate":22,
           "mais15":82,"menos15":18,"mais25":64,"menos25":36,"menos35":76}
}

LIGAS = {"⚽ Todas":"TODAS","🇧🇷 Série A":"BSA","🇧🇷 Série B":"BRB","🏆 Champions":"CL","🏴 Premier League":"PL"}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())

# ==============================
# 🔍 BUSCA DE DADOS
# ==============================
@st.cache_data(ttl=3600)
def buscar_jogos(sigla, dias):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    lista = []
    for s in (TODAS_SIGLAS if sigla == "TODAS" else [sigla]):
        try:
            r = requests.get(f"https://api.football-data.org/v4/competitions/{s}/matches",
                            headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("matches", []):
                    try:
                        dt = datetime.fromisoformat(j["utcDate"].replace("Z",""))
                        if dt.date() <= hoje + timedelta(days=dias):
                            lista.append(j)
                    except: pass
        except: pass
    return lista

@st.cache_data(ttl=3600)
def ultimos_5(time_id):
    time.sleep(0.3)
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        dados = r.json().get("matches", [])
        return dados if dados else []
    except: return []

# ==============================
# 🧮 CÁLCULO
# ==============================
def calcular_base(time_id, sigla, eh_casa=False):
    try:
        jogos = ultimos_5(time_id)
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        
        if not jogos:
            return {
                "pV":med["vit_casa"] if eh_casa else med["vit_fora"],
                "pE":med["empate"],
                "pD":med["vit_fora"] if eh_casa else med["vit_casa"],
                "mg":med["gols"],
                "mais15":med["mais15"],"menos15":med["menos15"],
                "mais25":med["mais25"],"menos25":med["menos25"],
                "menos35":med["menos35"],
                "amb":50,"esc":med["esc"],"cartao":med["cartao"],
                "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],"defesa_gk":med["defesa_gk"],
                "resumo":["📊 Média da Liga"]*5,"placares":["Sem dados"]
            }
        
        v = e = d = gf = gs = amb = 0
        resumo = []
        placares = []
        for j in jogos:
            try:
                cid = j["homeTeam"]["id"]
                gc = j["score"]["fullTime"].get("home",0) or 0
                ga = j["score"]["fullTime"].get("away",0) or 0
                if cid == time_id:
                    gf += gc; gs += ga
                    if gc>ga: v+=1; resumo.append("✅")
                    elif gc==ga: e+=1; resumo.append("⚖️")
                    else: d+=1; resumo.append("❌")
                    placares.append(f"{gc}x{ga}")
                else:
                    gf += ga; gs += gc
                    if ga>gc: v+=1; resumo.append("✅")
                    elif ga==gc: e+=1; resumo.append("⚖️")
                    else: d+=1; resumo.append("❌")
                    placares.append(f"{ga}x{gc}")
                if gc>0 and ga>0: amb+=1
            except: pass
        
        t = len(jogos)
        media_gols = (gf+gs)/t
        fator = media_gols/med["gols"] if med["gols"]>0 else 1
        
        pv = round((v/t)*100 * (1.15 if eh_casa else 0.95) * fator,1)
        pe = round((e/t)*100,1)
        pd = round((d/t)*100 * (1.10 if not eh_casa else 0.90) * fator,1)
        total = pv+pe+pd
        if total>0: pv,pe,pd = round(pv/total*100,1), round(pe/total*100,1), round(pd/total*100,1)
        
        return {
            "pV":pv,"pE":pe,"pD":pd,
            "mg":round(media_gols,1),
            "mais15":round(med["mais15"]*fator,0),"menos15":round(100-med["mais15"]*fator,0),
            "mais25":round(med["mais25"]*fator,0),"menos25":round(100-med["mais25"]*fator,0),
            "menos35":round(med["menos35"]/fator if fator>0 else med["menos35"],0),
            "amb":round((amb/t)*100,0),
            "esc":round(med["esc"]*fator,1),
            "cartao":round(med["cartao"],1),
            "fin":round(med["fin"]*fator,1),
            "chute_gol":round(med["chute_gol"]*fator,1),
            "fal":round(med["fal"]*fator,1),
            "defesa_gk":round(med["defesa_gk"]/fator if fator>0 else med["defesa_gk"],1),
            "resumo":resumo,"placares":placares
        }
    except:
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        return {"pV":med["vit_casa"] if eh_casa else med["vit_fora"],"pE":med["empate"],"pD":med["vit_fora"] if eh_casa else med["vit_casa"],
                "mg":med["gols"],"mais15":med["mais15"],"menos15":med["menos15"],
                "mais25":med["mais25"],"menos25":med["menos25"],"menos35":med["menos35"],
                "amb":50,"esc":med["esc"],"cartao":med["cartao"],
                "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],"defesa_gk":med["defesa_gk"],
                "resumo":["📊 Média da Liga"]*5,"placares":["Erro"]}

def dupla(v,e,d):
    return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

# ==============================
# 📝 MENSAGEM NO FORMATO QUE VOCÊ QUER
# ==============================
def msg_jogo(casa, fora, dt, dc, df, dup, mg_total):
    return f"""⚽ {casa} 🆚 {fora} | {dt.strftime('%d/%m %H:%M')}

📊 Probabilidades:
✅ {casa}: {dc['pV']}% | ⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 GOLS:
⚽ Média: {mg_total}
🔢 Mais 1.5: {round((dc['mais15']+df['mais15'])/2,0)}% | Menos 1.5: {round((dc['menos15']+df['menos15'])/2,0)}%
🔢 Mais 2.5: {round((dc['mais25']+df['mais25'])/2,0)}% | Menos 2.5: {round((dc['menos25']+df['menos25'])/2,0)}%
🔢 Menos 3.5: {round((dc['menos35']+df['menos35'])/2,0)}%
🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%

🎯 DADOS INDIVIDUAIS:
🏠 {casa}:
  • Chutes ao Gol: {dc['chute_gol']} | Finalizações: {dc['fin']} | Faltas: {dc['fal']}
  • Escanteios: {dc['esc']} | Defesas: {dc['defesa_gk']} | Cartões: {dc['cartao']}
  • Últimos 5: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}

✈️ {fora}:
  • Chutes ao Gol: {df['chute_gol']} | Finalizações: {df['fin']} | Faltas: {df['fal']}
  • Escanteios: {df['esc']} | Defesas: {df['defesa_gk']} | Cartões: {df['cartao']}
  • Últimos 5: {' '.join(df['resumo'])} | Placares: {' '.join(df['placares'])}
"""

# ==============================
# 🤖 ROTINA AUTOMÁTICA
# ==============================
def alerta():
    while True:
        try:
            if datetime.now().strftime("%H:%M") == HORARIO_ALERTA:
                for j in buscar_jogos("TODAS", DIAS_BUSCA):
                    try:
                        dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                        dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], True)
                        df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], False)
                        dup = dupla(dc['pV'],dc['pE'],dc['pD'])
                        mg_total = round((dc['mg']+df['mg']),1)
                        enviar_telegram(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg_total))
                        time.sleep(1)
                    except: pass
        except: pass
        time.sleep(30)
threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ TELA DO APP
# ==============================
esc = st.selectbox("Liga", list(LIGAS.keys()))
dias = st.number_input("Dias à frente", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Gerar e Enviar"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos: st.info("Nenhum jogo encontrado.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados:")
        enviados=0
        for j in jogos:
            try:
                dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], True)
                df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], False)
                dup = dupla(dc['pV'],dc['pE'],dc['pD'])
                mg_total = round((dc['mg']+df['mg']),1)
                st.markdown(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg_total))
                st.divider()
                ok,_ = enviar_telegram(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg_total))
                if ok: enviados+=1
            except: pass
        st.success(f"✅ Enviados {enviados}/{len(jogos)} para o Telegram!")
        

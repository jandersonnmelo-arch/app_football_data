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
# 🏆 MÉDIAS DAS LIGAS - TODAS ADICIONADAS
# ==============================
MEDIAS_LIGA = {
    # 🇧🇷 BRASIL
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
            "vit_casa":45,"vit_fora":30,"empate":25,
            "mais15":75,"menos15":25,"mais25":55,"menos25":45,"menos35":82,"mais35gols":38,
            "mais15cartao":92,"mais25cartao":60,"menos65cartao":88,
            "mais75esc":58,"menos125esc":92,
            "mais25fin":32,"menos25fin":95,
            "mais95chute":38,"menos95chute":62,
            "mais25fal":55,"menos25fal":50,
            "mais35defesa":65,"menos35defesa":35},
    # 🌍 COMPETIÇÕES INTERNACIONAIS
    "WC": {"esc":8.2,"cartao":3.0,"fin":10.0,"chute_gol":4.2,"fal":25.0,"defesa_gk":4.0,"gols":2.5,
           "vit_casa":42,"vit_fora":32,"empate":26,
           "mais15":74,"menos15":26,"mais25":53,"menos25":47,"menos35":80,"mais35gols":36,
           "mais15cartao":93,"mais25cartao":58,"menos65cartao":90,
           "mais75esc":55,"menos125esc":91,
           "mais25fin":35,"menos25fin":94,
           "mais95chute":40,"menos95chute":60,
           "mais25fal":52,"menos25fal":48,
           "mais35defesa":62,"menos35defesa":38},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "vit_casa":48,"vit_fora":29,"empate":23,
           "mais15":80,"menos15":20,"mais25":62,"menos25":38,"menos35":75,"mais35gols":45,
           "mais15cartao":95,"mais25cartao":52,"menos65cartao":92,
           "mais75esc":68,"menos125esc":88,
           "mais25fin":45,"menos25fin":90,
           "mais95chute":52,"menos95chute":48,
           "mais25fal":42,"menos25fal":60,
           "mais35defesa":52,"menos35defesa":48},
    "EC": {"esc":8.8,"cartao":2.9,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa_gk":3.8,"gols":2.7,
           "vit_casa":45,"vit_fora":30,"empate":25,
           "mais15":78,"menos15":22,"mais25":58,"menos25":42,"menos35":78,"mais35gols":40,
           "mais15cartao":94,"mais25cartao":55,"menos65cartao":91,
           "mais75esc":62,"menos125esc":89,
           "mais25fin":40,"menos25fin":92,
           "mais95chute":48,"menos95chute":52,
           "mais25fal":48,"menos25fal":52,
           "mais35defesa":58,"menos35defesa":42},
    # 🇪🇺 LIGAS EUROPEIAS
    "BL1": {"esc":9.8,"cartao":2.8,"fin":12.0,"chute_gol":5.5,"fal":24.5,"defesa_gk":3.2,"gols":3.1,
            "vit_casa":50,"vit_fora":28,"empate":22,
            "mais15":85,"menos15":15,"mais25":68,"menos25":32,"menos35":70,"mais35gols":50,
            "mais15cartao":94,"mais25cartao":55,"menos65cartao":91,
            "mais75esc":72,"menos125esc":85,
            "mais25fin":55,"menos25fin":85,
            "mais95chute":60,"menos95chute":40,
            "mais25fal":45,"menos25fal":55,
            "mais35defesa":48,"menos35defesa":52},
    "DED": {"esc":10.5,"cartao":2.5,"fin":12.5,"chute_gol":5.8,"fal":22.5,"defesa_gk":3.0,"gols":3.2,
            "vit_casa":52,"vit_fora":27,"empate":21,
            "mais15":88,"menos15":12,"mais25":70,"menos25":30,"menos35":68,"mais35gols":52,
            "mais15cartao":96,"mais25cartao":48,"menos65cartao":94,
            "mais75esc":75,"menos125esc":82,
            "mais25fin":58,"menos25fin":82,
            "mais95chute":62,"menos95chute":38,
            "mais25fal":38,"menos25fal":62,
            "mais35defesa":45,"menos35defesa":55},
    "PD": {"esc":9.2,"cartao":3.0,"fin":10.5,"chute_gol":4.6,"fal":25.5,"defesa_gk":3.6,"gols":2.8,
           "vit_casa":47,"vit_fora":29,"empate":24,
           "mais15":80,"menos15":20,"mais25":60,"menos25":40,"menos35":76,"mais35gols":42,
           "mais15cartao":93,"mais25cartao":58,"menos65cartao":89,
           "mais75esc":65,"menos125esc":87,
           "mais25fin":42,"menos25fin":91,
           "mais95chute":50,"menos95chute":50,
           "mais25fal":50,"menos25fal":50,
           "mais35defesa":55,"menos35defesa":45},
    "FL1": {"esc":8.5,"cartao":2.8,"fin":10.0,"chute_gol":4.3,"fal":24.0,"defesa_gk":3.9,"gols":2.7,
            "vit_casa":46,"vit_fora":29,"empate":25,
            "mais15":78,"menos15":22,"mais25":57,"menos25":43,"menos35":79,"mais35gols":39,
            "mais15cartao":94,"mais25cartao":54,"menos65cartao":92,
            "mais75esc":60,"menos125esc":90,
            "mais25fin":38,"menos25fin":93,
            "mais95chute":45,"menos95chute":55,
            "mais25fal":47,"menos25fal":53,
            "mais35defesa":60,"menos35defesa":40},
    "ELC": {"esc":8.0,"cartao":3.5,"fin":9.2,"chute_gol":3.8,"fal":28.0,"defesa_gk":4.5,"gols":2.4,
            "vit_casa":44,"vit_fora":27,"empate":29,
            "mais15":70,"menos15":30,"mais25":50,"menos25":50,"menos35":86,"mais35gols":32,
            "mais15cartao":88,"mais25cartao":65,"menos65cartao":85,
            "mais75esc":52,"menos125esc":95,
            "mais25fin":26,"menos25fin":97,
            "mais95chute":30,"menos95chute":70,
            "mais25fal":60,"menos25fal":40,
            "mais35defesa":72,"menos35defesa":28},
    "PPL": {"esc":8.8,"cartao":3.1,"fin":9.8,"chute_gol":4.1,"fal":26.0,"defesa_gk":4.1,"gols":2.5,
            "vit_casa":43,"vit_fora":28,"empate":29,
            "mais15":73,"menos15":27,"mais25":54,"menos25":46,"menos35":83,"mais35gols":35,
            "mais15cartao":91,"mais25cartao":62,"menos65cartao":87,
            "mais75esc":56,"menos125esc":93,
            "mais25fin":30,"menos25fin":96,
            "mais95chute":35,"menos95chute":65,
            "mais25fal":54,"menos25fal":46,
            "mais35defesa":68,"menos35defesa":32},
    "SA": {"esc":9.0,"cartao":3.0,"fin":10.8,"chute_gol":4.7,"fal":25.0,"defesa_gk":3.7,"gols":2.8,
           "vit_casa":48,"vit_fora":28,"empate":24,
           "mais15":82,"menos15":18,"mais25":61,"menos25":39,"menos35":77,"mais35gols":43,
           "mais15cartao":92,"mais25cartao":56,"menos65cartao":90,
           "mais75esc":63,"menos125esc":88,
           "mais25fin":44,"menos25fin":90,
           "mais95chute":49,"menos95chute":51,
           "mais25fal":49,"menos25fal":51,
           "mais35defesa":56,"menos35defesa":44},
    "PL": {"esc":10.2,"cartao":2.6,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa_gk":3.4,"gols":2.8,
           "vit_casa":48,"vit_fora":30,"empate":22,
           "mais15":82,"menos15":18,"mais25":64,"menos25":36,"menos35":76,"mais35gols":42,
           "mais15cartao":96,"mais25cartao":50,"menos65cartao":93,
           "mais75esc":70,"menos125esc":86,
           "mais25fin":48,"menos25fin":89,
           "mais95chute":55,"menos95chute":45,
           "mais25fal":40,"menos25fal":62,
           "mais35defesa":50,"menos35defesa":50}
}

LIGAS = {
    "⚽ Todas Competições": "TODAS",
    "🌍 Copa do Mundo FIFA": "WC",
    "🏆 UEFA Champions League": "CL",
    "🏆 Eurocopa": "EC",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇩🇪 Bundesliga": "BL1",
    "🇳🇱 Eredivisie": "DED",
    "🇪🇸 La Liga": "PD",
    "🇫🇷 Ligue 1": "FL1",
    "🇬🇧 Championship": "ELC",
    "🇵🇹 Primeira Liga": "PPL",
    "🇮🇹 Série A": "SA",
    "🇬🇧 Premier League": "PL"
}
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
# 🧮 CÁLCULO COMPLETO
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
                "menos35":med["menos35"],"mais35gols":med["mais35gols"],
                "mcartao":med["cartao"],"mais15cartao":med["mais15cartao"],"mais25cartao":med["mais25cartao"],"menos65cartao":med["menos65cartao"],
                "mesc":med["esc"],"mais75esc":med["mais75esc"],"menos125esc":med["menos125esc"],
                "mfin":med["fin"],"mais25fin":med["mais25fin"],"menos25fin":med["menos25fin"],
                "mchute":med["chute_gol"],"mais95chute":med["mais95chute"],"menos95chute":med["menos95chute"],
                "mfal":med["fal"],"mais25fal":med["mais25fal"],"menos25fal":med["menos25fal"],
                "mdefesa":med["defesa_gk"],"mais35defesa":med["mais35defesa"],"menos35defesa":med["menos35defesa"],
                "amb":50,"resumo":["📊 Média da Liga"]*5,"placares":["Sem dados"]
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
            "mais35gols":round(med["mais35gols"]*fator,0),
            "mcartao":round(med["cartao"]*fator,1),
            "mais15cartao":round(med["mais15cartao"],0),"mais25cartao":round(med["mais25cartao"]*fator,0),"menos65cartao":round(med["menos65cartao"]/fator if fator>0 else med["menos65cartao"],0),
            "mesc":round(med["esc"]*fator,1),
            "mais75esc":round(med["mais75esc"]*fator,0),"menos125esc":round(med["menos125esc"]/fator if fator>0 else med["menos125esc"],0),
            "mfin":round(med["fin"]*fator,1),
            "mais25fin":round(med["mais25fin"]*fator,0),"menos25fin":round(med["menos25fin"]/fator if fator>0 else med["menos25fin"],0),
            "mchute":round(med["chute_gol"]*fator,1),
            "mais95chute":round(med["mais95chute"]*fator,0),"menos95chute":round(med["menos95chute"]/fator if fator>0 else med["menos95chute"],0),
            "mfal":round(med["fal"]*fator,1),
            "mais25fal":round(med["mais25fal"]*fator,0),"menos25fal":round(med["menos25fal"]/fator if fator>0 else med["menos25fal"],0),
            "mdefesa":round(med["defesa_gk"]/fator if fator>0 else med["defesa_gk"],1),
            "mais35defesa":round(med["mais35defesa"]/fator if fator>0 else med["mais35defesa"],0),
            "menos35defesa":round(med["menos35defesa"]*fator,0),
            "amb":round((amb/t)*100,0),
            "resumo":resumo,"placares":placares
        }
    except:
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        return {"pV":med["vit_casa"] if eh_casa else med["vit_fora"],"pE":med["empate"],"pD":med["vit_fora"] if eh_casa else med["vit_casa"],
                "mg":med["gols"],"mais15":med["mais15"],"menos15":med["menos15"],
                "mais25":med["mais25"],"menos25":med["menos25"],"menos35":med["menos35"],"mais35gols":med["mais35gols"],
                "mcartao":med["cartao"],"mais15cartao":med["mais15cartao"],"mais25cartao":med["mais25cartao"],"menos65cartao":med["menos65cartao"],
                "mesc":med["esc"],"mais75esc":med["mais75esc"],"menos125esc":med["menos125esc"],
                "mfin":med["fin"],"mais25fin":med["mais25fin"],"menos25fin":med["menos25fin"],
                "mchute":med["chute_gol"],"mais95chute":med["mais95chute"],"menos95chute":med["menos95chute"],
                "mfal":med["fal"],"mais25fal":med["mais25fal"],"menos25fal":med["menos25fal"],
                "mdefesa":med["defesa_gk"],"mais35defesa":med["mais35defesa"],"menos35defesa":med["menos35defesa"],
                "amb":50,"resumo":["📊 Média da Liga"]*5,"placares":["Erro"]}

def dupla(v,e,d):
    return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

# ==============================
# 📝 MENSAGEM PADRONIZADA
# ==============================
def msg_jogo(casa, fora, dt, dc, df, dup):
    # MÉDIAS GERAIS DO CONFRONTO
    mg_total = round((dc['mg']+df['mg']),1)
    mcartao_total = round((dc['mcartao']+df['mcartao']),1)
    mesc_total = round((dc['mesc']+df['mesc']),1)
    mfin_total = round((dc['mfin']+df['mfin']),1)
    mchute_total = round((dc['mchute']+df['mchute']),1)
    mfal_total = round((dc['mfal']+df['mfal']),1)
    mdefesa_total = round((dc['mdefesa']+df['mdefesa']),1)

    # PROBABILIDADES GERAIS
    mais15cartao = round((dc['mais15cartao']+df['mais15cartao'])/2,0)
    mais25cartao = round((dc['mais25cartao']+df['mais25cartao'])/2,0)
    menos65cartao = round((dc['menos65cartao']+df['menos65cartao'])/2,0)
    mais75esc = round((dc['mais75esc']+df['mais75esc'])/2,0)
    menos125esc = round((dc['menos125esc']+df['menos125esc'])/2,0)
    mais25fin = round((dc['mais25fin']+df['mais25fin'])/2,0)
    menos25fin = round((dc['menos25fin']+df['menos25fin'])/2,0)
    mais95chute = round((dc['mais95chute']+df['mais95chute'])/2,0)
    menos95chute = round((dc['menos95chute']+df['menos95chute'])/2,0)
    mais25fal = round((dc['mais25fal']+df['mais25fal'])/2,0)
    menos25fal = round((dc['menos25fal']+df['menos25fal'])/2,0)
    mais35defesa = round((dc['mais35defesa']+df['mais35defesa'])/2,0)
    menos35defesa = round((dc['menos35defesa']+df['menos35defesa'])/2,0)

    return f"""⚽ {casa} 🆚 {fora} | {dt.strftime('%d/%m %H:%M')}

📊 Probabilidades:
✅ {casa}: {dc['pV']}% | ⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 GOLS:
⚽ Média: {mg_total}
🔢 Mais 1.5: {round((dc['mais15']+df['mais15'])/2,0)}% | Menos 1.5: {round((dc['menos15']+df['menos15'])/2,0)}%
🔢 Mais 2.5: {round((dc['mais25']+df['mais25'])/2,0)}% | Menos 2.5: {round((dc['menos25']+df['menos25'])/2,0)}%
🔢 Mais 3.5: {round((dc['mais35gols']+df['mais35gols'])/2,0)}% | Menos 3.5: {round((dc['menos35']+df['menos35'])/2,0)}%
🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%

🟨 CARTÕES:
🟨 Média: {mcartao_total}
🔢 Mais 1.5: {mais15cartao}% | Mais 2.5: {mais25cartao}% | Menos 6.5: {menos65cartao}%

📐 ESCANTEIOS:
📐 Média: {mesc_total}
🔢 Mais 7.5: {mais75esc}% | Menos 12.5: {menos125esc}%

🎯 FINALIZAÇÕES:
🎯 Média: {mfin_total}
🔢 Mais 25: {mais25fin}% | Menos 25: {menos25fin}%

⚽ CHUTES AO GOL:
⚽ Média: {mchute_total}
🔢 Mais 9.5: {mais95chute}% | Menos 9.5: {menos95chute}%

🤚 FALTAS:
🤚 Média: {mfal_total}
🔢 Mais 25: {mais25fal}% | Menos 25: {menos25fal}%

🧤 DEFESAS GOLEIRO:
🧤 Média: {mdefesa_total}
🔢 Mais 3.5: {mais35defesa}% | Menos 3.5: {menos35defesa}%

🎯 DADOS INDIVIDUAIS:
🏠 {casa}:
  • Chutes ao Gol: {dc['mchute']} | Finalizações: {dc['mfin']} | Faltas: {dc['mfal']}
  • Escanteios: {dc['mesc']} | Defesas: {dc['mdefesa']} | Cartões: {dc['mcartao']}
  • Últimos 5: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}

✈️ {fora}:
  • Chutes ao Gol: {df['mchute']} | Finalizações: {df['mfin']} | Faltas: {df['mfal']}
  • Escanteios: {df['mesc']} | Defesas: {df['mdefesa']} | Cartões: {df['mcartao']}
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
                        enviar_telegram(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup))
                        time.sleep(1)
                    except: pass
        except: pass
        time.sleep(30)
threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ TELA DO APP
# ==============================
esc = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
dias = st.number_input("Dias à frente", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Gerar e Enviar Análises"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos: st.info("Nenhum jogo encontrado para essa competição.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        enviados=0
        for j in jogos:
            try:
                dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], True)
                df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], False)
                dup = dupla(dc['pV'],dc['pE'],dc['pD'])
                st.markdown(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup))
                st.divider()
                ok,_ = enviar_telegram(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup))
                if ok: enviados+=1
            except: pass
        st.success(f"✅ Concluído! {enviados}/{len(jogos)} análises enviadas ao Telegram!")

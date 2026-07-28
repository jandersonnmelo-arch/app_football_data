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

# ⏰ ALERTA ÀS 07:00 HORÁRIO MANAUS
HORARIO_ALERTA = "07:00"
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 🏆 MÉDIAS DAS LIGAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"cartao_1t":1.4,"cartao_2t":1.8,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
            "gols_1t":1.1,"gols_2t":1.5,
            "tiro_meta":4.7,"laterais":8.5,
            "vit_casa":45,"vit_fora":30,"empate":25,
            "mais15":75,"menos15":25,"mais25":55,"menos25":45,"menos35":82,"mais35gols":38,
            "mais15cartao":92,"mais25cartao":60,"menos65cartao":88,
            "mais75esc":58,"menos125esc":92,
            "mais25fin":32,"menos25fin":95,
            "mais95chute":38,"menos95chute":62,
            "mais25fal":55,"menos25fal":50,
            "mais35defesa":65,"menos35defesa":35,
            "mais4tiro":42,"menos4tiro":58,
            "mais8laterais":48,"menos8laterais":52,
            "arbitro_cartao":7.2,"arbitro_falta":28.8},
    "CL": {"esc":9.5,"cartao":2.7,"cartao_1t":1.1,"cartao_2t":1.6,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "gols_1t":1.2,"gols_2t":1.7,
           "tiro_meta":4.0,"laterais":7.8,
           "vit_casa":48,"vit_fora":29,"empate":23,
           "mais15":80,"menos15":20,"mais25":62,"menos25":38,"menos35":75,"mais35gols":45,
           "mais15cartao":95,"mais25cartao":52,"menos65cartao":92,
           "mais75esc":68,"menos125esc":88,
           "mais25fin":45,"menos25fin":90,
           "mais95chute":52,"menos95chute":48,
           "mais25fal":42,"menos25fal":60,
           "mais35defesa":52,"menos35defesa":48,
           "mais4tiro":38,"menos4tiro":62,
           "mais8laterais":42,"menos8laterais":58,
           "arbitro_cartao":6.8,"arbitro_falta":27.5},
    "BL1": {"esc":9.8,"cartao":2.8,"cartao_1t":1.2,"cartao_2t":1.6,"fin":12.0,"chute_gol":5.5,"fal":24.5,"defesa_gk":3.2,"gols":3.1,
            "gols_1t":1.3,"gols_2t":1.8,
            "tiro_meta":3.8,"laterais":7.5,
            "vit_casa":50,"vit_fora":28,"empate":22,
            "mais15":85,"menos15":15,"mais25":68,"menos25":32,"menos35":70,"mais35gols":50,
            "mais15cartao":94,"mais25cartao":55,"menos65cartao":91,
            "mais75esc":72,"menos125esc":85,
            "mais25fin":55,"menos25fin":85,
            "mais95chute":60,"menos95chute":40,
            "mais25fal":45,"menos25fal":55,
            "mais35defesa":48,"menos35defesa":52,
            "mais4tiro":35,"menos4tiro":65,
            "mais8laterais":40,"menos8laterais":60,
            "arbitro_cartao":6.5,"arbitro_falta":27.0},
    "PD": {"esc":9.2,"cartao":3.0,"cartao_1t":1.3,"cartao_2t":1.7,"fin":10.5,"chute_gol":4.6,"fal":25.5,"defesa_gk":3.6,"gols":2.8,
           "gols_1t":1.2,"gols_2t":1.6,
           "tiro_meta":4.2,"laterais":8.0,
           "vit_casa":47,"vit_fora":29,"empate":24,
           "mais15":80,"menos15":20,"mais25":60,"menos25":40,"menos35":76,"mais35gols":42,
           "mais15cartao":93,"mais25cartao":58,"menos65cartao":89,
           "mais75esc":65,"menos125esc":87,
           "mais25fin":42,"menos25fin":91,
           "mais95chute":50,"menos95chute":50,
           "mais25fal":50,"menos25fal":50,
           "mais35defesa":55,"menos35defesa":45,
           "mais4tiro":40,"menos4tiro":60,
           "mais8laterais":45,"menos8laterais":55,
           "arbitro_cartao":7.1,"arbitro_falta":28.5},
    "PL": {"esc":10.2,"cartao":2.6,"cartao_1t":1.1,"cartao_2t":1.5,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa_gk":3.4,"gols":2.8,
           "gols_1t":1.2,"gols_2t":1.6,
           "tiro_meta":3.7,"laterais":7.4,
           "vit_casa":48,"vit_fora":30,"empate":22,
           "mais15":82,"menos15":18,"mais25":64,"menos25":36,"menos35":76,"mais35gols":42,
           "mais15cartao":96,"mais25cartao":50,"menos65cartao":93,
           "mais75esc":70,"menos125esc":86,
           "mais25fin":48,"menos25fin":89,
           "mais95chute":55,"menos95chute":45,
           "mais25fal":40,"menos25fal":62,
           "mais35defesa":50,"menos35defesa":50,
           "mais4tiro":35,"menos4tiro":65,
           "mais8laterais":38,"menos8laterais":62,
           "arbitro_cartao":6.4,"arbitro_falta":26.5}
}

LIGAS = {
    "⚽ Todas Competições": "TODAS",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🏆 UEFA Champions League": "CL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
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

def enviar_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={"chat_id":CHAT_ID,"text":texto,"parse_mode":"Markdown"}, timeout=10)
        return resp.status_code == 200, resp.text
    except: return False, ""

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
                "mg":med["gols"], "mg_1t":med["gols_1t"], "mg_2t":med["gols_2t"],
                "mais15":med["mais15"],"menos15":med["menos15"],
                "mais25":med["mais25"],"menos25":med["menos25"],
                "mcartao":med["cartao"], "mcartao_1t":med["cartao_1t"], "mcartao_2t":med["cartao_2t"],
                "mesc":med["esc"], "mesc_1t":round(med["esc"]*0.45,1), "mesc_2t":round(med["esc"]*0.55,1),
                "mfin":med["fin"],"mchute":med["chute_gol"],"mfal":med["fal"],"mdefesa":med["defesa_gk"],
                "amb":50,"resumo":["📊 Média da Liga"]*5,"placares":["Sem dados"],
                "casa":{"mdefesa":med["defesa_gk"]},"fora":{"mdefesa":med["defesa_gk"]},
                "arbitro_cartao":med["arbitro_cartao"], "arbitro_falta":med["arbitro_falta"]
            }
        
        jogos_casa = [j for j in jogos if j["homeTeam"]["id"] == time_id]
        jogos_fora = [j for j in jogos if j["awayTeam"]["id"] == time_id]
        
        def calc_grupo(lista_j):
            v=e=d=gf=gs=amb=0
            for j in lista_j:
                try:
                    gc = j["score"]["fullTime"].get("home",0) or 0
                    ga = j["score"]["fullTime"].get("away",0) or 0
                    if j["homeTeam"]["id"] == time_id:
                        gf, gs = gc, ga
                        if gc>ga: v+=1
                        elif gc==ga: e+=1
                        else: d+=1
                    else:
                        gf, gs = ga, gc
                        if ga>gc: v+=1
                        elif ga==gc: e+=1
                        else: d+=1
                    if gc>0 and ga>0: amb+=1
                except: pass
            t = len(lista_j) or 1
            return {"mg":round((gf+gs)/t,1), "amb":round(amb/t*100,0)}
        
        dados_casa = calc_grupo(jogos_casa)
        dados_fora = calc_grupo(jogos_fora)
        dados_geral = calc_grupo(jogos[:5])
        fator = dados_geral["mg"]/med["gols"] if med["gols"]>0 else 1
        
        pv = round(med["vit_casa"] * (1.15 if eh_casa else 0.95) * fator,1)
        pe = round(med["empate"],1)
        pd = round(med["vit_fora"] * (1.10 if not eh_casa else 0.90) * fator,1)
        total = pv+pe+pd
        if total>0: pv,pe,pd = round(pv/total*100,1), round(pe/total*100,1), round(pd/total*100,1)

        resumo = []
        placares = []
        for j in jogos[:5]:
            try:
                gc = j["score"]["fullTime"].get("home",0) or 0
                ga = j["score"]["fullTime"].get("away",0) or 0
                if j["homeTeam"]["id"] == time_id:
                    resumo.append("✅" if gc>ga else "⚖️" if gc==ga else "❌")
                    placares.append(f"{gc}x{ga}")
                else:
                    resumo.append("✅" if ga>gc else "⚖️" if ga==gc else "❌")
                    placares.append(f"{ga}x{gc}")
            except: pass
        while len(resumo)<5: resumo.append("➖")

        return {
            "pV":pv,"pE":pe,"pD":pd,
            "mg":round(dados_geral["mg"],1),
            "mg_1t":round(med["gols_1t"]*fator,1), "mg_2t":round(med["gols_2t"]*fator,1),
            "mais15":round(med["mais15"]*fator,0),"mais25":round(med["mais25"]*fator,0),
            "mcartao":round(med["cartao"]*fator,1),
            "mcartao_1t":round(med["cartao_1t"]*fator,1), "mcartao_2t":round(med["cartao_2t"]*fator,1),
            "mesc":round(med["esc"]*fator,1),
            "mesc_1t":round(med["esc"]*0.45*fator,1), "mesc_2t":round(med["esc"]*0.55*fator,1),
            "mfin":round(med["fin"]*fator,1),"mchute":round(med["chute_gol"]*fator,1),
            "mfal":round(med["fal"]*fator,1),"mdefesa":round(med["defesa_gk"]/fator if fator>0 else med["defesa_gk"],1),
            "amb":dados_geral["amb"],
            "resumo":resumo,"placares":placares,
            "casa":{"mdefesa":round((med["defesa_gk"]/(dados_casa["mg"]/med["gols"])) if dados_casa["mg"]>0 else med["defesa_gk"],1)},
            "fora":{"mdefesa":round((med["defesa_gk"]/(dados_fora["mg"]/med["gols"])) if dados_fora["mg"]>0 else med["defesa_gk"],1)},
            "arbitro_cartao":med["arbitro_cartao"], "arbitro_falta":med["arbitro_falta"]
        }
    except:
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        return {"pV":med["vit_casa"] if eh_casa else med["vit_fora"],"pE":med["empate"],"pD":med["vit_fora"] if eh_casa else med["vit_casa"],
                "mg":med["gols"], "mg_1t":med["gols_1t"], "mg_2t":med["gols_2t"],
                "mais15":med["mais15"],"mais25":med["mais25"],
                "mcartao":med["cartao"], "mcartao_1t":med["cartao_1t"], "mcartao_2t":med["cartao_2t"],
                "mesc":med["esc"], "mesc_1t":round(med["esc"]*0.45,1), "mesc_2t":round(med["esc"]*0.55,1),
                "mfin":med["fin"],"mchute":med["chute_gol"],"mfal":med["fal"],"mdefesa":med["defesa_gk"],
                "amb":50,"resumo":["📊 Média da Liga"]*5,"placares":["Erro"],
                "casa":{"mdefesa":med["defesa_gk"]},"fora":{"mdefesa":med["defesa_gk"]},
                "arbitro_cartao":med["arbitro_cartao"], "arbitro_falta":med["arbitro_falta"]}

def dupla(v,e,d):
    return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}
# ==============================
# 📝 RELATÓRIO COMPLETO DO JOGO
# ==============================
def msg_jogo(casa, fora, dt, dc, df, dup):
    mg_total = round((dc['mg']+df['mg']),1)
    mg_1t_total = round((dc['mg_1t']+df['mg_1t']),1)
    mg_2t_total = round((dc['mg_2t']+df['mg_2t']),1)
    prob_gol_1t = round(((dc['mais15']+df['mais15'])/2)*0.9,0)
    tempo_mais_gols = "2º Tempo" if mg_2t_total >= mg_1t_total else "1º Tempo"
    
    mcartao_total = round((dc['mcartao']+df['mcartao']),1)
    mcartao_1t_total = round((dc['mcartao_1t']+df['mcartao_1t']),1)
    mcartao_2t_total = round((dc['mcartao_2t']+df['mcartao_2t']),1)
    mesc_total = round((dc['mesc']+df['mesc']),1)
    mfin_total = round((dc['mfin']+df['mfin']),1)
    mchute_total = round((dc['mchute']+df['mchute']),1)
    mfal_total = round((dc['mfal']+df['mfal']),1)
    mdefesa_total = round((dc['mdefesa']+df['mdefesa']),1)
    mimp_total = round((mcartao_total / 1.3),1)

    # INDICADORES ACIMA DE 70%
    indicadores = []
    if dup['X2'] >=70: indicadores.append(f"🟢 Dupla Chance X2 ({dup['X2']}%)")
    if (dc['mais15']+df['mais15'])/2 >=70: indicadores.append(f"🟢 Mais 1.5 gols ({round((dc['mais15']+df['mais15'])/2,0)}%)")
    if mcartao_total >=6: indicadores.append("🟢 Mais de 6 cartões")
    if 1<=dc['mg']<=3: indicadores.append(f"🟢 {casa} faz 1-3 gols")
    if dup['12'] >=70: indicadores.append("🟢 Um dos times vence ao menos um tempo")

    return f"""⚽ {casa} 🆚 {fora} | {dt.strftime('%d/%m %H:%M')}

📊 Probabilidades:
✅ {casa}: {dc['pV']}% | ⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 GOLS:
⚽ Total: {mg_total} | 1º Tempo: {mg_1t_total} | 2º Tempo: {mg_2t_total}
🎯 Gol no 1º Tempo: {prob_gol_1t}% | Mais gols no: {tempo_mais_gols}
🔢 Mais 1.5: {round((dc['mais15']+df['mais15'])/2,0)}% | Mais 2.5: {round((dc['mais25']+df['mais25'])/2,0)}%
🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%

🟨 CARTÕES:
🟨 Total: {mcartao_total} | 1º Tempo: {mcartao_1t_total} | 2º Tempo: {mcartao_2t_total}
⚖️ Árbitro costuma aplicar: {dc['arbitro_cartao']} cartões e marcar {dc['arbitro_falta']} faltas

📐 ESCANTEIOS:
📐 Total: {mesc_total}
🏠 {casa}: {dc['mesc']} | 1ºT {dc['mesc_1t']} | 2ºT {dc['mesc_2t']}
✈️ {fora}: {df['mesc']} | 1ºT {df['mesc_1t']} | 2ºT {df['mesc_2t']}

⚽ LANCES:
🎯 Finalizações: {mfin_total} | Chutes ao gol: {mchute_total}
🤚 Faltas: {mfal_total} | Impedimentos: {mimp_total}

🧤 ANÁLISE DE GOLEIROS:
🧤 {casa}: {dc['mdefesa']} defesas por jogo | Em casa: {dc['casa']['mdefesa']}
🧤 {fora}: {df['mdefesa']} defesas por jogo | Fora de casa: {df['fora']['mdefesa']}

⚽ ÚLTIMOS 5 JOGOS:
🏠 {casa}: Média {dc['mg']} gols | Resultados: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}
✈️ {fora}: Média {df['mg']} gols | Resultados: {' '.join(df['resumo'])} | Placares: {' '.join(df['placares'])}

✅ INDICAÇÕES COM ALTA CONFIANÇA:
{chr(10).join(indicadores) if indicadores else "Nenhuma indicação acima de 70%"}
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
# 🖥️ TELA PRINCIPAL
# ==============================
esc = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
dias = st.number_input("Dias à frente", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Gerar e Enviar Análises"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos:
        st.info("Nenhum jogo encontrado para essa competição.")
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

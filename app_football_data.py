import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa + Telegram", page_icon="⚽", layout="wide")
st.title("⚽ Análise de Jogos + Envio Automático Telegram")

# 🔒 CHAVES OCULTAS
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves no Secrets! Erro: {e}")
    st.stop()

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

# ⏰ ALERTA DIÁRIO - HORÁRIO DE MANAUS
HORARIO_ALERTA = "07:00"
LIMIAR_ALERTA = 70
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 🏆 MÉDIAS E LIGAS COM SIGLAS CORRETAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
            "tiro_meta":4.7,"laterais":8.5,"imped":3.0,
            "vit_casa":45,"vit_fora":30,"empate":25,
            "mais15":75,"mais25":55,"mais35":38,
            "mais15cartao":92,"mais25cartao":72,"mais35cartao":50,"mais65cartao":26,
            "mais65esc":78,"mais75esc":69,"mais85esc":58,"mais95esc":45,"mais105esc":38,"mais115esc":30,
            "mais25imp":78,"mais35imp":62,
            "mais305lat":68,"mais325lat":55,"mais345lat":42,"mais365lat":28,
            "mais55tm":72,"mais65tm":60,"mais75tm":48,"mais95tm":30,
            "mais195fin":68,"mais205fin":60,"mais225fin":45,"mais255fin":25,
            "mais65cg":70,"mais75cg":55,"mais85cg":40,"mais95cg":46,
            "mais195fal":78,"mais225fal":62,"mais255fal":48,"mais295fal":32,
            "mais25def":80,"mais35def":54,"mais45def":38,"mais55def":30},
    "BRB": {"esc":8.5,"cartao":3.3,"fin":9.0,"chute_gol":3.8,"fal":27.0,"defesa_gk":4.5,"gols":2.4,
            "tiro_meta":5.0,"laterais":9.0,"imped":3.2,
            "vit_casa":44,"vit_fora":29,"empate":27,
            "mais15":72,"mais25":52,"mais35":35,
            "mais15cartao":90,"mais25cartao":70,"mais35cartao":48,"mais65cartao":28,
            "mais65esc":75,"mais75esc":65,"mais85esc":55,"mais95esc":42,"mais105esc":35,"mais115esc":28,
            "mais25imp":75,"mais35imp":60,
            "mais305lat":65,"mais325lat":52,"mais345lat":38,"mais365lat":25,
            "mais55tm":70,"mais65tm":58,"mais75tm":45,"mais95tm":28,
            "mais195fin":65,"mais205fin":58,"mais225fin":42,"mais255fin":22,
            "mais65cg":68,"mais75cg":54,"mais85cg":40,"mais95cg":45,
            "mais195fal":80,"mais225fal":65,"mais255fal":50,"mais295fal":35,
            "mais25def":82,"mais35def":65,"mais45def":48,"mais55def":32},
    "BRA": {"esc":8.8,"cartao":3.1,"fin":9.2,"chute_gol":3.9,"fal":26.0,"defesa_gk":4.3,"gols":2.5,
            "tiro_meta":4.8,"laterais":8.8,"imped":3.1,
            "vit_casa":45,"vit_fora":28,"empate":27,
            "mais15":74,"mais25":54,"mais35":37,
            "mais15cartao":91,"mais25cartao":71,"mais35cartao":49,"mais65cartao":27,
            "mais65esc":76,"mais75esc":67,"mais85esc":57,"mais95esc":44,"mais105esc":37,"mais115esc":29,
            "mais25imp":76,"mais35imp":61,
            "mais305lat":67,"mais325lat":54,"mais345lat":40,"mais365lat":27,
            "mais55tm":71,"mais65tm":59,"mais75tm":47,"mais95tm":29,
            "mais195fin":67,"mais205fin":59,"mais225fin":44,"mais255fin":24,
            "mais65cg":69,"mais75cg":55,"mais85cg":41,"mais95cg":47,
            "mais195fal":79,"mais225fal":64,"mais255fal":49,"mais295fal":34,
            "mais25def":81,"mais35def":63,"mais45def":46,"mais55def":31},
    "CSA": {"esc":8.7,"cartao":3.2,"fin":9.3,"chute_gol":4.1,"fal":25.5,"defesa_gk":4.1,"gols":2.6,
           "tiro_meta":4.6,"laterais":8.6,"imped":2.9,
           "vit_casa":46,"vit_fora":28,"empate":26,
           "mais15":76,"mais25":56,"mais35":39,
           "mais15cartao":92,"mais25cartao":72,"mais35cartao":50,"mais65cartao":26,
           "mais65esc":77,"mais75esc":68,"mais85esc":58,"mais95esc":45,"mais105esc":38,"mais115esc":30,
           "mais25imp":77,"mais35imp":62,
           "mais305lat":68,"mais325lat":55,"mais345lat":42,"mais365lat":28,
           "mais55tm":72,"mais65tm":60,"mais75tm":48,"mais95tm":30,
           "mais195fin":68,"mais205fin":60,"mais225fin":45,"mais255fin":25,
           "mais65cg":70,"mais75cg":56,"mais85cg":42,"mais95cg":48,
           "mais195fal":78,"mais225fal":63,"mais255fal":48,"mais295fal":33,
           "mais25def":80,"mais35def":60,"mais45def":44,"mais55def":30},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "tiro_meta":4.0,"laterais":7.8,"imped":2.5,
           "vit_casa":48,"vit_fora":29,"empate":23,
           "mais15":80,"mais25":62,"mais35":45,
           "mais15cartao":95,"mais25cartao":78,"mais35cartao":55,"mais65cartao":30,
           "mais65esc":80,"mais75esc":72,"mais85esc":62,"mais95esc":50,"mais105esc":42,"mais115esc":34,
           "mais25imp":80,"mais35imp":65,
           "mais305lat":70,"mais325lat":58,"mais345lat":45,"mais365lat":32,
           "mais55tm":74,"mais65tm":62,"mais75tm":50,"mais95tm":32,
           "mais195fin":75,"mais205fin":68,"mais225fin":52,"mais255fin":32,
           "mais65cg":75,"mais75cg":62,"mais85cg":48,"mais95cg":52,
           "mais195fal":70,"mais225fal":55,"mais255fal":42,"mais295fal":28,
           "mais25def":75,"mais35def":50,"mais45def":35,"mais55def":22},
    "EL": {"esc":8.8,"cartao":2.9,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa_gk":3.8,"gols":2.7,
           "tiro_meta":4.3,"laterais":8.2,"imped":2.7,
           "vit_casa":45,"vit_fora":30,"empate":25,
           "mais15":78,"mais25":58,"mais35":40,
           "mais15cartao":94,"mais25cartao":75,"mais35cartao":52,"mais65cartao":28,
           "mais65esc":78,"mais75esc":70,"mais85esc":60,"mais95esc":48,"mais105esc":40,"mais115esc":32,
           "mais25imp":78,"mais35imp":63,
           "mais305lat":68,"mais325lat":56,"mais345lat":43,"mais365lat":30,
           "mais55tm":72,"mais65tm":60,"mais75tm":48,"mais95tm":30,
           "mais195fin":72,"mais205fin":65,"mais225fin":50,"mais255fin":30,
           "mais65cg":72,"mais75cg":60,"mais85cg":45,"mais95cg":48,
           "mais195fal":72,"mais225fal":58,"mais255fal":45,"mais295fal":30,
           "mais25def":72,"mais35def":52,"mais45def":38,"mais55def":25},
    "BL1": {"esc":9.8,"cartao":2.8,"fin":12.0,"chute_gol":5.5,"fal":24.5,"defesa_gk":3.2,"gols":3.1,
            "tiro_meta":3.8,"laterais":7.5,"imped":2.4,
            "vit_casa":50,"vit_fora":28,"empate":22,
            "mais15":85,"mais25":68,"mais35":50,
            "mais15cartao":94,"mais25cartao":80,"mais35cartao":58,"mais65cartao":32,
            "mais65esc":82,"mais75esc":74,"mais85esc":64,"mais95esc":52,"mais105esc":44,"mais115esc":36,
            "mais25imp":82,"mais35imp":68,
            "mais305lat":72,"mais325lat":60,"mais345lat":48,"mais365lat":34,
            "mais55tm":76,"mais65tm":64,"mais75tm":52,"mais95tm":34,
            "mais195fin":80,"mais205fin":72,"mais225fin":58,"mais255fin":38,
            "mais65cg":80,"mais75cg":68,"mais85cg":52,"mais95cg":60,
            "mais195fal":68,"mais225fal":52,"mais255fal":38,"mais295fal":24,
            "mais25def":70,"mais35def":48,"mais45def":32,"mais55def":18},
    "PD": {"esc":9.2,"cartao":3.0,"fin":10.5,"chute_gol":4.6,"fal":25.5,"defesa_gk":3.6,"gols":2.8,
           "tiro_meta":4.2,"laterais":8.0,"imped":2.6,
           "vit_casa":47,"vit_fora":29,"empate":24,
           "mais15":80,"mais25":60,"mais35":42,
           "mais15cartao":93,"mais25cartao":73,"mais35cartao":50,"mais65cartao":28,
           "mais65esc":78,"mais75esc":70,"mais85esc":60,"mais95esc":48,"mais105esc":40,"mais115esc":32,
           "mais25imp":78,"mais35imp":62,
           "mais305lat":70,"mais325lat":58,"mais345lat":45,"mais365lat":32,
           "mais55tm":74,"mais65tm":62,"mais75tm":50,"mais95tm":32,
           "mais195fin":70,"mais205fin":62,"mais225fin":48,"mais255fin":28,
           "mais65cg":72,"mais75cg":60,"mais85cg":45,"mais95cg":50,
           "mais195fal":75,"mais225fal":60,"mais255fal":45,"mais295fal":30,
           "mais25def":78,"mais35def":55,"mais45def":40,"mais55def":25},
    "FL1": {"esc":8.5,"cartao":2.8,"fin":10.0,"chute_gol":4.3,"fal":24.0,"defesa_gk":3.9,"gols":2.7,
            "tiro_meta":4.4,"laterais":8.3,"imped":2.9,
            "vit_casa":46,"vit_fora":29,"empate":25,
            "mais15":78,"mais25":57,"mais35":39,
            "mais15cartao":94,"mais25cartao":72,"mais35cartao":48,"mais65cartao":25,
            "mais65esc":76,"mais75esc":68,"mais85esc":58,"mais95esc":46,"mais105esc":38,"mais115esc":30,
            "mais25imp":75,"mais35imp":58,
            "mais305lat":66,"mais325lat":54,"mais345lat":40,"mais365lat":28,
            "mais55tm":72,"mais65tm":60,"mais75tm":48,"mais95tm":30,
            "mais195fin":68,"mais205fin":60,"mais225fin":45,"mais255fin":25,
            "mais65cg":70,"mais75cg":58,"mais85cg":42,"mais95cg":48,
            "mais195fal":72,"mais225fal":58,"mais255fal":42,"mais295fal":28,
            "mais25def":80,"mais35def":62,"mais45def":45,"mais55def":28},
    "MX1": {"esc":8.0,"cartao":3.5,"fin":9.2,"chute_gol":3.8,"fal":28.0,"defesa_gk":4.5,"gols":2.4,
            "tiro_meta":5.0,"laterais":9.0,"imped":3.2,
            "vit_casa":44,"vit_fora":27,"empate":29,
            "mais15":70,"mais25":50,"mais35":32,
            "mais15cartao":88,"mais25cartao":65,"mais35cartao":42,"mais65cartao":20,
            "mais65esc":70,"mais75esc":60,"mais85esc":48,"mais95esc":36,"mais105esc":28,"mais115esc":22,
            "mais25imp":72,"mais35imp":55,
            "mais305lat":62,"mais325lat":50,"mais345lat":38,"mais365lat":26,
            "mais55tm":68,"mais65tm":56,"mais75tm":44,"mais95tm":28,
            "mais195fin":62,"mais205fin":54,"mais225fin":40,"mais255fin":20,
            "mais65cg":62,"mais75cg":50,"mais85cg":36,"mais95cg":40,
            "mais195fal":80,"mais225fal":65,"mais255fal":50,"mais295fal":38,
            "mais25def":85,"mais35def":70,"mais45def":55,"mais55def":35},
    "PPL": {"esc":8.8,"cartao":3.1,"fin":9.8,"chute_gol":4.1,"fal":26.0,"defesa_gk":4.1,"gols":2.5,
            "tiro_meta":4.8,"laterais":8.7,"imped":3.0,
            "vit_casa":43,"vit_fora":28,"empate":29,
            "mais15":73,"mais25":54,"mais35":35,
            "mais15cartao":91,"mais25cartao":62,"mais35cartao":40,"mais65cartao":22,
            "mais65esc":74,"mais75esc":64,"mais85esc":54,"mais95esc":42,"mais105esc":34,"mais115esc":26,
            "mais25imp":74,"mais35imp":58,
            "mais305lat":64,"mais325lat":52,"mais345lat":38,"mais365lat":26,
            "mais55tm":70,"mais65tm":58,"mais75tm":46,"mais95tm":30,
            "mais195fin":66,"mais205fin":58,"mais225fin":43,"mais255fin":23,
            "mais65cg":66,"mais75cg":52,"mais85cg":38,"mais95cg":44,
            "mais195fal":78,"mais225fal":62,"mais255fal":48,"mais295fal":34,
            "mais25def":82,"mais35def":68,"mais45def":50,"mais55def":32},
    "SA": {"esc":9.0,"cartao":3.0,"fin":10.8,"chute_gol":4.7,"fal":25.0,"defesa_gk":3.7,"gols":2.8,
           "tiro_meta":4.1,"laterais":7.9,"imped":2.8,
           "vit_casa":48,"vit_fora":28,"empate":24,
           "mais15":82,"mais25":61,"mais35":43,
           "mais15cartao":92,"mais25cartao":70,"mais35cartao":48,"mais65cartao":26,
           "mais65esc":78,"mais75esc":70,"mais85esc":60,"mais95esc":48,"mais105esc":40,"mais115esc":32,
           "mais25imp":78,"mais35imp":62,
           "mais305lat":70,"mais325lat":58,"mais345lat":45,"mais365lat":32,
           "mais55tm":74,"mais65tm":62,"mais75tm":50,"mais95tm":32,
           "mais195fin":72,"mais205fin":65,"mais225fin":50,"mais255fin":30,
           "mais65cg":74,"mais75cg":62,"mais85cg":48,"mais95cg":52,
           "mais195fal":74,"mais225fal":60,"mais255fal":45,"mais295fal":30,
           "mais25def":76,"mais35def":54,"mais45def":40,"mais55def":26},
    "PL": {"esc":10.2,"cartao":2.6,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa_gk":3.4,"gols":2.8,
           "tiro_meta":3.7,"laterais":7.4,"imped":2.3,
           "vit_casa":48,"vit_fora":30,"empate":22,
           "mais15":82,"mais25":64,"mais35":42,
           "mais15cartao":96,"mais25cartao":82,"mais35cartao":62,"mais65cartao":32,
           "mais65esc":80,"mais75esc":72,"mais85esc":62,"mais95esc":50,"mais105esc":42,"mais115esc":34,
           "mais25imp":80,"mais35imp":65,
           "mais305lat":72,"mais325lat":60,"mais345lat":48,"mais365lat":34,
           "mais55tm":76,"mais65tm":64,"mais75tm":52,"mais95tm":34,
           "mais195fin":78,"mais205fin":70,"mais225fin":58,"mais255fin":38,
           "mais65cg":78,"mais75cg":66,"mais85cg":50,"mais95cg":58,
           "mais195fal":62,"mais225fal":48,"mais255fal":35,"mais295fal":20,
           "mais25def":70,"mais35def":45,"mais45def":30,"mais55def":15}
}

LIGAS = {
    "⚽ Todas Competições": "TODAS",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🇧🇷 Copa do Brasil": "BRA",
    "🏆 Copa Sul-Americana": "CSA",
    "🏆 UEFA Champions League": "CL",
    "🏆 Europa League": "EL",
    "🇩🇪 Bundesliga": "BL1",
    "🇪🇸 La Liga": "PD",
    "🇫🇷 Ligue 1": "FL1",
    "🇲🇽 Liga MX": "MX1",
    "🇵🇹 Primeira Liga": "PPL",
    "🇮🇹 Série A": "SA",
    "🇬🇧 Premier League": "PL"
}
TODAS_SIGLAS = list(LIGAS.values())
TODAS_SIGLAS.remove("TODAS")

# ==============================
# 🔍 BUSCA E CÁLCULOS CORRIGIDOS
# ==============================
@st.cache_data(ttl=1800)
def buscar_jogos(sigla, dias):
    time.sleep(0.2)
    hoje = datetime.utcnow().date()
    lista = []
    siglas_buscar = TODAS_SIGLAS if sigla == "TODAS" else [sigla]
    
    for s in siglas_buscar:
        try:
            r = requests.get(
                f"https://api.football-data.org/v4/competitions/{s}/matches",
                headers=HEADERS,
                params={"status":"SCHEDULED"},
                timeout=20
            )
            if r.status_code == 200:
                dados = r.json().get("matches", [])
                for j in dados:
                    try:
                        dt = datetime.fromisoformat(j["utcDate"].replace("Z",""))
                        if dt.date() <= hoje + timedelta(days=dias):
                            lista.append(j)
                    except:
                        continue
        except:
            continue
    return lista

@st.cache_data(ttl=3600)
def ultimos_5(time_id):
    time.sleep(0.3)
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{time_id}/matches",
            headers=HEADERS,
            params={"status":"FINISHED","limit":5},
            timeout=15
        )
        return r.json().get("matches", [])
    except:
        return []

def enviar_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id":CHAT_ID,"text":texto,"parse_mode":"Markdown"}, timeout=10)
        return True
    except:
        return False

def calcular_base(time_id, sigla, eh_casa=False):
    try:
        jogos = ultimos_5(time_id)
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        if not jogos:
            return {
                "pV":med["vit_casa"] if eh_casa else med["vit_fora"],
                "pE":med["empate"], "pD":med["vit_fora"] if eh_casa else med["vit_casa"],
                "mg":med["gols"], "mais15":med["mais15"],"menos15":100-med["mais15"],
                "mais25":med["mais25"],"menos25":100-med["mais25"],
                "mais35":med["mais35"],"menos35":100-med["mais35"],
                "mcartao":med["cartao"],"mais15cartao":med["mais15cartao"],
                "mais25cartao":med["mais25cartao"],"mais35cartao":med["mais35cartao"],
                "mais65cartao":med["mais65cartao"],"mesc":med["esc"],
                "mais65esc":med["mais65esc"],"mais75esc":med["mais75esc"],
                "mais85esc":med["mais85esc"],"mais95esc":med["mais95esc"],
                "mais105esc":med["mais105esc"],"mais115esc":med["mais115esc"],
                "mimped":med["imped"],"mais25imp":med["mais25imp"],
                "mais35imp":med["mais35imp"],"mlateral":med["laterais"],
                "mais305lat":med["mais305lat"],"mais325lat":med["mais325lat"],
                "mais345lat":med["mais345lat"],"mais365lat":med["mais365lat"],
                "mtiro":med["tiro_meta"],"mais55tm":med["mais55tm"],
                "mais65tm":med["mais65tm"],"mais75tm":med["mais75tm"],
                "mais95tm":med["mais95tm"],"mfin":med["fin"],
                "mais195fin":med["mais195fin"],"mais205fin":med["mais205fin"],
                "mais225fin":med["mais225fin"],"mais255fin":med["mais255fin"],
                "mchute":med["chute_gol"],"mais65cg":med["mais65cg"],
                "mais75cg":med["mais75cg"],"mais85cg":med["mais85cg"],
                "mais95cg":med["mais95cg"],"mfal":med["fal"],
                "mais195fal":med["mais195fal"],"mais225fal":med["mais225fal"],
                "mais255fal":med["mais255fal"],"mais295fal":med["mais295fal"],
                "mdefesa":med["defesa_gk"],"mais25def":med["mais25def"],
                "mais35def":med["mais35def"],"mais45def":med["mais45def"],
                "mais55def":med["mais55def"],"amb":50,"resumo":["📊 Média"]*5,"placares":["Sem dados"]
            }
        v=e=d=gf=gs=amb=0
        resumo=[]; placares=[]
        for j in jogos:
            try:
                cid = j["homeTeam"]["id"]
                gc = j["score"]["fullTime"]["home"] or 0
                ga = j["score"]["fullTime"]["away"] or 0
                if cid == time_id:
                    gf+=gc; gs+=ga
                    if gc>ga: v+=1; resumo.append("✅")
                    elif gc==ga: e+=1; resumo.append("⚖️")
                    else: d+=1; resumo.append("❌")
                    placares.append(f"{gc}x{ga}")
                else:
                    gf+=ga; gs+=gc
                    if ga>gc: v+=1; resumo.append("✅")
                    elif ga==gc: e+=1; resumo.append("⚖️")
                    else: d+=1; resumo.append("❌")
                    placares.append(f"{ga}x{gc}")
                if gc>0 and ga>0: amb+=1
            except: pass
        t=len(jogos); media_gols=(gf+gs)/t; fator=media_gols/med["gols"] if med["gols"]>0 else 1
        pv=round((v/t)*100*(1.15 if eh_casa else 0.95)*fator,1)
        pe=round((e/t)*100,1)
        pd=round((d/t)*100*(1.10 if not eh_casa else 0.90)*fator,1)
        total=pv+pe+pd
        if total>0: pv,pe,pd=round(pv/total*100,1), round(pe/total*100,1), round(pd/total*100,1)
        def calc_mais(val): return round(val*fator,0)
        return {
            "pV":pv,"pE":pe,"pD":pd,"mg":round(media_gols,1),
            "mais15":calc_mais(med["mais15"]),"menos15":round(100-calc_mais(med["mais15"]),0),
            "mais25":calc_mais(med["mais25"]),"menos25":round(100-calc_mais(med["mais25"]),0),
            "mais35":calc_mais(med["mais35"]),"menos35":round(100-calc_mais(med["mais35"]),0),
            "mcartao":round(med["cartao"]*fator,1),
            "mais15cartao":calc_mais(med["mais15cartao"]),"mais25cartao":calc_mais(med["mais25cartao"]),
            "mais35cartao":calc_mais(med["mais35cartao"]),"mais65cartao":calc_mais(med["mais65cartao"]),
            "mesc":round(med["esc"]*fator,1),
            "mais65esc":calc_mais(med["mais65esc"]),"mais75esc":calc_mais(med["mais75esc"]),
            "mais85esc":calc_mais(med["mais85esc"]),"mais95esc":calc_mais(med["mais95esc"]),
            "mais105esc":calc_mais(med["mais105esc"]),"mais115esc":calc_mais(med["mais115esc"]),
            "mimped":round(med["imped"]*fator,1),
            "mais25imp":calc_mais(med["mais25imp"]),"mais35imp":calc_mais(med["mais35imp"]),
            "mlateral":round(med["laterais"]*fator,1),
            "mais305lat":calc_mais(med["mais305lat"]),"mais325lat":calc_mais(med["mais325lat"]),
            "mais345lat":calc_mais(med["mais345lat"]),"mais365lat":calc_mais(med["mais365lat"]),
            "mtiro":round(med["tiro_meta"]*fator,1),
            "mais55tm":calc_mais(med["mais55tm"]),"mais65tm":calc_mais(med["mais65tm"]),
            "mais75tm":calc_mais(med["mais75tm"]),"mais95tm":calc_mais(med["mais95tm"]),
            "mfin":round(med["fin"]*fator,1),
            "mais195fin":calc_mais(med["mais195fin"]),"mais205fin":calc_mais(med["mais205fin"]),
            "mais225fin":calc_mais(med["mais225fin"]),"mais255fin":calc_mais(med["mais255fin"]),
            "mchute":round(med["chute_gol"]*fator,1),
            "mais65cg":calc_mais(med["mais65cg"]),"mais75cg":calc_mais(med["mais75cg"]),
            "mais85cg":calc_mais(med["mais85cg"]),"mais95cg":calc_mais(med["mais95cg"]),
            "mfal":round(med["fal"]*fator,1),
            "mais195fal":calc_mais(med["mais195fal"]),"mais225fal":calc_mais(med["mais225fal"]),
            "mais255fal":calc_mais(med["mais255fal"]),"mais295fal":calc_mais(med["mais295fal"]),
            "mdefesa":round(med["defesa_gk"]*fator,1),
            "mais25def":calc_mais(med["mais25def"]),"mais35def":calc_mais(med["mais35def"]),
            "mais45def":calc_mais(med["mais45def"]),"mais55def":calc_mais(med["mais55def"]),
            "amb":round((amb/t)*100,0),"resumo":resumo,"placares":placares
        }
    except: return calcular_base(time_id, sigla, eh_casa)

def dupla(v,e,d): return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

def msg_jogo(casa, fora, dt, dc, df, dup):
    def m(a,b): return round((a+b)/2,1)
    def m0(a,b): return round((a+b)/2,0)
    return f"""⚽ {casa} 🆚 {fora} | {dt.strftime('%d/%m %H:%M')}
📊 Probabilidades:
✅ {casa}: {dc['pV']}% | ⚖️ Empate: {m(dc['pE'],df['pE'])}% | ✅ {fora}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 Estimativa Total do Jogo:
⚽ Gols: Média {m(dc['mg'],df['mg'])} | Mais 1.5: {m0(dc['mais15'],df['mais15'])}% | Mais 2.5: {m0(dc['mais25'],df['mais25'])}%
🟨 Cartões: Média {m(dc['mcartao'],df['mcartao'])} | Mais 3.5: {m0(dc['mais35cartao'],df['mais35cartao'])}%
📐 Escanteios: Média {m(dc['mesc'],df['mesc'])} | Mais 9.5: {m0(dc['mais95esc'],df['mais95esc'])}%
⚽ Finalizações: Média {m(dc['mfin'],df['mfin'])} | Mais 19.5: {m0(dc['mais195fin'],df['mais195fin'])}%
🎯 Chutes ao Gol: Média {m(dc['mchute'],df['mchute'])} | Mais 6.5: {m0(dc['mais65cg'],df['mais65cg'])}%
🤚 Faltas: Média {m(dc['mfal'],df['mfal'])} | Mais 25.5: {m0(dc['mais255fal'],df['mais255fal'])}%
🧤 Defesas: Média {m(dc['mdefesa'],df['mdefesa'])} | Mais 3.5: {m0(dc['mais35def'],df['mais35def'])}%

📊 Últimos 5 Jogos:
🏠 {casa}: {' '.join(dc['resumo'])} | Placares: {', '.join(dc['placares'])}
✈️ {fora}: {' '.join(df['resumo'])} | Placares: {', '.join(df['placares'])}
"""
# ==============================
# 🖥️ INTERFACE E ALERTA AUTOMÁTICO
# ==============================
col1, col2 = st.columns([2,1])
with col1:
    liga_escolhida = st.selectbox("🏆 Selecione a Competição", list(LIGAS.keys()))
with col2:
    dias = st.slider("📅 Dias de Busca", 1, 14, DIAS_BUSCA)

sigla = LIGAS[liga_escolhida]
jogos = buscar_jogos(sigla, dias)

if not jogos:
    st.warning("⚠️ Nenhum jogo encontrado no período selecionado.")
else:
    st.success(f"✅ Encontrados {len(jogos)} jogos!")
    for jogo in jogos:
        try:
            casa = jogo["homeTeam"]["name"]
            fora = jogo["awayTeam"]["name"]
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z",""))
            sigla_jogo = jogo["competition"]["code"]
            dc = calcular_base(jogo["homeTeam"]["id"], sigla_jogo, True)
            df = calcular_base(jogo["awayTeam"]["id"], sigla_jogo, False)
            dup = dupla(dc["pV"], dc["pE"], dc["pD"])
            texto = msg_jogo(casa, fora, dt, dc, df, dup)

            with st.expander(f"⚽ {casa} vs {fora} | {dt.strftime('%d/%m %H:%M')}"):
                st.markdown(texto)
                if max(dc["pV"], df["pD"]) >= LIMIAR_ALERTA:
                    st.info(f"🔔 Probabilidade ≥ {LIMIAR_ALERTA}% — alerta ativado!")
                    if st.button(f"📤 Enviar ao Telegram", key=f"btn_{casa}_{fora}"):
                        enviar_telegram(texto)
                        st.success("✅ Enviado!")
        except:
            continue

# ⏰ ROTINA AUTOMÁTICA
if 'ultimo_envio' not in st.session_state:
    st.session_state.ultimo_envio = None

def rotina_alerta():
    while True:
        agora = datetime.now() - timedelta(hours=4)
        horario = agora.strftime("%H:%M")
        if horario == HORARIO_ALERTA and st.session_state.ultimo_envio != agora.date():
            st.session_state.ultimo_envio = agora.date()
            enviar_telegram(f"📢 ALERTA DIÁRIO {agora.strftime('%d/%m/%Y')}\n🔍 Jogos com chance ≥ {LIMIAR_ALERTA}%:")
            for s in TODAS_SIGLAS:
                for j in buscar_jogos(s, DIAS_BUSCA):
                    try:
                        dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], True)
                        df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], False)
                        if max(dc["pV"], df["pD"]) >= LIMIAR_ALERTA:
                            enviar_telegram(msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"],
                                datetime.fromisoformat(j["utcDate"].replace("Z","")), dc, df, dupla(dc["pV"],dc["pE"],dc["pD"])))
                            time.sleep(2)
                    except:
                        pass
        time.sleep(60)

if 'iniciou' not in st.session_state:
    st.session_state.iniciou = True
    threading.Thread(target=rotina_alerta, daemon=True).start()

st.info(f"⏰ Alerta automático: {HORARIO_ALERTA} (Manaus) | Limiar: {LIMIAR_ALERTA}%")

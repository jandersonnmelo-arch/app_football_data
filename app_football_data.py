import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa | Todas as Métricas", page_icon="⚽", layout="wide")
st.title("⚽ Análise Completa | Probabilidades + Todas as Métricas")

# 🔒 CHAVES OCULTAS
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves corretamente! Erro: {e}")
    st.stop()

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

# ⏰ HORÁRIO DE ALERTA: 07:00 MANAUS
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
        resposta = requests.post(url, data=payload, timeout=20)
        if resposta.status_code == 200:
            return True, "✅ Enviado com sucesso!"
        else:
            return False, f"❌ Erro Telegram: Código {resposta.status_code} - {resposta.text}"
    except Exception as e:
        return False, f"❌ Falha na conexão: {str(e)}"

# ==============================
# 🏆 MÉDIAS DAS LIGAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
            "vit_casa":45,"vit_fora":30,"empate":25,
            "mais15":75,"menos15":25,"mais25":55,"menos25":45,"menos35":82,
            "esc_mais75":58,"esc_menos125":92,
            "chute_mais95":38,"chute_menos95":62,
            "defesa_mais35":65,"defesa_menos35":35,
            "cartao_mais3":60,"cartao_menos3":40},
    "BRB": {"esc":8.5,"cartao":3.5,"fin":9.0,"chute_gol":3.5,"fal":27.5,"defesa_gk":4.5,"gols":2.4,
            "vit_casa":42,"vit_fora":28,"empate":30,
            "mais15":72,"menos15":28,"mais25":52,"menos25":48,"menos35":85,
            "esc_mais75":54,"esc_menos125":94,
            "chute_mais95":32,"chute_menos95":68,
            "defesa_mais35":70,"defesa_menos35":30,
            "cartao_mais3":65,"cartao_menos3":35},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "vit_casa":48,"vit_fora":29,"empate":23,
           "mais15":80,"menos15":20,"mais25":62,"menos25":38,"menos35":75,
           "esc_mais75":68,"esc_menos125":88,
           "chute_mais95":52,"chute_menos95":48,
           "defesa_mais35":52,"defesa_menos35":48,
           "cartao_mais3":52,"cartao_menos3":48},
    "PL": {"esc":10.2,"cartao":2.6,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa_gk":3.4,"gols":2.8,
           "vit_casa":48,"vit_fora":30,"empate":22,
           "mais15":82,"menos15":18,"mais25":64,"menos25":36,"menos35":76,
           "esc_mais75":70,"esc_menos125":86,
           "chute_mais95":55,"chute_menos95":45,
           "defesa_mais35":50,"defesa_menos35":50,
           "cartao_mais3":50,"cartao_menos3":50}
}

LIGAS = {
    "⚽ Todas": "TODAS","🇧🇷 Série A":"BSA","🇧🇷 Série B":"BRB","🏆 Champions":"CL",
    "🏴 Premier League":"PL"
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
                    except:
                        pass
        except:
            pass
    return lista

@st.cache_data(ttl=3600)
def ultimos_5(time_id):
    time.sleep(0.3)
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        dados = r.json().get("matches", [])
        if dados:
            return dados
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=HEADERS, params={"limit":10}, timeout=15)
        return [j for j in r.json().get("matches", []) if j.get("status") == "FINISHED"][:5]
    except:
        return []

# ==============================
# 🧮 CÁLCULO COMPLETO
# ==============================
def calcular_base(time_id, sigla, eh_casa=False):
    try:
        jogos = ultimos_5(time_id)
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        
        if not jogos:
            if eh_casa:
                return {"pV":med["vit_casa"],"pE":med["empate"],"pD":med["vit_fora"],"mg":med["gols"],
                        "mais15":med["mais15"],"menos15":med["menos15"],
                        "mais25":med["mais25"],"menos25":med["menos25"],
                        "menos35":med["menos35"],
                        "esc_mais75":med["esc_mais75"],"esc_menos125":med["esc_menos125"],
                        "chute_mais95":med["chute_mais95"],"chute_menos95":med["chute_menos95"],
                        "defesa_mais35":med["defesa_mais35"],"defesa_menos35":med["defesa_menos35"],
                        "cartao_mais3":med["cartao_mais3"],"cartao_menos3":med["cartao_menos3"],
                        "amb":50,"esc":med["esc"],"cartao":med["cartao"],
                        "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],"defesa_gk":med["defesa_gk"],
                        "resumo":["📊 Média da Liga"]*5,"placares":["Sem dados → Média"]}
            else:
                return {"pV":med["vit_fora"],"pE":med["empate"],"pD":med["vit_casa"],"mg":med["gols"],
                        "mais15":med["mais15"],"menos15":med["menos15"],
                        "mais25":med["mais25"],"menos25":med["menos25"],
                        "menos35":med["menos35"],
                        "esc_mais75":med["esc_mais75"],"esc_menos125":med["esc_menos125"],
                        "chute_mais95":med["chute_mais95"],"chute_menos95":med["chute_menos95"],
                        "defesa_mais35":med["defesa_mais35"],"defesa_menos35":med["defesa_menos35"],
                        "cartao_mais3":med["cartao_mais3"],"cartao_menos3":med["cartao_menos3"],
                        "amb":50,"esc":med["esc"],"cartao":med["cartao"],
                        "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],"defesa_gk":med["defesa_gk"],
                        "resumo":["📊 Média da Liga"]*5,"placares":["Sem dados → Média"]}
        
        v = e = d = gf = gs = amb = 0
        resumo = []
        placares = []
        total_cartao = 0
        for j in jogos:
            try:
                cid = j["homeTeam"]["id"]
                gc = j["score"]["fullTime"].get("home", 0) or 0
                ga = j["score"]["fullTime"].get("away", 0) or 0
                if cid == time_id:
                    gf += gc
                    gs += ga
                    if gc > ga:
                        v += 1
                        resumo.append("✅")
                    elif gc == ga:
                        e += 1
                        resumo.append("⚖️")
                    else:
                        d += 1
                        resumo.append("❌")
                    placares.append(f"{gc}x{ga}")
                else:
                    gf += ga
                    gs += gc
                    if ga > gc:
                        v += 1
                        resumo.append("✅")
                    elif ga == gc:
                        e += 1
                        resumo.append("⚖️")
                    else:
                        d += 1
                        resumo.append("❌")
                    placares.append(f"{ga}x{gc}")
                if gc > 0 and ga > 0:
                    amb += 1
                total_cartao += med["cartao"] / 5
            except:
                continue
        
        t = len(jogos)
        if t == 0:
            return calcular_base(time_id, sigla, eh_casa)
            
        media_gols_time = (gf + gs) / t
        fator_gols = media_gols_time / med["gols"] if med["gols"] > 0 else 1
        fator_esc = media_gols_time / med["gols"] if med["gols"] > 0 else 1
        fator_chute = media_gols_time / med["gols"] if med["gols"] > 0 else 1
        fator_defesa = med["gols"] / media_gols_time if media_gols_time > 0 else 1
        
        pv_base = (v / t) * 100
        pe_base = (e / t) * 100
        pd_base = (d / t) * 100
        
        if eh_casa:
            pv_base *= 1.15
            pd_base *= 0.90
        else:
            pd_base *= 1.10
            pv_base *= 0.95
        
        pv_base *= fator_gols
        pd_base *= fator_gols
        
        total = pv_base + pe_base + pd_base
        if total == 0:
            total = 1
        pv = round(pv_base / total * 100, 1)
        pe = round(pe_base / total * 100, 1)
        pd = round(pd_base / total * 100, 1)
        
        mais15 = round(med["mais15"] * fator_gols, 0)
        menos15 = round(100 - mais15, 0)
        mais25 = round(med["mais25"] * fator_gols, 0)
        menos25 = round(100 - mais25, 0)
        menos35 = round(med["menos35"] / fator_gols if fator_gols > 0 else med["menos35"], 0)
        
        esc_mais75 = round(med["esc_mais75"] * fator_esc, 0)
        esc_menos125 = round(med["esc_menos125"] / fator_esc if fator_esc > 0 else med["esc_menos125"], 0)
        
        chute_mais95 = round(med["chute_mais95"] * fator_chute, 0)
        chute_menos95 = round(100 - chute_mais95, 0)
        
        defesa_mais35 = round(med["defesa_mais35"] * fator_defesa, 0)
        defesa_menos35 = round(100 - defesa_mais35, 0)
        
        cartao_mais3 = round(med["cartao_mais3"] * (total_cartao / med["cartao"] if med["cartao"] > 0 else 1), 0)
        cartao_menos3 = round(100 - cartao_mais3, 0)
        
        return {
            "pV":pv,"pE":pe,"pD":pd,
            "mg":round(media_gols_time, 2),
            "mais15":mais15,"menos15":menos15,
            "mais25":mais25,"menos25":menos25,
            "menos35":menos35,
            "esc_mais75":esc_mais75,"esc_menos125":esc_menos125,
            "chute_mais95":chute_mais95,"chute_menos95":chute_menos95,
            "defesa_mais35":defesa_mais35,"defesa_menos35":defesa_menos35,
            "cartao_mais3":cartao_mais3,"cartao_menos3":cartao_menos3,
            "amb":round((amb/t)*100,0),
            "esc":round(med["esc"]*fator_gols,1),
            "cartao":round(total_cartao,1),
            "fin":round(med["fin"]*fator_gols,1),
            "chute_gol":round(med["chute_gol"]*fator_gols,1),
            "fal":round(med["fal"]*fator_gols,1),
            "defesa_gk":round(med["defesa_gk"]*fator_defesa,1),
            "resumo":resumo,"placares":placares
        }
    except Exception as e:
        st.error(f"Erro no cálculo: {str(e)}")
        med = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
        return {"pV":med["vit_casa"] if eh_casa else med["vit_fora"],"pE":med["empate"],"pD":med["vit_fora"] if eh_casa else med["vit_casa"],
                "mg":med["gols"],"mais15":med["mais15"],"menos15":med["menos15"],
                "mais25":med["mais25"],"menos25":med["menos25"],"menos35":med["menos35"],
                "esc_mais75":med["esc_mais75"],"esc_menos125":med["esc_menos125"],
                "chute_mais95":med["chute_mais95"],"chute_menos95":med["chute_menos95"],
                "defesa_mais35":med["defesa_mais35"],"defesa_menos35":med["defesa_menos35"],
                "cartao_mais3":med["cartao_mais3"],"cartao_menos3":med["cartao_menos3"],
                "amb":50,"esc":med["esc"],"cartao":med["cartao"],
                "fin":med["fin"],"chute_gol":med["chute_gol"],"fal":med["fal"],"defesa_gk":med["defesa_gk"],
                "resumo":["📊 Média da Liga"]*5,"placares":["Erro → Média"]}

def dupla(v, e, d):
    return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

# ==============================
# 📝 MENSAGEM COMPLETA
# ==============================
def msg_jogo(casa_nome, fora_nome, dt, dc, df, dup, mg, 
             mais15, menos15, mais25, menos25, menos35,
             esc_mais75, esc_menos125,
             chute_mais95, chute_menos95,
             defesa_mais35, defesa_menos35,
             amb, cartao_mais, cartao_menos, 
             total_esc, total_fal, total_fin, total_chute, total_defesa):
    return f"""
⚽ *{casa_nome} 🆚 {fora_nome}* | {dt.strftime('%d/%m %H:%M')}

📊 *Probabilidades:*
✅ {casa_nome}: {dc['pV']}% | ⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}% | ✅ {fora_nome}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 *GOLS:*
⚽ Média: {mg}
🔢 Mais 1.5: {mais15}% | Menos 1.5: {menos15}%
🔢 Mais 2.5: {mais25}% | Menos 2.5: {menos25}%
🔢 Menos 3.5: {menos35}%
🔄 Ambos Marcam: {amb}%

🎯 *DADOS INDIVIDUAIS:*
🏠 {casa_nome}:
  • Chutes ao Gol: {dc['chute_gol']} | Finalizações: {dc['fin']} | Faltas: {dc['fal']}
  • Escanteios: {dc['esc']} | Defesas: {dc['defesa_gk']} | Cartões: {dc['cartao']}
  • Últimos 5: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}

✈️ {fora_nome}:
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
            agora = datetime.now()
            if agora.strftime("%H:%M") == HORARIO_ALERTA:
                jogos = buscar_jogos("TODAS", DIAS_BUSCA)
                for j in jogos:
                    try:
                        dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                        dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], eh_casa=True)
                        df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], eh_casa=False)
                        dup = dupla(dc['pV'],dc['pE'],dc['pD'])
                        mg = round((dc['mg']+df['mg'])/2,2)
                        mais15 = round((dc['mais15']+df['mais15'])/2,0)
                        menos15 = round((dc['menos15']+df['menos15'])/2,0)
                        mais25 = round((dc['mais25']+df['mais25'])/2,0)
                        menos25 = round((dc['menos25']+df['menos25'])/2,0)
                        menos35 = round((dc['menos35']+df['menos35'])/2,0)
                        esc_mais75 = round((dc['esc_mais75']+df['esc_mais75'])/2,0)
                        esc_menos125 = round((dc['esc_menos125']+df['esc_menos125'])/2,0)
                        chute_mais95 = round((dc['chute_mais95']+df['chute_mais95'])/2,0)
                        chute_menos95 = round((dc['chute_menos95']+df['chute_menos95'])/2,0)
                        defesa_mais35 = round((dc['defesa_mais35']+df['defesa_mais35'])/2,0)
                        defesa_menos35 = round((dc['defesa_menos35']+df['defesa_menos35'])/2,0)
                        amb = round((dc['amb']+df['amb'])/2,0)
                        cartao_mais = round((dc['cartao_mais3']+df['cartao_mais3'])/2,0)
                        cartao_menos = round((dc['cartao_menos3']+df['cartao_menos3'])/2,0)
                        total_esc = round((dc['esc']+df['esc'])/2,1)
                        total_fal = round(dc['fal'] + df['fal'],1)
                        total_fin = round(dc['fin'] + df['fin'],1)
                        total_chute = round(dc['chute_gol'] + df['chute_gol'],1)
                        total_defesa = round((dc['defesa_gk']+df['defesa_gk'])/2,1)
                        
                        msg = msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg,
                                       mais15, menos15, mais25, menos25, menos35,
                                       esc_mais75, esc_menos125,
                                       chute_mais95, chute_menos95,
                                       defesa_mais35, defesa_menos35,
                                       amb, cartao_mais, cartao_menos,
                                       total_esc, total_fal, total_fin, total_chute, total_defesa)
                        enviar_telegram(msg)
                        time.sleep(1)
                    except:
                        pass
        except:
            pass
        time.sleep(30)
threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ INTERFACE
# ==============================
esc = st.selectbox("Liga", list(LIGAS.keys()))
dias = st.number_input("Dias à frente", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar"):
    st.cache_data.clear()
    jogos = buscar_jogos(LIGAS[esc], dias)
    if not jogos:
        st.info("Nenhum jogo encontrado.")
    else:
        st.success(f"✅ {len(jogos)} jogos carregados!")
        enviados = 0
        for j in jogos:
            try:
                dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                dc = calcular_base(j["homeTeam"]["id"], j["competition"]["code"], eh_casa=True)
                df = calcular_base(j["awayTeam"]["id"], j["competition"]["code"], eh_casa=False)
                dup = dupla(dc['pV'],dc['pE'],dc['pD'])
                mg = round((dc['mg']+df['mg'])/2,2)
                mais15 = round((dc['mais15']+df['mais15'])/2,0)
                menos15 = round((dc['menos15']+df['menos15'])/2,0)
                mais25 = round((dc['mais25']+df['mais25'])/2,0)
                menos25 = round((dc['menos25']+df['menos25'])/2,0)
                menos35 = round((dc['menos35']+df['menos35'])/2,0)
                esc_mais75 = round((dc['esc_mais75']+df['esc_mais75'])/2,0)
                esc_menos125 = round((dc['esc_menos125']+df['esc_menos125'])/2,0)
                chute_mais95 = round((dc['chute_mais95']+df['chute_mais95'])/2,0)
                chute_menos95 = round((dc['chute_menos95']+df['chute_menos95'])/2,0)
                defesa_mais35 = round((dc['defesa_mais35']+df['defesa_mais35'])/2,0)
                defesa_menos35 = round((dc['defesa_menos35']+df['defesa_menos35'])/2,0)
                amb = round((dc['amb']+df['amb'])/2,0)
                cartao_mais = round((dc['cartao_mais3']+df['cartao_mais3'])/2,0)
                cartao_menos = round((dc['cartao_menos3']+df['cartao_menos3'])/2,0)
                total_esc = round((dc['esc']+df['esc'])/2,1)
                total_fal = round(dc['fal'] + df['fal'],1)
                total_fin = round(dc['fin'] + df['fin'],1)
                total_chute = round(dc['chute_gol'] + df['chute_gol'],1)
                total_defesa = round((dc['defesa_gk']+df['defesa_gk'])/2,1)
                
                msg = msg_jogo(j["homeTeam"]["name"], j["awayTeam"]["name"], dt, dc, df, dup, mg,
                               mais15, menos15, mais25, menos25, menos35,
                               esc_mais75, esc_menos125,
                               chute_mais95, chute_menos95,
                               defesa_mais35, defesa_menos35,
                               amb, cartao_mais, cartao_menos,
                               total_esc, total_fal, total_fin, total_chute, total_defesa)
                
                st.subheader(f"⚽ {j['homeTeam']['name']} 🆚 {j['awayTeam']['name']}")
                st.write(f"🏠 Casa: {dc['pV']}% | Chutes: {dc['chute_gol']} | Últimos: {' '.join(dc['resumo'])}")
                st.write(f"✈️ Fora: {df['pD']}% | Chutes: {df['chute_gol']} | Últimos: {' '.join(df['resumo'])}")
                st.divider()
                
                ok, aviso = enviar_telegram(msg)
                if ok:
                    enviados +=1
                else:
                    st.warning(f"⚠️ {j['homeTeam']['name']} x {j['awayTeam']['name']}: {aviso}")
                time.sleep(1)
            except Exception as e:
                st.warning(f"⚠️ Erro no jogo: {str(e)}")
                continue
        
        st.success(f"✅ Concluído! {enviados}/{len(jogos)} enviados!")

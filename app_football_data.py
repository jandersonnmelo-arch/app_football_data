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
API_KEY = st.secrets["CHAVE_FD"]
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

# ⏰ AJUSTE AQUI O HORÁRIO DO ALERTA
HORARIO_ALERTA = "08:30"
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 📤 FUNÇÃO ENVIO TELEGRAM
# ==============================
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=10)
        return True
    except Exception as e:
        print(f"Erro envio: {e}")
        return False

# ==============================
# 🏆 TODAS AS LIGAS E MÉDIAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"laterais":8.5,"tiro_meta":4.7,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa":3.8},
    "BRB": {"esc":8.5,"laterais":9.0,"tiro_meta":5.0,"fin":9.0,"chute_gol":3.5,"fal":27.5,"defesa":4.2},
    "WC": {"esc":8.8,"laterais":7.0,"tiro_meta":4.2,"fin":10.0,"chute_gol":4.5,"fal":24.0,"defesa":3.5},
    "CL": {"esc":9.5,"laterais":7.2,"tiro_meta":4.3,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa":3.4},
    "BL1": {"esc":9.8,"laterais":6.5,"tiro_meta":3.7,"fin":12.5,"chute_gol":5.8,"fal":21.0,"defesa":2.8},
    "ED": {"esc":9.2,"laterais":7.5,"tiro_meta":4.5,"fin":11.0,"chute_gol":5.0,"fal":22.5,"defesa":3.2},
    "PD": {"esc":9.0,"laterais":7.8,"tiro_meta":4.5,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa":3.6},
    "FL1": {"esc":9.5,"laterais":7.0,"tiro_meta":4.2,"fin":10.8,"chute_gol":4.8,"fal":23.0,"defesa":3.3},
    "ELC": {"esc":8.5,"laterais":8.0,"tiro_meta":4.8,"fin":9.2,"chute_gol":4.0,"fal":25.5,"defesa":3.9},
    "PPL": {"esc":8.8,"laterais":7.8,"tiro_meta":4.6,"fin":10.2,"chute_gol":4.3,"fal":24.5,"defesa":3.7},
    "EC": {"esc":9.0,"laterais":7.5,"tiro_meta":4.4,"fin":10.5,"chute_gol":4.6,"fal":23.0,"defesa":3.4},
    "SA": {"esc":8.7,"laterais":9.2,"tiro_meta":5.0,"fin":9.5,"chute_gol":3.8,"fal":25.5,"defesa":4.0},
    "PL": {"esc":10.2,"laterais":6.8,"tiro_meta":4.0,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa":3.1}
}

LIGAS = {
    "⚽ Todas as Ligas": "TODAS",
    "🌍 Copa do Mundo": "WC",
    "🏆 Champions League": "CL",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏴 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA",
    "🇫🇷 Ligue 1": "FL1",
    "🇳🇱 Eredivisie": "ED",
    "🇵🇹 Primeira Liga": "PPL",
    "🏆 Eurocopa": "EC",
    "🏴 Championship": "ELC"
}

TODAS_SIGLAS = ["BSA","BRB","WC","CL","BL1","ED","PD","FL1","ELC","PPL","EC","SA","PL"]

# ==============================
# 🔍 BUSCA COM TRATAMENTO DE ERRO
# ==============================
@st.cache_data(ttl=3600)
def buscar_jogos(sigla, dias):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    lista_jogos = []
    lista_busca = TODAS_SIGLAS if sigla == "TODAS" else [sigla]
    
    for s in lista_busca:
        try:
            r = requests.get(
                f"https://api.football-data.org/v4/competitions/{s}/matches",
                headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15
            )
            if r.status_code == 200:
                dados = r.json().get("matches",[])
                for j in dados:
                    try:
                        dt_jogo = datetime.fromisoformat(j["utcDate"].replace("Z",""))
                        if dt_jogo.date() <= hoje + timedelta(days=dias):
                            lista_jogos.append(j)
                    except:
                        continue
        except:
            continue
    return lista_jogos

@st.cache_data(ttl=3600)
def ultimos_5_jogos(time_id, sigla):
    time.sleep(0.3)
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{time_id}/matches",
            headers=HEADERS, params={"competitions":sigla,"status":"FINISHED","limit":5}, timeout=15
        )
        return r.json().get("matches", [])
    except:
        return []

def calcular_base(time_id, sigla):
    jogos = ultimos_5_jogos(time_id, sigla)
    medias = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    
    if not jogos:
        return {"pV":33.3,"pE":33.3,"pD":33.4,"mg":2.5,"ma25":50,"amb":50,
                "esc":medias["esc"],"laterais":medias["laterais"],"tiro_meta":medias["tiro_meta"],
                "fin":medias["fin"],"chute_gol":medias["chute_gol"],"fal":medias["fal"],"defesa":medias["defesa"],"resumo":["❔"]*5}
    
    v=e=d=gf=gs=amb=0; resumo=[]
    for j in jogos:
        try:
            cid = j.get("homeTeam",{}).get("id")
            gc = j.get("score",{}).get("fullTime",{}).get("home",0) or 0
            ga = j.get("score",{}).get("fullTime",{}).get("away",0) or 0
            if cid == time_id:
                gf+=gc; gs+=ga
                if gc>ga:v+=1;resumo.append("✅")
                elif gc==ga:e+=1;resumo.append("⚖️")
                else:d+=1;resumo.append("❌")
            else:
                gf+=ga; gs+=gc
                if ga>gc:v+=1;resumo.append("✅")
                elif ga==gc:e+=1;resumo.append("⚖️")
                else:d+=1;resumo.append("❌")
            if gc>0 and ga>0:amb+=1
        except:
            continue
    t=len(jogos)
    if t==0:
        return {"pV":33.3,"pE":33.3,"pD":33.4,"mg":2.5,"ma25":50,"amb":50,
                "esc":medias["esc"],"laterais":medias["laterais"],"tiro_meta":medias["tiro_meta"],
                "fin":medias["fin"],"chute_gol":medias["chute_gol"],"fal":medias["fal"],"defesa":medias["defesa"],"resumo":["❔"]*5}
    
    fator_a = (gf/t)/1.5; fator_d = (gs/t)/1.5
    return {
        "pV":round((v/t)*100,1),"pE":round((e/t)*100,1),"pD":round((d/t)*100,1),
        "mg":round((gf+gs)/t,2),"ma25":round(70 if (gf+gs)/t>2.5 else 45,0),"amb":round((amb/t)*100,0),
        "esc":round(medias["esc"]*fator_a,1),"laterais":round(medias["laterais"]*fator_d,1),
        "tiro_meta":round(medias["tiro_meta"]*fator_d,1),"fin":round(medias["fin"]*fator_a,1),
        "chute_gol":round(medias["chute_gol"]*fator_a,1),"fal":round(medias["fal"]*fator_d,1),
        "defesa":round(medias["defesa"]*fator_d,1),"resumo":resumo
    }

def dupla_chance(pV,pE,pD):
    return {"1X":round(pV+pE,1),"X2":round(pE+pD,1),"12":round(pV+pD,1)}

# ==============================
# 📝 MENSAGEM COM CHUTES E FINALIZAÇÕES ADICIONADOS
# ==============================
def gerar_mensagem_jogo(casa, fora, dt, dc, df, dup, media_gols, prob_mais25, prob_ambos, total_esc, total_fal, total_fin, total_chute_gol, conf):
    return f"""
⚽ *{casa['name']} 🆚 {fora['name']}*
📅 {dt.strftime('%d/%m às %H:%M')}

📊 *Probabilidades:*
✅ {casa['name']}: {dc['pV']}%
⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%
✅ {fora['name']}: {df['pD']}%

🔀 *Dupla Chance:*
1X: {dup['1X']}%
X2: {dup['X2']}%
12: {dup['12']}%

📈 *Métricas do Jogo:*
⚽ Média Gols: {media_gols}
🔢 Mais 2.5 Gols: {prob_mais25}%
🔄 Ambos Marcam: {prob_ambos}%
📐 Escanteios: {total_esc}
👟 Faltas: {total_fal}
🎯 Finalizações: {total_fin}
⚽ Chutes ao Gol: {total_chute_gol}

📋 *Últimos 5 Jogos:*
🟢 {casa['name']}: {' '.join(dc['resumo'])}
🔴 {fora['name']}: {' '.join(df['resumo'])}

{'🚨 *ALTA CONFIANÇA ACIMA DE 70%!*' if conf >=70 else ''}
---
"""

# ==============================
# 🤖 ENVIO AUTOMÁTICO
# ==============================
def servico_automatico():
    while True:
        try:
            if datetime.now().strftime("%H:%M") == HORARIO_ALERTA:
                jogos = buscar_jogos("TODAS", DIAS_BUSCA)
                msg = f"🔔 *RELATÓRIO AUTOMÁTICO DIÁRIO*\n🕒 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n📅 Período: {DIAS_BUSCA} dias à frente\n\n"
                
                for jogo in jogos:
                    try:
                        sigla_j = jogo["competition"]["code"]
                        casa = jogo["homeTeam"]
                        fora = jogo["awayTeam"]
                        dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","")) - timedelta(hours=4)
                        dc = calcular_base(casa["id"], sigla_j)
                        df = calcular_base(fora["id"], sigla_j)
                        dup = dupla_chance(dc["pV"],dc["pE"],dc["pD"])
                        media_gols = round((dc['mg']+df['mg'])/2,2)
                        prob_mais25 = round((dc['ma25']+df['ma25'])/2,0)
                        prob_ambos = round((dc['amb']+df['amb'])/2,0)
                        total_esc = round((dc['esc']+df['esc'])/2,1)
                        total_fal = round((dc['fal']+df['fal'])/2,1)
                        total_fin = round((dc['fin']+df['fin'])/2,1)
                        total_chute_gol = round((dc['chute_gol']+df['chute_gol'])/2,1)
                        conf = max(dc['pV'], df['pD'])
                        msg += gerar_mensagem_jogo(casa, fora, dt, dc, df, dup, media_gols, prob_mais25, prob_ambos, total_esc, total_fal, total_fin, total_chute_gol, conf)
                    except:
                        continue
                enviar_telegram(msg)
                time.sleep(120)
        except:
            pass
        time.sleep(30)

threading.Thread(target=servico_automatico, daemon=True).start()

# ==============================
# 🖥️ INTERFACE PRINCIPAL
# ==============================
escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
sigla = LIGAS[escolha]
dias_usuario = st.number_input("Buscar quantos dias à frente?", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar Agora"):
    st.cache_data.clear()
    jogos = buscar_jogos(sigla, dias_usuario)
    
    if not jogos:
        st.info("ℹ️ Nenhum jogo encontrado ou aguarde atualização.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        msg_relatorio = f"🔔 *RELATÓRIO SOLICITADO*\n🕒 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n📅 Período: {dias_usuario} dias à frente\n\n"
        
        for jogo in jogos:
            try:
                sigla_j = jogo["competition"]["code"]
                casa = jogo["homeTeam"]
                fora = jogo["awayTeam"]
                dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","")) - timedelta(hours=4)
                dc = calcular_base(casa["id"], sigla_j)
                df = calcular_base(fora["id"], sigla_j)
                dup = dupla_chance(dc["pV"],dc["pE"],dc["pD"])
                media_gols = round((dc['mg']+df['mg'])/2,2)
                prob_mais25 = round((dc['ma25']+df['ma25'])/2,0)
                prob_ambos = round((dc['amb']+df['amb'])/2,0)
                total_esc = round((dc['esc']+df['esc'])/2,1)
                total_fal = round((dc['fal']+df['fal'])/2,1)
                total_fin = round((dc['fin']+df['fin'])/2,1)
                total_chute_gol = round((dc['chute_gol']+df['chute_gol'])/2,1)
                conf = max(dc['pV'], df['pD'])

                msg_relatorio += gerar_mensagem_jogo(casa, fora, dt, dc, df, dup, media_gols, prob_mais25, prob_ambos, total_esc, total_fal, total_fin, total_chute_gol, conf)

                st.markdown("---")
                st.subheader(f"⚽ {casa['name']} 🆚 {fora['name']} | {dt.strftime('%d/%m %H:%M')}")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📈 Probabilidades Gerais")
                    st.write(f"✅ {casa['name']}: {dc['pV']}%")
                    st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
                    st.write(f"✅ {fora['name']}: {df['pD']}%")
                    st.divider()
                    st.subheader("🔀 Dupla Chance")
                    st.write(f"1X: {dup['1X']}%")
                    st.write(f"X2: {dup['X2']}%")
                    st.write(f"12: {dup['12']}%")
                    st.divider()
                    st.subheader("📊 Últimos 5 Jogos")
                    st.write(f"🟢 {casa['name']}: {' '.join(dc['resumo'])}")
                    st.write(f"🔴 {fora['name']}: {' '.join(df['resumo'])}")

                with col2:
                    st.subheader("📐 Estatísticas por Equipe")
                    st.write(f"🏠 {casa['name']}")
                    st.write(f"Escanteios: {dc['esc']} | Laterais: {dc['laterais']} | Tiros Meta: {dc['tiro_meta']}")
                    st.write(f"Finalizações: {dc['fin']} | Chutes Gol: {dc['chute_gol']} | Faltas: {dc['fal']}")
                    st.write(f"🚩 {fora['name']}")
                    st.write(f"Escanteios: {df['esc']} | Laterais: {df['laterais']} | Tiros Meta: {df['tiro_meta']}")
                    st.write(f"Finalizações: {df['fin']} | Chutes Gol: {df['chute_gol']} | Faltas: {df['fal']}")

                st.markdown("---")
                st.subheader("📊 ESTIMATIVA GERAL DO JOGO")
                st.write(f"⚽ Média Gols: {media_gols} | Mais 2.5: {prob_mais25}% | Ambos Marcam: {prob_ambos}%")
                st.write(f"📐 Escanteios: {total_esc} | Faltas: {total_fal}")
                st.write(f"🎯 Finalizações: {total_fin} | ⚽ Chutes ao Gol: {total_chute_gol}")

                if conf >=70:
                    st.error("🚨 ALTA CONFIANÇA ACIMA DE 70%!")
            except:
                continue
        
        enviar_telegram(msg_relatorio)
        st.success("✅ Análise completa enviada ao Telegram!")
                

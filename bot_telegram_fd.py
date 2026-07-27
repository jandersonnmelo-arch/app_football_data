import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import schedule
import threading

# ==============================
# 🔴 CONFIGURAÇÕES
# ==============================
BOT_TOKEN = "8289316862:AAFIhpQqoc2kRlW6B6I5zk5pqmecXaPMpmw"
CHAT_ID = "1100260912"
API_KEY = st.secrets["CHAVE_FD"]
HEADERS = {"X-Auth-Token": API_KEY}

# Horário do alerta: 07:00 MANAUS (UTC-4)
HORARIO_ALERTA = "07:00"

def enviar_telegram(mensagem):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

# ==============================
# DEMAIS FUNÇÕES (IGUAIS ÀS ANTERIORES)
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"laterais":8.5,"tiro_meta":4.7,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa":3.8},
    "BRB": {"esc":8.5,"laterais":9.0,"tiro_meta":5.0,"fin":9.0,"chute_gol":3.5,"fal":27.5,"defesa":4.2},
    "CLI": {"esc":9.5,"laterais":7.2,"tiro_meta":4.3,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa":3.4},
    "PL": {"esc":10.2,"laterais":6.8,"tiro_meta":4.0,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa":3.1},
    "PD": {"esc":9.0,"laterais":7.8,"tiro_meta":4.5,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa":3.6},
    "BL1": {"esc":9.8,"laterais":6.5,"tiro_meta":3.7,"fin":12.5,"chute_gol":5.8,"fal":21.0,"defesa":2.8},
    "SA": {"esc":8.7,"laterais":9.2,"tiro_meta":5.0,"fin":9.5,"chute_gol":3.8,"fal":25.5,"defesa":4.0}
}

LIGAS = {
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏆 Libertadores": "CLI",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA"
}

@st.cache_data(ttl=3600)
def buscar_jogos(sigla):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    try:
        r = requests.get(f"https://api.football-data.org/v4/competitions/{sigla}/matches", headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
        if r.status_code == 429: return []
        return [j for j in r.json().get("matches",[]) if datetime.fromisoformat(j["utcDate"].replace("Z","")).date() <= hoje + timedelta(days=7)]
    except: return []

@st.cache_data(ttl=3600)
def ultimos_5_jogos(time_id, sigla):
    time.sleep(0.3)
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches", headers=HEADERS, params={"competitions":sigla,"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except: return []

def calcular_base(time_id, sigla):
    jogos = ultimos_5_jogos(time_id, sigla)
    medias = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    if not jogos:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"esc":medias["esc"],"laterais":medias["laterais"],"tiro_meta":medias["tiro_meta"],"fin":medias["fin"],"chute_gol":medias["chute_gol"],"fal":medias["fal"],"defesa":medias["defesa"],"resumo":[]}
    v=e=d=gf=gs=amb=0; resumo=[]
    for j in jogos:
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
    t=len(jogos)
    fator_a = (gf/t)/1.5; fator_d = (gs/t)/1.5
    return {"pV":round((v/t)*100,1),"pE":round((e/t)*100,1),"pD":round((d/t)*100,1),"mg":round((gf+gs)/t,2),"ma25":round(70 if (gf+gs)/t>2.5 else 45,0),"amb":round((amb/t)*100,0),"esc":round(medias["esc"]*fator_a,1),"laterais":round(medias["laterais"]*fator_d,1),"tiro_meta":round(medias["tiro_meta"]*fator_d,1),"fin":round(medias["fin"]*fator_a,1),"chute_gol":round(medias["chute_gol"]*fator_a,1),"fal":round(medias["fal"]*fator_d,1),"defesa":round(medias["defesa"]*fator_d,1),"resumo":resumo}

def dupla_chance(pV,pE,pD):
    return {"1X":round(pV+pE,1),"X2":round(pE+pD,1),"12":round(pV+pD,1)}

def prob_estatistica(valor, media):
    if valor <=0 or media <=0: return 50
    dif = (valor/media)-1
    return max(30, min(80, round(50 + dif*25, 0)))

# ==============================
# ⏰ FUNÇÃO QUE RODA AUTOMATICAMENTE
# ==============================
def verificar_e_enviar():
    horario_agora = datetime.now().strftime("%d/%m %H:%M")
    mensagem_inicio = f"🔔 Verificação automática executada às {horario_agora} (horário Manaus)\n\n"
    tem_alerta = False

    for nome_liga, sigla in LIGAS.items():
        jogos = buscar_jogos(sigla)
        for jogo in jogos:
            casa = jogo.get("homeTeam",{})
            fora = jogo.get("awayTeam",{})
            nome_casa = casa.get('name')
            nome_fora = fora.get('name')
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            dc = calcular_base(casa.get("id"), sigla)
            df = calcular_base(fora.get("id"), sigla)
            confianca_max = max(dc['pV'], df['pD'])

            if confianca_max >=70:
                tem_alerta = True
                media_gols = round((dc['mg'] + df['mg'])/2,2)
                prob_mais25 = round((dc['ma25'] + df['ma25'])/2,0)
                prob_ambos = round((dc['amb'] + df['amb'])/2,0)
                mensagem_inicio += f"""🚨 *ALTA CONFIANÇA* ⚽
{nome_casa} 🆚 {nome_fora}
📅 {dt.strftime('%d/%m às %H:%M')}
✅ {nome_casa}: {dc['pV']}% | ✅ {nome_fora}: {df['pD']}%
⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%
🔢 Média Gols: {media_gols} | +2.5: {prob_mais25}% | Ambos: {prob_ambos}%
---
"""
    if tem_alerta:
        enviar_telegram(mensagem_inicio)
    else:
        enviar_telegram(f"🔔 Verificação das {HORARIO_ALERTA}: Nenhum jogo com confiança acima de 70% encontrado.")

# Inicia o agendador em segundo plano
def rodar_agendador():
    schedule.every().day.at(HORARIO_ALERTA).do(verificar_e_enviar)
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=rodar_agendador, daemon=True).start()

# ==============================
# INTERFACE VISUAL NO STREAMLIT
# ==============================
st.set_page_config(page_title="Análise + Alerta Automático", page_icon="⏰", layout="wide")
st.title("⚽ Análise + Alerta Automático às 07h | Manaus")
st.info(f"✅ Agendamento ativo: Verificação diária às {HORARIO_ALERTA} horário local.")

try:
    escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
    sigla = LIGAS[escolha]
    medias_base = MEDIAS_LIGA[sigla]

    jogos = buscar_jogos(sigla)
    if not jogos:
        st.info("ℹ️ Nenhum jogo encontrado ou limite temporário.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        for jogo in jogos:
            casa = jogo.get("homeTeam",{})
            fora = jogo.get("awayTeam",{})
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            nome_casa = casa.get('name')
            nome_fora = fora.get('name')
            
            st.markdown("---")
            st.subheader(f"⚽ {nome_casa} 🆚 {nome_fora} | {dt.strftime('%d/%m %H:%M')}")

            dc = calcular_base(casa.get("id"), sigla)
            df = calcular_base(fora.get("id"), sigla)
            dup = dupla_chance(dc["pV"],dc["pE"],dc["pD"])

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Probabilidades")
                st.write(f"✅ {nome_casa}: {dc['pV']}%")
                st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
                st.write(f"✅ {nome_fora}: {df['pD']}%")
                st.divider()
                st.subheader("🔀 Dupla Chance")
                st.write(f"1X: {dup['1X']}% | X2: {dup['X2']}% | 12: {dup['12']}%")
                st.divider()
                st.subheader("📊 Últimos 5")
                st.write(f"🟢 {nome_casa}: {' '.join(dc['resumo']) if dc['resumo'] else 'Sem dados'}")
                st.write(f"🔴 {nome_fora}: {' '.join(df['resumo']) if df['resumo'] else 'Sem dados'}")

            with col2:
                st.subheader("📐 Estatísticas")
                c1,c2 = st.columns(2)
                with c1:
                    st.write(f"🏠 {nome_casa}")
                    st.write(f"Escanteios: {dc['esc']} | Tiro Meta: {dc['tiro_meta']}")
                    st.write(f"Finalizações: {dc['fin']} | Chute Gol: {dc['chute_gol']}")
                    st.write(f"Faltas: {dc['fal']}")
                with c2:
                    st.write(f"🚩 {nome_fora}")
                    st.write(f"Escanteios: {df['esc']} | Tiro Meta: {df['tiro_meta']}")
                    st.write(f"Finalizações: {df['fin']} | Chute Gol: {df['chute_gol']}")
                    st.write(f"Faltas: {df['fal']}")

            st.markdown("---")
            total_esc = round((dc['esc'] + df['esc'])/2,1)
            total_tm = round((dc['tiro_meta'] + df['tiro_meta'])/2,1)
            total_fin = round((dc['fin'] + df['fin'])/2,1)
            total_cg = round((dc['chute_gol'] + df['chute_gol'])/2,1)
            media_gols = round((dc['mg'] + df['mg'])/2,2)
            pe = prob_estatistica(total_esc, medias_base['esc'])
            ptm = prob_estatistica(total_tm, medias_base['tiro_meta'])
            pfin = prob_estatistica(total_fin, medias_base['fin'])
            pcg = prob_estatistica(total_cg, medias_base['chute_gol'])

            st.subheader("📊 ESTIMATIVA TOTAL DO JOGO")
            t1,t2 = st.columns(2)
            with t1:
                st.write(f"📐 Escanteios: {total_esc} ({pe}%)")
                st.write(f"🚩 Tiro Meta: {total_tm} ({ptm}%)")
                st.write(f"👟 Finalizações: {total_fin} ({pfin}%)")
            with t2:
                st.write(f"🎯 Chute Gol: {total_cg} ({pcg}%)")
                st.write(f"⚽ Média Gols: {media_gols}")
                st.write(f"🔢 +2.5 Gols: {round((dc['ma25']+df['ma25'])/2,0)}%")

            if max(dc['pV'], df['pD']) >=70:
                st.error(f"🚨 ALTA CONFIANÇA ACIMA DE 70%!")

except Exception as e:
    st.error(f"Erro: {str(e)}")
            

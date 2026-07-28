import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="📊 Análise de Futebol", page_icon="⚽", layout="wide")
st.title("📊 Análise de Futebol | Validação de Resultados")

# 🔒 CHAVES OCULTAS
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves nos Secrets! Erro: {e}")
    st.stop()

LIMITE_CONFIANCA = 70
HEADERS = {"X-Auth-Token": API_KEY}
FUSO_MAN = ZoneInfo("America/Manaus")

# Controle de envio de validação
if "jogos_validados" not in st.session_state:
    st.session_state.jogos_validados = []

# ==============================
# 🏆 LIGAS + MÉDIAS + PERFIL DE JUÍZES
# ==============================
MEDIAS_LIGA = {
    "WC": {"esc":9.2,"cartao":3.0,"fin":10.8,"chute_gol":4.5,"fal":25.0,"defesa_gk":3.8,"gols":2.7,
           "tiro_meta":4.2,"laterais":8.0,"impedimentos":2.2,"vit_casa":47,"vit_fora":28,"empate":25,
           "juiz_tipo":"Equilibrado","juiz_media_cartao":3.2,"juiz_media_falta":26},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "tiro_meta":4.0,"laterais":7.8,"impedimentos":2.4,"vit_casa":48,"vit_fora":29,"empate":23,
           "juiz_tipo":"Rigoroso com faltas","juiz_media_cartao":3.5,"juiz_media_falta":28},
    "BL1": {"esc":9.8,"cartao":2.8,"fin":11.5,"chute_gol":5.0,"fal":24.0,"defesa_gk":3.4,"gols":3.1,
            "tiro_meta":3.9,"laterais":7.7,"impedimentos":2.1,"vit_casa":50,"vit_fora":27,"empate":23,
            "juiz_tipo":"Permissivo","juiz_media_cartao":2.5,"juiz_media_falta":23},
    "ERD": {"esc":9.3,"cartao":2.9,"fin":11.2,"chute_gol":4.9,"fal":24.5,"defesa_gk":3.6,"gols":3.0,
            "tiro_meta":4.1,"laterais":7.9,"impedimentos":2.3,"vit_casa":49,"vit_fora":28,"empate":23,
            "juiz_tipo":"Equilibrado","juiz_media_cartao":3.0,"juiz_media_falta":25},
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
           "tiro_meta":4.7,"laterais":8.5,"impedimentos":2.0,"vit_casa":45,"vit_fora":30,"empate":25,
           "juiz_tipo":"Rigoroso","juiz_media_cartao":3.8,"juiz_media_falta":29},
    "PD": {"esc":9.4,"cartao":3.1,"fin":10.5,"chute_gol":4.7,"fal":25.5,"defesa_gk":3.7,"gols":2.8,
           "tiro_meta":4.2,"laterais":8.0,"impedimentos":2.5,"vit_casa":47,"vit_fora":28,"empate":25,
           "juiz_tipo":"Muito rigoroso","juiz_media_cartao":4.0,"juiz_media_falta":30},
    "FL1": {"esc":9.1,"cartao":3.0,"fin":10.3,"chute_gol":4.6,"fal":25.0,"defesa_gk":3.8,"gols":2.7,
            "tiro_meta":4.3,"laterais":8.1,"impedimentos":2.3,"vit_casa":46,"vit_fora":29,"empate":25,
            "juiz_tipo":"Equilibrado","juiz_media_cartao":3.2,"juiz_media_falta":26},
    "ELC": {"esc":8.7,"cartao":3.4,"fin":9.8,"chute_gol":4.2,"fal":27.5,"defesa_gk":4.1,"gols":2.5,
            "tiro_meta":4.6,"laterais":8.4,"impedimentos":1.9,"vit_casa":44,"vit_fora":28,"empate":28,
            "juiz_tipo":"Rigoroso","juiz_media_cartao":3.7,"juiz_media_falta":28},
    "PPL": {"esc":8.8,"cartao":3.3,"fin":9.7,"chute_gol":4.1,"fal":27.0,"defesa_gk":4.0,"gols":2.6,
            "tiro_meta":4.5,"laterais":8.3,"impedimentos":2.0,"vit_casa":45,"vit_fora":27,"empate":28,
            "juiz_tipo":"Equilibrado","juiz_media_cartao":3.3,"juiz_media_falta":27},
    "EC": {"esc":9.2,"cartao":3.0,"fin":10.7,"chute_gol":4.6,"fal":25.0,"defesa_gk":3.7,"gols":2.8,
           "tiro_meta":4.1,"laterais":7.9,"impedimentos":2.2,"vit_casa":47,"vit_fora":28,"empate":25,
           "juiz_tipo":"Equilibrado","juiz_media_cartao":3.1,"juiz_media_falta":25},
    "SA": {"esc":9.3,"cartao":3.1,"fin":10.6,"chute_gol":4.7,"fal":25.5,"defesa_gk":3.6,"gols":2.9,
           "tiro_meta":4.0,"laterais":7.8,"impedimentos":2.4,"vit_casa":48,"vit_fora":27,"empate":25,
           "juiz_tipo":"Muito rigoroso","juiz_media_cartao":3.9,"juiz_media_falta":29},
    "PL": {"esc":9.6,"cartao":2.9,"fin":11.3,"chute_gol":4.9,"fal":24.0,"defesa_gk":3.5,"gols":3.0,
           "tiro_meta":3.8,"laterais":7.6,"impedimentos":2.6,"vit_casa":49,"vit_fora":28,"empate":23,
           "juiz_tipo":"Permissivo","juiz_media_cartao":2.8,"juiz_media_falta":24}
}

LIGAS = {
    "🌍 Copa do Mundo FIFA": "WC",
    "🏆 Liga dos Campeões UEFA": "CL",
    "🇩🇪 Bundesliga": "BL1",
    "🇳🇱 Eredivisie": "ERD",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇪🇸 La Liga": "PD",
    "🇫🇷 Ligue 1": "FL1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Championship": "ELC",
    "🇵🇹 Primeira Liga": "PPL",
    "🏆 Eurocopa": "EC",
    "🇮🇹 Série A": "SA",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "📋 Todas as Ligas": "TODAS"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())

# ==============================
# 🔍 BUSCA DE DADOS COM PERÍODO AJUSTADO
# ==============================
@st.cache_data(ttl=1800)
def buscar_jogos(sigla):
    time.sleep(0.5)
    hoje_man = datetime.now(FUSO_MAN).date()
    data_inicio = hoje_man - timedelta(days=1)
    data_fim = hoje_man + timedelta(days=7)
    lista = []
    siglas_busca = TODAS_SIGLAS if sigla == "TODAS" else [sigla]
    for s in siglas_busca:
        try:
            r = requests.get(f"https://api.football-data.org/v4/competitions/{s}/matches", headers=HEADERS, params={"limit":200}, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("matches", []):
                    try:
                        dt_utc = datetime.fromisoformat(j["utcDate"].replace("Z","")).replace(tzinfo=ZoneInfo("UTC"))
                        dt_man = dt_utc.astimezone(FUSO_MAN)
                        if data_inicio <= dt_man.date() <= data_fim:
                            j["dt_manaus"] = dt_man
                            lista.append(j)
                    except:
                        continue
        except:
            continue
    return lista

@st.cache_data(ttl=3600)
def buscar_ultimos_5_jogos(time_id):
    time.sleep(0.3)
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches", headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

@st.cache_data(ttl=86400)
def buscar_confrontos_diretos(id_casa, id_fora):
    try:
        r = requests.get("https://api.football-data.org/v4/matches", headers=HEADERS, params={
            "teams":f"{id_casa},{id_fora}","status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []
# ==============================
# ✅ ENVIO TELEGRAM
# ==============================
def enviar_mensagem_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        texto = texto.replace("`","").replace("*","").replace("_","")
        limite = 3700
        if len(texto) <= limite:
            resp = requests.post(url, data={"chat_id":CHAT_ID,"text":texto,"disable_web_page_preview":True}, timeout=20)
            return resp.status_code == 200
        while len(texto) > limite:
            corte = texto.rfind("\n",0,limite)
            parte = texto[:corte if corte!=-1 else limite]
            texto = texto[corte if corte!=-1 else limite:]
            requests.post(url, data={"chat_id":CHAT_ID,"text":parte,"disable_web_page_preview":True}, timeout=20)
            time.sleep(0.7)
        requests.post(url, data={"chat_id":CHAT_ID,"text":texto,"disable_web_page_preview":True}, timeout=20)
        return True
    except Exception as e:
        print(f"Erro envio: {e}")
        return False

# ==============================
# 🚀 ENVIO AUTOMÁTICO DE VALIDAÇÃO
# ==============================
def verificar_e_enviar_validacao(nome_casa, nome_fora, placar, validacao):
    id_jogo = f"{nome_casa}_x_{nome_fora}_{placar}"
    if id_jogo not in st.session_state.jogos_validados:
        mensagem = f"""🧾 VALIDAÇÃO DE PALPITES DISPONÍVEL!
⚽ {nome_casa} VS {nome_fora}
🏁 Resultado final: {placar}

{validacao}
"""
        if enviar_mensagem_telegram(mensagem):
            st.session_state.jogos_validados.append(id_jogo)
            return True
    return False

# ==============================
# 🧮 CÁLCULOS COM FATOR CASA/FORA
# ==============================
def calcular_dados_time(time_id, sigla_liga, joga_em_casa=False):
    try:
        jogos = buscar_ultimos_5_jogos(time_id)
        m = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
        fator_casa = 1.15 if joga_em_casa else 0.90
        fator_fora = 0.92 if joga_em_casa else 1.10
        if not jogos:
            return {
                "pV":m["vit_casa"]if joga_em_casa else m["vit_fora"],
                "pE":m["empate"],
                "pD":m["vit_fora"]if joga_em_casa else m["vit_casa"],
                "mg":m["gols"],"mcartao":m["cartao"],"mesc":m["esc"],
                "mfin":m["fin"],"mchute":round(m["chute_gol"]*fator_casa,1),
                "mfal":m["fal"],"mimped":round(m["impedimentos"]*fator_casa,1),
                "mdefesa":m["defesa_gk"],"mtiro":m["tiro_meta"],"mlateral":m["laterais"],
                "resumo":["📊 Liga"]*5,"placares":["Sem dados"]
            }
        v=e=d=gf=gs=tcg=ti=0
        resumo=[]
        placares=[]
        for j in jogos:
            try:
                idc = j["homeTeam"]["id"]
                gc = j["score"]["fullTime"].get("home",0) or 0
                ga = j["score"]["fullTime"].get("away",0) or 0
                if "statistics" in j:
                    for s in j["statistics"]:
                        if s["team"]["id"] == time_id:
                            tcg += s.get("shotsOnTarget",0) or m["chute_gol"]
                            ti += s.get("offsides",0) or m["impedimentos"]
                            break
                else:
                    tcg += m["chute_gol"]
                    ti += m["impedimentos"]
                if idc == time_id:
                    gf += gc
                    gs += ga
                    if gc>ga:
                        v+=1; resumo.append("✅")
                    elif gc==ga:
                        e+=1; resumo.append("⚖️")
                    else:
                        d+=1; resumo.append("❌")
                    placares.append(f"{gc}x{ga}")
                else:
                    gf += ga
                    gs += gc
                    if ga>gc:
                        v+=1; resumo.append("✅")
                    elif ga==gc:
                        e+=1; resumo.append("⚖️")
                    else:
                        d+=1; resumo.append("❌")
                    placares.append(f"{ga}x{gc}")
            except:
                tcg += m["chute_gol"]
                ti += m["impedimentos"]
                continue
        tj = len(jogos)
        mg = round((gf+gs)/tj,1)
        pv_base = round((v/tj)*100*fator_casa,1)
        pe_base = round((e/tj)*100,1)
        pd_base = round((d/tj)*100*fator_fora,1)
        total = pv_base+pe_base+pd_base
        if total>0:
            pv=round((pv_base/total)*100,1)
            pe=round((pe_base/total)*100,1)
            pd=round((pd_base/total)*100,1)
        else:
            pv=m["vit_casa"]if joga_em_casa else m["vit_fora"]
            pe=m["empate"]
            pd=m["vit_fora"]if joga_em_casa else m["vit_casa"]
        return {
            "pV":pv,"pE":pe,"pD":pd,"mg":mg,
            "mcartao":round(m["cartao"]*(mg/m["gols"]),1),
            "mesc":round(m["esc"]*(mg/m["gols"]),1),
            "mfin":round(m["fin"]*(mg/m["gols"]),1),
            "mchute":round((tcg/tj)*fator_casa,1),
            "mfal":round(m["fal"]*(mg/m["gols"]),1),
            "mimped":round((ti/tj)*fator_casa,1),
            "mdefesa":round(m["defesa_gk"]/(mg/m["gols"]),1),
            "mtiro":round(m["tiro_meta"]*(mg/m["gols"]),1),
            "mlateral":round(m["laterais"]*(mg/m["gols"]),1),
            "resumo":resumo,"placares":placares
        }
    except:
        m = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
        return {
            "pV":m["vit_casa"]if joga_em_casa else m["vit_fora"],
            "pE":m["empate"],
            "pD":m["vit_fora"]if joga_em_casa else m["vit_casa"],
            "mg":m["gols"],"mcartao":m["cartao"],"mesc":m["esc"],
            "mfin":m["fin"],"mchute":round(m["chute_gol"]*(1.15 if joga_em_casa else 0.90),1),
            "mfal":m["fal"],"mimped":round(m["impedimentos"]*(1.15 if joga_em_casa else 0.90),1),
            "mdefesa":m["defesa_gk"],"mtiro":m["tiro_meta"],"mlateral":m["laterais"],
            "resumo":["📊 Liga"]*5,"placares":["Erro"]
        }

def calcular_dupla_chance(pv,pe,pd):
    return {"1X":round(pv+pe,1),"X2":round(pe+pd,1),"12":round(pv+pd,1)}

def conf_maior(v,l):
    if v<=0: return 0
    return min(round((v/l)*100,1),95)

def conf_menor(v,l):
    if v<=0 or v>=l: return 0
    return min(round((1-(v/l))*100,1),95)

# ==============================
# 🧾 VALIDAÇÃO DOS PALPITES
# ==============================
def validar_palpites(jogo, indicacoes, nc, nf):
    status = jogo.get("status","")
    validacao = []
    if status != "FINISHED":
        return ["⏳ Aguardando resultado"], ""
    
    gc_real = jogo["score"]["fullTime"].get("home",0) or 0
    ga_real = jogo["score"]["fullTime"].get("away",0) or 0
    total_gols_real = gc_real + ga_real
    placar = f"{nc} {gc_real} x {ga_real} {nf}"

    for ind in indicacoes:
        acertou = False
        if "Mais de 1.5 gols" in ind:
            acertou = total_gols_real > 1.5
        elif "Menos de 3.5 gols" in ind:
            acertou = total_gols_real < 3.5
        elif f"{nc} marca entre 1 e 3 gols" in ind:
            acertou = 1 <= gc_real <=3
        elif f"{nf} marca entre 1 e 3 gols" in ind:
            acertou = 1 <= ga_real <=3
        elif "Dupla Chance" in ind:
            if f"{nf} ou Empate" in ind:
                acertou = (ga_real>gc_real) or (gc_real==ga_real)
            elif f"{nc} ou Empate" in ind:
                acertou = (gc_real>ga_real) or (gc_real==ga_real)
        validacao.append(f"{ind.split(' - ')[0]} - {'✅ ACERTOU' if acertou else '❌ ERROU'}")
    return validacao, placar

# ==============================
# 📊 ANÁLISES COMPLEMENTARES
# ==============================
def analise_juiz(sigla_liga, dc, df):
    m = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
    texto = f"⚖️ Perfil médio dos juízes da competição: {m['juiz_tipo']}\n"
    texto += f"• Média esperada: {m['juiz_media_cartao']} cartões | {m['juiz_media_falta']} faltas\n"
    media_cartoes_times = (dc['mcartao'] + df['mcartao']) / 2
    if m["juiz_media_cartao"] > media_cartoes_times + 0.5:
        texto += "• 📈 Tendência: juízes costumam aplicar mais cartões que a média dos times\n"
    elif m["juiz_media_cartao"] < media_cartoes_times - 0.5:
        texto += "• 📉 Tendência: juízes costumam aplicar menos cartões que a média dos times\n"
    return texto

def analise_confrontos(id_casa, id_fora, nome_casa, nome_fora):
    jogos = buscar_confrontos_diretos(id_casa, id_fora)
    if not jogos:
        return "🤝 Últimos confrontos: Sem dados disponíveis de confrontos diretos recentes."
    resumo = f"🤝 Últimos {len(jogos)} confrontos diretos:\n"
    v_casa = 0
    v_fora = 0
    emp = 0
    for j in jogos:
        gc = j["score"]["fullTime"].get("home",0) or 0
        ga = j["score"]["fullTime"].get("away",0) or 0
        mandante = j["homeTeam"]["name"]
        visitante = j["awayTeam"]["name"]
        resumo += f"• {mandante} {gc} x {ga} {visitante}\n"
        if gc > ga:
            if mandante == nome_casa:
                v_casa +=1
            else:
                v_fora +=1
        elif gc == ga:
            emp +=1
        else:
            if mandante == nome_casa:
                v_fora +=1
            else:
                v_casa +=1
    resumo += f"📌 Resumo: {nome_casa} {v_casa} vitórias | {emp} empates | {nome_fora} {v_fora} vitórias"
    return resumo
# ==============================
# 📝 RELATÓRIO COMPLETO COM VALIDAÇÃO
# ==============================
def gerar_relatorio(nc,nf,dt_man,dc,df,dupla,juiz_info,confronto_info,jogo):
    tg=round(dc['mg']+df['mg'],1)
    tc=round(dc['mcartao']+df['mcartao'],1)
    te=round(dc['mesc']+df['mesc'],1)
    tf=round(dc['mfin']+df['mfin'],1)
    tcg=round(dc['mchute']+df['mchute'],1)
    tfa=round(dc['mfal']+df['mfal'],1)
    timped=round(dc['mimped']+df['mimped'],1)
    ind=[]

    if dupla['X2']>=LIMITE_CONFIANCA: ind.append(f"🔹 Dupla Chance: {nf} ou Empate - {dupla['X2']}%")
    if dupla['1X']>=LIMITE_CONFIANCA: ind.append(f"🔹 Dupla Chance: {nc} ou Empate - {dupla['1X']}%")
    if conf_maior(tg,1.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Mais de 1.5 gols - {conf_maior(tg,1.5)}%")
    if conf_menor(tg,3.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Menos de 3.5 gols - {conf_menor(tg,3.5)}%")
    if conf_maior(tcg,6.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Mais de 6.5 chutes ao gol - {conf_maior(tcg,6.5)}%")
    if conf_maior(tf,19.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Mais de 19.5 finalizações - {conf_maior(tf,19.5)}%")
    if conf_maior(tfa,25)>=LIMITE_CONFIANCA: ind.append(f"🔹 Mais de 25 faltas - {conf_maior(tfa,25)}%")
    if conf_menor(te,12.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Menos de 12.5 escanteios - {conf_menor(te,12.5)}%")
    if conf_menor(tc,6.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Menos de 6.5 cartões - {conf_menor(tc,6.5)}%")
    if conf_maior(timped,2.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Mais de 2.5 impedimentos - {conf_maior(timped,2.5)}%")
    if 1<=dc['mg']<=3: ind.append(f"🔹 {nc} marca entre 1 e 3 gols")
    if 1<=df['mg']<=3: ind.append(f"🔹 {nf} marca entre 1 e 3 gols")

    lista_ind = "\n".join(ind) if ind else f"Nenhuma indicação acima de {LIMITE_CONFIANCA}% de confiança"
    validacao, placar = validar_palpites(jogo, ind, nc, nf)
    lista_validacao = "\n".join(validacao)

    placar_real = ""
    if jogo.get("status") == "FINISHED":
        gc = jogo["score"]["fullTime"].get("home",0) or 0
        ga = jogo["score"]["fullTime"].get("away",0) or 0
        placar_real = f"\n🏁 RESULTADO FINAL: {nc} {gc} x {ga} {nf}"
        # Envia validação automaticamente se ainda não enviou
        verificar_e_enviar_validacao(nc, nf, placar, lista_validacao)

    return f"""⚽ {nc} VS {nf} | 🕒 {dt_man.strftime('%d/%m %H:%M')} (Horário de Manaus)
{placar_real}

📊 PROBABILIDADES DE RESULTADO (SOMA 100%):
✅ Vitória {nc}: {dc['pV']}% | ⚖️ Empate: {dc['pE']}% | ✅ Vitória {nf}: {dc['pD']}%
🔀 Dupla Chance: 1X {dupla['1X']}% | X2 {dupla['X2']}% | 12 {dupla['12']}%

{confronto_info}

{juiz_info}

📈 TOTAIS ESPERADOS NO JOGO:
⚽ Gols: {tg} | 🟨 Cartões: {tc} | 📐 Escanteios: {te}
🎯 Finalizações: {tf} | Chutes ao gol: {tcg} | 🤜 Faltas: {tfa} | 🚫 Impedimentos: {timped}

📊 MÉTRICAS INDIVIDUAIS DOS TIMES:
🏠 {nc} (Joga em Casa - últimos 5 jogos):
• Resultados: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}
• ⚽ Gols: {dc['mg']} | 🟨 Cartões: {dc['mcartao']} | 📐 Escanteios: {dc['mesc']}
• 🎯 Finalizações: {dc['mfin']} | Chutes ao gol: {dc['mchute']} | 🤜 Faltas: {dc['mfal']}
• 🚫 Impedimentos: {dc['mimped']} | 🛡️ Defesas: {dc['mdefesa']} | ⚾ Tiros de meta: {dc['mtiro']} | ↔️ Laterais: {dc['mlateral']}

✈️ {nf} (Joga Fora - últimos 5 jogos):
• Resultados: {' '.join(df['resumo'])} | Placares: {' '.join(df['placares'])}
• ⚽ Gols: {df['mg']} | 🟨 Cartões: {df['mcartao']} | 📐 Escanteios: {df['mesc']}
• 🎯 Finalizações: {df['mfin']} | Chutes ao gol: {df['mchute']} | 🤜 Faltas: {df['mfal']}
• 🚫 Impedimentos: {df['mimped']} | 🛡️ Defesas: {df['mdefesa']} | ⚾ Tiros de meta: {df['mtiro']} | ↔️ Laterais: {df['mlateral']}

💡 INDICAÇÕES COM ≥ {LIMITE_CONFIANCA}% DE CONFIANÇA:
{lista_ind}

🧾 VALIDAÇÃO DOS PALPITES:
{lista_validacao}
"""

# ==============================
# 🖥️ INTERFACE PRINCIPAL
# ==============================
st.info(f"📅 Período exibido: **Dia anterior até 7 dias à frente** | Horário de Manaus | Confiança mínima: {LIMITE_CONFIANCA}%\n🔔 Validação dos resultados é enviada automaticamente ao Telegram assim que detectada!")
escolha = st.selectbox("🏆 Selecione a Competição", list(LIGAS.keys()))
sigla = LIGAS[escolha]

if st.button("🔍 Carregar Jogos e Análises"):
    with st.spinner("Processando todos os dados..."):
        jogos = buscar_jogos(sigla)
        if not jogos:
            st.warning("⚠️ Nenhum jogo encontrado no período selecionado.")
        else:
            st.success(f"✅ {len(jogos)} jogos encontrados!")
            for jogo in jogos:
                try:
                    nc = jogo["homeTeam"]["name"]
                    nf = jogo["awayTeam"]["name"]
                    idc = jogo["homeTeam"]["id"]
                    idf = jogo["awayTeam"]["id"]
                    dt_man = jogo["dt_manaus"]
                    
                    dc = calcular_dados_time(idc, sigla, True)
                    df = calcular_dados_time(idf, sigla, False)
                    dupla = calcular_dupla_chance(dc['pV'],dc['pE'],dc['pD'])
                    juiz_txt = analise_juiz(sigla, dc, df)
                    confronto_txt = analise_confrontos(idc, idf, nc, nf)
                    
                    rel = gerar_relatorio(nc,nf,dt_man,dc,df,dupla,juiz_txt,confronto_txt,jogo)
                    st.markdown("---")
                    st.markdown(rel)
                    
                    if dupla['X2']>=LIMITE_CONFIANCA or dupla['1X']>=LIMITE_CONFIANCA:
                        with st.spinner("Enviando relatório ao Telegram..."):
                            if enviar_mensagem_telegram(rel):
                                st.success("✅ Relatório enviado ao Telegram com sucesso!")
                            else:
                                st.error("❌ Ocorreu um erro ao enviar ao Telegram")
                    time.sleep(0.5)
                except Exception as e:
                    st.error(f"⚠️ Erro ao processar jogo: {str(e)}")
                    continue

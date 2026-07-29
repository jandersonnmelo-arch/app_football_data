import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Correta | Envio Telegram", page_icon="✅", layout="wide")
st.title("⚽ Análise Completa | Campeonatos Confirmados")

# 🔒 CHAVES OCULTAS
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves nos Secrets! Erro: {e}")
    st.stop()

LIMITE_CONFIANCA = 70
FUSO_MAN = ZoneInfo("America/Manaus")
HORARIO_ALERTA = "07:00"
STATUS_INVALIDOS = ["CANCELLED", "POSTPONED", "SUSPENDED", "ABANDONED"]
HEADERS = {"X-Auth-Token": API_KEY}

# 🧠 MEMÓRIA E CONTROLE
if "memoria_ia" not in st.session_state:
    st.session_state.memoria_ia = {"times": {}, "acertos": 0, "erros": 0, "ultima_atualizacao": None}
if "ultimo_envio_diario" not in st.session_state:
    st.session_state.ultimo_envio_diario = None
memoria = st.session_state.memoria_ia

# ==============================
# 🧠 MOTOR DE ANÁLISE
# ==============================
def analise_ia(nome_casa, nome_fora, id_casa, id_fora, dc, df, dupla, liga_dados, confronto, gols_t):
    motivos = []
    conf_base = 50

    ajuste_casa = ajuste_fora = 0
    if str(id_casa) in memoria["times"]:
        tx = memoria["times"][str(id_casa)]["acertos"] / max(1, memoria["times"][str(id_casa)]["total_analises"])
        ajuste_casa = round((tx - 0.5) * 15)
        if ajuste_casa > 2: motivos.append(f"📚 Histórico positivo para {nome_casa}")
        if ajuste_casa < -2: motivos.append(f"⚠️ Menor confiança em {nome_casa}")
    if str(id_fora) in memoria["times"]:
        tx = memoria["times"][str(id_fora)]["acertos"] / max(1, memoria["times"][str(id_fora)]["total_analises"])
        ajuste_fora = round((tx - 0.5) * 15)
        if ajuste_fora > 2: motivos.append(f"📚 Histórico positivo para {nome_fora}")
        if ajuste_fora < -2: motivos.append(f"⚠️ Menor confiança em {nome_fora}")
    conf_base += max(ajuste_casa, ajuste_fora)

    if dc['pV'] > df['pV'] + 10: conf_base +=12; motivos.append(f"✅ {nome_casa} vantagem clara em casa")
    if df['pV'] > dc['pV'] + 10: conf_base +=12; motivos.append(f"✅ {nome_fora} bom desempenho fora")
    cons_casa = dc['resumo'].count("✅") * 20
    cons_fora = df['resumo'].count("✅") * 20
    if cons_casa >=60: conf_base +=8; motivos.append(f"📈 {nome_casa} consistente")
    if cons_fora >=60: conf_base +=8; motivos.append(f"📈 {nome_fora} regular")
    if cons_casa <40: conf_base -=7; motivos.append(f"📉 {nome_casa} em queda")
    if cons_fora <40: conf_base -=7; motivos.append(f"📉 {nome_fora} com dificuldades")
    if gols_t['total_1t'] >1.0: conf_base +=7; motivos.append("⚽ Mais gols no 1º tempo")
    if gols_t['total_2t'] >1.2: conf_base +=7; motivos.append("⚽ Mais gols no 2º tempo")

    conf_final = max(30, min(conf_base, 94))
    resumo = f"🔮 IA indica tendência ao {nome_casa}" if conf_final >= LIMITE_CONFIANCA and dc['pV']>df['pV'] else \
             f"🔮 IA indica tendência ao {nome_fora}" if conf_final >= LIMITE_CONFIANCA and df['pV']>dc['pV'] else \
             "🔮 Equilíbrio ou dados insuficientes"
    return resumo, round(conf_final,1), "• "+"\n• ".join(motivos) if motivos else "• Dados alinhados com a média"

def atualizar_aprendizado(id_casa, id_fora, analise_vencedor, resultado_real):
    for tid in [str(id_casa), str(id_fora)]:
        if tid not in memoria["times"]: memoria["times"][tid] = {"acertos":0, "total_analises":0}
        memoria["times"][tid]["total_analises"] +=1
    acertou = (analise_vencedor == resultado_real)
    if acertou:
        memoria["acertos"] +=1
        memoria["times"][str(id_casa)]["acertos"] +=1
        memoria["times"][str(id_fora)]["acertos"] +=1
    else: memoria["erros"] +=1
    memoria["ultima_atualizacao"] = datetime.now(FUSO_MAN).strftime("%d/%m %H:%M")

# ==============================
# 🏆 CAMPEONATOS EXATOS DA IMAGEM
# ==============================
MEDIAS_LIGA = {
    "WC": {"nome":"Copa do Mundo FIFA","esc":8.0,"cartao":2.7,"fin":9.0,"chute_gol":4.0,"fal":24.5,"defesa_gk":3.9,"gols":2.8,"gols_1t":1.2,"gols_2t":1.6,"juiz_tipo":"Equilibrado"},
    "CL": {"nome":"Liga dos Campeões UEFA","esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,"gols_1t":1.2,"gols_2t":1.7,"juiz_tipo":"Equilibrado"},
    "BL1": {"nome":"Bundesliga","esc":9.2,"cartao":3.0,"fin":10.8,"chute_gol":4.7,"fal":25.0,"defesa_gk":3.6,"gols":3.1,"gols_1t":1.3,"gols_2t":1.8,"juiz_tipo":"Permissivo"},
    "ERD": {"nome":"Eredivisie","esc":9.8,"cartao":2.8,"fin":11.5,"chute_gol":5.0,"fal":23.0,"defesa_gk":3.4,"gols":3.2,"gols_1t":1.4,"gols_2t":1.8,"juiz_tipo":"Permissivo"},
    "BSA": {"nome":"Campeonato Brasileiro Série A","esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,"gols_1t":1.1,"gols_2t":1.5,"juiz_tipo":"Rigoroso"},
    "PD": {"nome":"Primera División (La Liga)","esc":9.4,"cartao":3.1,"fin":10.5,"chute_gol":4.7,"fal":25.5,"defesa_gk":3.7,"gols":2.8,"gols_1t":1.2,"gols_2t":1.6,"juiz_tipo":"Muito rigoroso"},
    "FL1": {"nome":"Ligue 1","esc":9.1,"cartao":3.0,"fin":10.3,"chute_gol":4.6,"fal":25.0,"defesa_gk":3.8,"gols":2.7,"gols_1t":1.1,"gols_2t":1.6,"juiz_tipo":"Equilibrado"},
    "ELC": {"nome":"Championship (Inglaterra)","esc":8.6,"cartao":3.5,"fin":9.2,"chute_gol":3.9,"fal":27.0,"defesa_gk":4.3,"gols":2.5,"gols_1t":1.0,"gols_2t":1.5,"juiz_tipo":"Rigoroso"},
    "PPL": {"nome":"Primeira Liga (Portugal)","esc":8.8,"cartao":3.2,"fin":9.7,"chute_gol":4.2,"fal":26.0,"defesa_gk":4.0,"gols":2.6,"gols_1t":1.1,"gols_2t":1.5,"juiz_tipo":"Equilibrado"},
    "EC": {"nome":"Campeonato Europeu","esc":8.5,"cartao":2.8,"fin":9.5,"chute_gol":4.1,"fal":24.0,"defesa_gk":3.8,"gols":2.7,"gols_1t":1.2,"gols_2t":1.5,"juiz_tipo":"Equilibrado"},
    "SA": {"nome":"Série A Italiana","esc":9.3,"cartao":3.1,"fin":10.6,"chute_gol":4.7,"fal":25.5,"defesa_gk":3.6,"gols":2.9,"gols_1t":1.2,"gols_2t":1.7,"juiz_tipo":"Muito rigoroso"},
    "PL": {"nome":"Premier League","esc":9.6,"cartao":2.9,"fin":11.3,"chute_gol":4.9,"fal":24.0,"defesa_gk":3.5,"gols":3.0,"gols_1t":1.3,"gols_2t":1.7,"juiz_tipo":"Permissivo"}
}

LIGAS = {
    "🌍 Copa do Mundo FIFA": "WC",
    "🏆 Liga dos Campeões UEFA": "CL",
    "🇩🇪 Bundesliga": "BL1",
    "🇳🇱 Eredivisie": "ERD",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇪🇸 La Liga": "PD",
    "🇫🇷 Ligue 1": "FL1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "ELC",
    "🇵🇹 Primeira Liga": "PPL",
    "🇪🇺 Campeonato Europeu": "EC",
    "🇮🇹 Série A Italiana": "SA",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "📋 Todas as Ligas": "TODAS"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())
# ==============================
# 🔍 BUSCA DE JOGOS OTIMIZADA
# ==============================
@st.cache_data(ttl=900, show_spinner=False)
def buscar_jogos(sigla):
    time.sleep(0.3)
    hoje_man = datetime.now(FUSO_MAN).date()
    data_ini = hoje_man - timedelta(days=2)
    data_fim = hoje_man + timedelta(days=14)
    lista = []
    siglas = TODAS_SIGLAS if sigla == "TODAS" else [sigla]
    
    for s in siglas:
        try:
            r = requests.get(
                f"https://api.football-data.org/v4/competitions/{s}/matches",
                headers=HEADERS,
                params={"dateFrom": data_ini.isoformat(), "dateTo": data_fim.isoformat()},
                timeout=20
            )
            if r.status_code == 200:
                dados = r.json().get("matches", [])
                for j in dados:
                    try:
                        if j.get("status","") in STATUS_INVALIDOS: continue
                        dt_utc = datetime.fromisoformat(j["utcDate"].replace("Z","")).replace(tzinfo=ZoneInfo("UTC"))
                        dt_man = dt_utc.astimezone(FUSO_MAN)
                        j["dt_manaus"] = dt_man
                        lista.append(j)
                    except: continue
        except Exception as e:
            st.warning(f"⚠️ Erro na busca de {MEDIAS_LIGA.get(s,{}).get('nome',s)}: {str(e)}")
            continue
    return lista

@st.cache_data(ttl=3600)
def buscar_ultimos5(time_id):
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches", headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except: return []

@st.cache_data(ttl=86400)
def buscar_confrontos(id1, id2):
    try:
        r = requests.get(f"https://api.football-data.org/v4/matches", headers=HEADERS, params={"teams":f"{id1},{id2}","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except: return []

# ==============================
# ✅ ENVIO TELEGRAM COM RELATÓRIO
# ==============================
def enviar_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        texto = texto.replace("`","").replace("*","")
        if len(texto) <= 3700:
            resp = requests.post(url, data={"chat_id":CHAT_ID,"text":texto}, timeout=20)
            return resp.status_code == 200
        while texto:
            parte = texto[:3700]
            corte = parte.rfind("\n") if "\n" in parte else 3700
            requests.post(url, data={"chat_id":CHAT_ID,"text":texto[:corte]}, timeout=20)
            texto = texto[corte:]
            time.sleep(0.5)
        return True
    except Exception as e:
        st.error(f"Erro ao enviar: {str(e)}")
        return False

def enviar_validacao(nc, nf, placar, txt):
    msg = f"🧾 VALIDAÇÃO!\n⚽ {nc} VS {nf}\n🏁 {placar}\n\n{txt}"
    enviar_telegram(msg)

# ==============================
# ⏰ ENVIO AUTOMÁTICO OTIMIZADO
# ==============================
def executar_envio_automatico():
    agora = datetime.now(FUSO_MAN)
    horario_atual = agora.strftime("%H:%M")
    hoje = agora.date()

    if horario_atual == HORARIO_ALERTA and st.session_state.ultimo_envio_diario != hoje:
        st.toast(f"⏰ Iniciando envio automático das {HORARIO_ALERTA}...")
        jogos = buscar_jogos("TODAS")
        qtd_enviados = 0
        qtd_analisados = 0
        motivos_nao_envio = []

        for jg in jogos:
            try:
                dt_jogo = jg["dt_manaus"]
                if dt_jogo < agora:
                    motivos_nao_envio.append(f"{jg['homeTeam']['name']} x {jg['awayTeam']['name']}: já começou")
                    continue

                nc = jg["homeTeam"]["name"]; nf = jg["awayTeam"]["name"]
                idc = jg["homeTeam"]["id"]; idf = jg["awayTeam"]["id"]
                dc = dados_time(idc, "TODAS", True)
                df = dados_time(idf, "TODAS", False)
                dupla = dupla_chance(dc['pV'],dc['pE'],dc['pD'])
                qtd_analisados +=1

                if dupla['1X']>=LIMITE_CONFIANCA or dupla['X2']>=LIMITE_CONFIANCA:
                    juiz = analise_juiz("TODAS")
                    confronto = analise_confronto(idc,idf,nc,nf)
                    rel = gerar_relatorio(nc,nf,dt_jogo,dc,df,idc,idf,dupla,juiz,confronto,jg,"TODAS")
                    if enviar_telegram(rel): qtd_enviados +=1
                    time.sleep(0.7)
                else:
                    motivos_nao_envio.append(f"{nc} x {nf}: confiança abaixo de {LIMITE_CONFIANCA}%")
            except Exception as e:
                motivos_nao_envio.append(f"Erro em {jg.get('homeTeam',{}).get('name','jogo')}: {str(e)}")
                continue

        st.session_state.ultimo_envio_diario = hoje
        st.success(f"✅ Envio concluído! Analisados: {qtd_analisados} | Enviados: {qtd_enviados}")
        if motivos_nao_envio:
            st.info(f"ℹ️ Motivos dos não envios:\n" + "\n".join(motivos_nao_envio[:10]))

executar_envio_automatico()

# ==============================
# 🧮 CÁLCULOS CORRIGIDOS
# ==============================
def dados_time(time_id, sigla, casa=False):
    jogos = buscar_ultimos5(time_id)
    m = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    fc = 1.15 if casa else 0.90
    ff = 0.92 if casa else 1.10
    if not jogos:
        return {"pV":round(45*fc,1),"pE":28,"pD":round(45*ff,1),"mg":m["gols"],"mg_1t":m["gols_1t"],"mg_2t":m["gols_2t"],"mcartao":m["cartao"],"mesc":m["esc"],"resumo":["📊 Sem dados"]*5,"placares":["-"]}
    v=e=d=gf=gs=gf1=gf2=0; resumo=[]; placares=[]
    for j in jogos:
        try:
            idc = j["homeTeam"]["id"]
            gc = j["score"]["fullTime"].get("home",0) or 0
            ga = j["score"]["fullTime"].get("away",0) or 0
            g1c = j["score"]["halfTime"].get("home",0) or 0
            g1a = j["score"]["halfTime"].get("away",0) or 0
            if idc == time_id:
                gf+=gc; gs+=ga; gf1+=g1c; gf2+=gc-g1c
                resumo.append("✅"if gc>ga else "⚖️"if gc==ga else "❌"); placares.append(f"{gc}x{ga}")
                v+=1 if gc>ga else 0; e+=1 if gc==ga else 0; d+=1 if gc<ga else 0
            else:
                gf+=ga; gs+=gc; gf1+=g1a; gf2+=ga-g1a
                resumo.append("✅"if ga>gc else "⚖️"if ga==gc else "❌"); placares.append(f"{ga}x{gc}")
                v+=1 if ga>gc else 0; e+=1 if ga==gc else 0; d+=1 if ga<gc else 0
        except: continue
    tj = max(len(jogos),1)
    mg = round((gf+gs)/tj,1); mg1t = round(gf1/tj*fc,1); mg2t = round(gf2/tj*fc,1)
    pv = round((v/tj)*100*fc,1); pe = round((e/tj)*100,1); pd = round((d/tj)*100*ff,1)
    total = max(pv+pe+pd,1)
    pv,pe,pd = round(pv/total*100,1), round(pe/total*100,1), round(pd/total*100,1)
    return {"pV":pv,"pE":pe,"pD":pd,"mg":mg,"mg_1t":mg1t,"mg_2t":mg2t,"mcartao":round(m["cartao"]*(mg/m["gols"]),1),"mesc":round(m["esc"]*(mg/m["gols"]),1),"resumo":resumo,"placares":placares}

def calcular_gols_tempo(dc, df):
    return {"casa_1t":dc['mg_1t'],"casa_2t":dc['mg_2t'],"fora_1t":df['mg_1t'],"fora_2t":df['mg_2t'],"total_1t":round(dc['mg_1t']+df['mg_1t'],1),"total_2t":round(dc['mg_2t']+df['mg_2t'],1)}
def dupla_chance(pv,pe,pd): return {"1X":round(pv+pe,1),"X2":round(pe+pd,1),"12":round(pv+pd,1)}
def confMaior(v,l): return min(round((v/l)*100,1),95) if v>0 else 0

def analise_juiz(sigla):
    m = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    return f"⚖️ Perfil: {m['juiz_tipo']}"

def analise_confronto(idc, idf, nc, nf):
    jogos = buscar_confrontos(idc, idf)
    if not jogos: return "🤝 Sem dados de confrontos diretos"
    vc=ve=vf=0; txt="🤝 Últimos confrontos:\n"
    for j in jogos:
        gc = j["score"]["fullTime"].get("home",0) or 0; ga = j["score"]["fullTime"].get("away",0) or 0
        txt += f"• {j['homeTeam']['name']} {gc}x{ga} {j['awayTeam']['name']}\n"
        if gc>ga: vc +=1 if j["homeTeam"]["name"]==nc else 0; vf +=1 if j["awayTeam"]["name"]==nc else 0
        elif gc==ga: ve +=1
        else: vf +=1 if j["homeTeam"]["name"]==nc else 0; vc +=1 if j["awayTeam"]["name"]==nc else 0
    txt += f"📌 {nc} {vc} vitórias | {ve} empates | {nf} {vf} vitórias"
    return txt

def validar_e_aprender(jogo, indicacoes, nc, nf, idc, idf, vencedor_analise):
    if jogo.get("status") != "FINISHED": return ["⏳ Aguardando resultado"], ""
    gc = jogo["score"]["fullTime"].get("home",0) or 0; ga = jogo["score"]["fullTime"].get("away",0) or 0
    placar = f"{nc} {gc}x{ga} {nf}"
    res_real = "casa" if gc>ga else "fora" if ga>gc else "empate"
    atualizar_aprendizado(idc, idf, vencedor_analise, res_real)
    g1c = jogo["score"]["halfTime"].get("home",0) or 0; g1a = jogo["score"]["halfTime"].get("away",0) or 0
    res = []
    for ind in indicacoes:
        ok=False
        if "Mais de 1.5" in ind: ok = (gc+ga)>1.5
        elif "1º Tempo tem gol" in ind: ok = (g1c+g1a)>=1
        elif "2º Tempo tem gol" in ind: ok = ((gc-g1c)+(ga-g1a))>=1
        elif f"{nc} marca no 1º" in ind: ok = g1c>=1
        elif f"{nf} marca no 1º" in ind: ok = g1a>=1
        elif f"{nc} marca no 2º" in ind: ok = (gc-g1c)>=1
        elif f"{nf} marca no 2º" in ind: ok = (ga-g1a)>=1
        res.append(f"{ind.split(' - ')[0]} - {'✅'if ok else '❌'}")
    enviar_validacao(nc,nf,placar,"\n".join(res))
    return res, placar
# ==============================
# 📝 RELATÓRIO COMPLETO
# ==============================
def gerar_relatorio(nc,nf,dt,dc,df,idc,idf,dupla,juiz,confronto,jogo,sigla):
    tg=round(dc['mg']+df['mg'],1)
    gols_t = calcular_gols_tempo(dc, df)
    m_liga = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    vencedor_analise = "casa" if dc['pV']>df['pV'] else "fora" if df['pV']>dc['pV'] else "empate"
    ia_res, ia_conf, ia_mot = analise_ia(nc,nf,idc,idf,dc,df,dupla,m_liga,confronto,gols_t)

    ind=[]
    if dupla['1X']>=LIMITE_CONFIANCA: ind.append(f"🔹 {nc} ou Empate - {dupla['1X']}%")
    if dupla['X2']>=LIMITE_CONFIANCA: ind.append(f"🔹 {nf} ou Empate - {dupla['X2']}%")
    if confMaior(tg,1.5)>=LIMITE_CONFIANCA: ind.append(f"🔹 Mais de 1.5 gols - {confMaior(tg,1.5)}%")
    conf_1t = confMaior(gols_t['total_1t'],0.8); conf_2t = confMaior(gols_t['total_2t'],0.9)
    conf_casa1 = confMaior(gols_t['casa_1t'],0.4); conf_fora1 = confMaior(gols_t['fora_1t'],0.3)
    conf_casa2 = confMaior(gols_t['casa_2t'],0.5); conf_fora2 = confMaior(gols_t['fora_2t'],0.4)
    if conf_1t>=LIMITE_CONFIANCA: ind.append(f"🔹 1º Tempo tem gol - {conf_1t}%")
    if conf_2t>=LIMITE_CONFIANCA: ind.append(f"🔹 2º Tempo tem gol - {conf_2t}%")
    if conf_casa1>=LIMITE_CONFIANCA: ind.append(f"🔹 {nc} marca no 1º tempo - {conf_casa1}%")
    if conf_fora1>=LIMITE_CONFIANCA: ind.append(f"🔹 {nf} marca no 1º tempo - {conf_fora1}%")
    if conf_casa2>=LIMITE_CONFIANCA: ind.append(f"🔹 {nc} marca no 2º tempo - {conf_casa2}%")
    if conf_fora2>=LIMITE_CONFIANCA: ind.append(f"🔹 {nf} marca no 2º tempo - {conf_fora2}%")

    val, placar = validar_e_aprender(jogo,ind,nc,nf,idc,idf,vencedor_analise) if jogo else ([], "")
    ind_txt = "\n".join(ind) if ind else f"Nenhuma indicação acima de {LIMITE_CONFIANCA}%"
    placar_final = f"\n🏁 RESULTADO: {placar}" if jogo and jogo.get("status")=="FINISHED" else ""

    return f"""⚽ {nc} VS {nf} | 🕒 {dt.strftime('%d/%m %H:%M')} Manaus
{placar_final}
🏆 Competição: {m_liga['nome']}

📊 PROBABILIDADES:
✅ {nc}: {dc['pV']}% | ⚖️ Empate: {dc['pE']}% | ✅ {nf}: {dc['pD']}%

🧠 ANÁLISE DA IA:
{ia_res} | Confiança: {ia_conf}%
{ia_mot}

⏱️ GOLS POR TEMPO:
1º Tempo: Total {gols_t['total_1t']} | {nc} {gols_t['casa_1t']} | {nf} {gols_t['fora_1t']}
2º Tempo: Total {gols_t['total_2t']} | {nc} {gols_t['casa_2t']} | {nf} {gols_t['fora_2t']}

{confronto}
{juiz}

📈 TOTAIS:
⚽ Gols: {tg} | 🟨 Cartões: {round(dc['mcartao']+df['mcartao'],1)} | 📐 Escanteios: {round(dc['mesc']+df['mesc'],1)}

📊 DESEMPENHO RECENTE:
🏠 {nc}: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}
✈️ {nf}: {' '.join(df['resumo'])} | Placares: {' '.join(df['placares'])}

💡 INDICAÇÕES ≥ {LIMITE_CONFIANCA}%:
{ind_txt}

🧾 VALIDAÇÃO:
{chr(10).join(val)}
"""

# ==============================
# 🖥️ INTERFACE FINAL
# ==============================
st.sidebar.header("⚙️ STATUS DO SISTEMA")
st.sidebar.info(f"""
🧠 Taxa de acerto: {round((memoria["acertos"] / max(1, memoria["acertos"]+memoria["erros"]))*100,1)}%
⏰ Envio automático: {HORARIO_ALERTA} Manaus
📅 Último envio: {st.session_state.ultimo_envio_diario or "Hoje"}
🔍 Período de busca: até 14 dias
""")

sel = st.selectbox("🏆 Selecione a Competição", list(LIGAS.keys()))
sigla = LIGAS[sel]

st.info(f"✅ Campeonatos confirmados na API | Confiança ≥ {LIMITE_CONFIANCA}%")
if st.button("🔍 Analisar Todos os Jogos Agora"):
    with st.spinner("Buscando e analisando..."):
        jogos = buscar_jogos(sigla)
        if not jogos:
            st.warning("⚠️ Nenhum jogo encontrado no período selecionado")
        else:
            st.success(f"✅ {len(jogos)} jogos encontrados")
            enviados_agora = 0
            for jg in jogos:
                try:
                    nc = jg["homeTeam"]["name"]; nf = jg["awayTeam"]["name"]
                    dc = dados_time(jg["homeTeam"]["id"], sigla, True)
                    df = dados_time(jg["awayTeam"]["id"], sigla, False)
                    dupla = dupla_chance(dc['pV'],dc['pE'],dc['pD'])
                    rel = gerar_relatorio(nc,nf,jg["dt_manaus"],dc,df,jg["homeTeam"]["id"],jg["awayTeam"]["id"],dupla,analise_juiz(sigla),analise_confronto(jg["homeTeam"]["id"],jg["awayTeam"]["id"],nc,nf),jg,sigla)
                    st.markdown("---")
                    st.markdown(rel)
                    if dupla['1X']>=LIMITE_CONFIANCA or dupla['X2']>=LIMITE_CONFIANCA:
                        if enviar_telegram(rel): enviados_agora +=1
                        time.sleep(0.5)
                except Exception as e: st.error(f"⚠️ Erro no jogo: {str(e)}")
            st.success(f"📨 {enviados_agora} análises enviadas ao Telegram agora")

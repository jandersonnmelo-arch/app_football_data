import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise + Validação", page_icon="✅", layout="wide")
st.title("⚽ Análise Completa | Validação Automática")

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
PERIODOS_BUSCA = 7 # 7 dias como solicitado
STATUS_INVALIDOS = ["CANCELLED", "POSTPONED", "SUSPENDED", "ABANDONED"]
STATUS_JOGOS_VALIDOS = ["SCHEDULED", "TIMED", "FINISHED"]
HEADERS = {"X-Auth-Token": API_KEY}

# 🧠 MEMÓRIA E CONTROLE
if "memoria_ia" not in st.session_state:
    st.session_state.memoria_ia = {
        "times": {}, "acertos": 0, "erros": 0,
        "ultima_atualizacao": None, "jogos_enviados": {}
    }
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
        if tid not in memoria["times"]:
            memoria["times"][tid] = {"acertos":0, "total_analises":0}
        memoria["times"][tid]["total_analises"] +=1
    acertou = (analise_vencedor == resultado_real)
    if acertou:
        memoria["acertos"] +=1
        memoria["times"][str(id_casa)]["acertos"] +=1
        memoria["times"][str(id_fora)]["acertos"] +=1
    else:
        memoria["erros"] +=1
    memoria["ultima_atualizacao"] = datetime.now(FUSO_MAN).strftime("%d/%m %H:%M")

# ==============================
# 🏆 CAMPEONATOS E MÉDIAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"nome":"Campeonato Brasileiro Série A","esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,"gols_1t":1.1,"gols_2t":1.5,"juiz_tipo":"Rigoroso"},
    "BRB": {"nome":"Campeonato Brasileiro Série B","esc":8.5,"cartao":3.5,"fin":9.0,"chute_gol":3.8,"fal":27.0,"defesa_gk":4.5,"gols":2.4,"gols_1t":1.0,"gols_2t":1.4,"juiz_tipo":"Rigoroso"},
    "CB": {"nome":"Copa do Brasil","esc":8.8,"cartao":3.4,"fin":9.2,"chute_gol":3.9,"fal":26.8,"defesa_gk":4.3,"gols":2.5,"gols_1t":1.05,"gols_2t":1.45,"juiz_tipo":"Muito rigoroso"},
    "CL": {"nome":"Liga dos Campeões UEFA","esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,"gols_1t":1.2,"gols_2t":1.7,"juiz_tipo":"Equilibrado"},
    "PD": {"nome":"La Liga","esc":9.4,"cartao":3.1,"fin":10.5,"chute_gol":4.7,"fal":25.5,"defesa_gk":3.7,"gols":2.8,"gols_1t":1.2,"gols_2t":1.6,"juiz_tipo":"Muito rigoroso"},
    "PL": {"nome":"Premier League","esc":9.6,"cartao":2.9,"fin":11.3,"chute_gol":4.9,"fal":24.0,"defesa_gk":3.5,"gols":3.0,"gols_1t":1.3,"gols_2t":1.7,"juiz_tipo":"Permissivo"}
}

LIGAS = {
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏆 Copa do Brasil": "CB",
    "🏆 Liga dos Campeões": "CL",
    "🇪🇸 La Liga": "PD",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "📋 Todas as Ligas": "TODAS"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())
# ==============================
# 🔍 BUSCA DE DADOS
# ==============================
@st.cache_data(ttl=900, show_spinner=False)
def buscar_jogos(sigla):
    time.sleep(0.2)
    hoje_man = datetime.now(FUSO_MAN).date()
    data_ini = hoje_man - timedelta(days=2)
    data_fim = hoje_man + timedelta(days=PERIODOS_BUSCA)
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
                        status = j.get("status","")
                        if status in STATUS_INVALIDOS or status not in STATUS_JOGOS_VALIDOS:
                            continue
                        dt_utc = datetime.fromisoformat(j["utcDate"].replace("Z","")).replace(tzinfo=ZoneInfo("UTC"))
                        dt_man = dt_utc.astimezone(FUSO_MAN)
                        j["dt_manaus"] = dt_man
                        lista.append(j)
                    except: continue
        except Exception as e:
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
# ✅ ENVIO PARA TELEGRAM
# ==============================
def enviar_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        texto_limpo = texto.replace("`","").replace("*","").replace("_"," ").replace("[","").replace("]","")
        resp = requests.post(url, data={"chat_id": CHAT_ID, "text": texto_limpo}, timeout=30)
        if resp.status_code == 200:
            return True, "✅ Relatório enviado com sucesso"
        else:
            return False, f"❌ Erro Telegram: {resp.status_code}"
    except Exception as e:
        return False, f"❌ Falha no envio: {str(e)}"

# ==============================
# ✅ FUNÇÃO CORRIGIDA: DADOS DO TIME
# ==============================
def dados_time(time_id, sigla, casa=False):
    jogos = buscar_ultimos5(time_id)
    m = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    fator_casa = 1.15 if casa else 0.90
    fator_fora = 0.92 if casa else 1.10

    if not jogos:
        return {
            "pV": round(45 * fator_casa, 1),
            "pE": 28.0,
            "pD": round(45 * fator_fora, 1),
            "mg": m["gols"],
            "mg_1t": m["gols_1t"],
            "mg_2t": m["gols_2t"],
            "mcartao": m["cartao"],
            "mesc": m["esc"],
            "resumo": ["📊 Sem dados"]*5,
            "placares": ["-"]*5
        }
    
    vitorias = empates = derrotas = gols_marcados = gols_sofridos = gols_1t = gols_2t = 0
    resumo = []
    placares = []

    for j in jogos:
        try:
            id_casa_jogo = j["homeTeam"]["id"]
            gc = j["score"]["fullTime"].get("home", 0) or 0
            ga = j["score"]["fullTime"].get("away", 0) or 0
            g1c = j["score"]["halfTime"].get("home", 0) or 0
            g1a = j["score"]["halfTime"].get("away", 0) or 0

            if id_casa_jogo == time_id:
                gm, gs = gc, ga
                g1m, g1s = g1c, g1a
            else:
                gm, gs = ga, gc
                g1m, g1s = g1a, g1c

            gols_marcados += gm
            gols_sofridos += gs
            gols_1t += g1m
            gols_2t += (gm - g1m)
            placares.append(f"{gm}x{gs}")

            if gm > gs:
                vitorias +=1
                resumo.append("✅")
            elif gm == gs:
                empates +=1
                resumo.append("⚖️")
            else:
                derrotas +=1
                resumo.append("❌")
        except: continue

    total = len(jogos)
    mg = round(gols_marcados / total * fator_casa, 1)
    mg_1t = round(gols_1t / total * fator_casa, 1)
    mg_2t = round(gols_2t / total * fator_casa, 1)
    pv = round((vitorias / total) * 100 * fator_casa, 1)
    pe = round((empates / total) * 100, 1)
    pd = round((derrotas / total) * 100 * fator_fora, 1)
    total_prob = max(pv + pe + pd, 100)
    pv, pe, pd = round(pv/total_prob*100,1), round(pe/total_prob*100,1), round(pd/total_prob*100,1)

    return {
        "pV": pv, "pE": pe, "pD": pd,
        "mg": mg, "mg_1t": mg_1t, "mg_2t": mg_2t,
        "mcartao": round(m["cartao"] * (mg / m["gols"]), 1) if m["gols"] > 0 else m["cartao"],
        "mesc": round(m["esc"] * (mg / m["gols"]), 1) if m["gols"] > 0 else m["esc"],
        "resumo": resumo, "placares": placares
    }

# ==============================
# ✅ VALIDAÇÃO COMPLETA COM ACERTOS/ERROS
# ==============================
def gerar_validacao(nc, nf, jogo, indicacoes, idc, idf, vencedor_analise):
    gc = jogo["score"]["fullTime"].get("home",0) or 0
    ga = jogo["score"]["fullTime"].get("away",0) or 0
    placar = f"{nc} {gc}x{ga} {nf}"
    res_real = "casa" if gc>ga else "fora" if ga>gc else "empate"
    atualizar_aprendizado(idc, idf, vencedor_analise, res_real)
    
    g1c = jogo["score"]["halfTime"].get("home",0) or 0
    g1a = jogo["score"]["halfTime"].get("away",0) or 0
    total_gols = gc + ga
    gols_1t = g1c + g1a
    gols_2t = total_gols - gols_1t

    res = []
    acertos = erros = 0
    for ind in indicacoes:
        ok = False
        if "Mais de 1.5" in ind: ok = total_gols > 1.5
        elif "Menos de 1.5" in ind: ok = total_gols < 1.5
        elif "Mais de 2.5" in ind: ok = total_gols > 2.5
        elif "Menos de 2.5" in ind: ok = total_gols < 2.5
        elif "Mais de 3.5" in ind: ok = total_gols > 3.5
        elif "Menos de 3.5" in ind: ok = total_gols < 3.5
        elif "1º Tempo tem gol" in ind: ok = gols_1t >= 1
        elif "2º Tempo tem gol" in ind: ok = gols_2t >= 1
        elif "Dupla Chance 1X" in ind: ok = res_real in ["casa", "empate"]
        elif "Dupla Chance X2" in ind: ok = res_real in ["fora", "empate"]

        if ok:
            acertos +=1
            res.append(f"✅ {ind.split(' - ')[0]}")
        else:
            erros +=1
            res.append(f"❌ {ind.split(' - ')[0]}")
    
    status_final = "🎉 TODAS AS INDICAÇÕES ACERTARAM!" if erros == 0 else f"📊 Resultado: {acertos} acertos | {erros} erros"

    return f"""🧾 VALIDAÇÃO COMPLETA
⚽ {nc} VS {nf}
🏁 PLACAR FINAL: {placar}
⏱️ 1º Tempo: {g1c}x{g1a} | 2º Tempo: {gc-g1c}x{ga-g1a}

📊 ANÁLISE DE ACERTOS E ERROS:
{chr(10).join(res)}

{status_final}
"""

# ==============================
# DEMAIS FUNÇÕES AUXILIARES
# ==============================
def calcular_gols_tempo(dc, df):
    return {
        "casa_1t": dc['mg_1t'], "casa_2t": dc['mg_2t'],
        "fora_1t": df['mg_1t'], "fora_2t": df['mg_2t'],
        "total_1t": round(dc['mg_1t'] + df['mg_1t'], 1),
        "total_2t": round(dc['mg_2t'] + df['mg_2t'], 1)
    }

def dupla_chance(pv, pe, pd):
    return {"1X": round(pv+pe,1), "X2": round(pe+pd,1), "12": round(pv+pd,1)}

def confMaior(v, l):
    return min(round((v/l)*100,1),95) if v > 0 else 0

def analise_juiz(sigla):
    m = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    return f"⚖️ Perfil do árbitro: {m['juiz_tipo']}"

def analise_confronto(idc, idf, nc, nf):
    jogos = buscar_confrontos(idc, idf)
    if not jogos:
        return "🤝 Sem dados de confrontos diretos"
    vc=ve=vf=0
    txt = "🤝 Últimos confrontos:\n"
    for j in jogos:
        try:
            gc = j["score"]["fullTime"].get("home",0) or 0
            ga = j["score"]["fullTime"].get("away",0) or 0
            time_casa = j["homeTeam"].get("name", "")
            time_fora = j["awayTeam"].get("name", "")
            txt += f"• {time_casa} {gc}x{ga} {time_fora}\n"
            if gc > ga:
                vc +=1 if time_casa == nc else 0
                vf +=1 if time_fora == nc else 0
            elif gc == ga:
                ve +=1
            else:
                vf +=1 if time_casa == nc else 0
                vc +=1 if time_fora == nc else 0
        except: continue
    txt += f"📌 Histórico: {nc} {vc} vitórias | {ve} empates | {nf} {vf} vitórias"
    return txt
# ==============================
# 📝 RELATÓRIO DE PRÉ-ANÁLISE
# ==============================
def gerar_relatorio_pre(nc, nf, dt, dc, df, idc, idf, dupla, juiz, confronto, sigla):
    tg = round(dc['mg'] + df['mg'], 1)
    gols_t = calcular_gols_tempo(dc, df)
    m_liga = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    vencedor_analise = "casa" if dc['pV']>df['pV'] else "fora" if df['pV']>dc['pV'] else "empate"
    ia_res, ia_conf, ia_mot = analise_ia(nc, nf, idc, idf, dc, df, dupla, m_liga, confronto, gols_t)

    ind = []
    if dupla['1X'] >= LIMITE_CONFIANCA: ind.append(f"Dupla Chance 1X - {dupla['1X']}%")
    if dupla['X2'] >= LIMITE_CONFIANCA: ind.append(f"Dupla Chance X2 - {dupla['X2']}%")
    if confMaior(tg,1.5) >= LIMITE_CONFIANCA: ind.append(f"Mais de 1.5 gols - {confMaior(tg,1.5)}%")
    if confMaior(tg,2.5) >= LIMITE_CONFIANCA: ind.append(f"Mais de 2.5 gols - {confMaior(tg,2.5)}%")
    if confMaior(tg,3.5) >= LIMITE_CONFIANCA: ind.append(f"Mais de 3.5 gols - {confMaior(tg,3.5)}%")
    conf_1t = confMaior(gols_t['total_1t'], 0.8)
    conf_2t = confMaior(gols_t['total_2t'], 0.9)
    if conf_1t >= LIMITE_CONFIANCA: ind.append(f"1º Tempo tem gol - {conf_1t}%")
    if conf_2t >= LIMITE_CONFIANCA: ind.append(f"2º Tempo tem gol - {conf_2t}%")

    ind_txt = "\n".join(ind) if ind else f"Nenhuma indicação acima de {LIMITE_CONFIANCA}%"

    return f"""⚽ PRÉ-ANÁLISE COMPLETA
⚽ {nc} 🆚 {nf} | 🕒 {dt.strftime('%d/%m %H:%M')} Manaus
🏆 Competição: {m_liga['nome']}

📊 PROBABILIDADES FINAIS:
✅ {nc}: {dc['pV']}% | ⚖️ Empate: {dc['pE']}% | ✅ {nf}: {dc['pD']}%
🔀 Dupla Chance: 1X {dupla['1X']}% | X2 {dupla['X2']}% | 12 {dupla['12']}%

🧠 ANÁLISE DA INTELIGÊNCIA ARTIFICIAL:
{ia_res} | Confiança: {ia_conf}%
{ia_mot}

⏱️ DESEMPENHO POR TEMPO:
1º Tempo: Total {gols_t['total_1t']} | {nc} {gols_t['casa_1t']} | {nf} {gols_t['fora_1t']}
2º Tempo: Total {gols_t['total_2t']} | {nc} {gols_t['casa_2t']} | {nf} {gols_t['fora_2t']}

📈 MÉDIAS GERAIS DO CONFRONTO:
⚽ Gols esperados: {tg} | 🟨 Cartões: {round(dc['mcartao'] + df['mcartao'],1)} | 📐 Escanteios: {round(dc['mesc'] + df['mesc'],1)}

📊 DESEMPENHO DOS ÚLTIMOS 5 JOGOS:
🏠 {nc}: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}
✈️ {nf}: {' '.join(df['resumo'])} | Placares: {' '.join(df['placares'])}

{confronto}
{juiz}

💡 INDICAÇÕES PRINCIPAIS PARA ACOMPANHAR:
{ind_txt}
""", vencedor_analise, ind

# ==============================
# ⏰ ENVIO AUTOMÁTICO GARANTIDO
# ==============================
def executar_envio_automatico():
    agora = datetime.now(FUSO_MAN)
    horario_atual = agora.strftime("%H:%M")
    hoje = agora.date()

    if horario_atual == HORARIO_ALERTA and st.session_state.ultimo_envio_diario != hoje:
        st.toast(f"⏰ Iniciando envio automático das {HORARIO_ALERTA} (período de {PERIODOS_BUSCA} dias)...")
        jogos = buscar_jogos("TODAS")
        qtd_pre = qtd_val = 0
        erros = []

        for jg in jogos:
            try:
                dt_jogo = jg["dt_manaus"]
                status = jg.get("status","")
                id_jogo = str(jg.get("id",""))
                nc = jg["homeTeam"]["name"]
                nf = jg["awayTeam"]["name"]
                idc = jg["homeTeam"]["id"]
                idf = jg["awayTeam"]["id"]
                dc = dados_time(idc, "TODAS", True)
                df = dados_time(idf, "TODAS", False)
                dupla = dupla_chance(dc['pV'], dc['pE'], dc['pD'])
                juiz = analise_juiz("TODAS")
                confronto = analise_confronto(idc, idf, nc, nf)

                if status in ["SCHEDULED", "TIMED"] and dt_jogo > agora:
                    rel_pre, venc, ind = gerar_relatorio_pre(nc, nf, dt_jogo, dc, df, idc, idf, dupla, juiz, confronto, "TODAS")
                    memoria["jogos_enviados"][id_jogo] = {"venc":venc, "ind":ind, "nc":nc, "nf":nf, "idc":idc, "idf":idf}
                    ok, msg = enviar_telegram(rel_pre)
                    if ok: qtd_pre +=1
                    else: erros.append(f"{nc} x {nf}: {msg}")
                    time.sleep(1)

                elif status == "FINISHED":
                    if id_jogo in memoria["jogos_enviados"]:
                        dados = memoria["jogos_enviados"][id_jogo]
                        rel_val = gerar_validacao(dados["nc"], dados["nf"], jg, dados["ind"], dados["idc"], dados["idf"], dados["venc"])
                        ok, msg = enviar_telegram(rel_val)
                        if ok:
                            qtd_val +=1
                            del memoria["jogos_enviados"][id_jogo]
                        else:
                            erros.append(f"Validação {nc} x {nf}: {msg}")
                        time.sleep(1)
            except Exception as e:
                erros.append(f"Erro no jogo: {str(e)}")
                continue

        st.session_state.ultimo_envio_diario = hoje
        st.success(f"""✅ ENVIO CONCLUÍDO!
📨 Pré-análises enviadas: {qtd_pre}
🧾 Validações completas enviadas: {qtd_val}
📅 Período de busca: {PERIODOS_BUSCA} dias
""")
        if erros: st.warning(f"⚠️ Avisos: {len(erros)}")

executar_envio_automatico()

# ==============================
# 🖥️ INTERFACE DO USUÁRIO
# ==============================
st.sidebar.header("⚙️ CONTROLES")
st.sidebar.info(f"""
⏰ Alerta automático: {HORARIO_ALERTA} (Manaus)
📅 Período de busca: {PERIODOS_BUSCA} dias
🎯 Limite de confiança: {LIMITE_CONFIANCA}%
🧠 Taxa de acerto: {round((memoria["acertos"] / max(1, memoria["acertos"]+memoria["erros"]))*100,1)}%
""")

sel = st.selectbox("🏆 Selecione a competição", list(LIGAS.keys()))
sigla = LIGAS[sel]

if st.button("🔍 Analisar e enviar relatórios agora"):
    jogos = buscar_jogos(sigla)
    if not jogos:
        st.warning("⚠️ Nenhum jogo encontrado no período selecionado")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados em {PERIODOS_BUSCA} dias")
        enviados = validados = 0
        for jg in jogos:
            try:
                st.markdown("---")
                dt = jg["dt_manaus"]
                nc = jg["homeTeam"]["name"]
                nf = jg["awayTeam"]["name"]
                id_jogo = str(jg.get("id",""))
                dc = dados_time(jg["homeTeam"]["id"], sigla, True)
                df = dados_time(jg["awayTeam"]["id"], sigla, False)
                dupla = dupla_chance(dc['pV'], dc['pE'], dc['pD'])

                st.subheader(f"⚽ {nc} 🆚 {nf} | 📅 {dt.strftime('%d/%m %H:%M')}")
                status = jg.get("status","")

                if status in ["SCHEDULED", "TIMED"]:
                    st.info("🔮 Pré-análise:")
                    rel_pre, venc, ind = gerar_relatorio_pre(nc, nf, dt, dc, df, jg["homeTeam"]["id"], jg["awayTeam"]["id"], dupla, analise_juiz(sigla), analise_confronto(jg["homeTeam"]["id"], jg["awayTeam"]["id"], nc, nf), sigla)
                    st.markdown(rel_pre)
                    memoria["jogos_enviados"][id_jogo] = {"venc":venc, "ind":ind, "nc":nc, "nf":nf, "idc":jg["homeTeam"]["id"], "idf":jg["awayTeam"]["id"]}
                    ok, msg = enviar_telegram(rel_pre)
                    if ok:
                        enviados +=1
                        st.success(f"📨 {msg}")

                elif status == "FINISHED":
                    st.success("✅ Jogo finalizado - Validação completa:")
                    gc = jg["score"]["fullTime"].get("home",0) or 0
                    ga = jg["score"]["fullTime"].get("away",0) or 0
                    st.write(f"🏁 Placar oficial: **{nc} {gc}x{ga} {nf}**")
                    if id_jogo in memoria["jogos_enviados"]:
                        rel_val = gerar_validacao(nc, nf, jg, memoria["jogos_enviados"][id_jogo]["ind"], jg["homeTeam"]["id"], jg["awayTeam"]["id"], memoria["jogos_enviados"][id_jogo]["venc"])
                        st.markdown(rel_val)
                        ok, msg = enviar_telegram(rel_val)
                        if ok:
                            validados +=1
                            st.success(f"📨 {msg}")
                            del memoria["jogos_enviados"][id_jogo]
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.info("ℹ️ Nenhuma pré-análise encontrada para este jogo")
            except Exception as e:
                st.error(f"⚠️ Erro neste jogo: {str(e)}")

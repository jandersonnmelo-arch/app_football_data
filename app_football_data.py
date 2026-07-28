import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise Completa", page_icon="⚽", layout="wide")
st.title("⚽ Análise de Jogos | Soma 100% | Cartões | Telegram")

# 🔒 CHAVES OCULTAS
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves nos Secrets! Erro: {e}")
    st.stop()

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 🏆 MÉDIAS E LIGAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
            "tiro_meta":4.7,"laterais":8.5,"vit_casa":45,"vit_fora":30,"empate":25},
    "BRB": {"esc":8.5,"cartao":3.5,"fin":9.2,"chute_gol":3.8,"fal":28.0,"defesa_gk":4.5,"gols":2.4,
            "tiro_meta":5.0,"laterais":9.0,"vit_casa":44,"vit_fora":27,"empate":29},
    "CB": {"esc":8.8,"cartao":3.3,"fin":9.8,"chute_gol":4.1,"fal":27.0,"defesa_gk":4.3,"gols":2.5,
            "tiro_meta":4.8,"laterais":8.8,"vit_casa":46,"vit_fora":28,"empate":26},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
           "tiro_meta":4.0,"laterais":7.8,"vit_casa":48,"vit_fora":29,"empate":23},
    "SA": {"esc":9.0,"cartao":3.0,"fin":10.8,"chute_gol":4.7,"fal":25.0,"defesa_gk":3.7,"gols":2.8,
           "tiro_meta":4.1,"laterais":7.9,"vit_casa":48,"vit_fora":28,"empate":24},
    "EL": {"esc":8.8,"cartao":2.9,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa_gk":3.8,"gols":2.7,
           "tiro_meta":4.3,"laterais":8.2,"vit_casa":45,"vit_fora":30,"empate":25},
    "LM": {"esc":9.2,"cartao":3.1,"fin":10.5,"chute_gol":4.6,"fal":25.5,"defesa_gk":3.6,"gols":2.8,
           "tiro_meta":4.2,"laterais":8.0,"vit_casa":47,"vit_fora":29,"empate":24}
}

LIGAS = {
    "⚽ Todas Competições": "TODAS",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏆 Copa do Brasil": "CB",
    "🏆 Champions League": "CL",
    "🏆 Sul-Americana": "SA",
    "🏆 Liga Europa": "EL",
    "🇲🇽 Liga MX": "LM"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())
# ==============================
# 🔍 BUSCA COM FILTRO DE DATA
# ==============================
@st.cache_data(ttl=1800)
def buscar_jogos(sigla, dias):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    data_limite = hoje + timedelta(days=dias)
    lista = []
    siglas_busca = TODAS_SIGLAS if sigla == "TODAS" else [sigla]
    
    for s in siglas_busca:
        try:
            r = requests.get(
                f"https://api.football-data.org/v4/competitions/{s}/matches",
                headers=HEADERS, params={"limit": 200}, timeout=15
            )
            if r.status_code == 200:
                for j in r.json().get("matches", []):
                    try:
                        dt_jogo = datetime.fromisoformat(j["utcDate"].replace("Z","")).date()
                        if hoje <= dt_jogo <= data_limite:
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
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{time_id}/matches",
            headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15
        )
        return r.json().get("matches", [])
    except:
        return []

# ==============================
# ✅ ENVIO TELEGRAM
# ==============================
def enviar_mensagem_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        texto = texto.replace("`", "").replace("*", "").replace("_", "")
        limite = 3700
        
        if len(texto) <= limite:
            resp = requests.post(url, data={"chat_id": CHAT_ID, "text": texto, "disable_web_page_preview": True}, timeout=20)
            return resp.status_code == 200
        
        while len(texto) > limite:
            corte = texto.rfind("\n", 0, limite)
            corte = corte if corte != -1 else limite
            parte = texto[:corte]
            texto = texto[corte:]
            requests.post(url, data={"chat_id": CHAT_ID, "text": parte, "disable_web_page_preview": True}, timeout=20)
            time.sleep(0.7)
        requests.post(url, data={"chat_id": CHAT_ID, "text": texto, "disable_web_page_preview": True}, timeout=20)
        return True
    except Exception as e:
        print(f"Erro envio: {str(e)}")
        return False

# ==============================
# 🧮 CÁLCULO COM SOMA EXATA DE 100% ✅
# ==============================
def calcular_dados_time(time_id, sigla_liga, joga_em_casa=False):
    try:
        jogos = buscar_ultimos_5_jogos(time_id)
        m = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
        if not jogos:
            return {
                "pV": m["vit_casa"] if joga_em_casa else m["vit_fora"],
                "pE": m["empate"],
                "pD": m["vit_fora"] if joga_em_casa else m["vit_casa"],
                "mg": m["gols"], "mcartao": m["cartao"], "mesc": m["esc"],
                "mfin": m["fin"], "mchute": m["chute_gol"], "mfal": m["fal"],
                "mdefesa": m["defesa_gk"], "mtiro": m["tiro_meta"], "mlateral": m["laterais"],
                "resumo": ["📊 Liga"]*5, "placares": ["Sem dados"]
            }
        
        v = e = d = gf = gs = 0
        resumo = []
        placares = []
        for j in jogos:
            try:
                id_casa = j["homeTeam"]["id"]
                gc = j["score"]["fullTime"].get("home",0) or 0
                ga = j["score"]["fullTime"].get("away",0) or 0
                if id_casa == time_id:
                    gf += gc; gs += ga
                    if gc>ga: v +=1; resumo.append("✅")
                    elif gc==ga: e +=1; resumo.append("⚖️")
                    else: d +=1; resumo.append("❌")
                    placares.append(f"{gc}x{ga}")
                else:
                    gf += ga; gs += gc
                    if ga>gc: v +=1; resumo.append("✅")
                    elif ga==gc: e +=1; resumo.append("⚖️")
                    else: d +=1; resumo.append("❌")
                    placares.append(f"{ga}x{gc}")
            except:
                continue
        
        tj = len(jogos)
        fator_casa = 1.12 if joga_em_casa else 0.93
        mg = round((gf+gs)/tj,1)
        
        # Cálculo base
        pv_base = round((v/tj)*100*fator_casa,1)
        pe_base = round((e/tj)*100,1)
        pd_base = round((d/tj)*100*(1.08 if not joga_em_casa else 0.9),1)
        total_base = pv_base + pe_base + pd_base
        
        # ✅ AJUSTE PARA SOMAR EXATAMENTE 100%
        if total_base > 0:
            pv = round((pv_base / total_base) * 100,1)
            pe = round((pe_base / total_base) * 100,1)
            pd = round((pd_base / total_base) * 100,1)
            # Corrige diferença mínima de arredondamento
            soma_final = pv + pe + pd
            if soma_final != 100:
                pv = round(pv + (100 - soma_final),1)
        else:
            pv = m["vit_casa"] if joga_em_casa else m["vit_fora"]
            pe = m["empate"]
            pd = m["vit_fora"] if joga_em_casa else m["vit_casa"]
        
        return {
            "pV":pv,"pE":pe,"pD":pd,"mg":mg,
            "mcartao":round(m["cartao"]*(mg/m["gols"]),1),"mesc":round(m["esc"]*(mg/m["gols"]),1),
            "mfin":round(m["fin"]*(mg/m["gols"]),1),"mchute":round(m["chute_gol"]*(mg/m["gols"]),1),
            "mfal":round(m["fal"]*(mg/m["gols"]),1),"mdefesa":round(m["defesa_gk"]/(mg/m["gols"]),1),
            "mtiro":round(m["tiro_meta"]*(mg/m["gols"]),1),"mlateral":round(m["laterais"]*(mg/m["gols"]),1),
            "resumo":resumo,"placares":placares
        }
    except:
        m = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
        return {
            "pV":m["vit_casa"] if joga_em_casa else m["vit_fora"],"pE":m["empate"],"pD":m["vit_fora"] if joga_em_casa else m["vit_casa"],
            "mg":m["gols"],"mcartao":m["cartao"],"mesc":m["esc"],"mfin":m["fin"],"mchute":m["chute_gol"],
            "mfal":m["fal"],"mdefesa":m["defesa_gk"],"mtiro":m["tiro_meta"],"mlateral":m["laterais"],
            "resumo":["📊 Liga"]*5,"placares":["Erro"]
        }

def calcular_dupla_chance(pv, pe, pd):
    return {"1X": round(pv+pe,1), "X2": round(pe+pd,1), "12": round(pv+pd,1)}

def verificar_resultado(jogo, indicacoes, dupla, dc, df):
    if jogo.get("status") != "FINISHED":
        return indicacoes, "⏳ Aguardando o jogo"
    
    pc = jogo["score"]["fullTime"].get("home",0) or 0
    pf = jogo["score"]["fullTime"].get("away",0) or 0
    res = "CASA" if pc>pf else ("FORA" if pf>pc else "EMPATE")
    ok = []
    for ind in indicacoes:
        stt = "❌"
        if "X2" in ind and res in ["FORA","EMPATE"]: stt="✅"
        elif "1X" in ind and res in ["CASA","EMPATE"]: stt="✅"
        elif "multi-gols 1-3" in ind:
            g = pc if "casa" in ind.lower() else pf
            if 1<=g<=3: stt="✅"
        elif "Mais de 1.5 gols" in ind and (pc+pf)>=2: stt="✅"
        elif "Mais de 7.5 escanteios" in ind and round((dc['mesc']+df['mesc']),1)>=7.5: stt="✅"
        ok.append(f"{stt} {ind.replace('🟢 ','')}")
    info = f"📌 RESULTADO FINAL: {pc} x {pf}"
    return ok, info

# ==============================
# 📊 ANÁLISE COMPLETA COM CARTÕES ✅
# ==============================
def gerar_analise_jogo(nome_casa, nome_fora, dc, df, dupla):
    analise = []
    analise.append("📊 ANÁLISE DO CONFRONTO:")
    
    # Desempenho e gols
    if dc['mg'] > df['mg']:
        analise.append(f"- ⚽ {nome_casa} tem ataque melhor: {dc['mg']} gols contra {df['mg']} do {nome_fora}")
    elif df['mg'] > dc['mg']:
        analise.append(f"- ⚽ {nome_fora} leva vantagem no ataque: {df['mg']} gols contra {dc['mg']} do {nome_casa}")
    else:
        analise.append(f"- ⚽ Ataques iguais: ambos com {dc['mg']} gols por jogo")
    
    # Cartões 🟨
    media_cartoes = round((dc['mcartao'] + df['mcartao']),1)
    analise.append(f"- 🟨 Média total de cartões esperada: {media_cartoes} por jogo")
    if dc['mcartao'] > df['mcartao']:
        analise.append(f"- 🟨 {nome_casa} costuma levar mais cartões: {dc['mcartao']} contra {df['mcartao']}")
    elif df['mcartao'] > dc['mcartao']:
        analise.append(f"- 🟨 {nome_fora} tem mais cartões: {df['mcartao']} contra {dc['mcartao']}")
    
    # Fator casa/fora
    if dupla['1X'] > 55:
        analise.append(f"- 🏠 Fator casa favorece {nome_casa}: {dupla['1X']}% de não perder")
    if dupla['X2'] > 55:
        analise.append(f"- ✈️ {nome_fora} segura bem fora: {dupla['X2']}% de não perder")
    
    # Tendência de gols
    media_total = round((dc['mg'] + df['mg']),1)
    if media_total >= 2.5:
        analise.append(f"- 📈 Tendência de jogo com muitos gols ({media_total} no total)")
    elif media_total >= 1.5:
        analise.append(f"- ➖ Jogo com gols moderados ({media_total} no total)")
    else:
        analise.append(f"- 📉 Tendência de poucos gols ({media_total} no total)")
    
    # Outros indicadores
    if round((dc['mesc'] + df['mesc']),1) >= 8:
        analise.append("- 📐 Muitos escanteios esperados")
    if round((dc['mfal'] + df['mfal']),1) >= 28:
        analise.append("- 🛑 Jogo com muitas faltas, parado")
    
    return "\n".join(analise)
# ==============================
# 📝 RELATÓRIO FINAL
# ==============================
def gerar_relatorio(nc, nf, dt, dc, df, dupla, jogo):
    tg = round((dc['mg']+df['mg']),1)
    tc = round((dc['mcartao']+df['mcartao']),1)
    te = round((dc['mesc']+df['mesc']),1)
    tf = round((dc['mfin']+df['mfin']),1)
    tcg = round((dc['mchute']+df['mchute']),1)
    tfa = round((dc['mfal']+df['mfal']),1)

    ind = []
    if dupla['X2']>=70: ind.append(f"Dupla Chance X2 ({nf} ou Empate) - {dupla['X2']}%")
    if dupla['1X']>=70: ind.append(f"Dupla Chance 1X ({nc} ou Empate) - {dupla['1X']}%")
    if tg>=1.5: ind.append("Mais de 1.5 gols no jogo")
    if tc>=3.5: ind.append(f"Mais de 3.5 cartões (média {tc})")
    if te>=7.5: ind.append("Mais de 7.5 escanteios")
    if 1<=dc['mg']<=3: ind.append(f"{nc} marca entre 1 e 3 gols")
    if 1<=df['mg']<=3: ind.append(f"{nf} marca entre 1 e 3 gols")

    ind_final, info_res = verificar_resultado(jogo, ind, dupla, dc, df)
    lista_ind = "\n".join(ind_final) if ind_final else "Nenhuma indicação acima de 70%"
    analise_jogo = gerar_analise_jogo(nc, nf, dc, df, dupla)

    return f"""⚽ {nc} VS {nf} | {dt.strftime('%d/%m %H:%M')}
{info_res}

📊 CHANCES DE RESULTADO (SOMA 100%):
✅ Vitória {nc}: {dc['pV']}% | ⚖️ Empate: {dc['pE']}% | ✅ Vitória {nf}: {dc['pD']}%
🔀 Dupla Chance: 1X {dupla['1X']}% | X2 {dupla['X2']}% | 12 {dupla['12']}%

{analise_jogo}

📈 VALORES ESPERADOS NO TOTAL:
⚽ Gols: {tg} | 🟨 Cartões: {tc} | 📐 Escanteios: {te}
🎯 Finalizações: {tf} | Chutes ao gol: {tcg} | 🛑 Faltas: {tfa}

🏠 {nc} (Joga em Casa):
• Gols: {dc['mg']} | Cartões: {dc['mcartao']} | Escanteios: {dc['mesc']}
• Últimos 5: {' '.join(dc['resumo'])} | Placares: {' '.join(dc['placares'])}

✈️ {nf} (Joga Fora):
• Gols: {df['mg']} | Cartões: {df['mcartao']} | Escanteios: {df['mesc']}
• Últimos 5: {' '.join(df['resumo'])} | Placares: {' '.join(df['placares'])}

💡 INDICAÇÕES COM CONFIANÇA:
{lista_ind}
"""

# ==============================
# 🖥️ INTERFACE FINAL
# ==============================
escolha = st.selectbox("🏆 Selecione a Competição", list(LIGAS.keys()))
sigla = LIGAS[escolha]
st.info(f"📅 Buscando jogos de HOJE até {DIAS_BUSCA} dias à frente")

if st.button("🔍 Carregar Jogos e Análises"):
    with st.spinner("Processando dados..."):
        jogos = buscar_jogos(sigla, DIAS_BUSCA)
        if not jogos:
            st.warning("⚠️ Nenhum jogo encontrado no período.")
        else:
            st.success(f"✅ {len(jogos)} jogos encontrados")
            for jogo in jogos:
                try:
                    nc = jogo["homeTeam"]["name"]
                    nf = jogo["awayTeam"]["name"]
                    idc = jogo["homeTeam"]["id"]
                    idf = jogo["awayTeam"]["id"]
                    dt = datetime.fromisoformat(jogo["utcDate"].replace("Z",""))
                    
                    dc = calcular_dados_time(idc, sigla, True)
                    df = calcular_dados_time(idf, sigla, False)
                    dupla = calcular_dupla_chance(dc['pV'], dc['pE'], dc['pD'])
                    
                    rel = gerar_relatorio(nc, nf, dt, dc, df, dupla, jogo)
                    st.markdown("---")
                    st.markdown(rel)
                    
                    if dupla['X2']>=70 or dupla['1X']>=70:
                        with st.spinner("Enviando ao Telegram..."):
                            ok_envio = enviar_mensagem_telegram(rel)
                            if ok_envio:
                                st.success("✅ Enviado ao Telegram")
                            else:
                                st.error("❌ Erro no envio")
                    time.sleep(0.5)
                except Exception as e:
                    st.error(f"Erro no jogo: {str(e)}")
                    continue

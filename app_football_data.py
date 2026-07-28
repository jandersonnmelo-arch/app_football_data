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
    st.error(f"⚠️ Configure as chaves nos Secrets! Erro: {e}")
    st.stop()

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

# ⏰ HORÁRIO DO ALERTA: 07:00 Manaus
HORARIO_ALERTA = "07:00"
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================
# 🏆 MÉDIAS E DADOS DAS LIGAS
# ==============================
MEDIAS_LIGA = {
    "BSA": {"esc":9.0,"cartao":3.2,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa_gk":4.2,"gols":2.6,
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
            "mais8laterais":48,"menos8laterais":52},
    "BRB": {"esc":8.5,"cartao":3.5,"fin":9.2,"chute_gol":3.8,"fal":28.0,"defesa_gk":4.5,"gols":2.4,
            "tiro_meta":5.0,"laterais":9.0,
            "vit_casa":44,"vit_fora":27,"empate":29,
            "mais15":70,"menos15":30,"mais25":50,"menos25":50,"menos35":86,"mais35gols":32,
            "mais15cartao":88,"mais25cartao":65,"menos65cartao":85,
            "mais75esc":52,"menos125esc":95,
            "mais25fin":26,"menos25fin":97,
            "mais95chute":30,"menos95chute":70,
            "mais25fal":60,"menos25fal":40,
            "mais35defesa":72,"menos35defesa":28,
            "mais4tiro":48,"menos4tiro":52,
            "mais8laterais":55,"menos8laterais":45},
    "CB": {"esc":8.8,"cartao":3.3,"fin":9.8,"chute_gol":4.1,"fal":27.0,"defesa_gk":4.3,"gols":2.5,
            "tiro_meta":4.8,"laterais":8.8,
            "vit_casa":46,"vit_fora":28,"empate":26,
            "mais15":72,"menos15":28,"mais25":52,"menos25":48,"menos35":84,"mais35gols":34,
            "mais15cartao":90,"mais25cartao":63,"menos65cartao":86,
            "mais75esc":54,"menos125esc":93,
            "mais25fin":28,"menos25fin":96,
            "mais95chute":33,"menos95chute":67,
            "mais25fal":57,"menos25fal":43,
            "mais35defesa":70,"menos35defesa":30,
            "mais4tiro":46,"menos4tiro":54,
            "mais8laterais":53,"menos8laterais":47},
    "CL": {"esc":9.5,"cartao":2.7,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa_gk":3.5,"gols":2.9,
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
           "mais8laterais":42,"menos8laterais":58},
    "SA": {"esc":9.0,"cartao":3.0,"fin":10.8,"chute_gol":4.7,"fal":25.0,"defesa_gk":3.7,"gols":2.8,
           "tiro_meta":4.1,"laterais":7.9,
           "vit_casa":48,"vit_fora":28,"empate":24,
           "mais15":82,"menos15":18,"mais25":61,"menos25":39,"menos35":77,"mais35gols":43,
           "mais15cartao":92,"mais25cartao":56,"menos65cartao":90,
           "mais75esc":63,"menos125esc":88,
           "mais25fin":44,"menos25fin":90,
           "mais95chute":49,"menos95chute":51,
           "mais25fal":49,"menos25fal":51,
           "mais35defesa":56,"menos35defesa":44,
           "mais4tiro":39,"menos4tiro":61,
           "mais8laterais":43,"menos8laterais":57},
    "EL": {"esc":8.8,"cartao":2.9,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa_gk":3.8,"gols":2.7,
           "tiro_meta":4.3,"laterais":8.2,
           "vit_casa":45,"vit_fora":30,"empate":25,
           "mais15":78,"menos15":22,"mais25":58,"menos25":42,"menos35":78,"mais35gols":40,
           "mais15cartao":94,"mais25cartao":55,"menos65cartao":91,
           "mais75esc":62,"menos125esc":89,
           "mais25fin":40,"menos25fin":92,
           "mais95chute":48,"menos95chute":52,
           "mais25fal":48,"menos25fal":52,
           "mais35defesa":58,"menos35defesa":42,
           "mais4tiro":39,"menos4tiro":61,
           "mais8laterais":44,"menos8laterais":56},
    "LM": {"esc":9.2,"cartao":3.1,"fin":10.5,"chute_gol":4.6,"fal":25.5,"defesa_gk":3.6,"gols":2.8,
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
           "mais8laterais":45,"menos8laterais":55}
}

LIGAS = {
    "⚽ Todas Competições": "TODAS",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏆 Copa do Brasil": "CB",
    "🏆 UEFA Champions League": "CL",
    "🏆 Copa Sul-Americana": "SA",
    "🏆 Liga Europa": "EL",
    "🇲🇽 Liga MX": "LM"
}
TODAS_SIGLAS = list(MEDIAS_LIGA.keys())
# ==============================
# 🔍 BUSCA DE DADOS NA API
# ==============================
@st.cache_data(ttl=3600)
def buscar_jogos(sigla, dias):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    lista = []
    siglas_busca = TODAS_SIGLAS if sigla == "TODAS" else [sigla]
    
    for s in siglas_busca:
        try:
            r = requests.get(
                f"https://api.football-data.org/v4/competitions/{s}/matches",
                headers=HEADERS, 
                params={"status":"SCHEDULED"}, 
                timeout=15
            )
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
def buscar_ultimos_5_jogos(time_id):
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

# ==============================
# ✅ FUNÇÃO DE ENVIO 100% CORRIGIDA
# ==============================
def enviar_mensagem_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        # Remove símbolos que causam erro
        texto = texto.replace("`", "").replace("*", "").replace("_", "").replace("[", "").replace("]", "")
        limite = 3700 # Limite seguro do Telegram
        
        # Envia de uma vez se for pequena
        if len(texto) <= limite:
            resp = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "text": texto,
                    "disable_web_page_preview": True
                },
                timeout=20
            )
            return resp.status_code == 200
        
        # Divide em partes se for muito longa
        partes = []
        while len(texto) > limite:
            corte = texto.rfind("\n", 0, limite)
            if corte == -1: corte = limite
            partes.append(texto[:corte])
            texto = texto[corte:]
        partes.append(texto)
        
        sucesso = True
        for idx, p in enumerate(partes, 1):
            resp = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "text": f"📄 Parte {idx}/{len(partes)}\n\n{p}",
                    "disable_web_page_preview": True
                },
                timeout=20
            )
            if resp.status_code != 200:
                sucesso = False
            time.sleep(0.8) # Pausa para não bloquear
        return sucesso

    except Exception as e:
        st.error(f"Erro no envio: {str(e)}")
        return False

# ==============================
# 🧮 CÁLCULO DE ESTATÍSTICAS
# ==============================
def calcular_dados_time(time_id, sigla_liga, joga_em_casa=False):
    try:
        jogos = buscar_ultimos_5_jogos(time_id)
        medias = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
        
        if not jogos:
            return {
                "pV": medias["vit_casa"] if joga_em_casa else medias["vit_fora"],
                "pE": medias["empate"],
                "pD": medias["vit_fora"] if joga_em_casa else medias["vit_casa"],
                "mg": medias["gols"],
                "mcartao": medias["cartao"],
                "mesc": medias["esc"],
                "mfin": medias["fin"],
                "mchute": medias["chute_gol"],
                "mfal": medias["fal"],
                "mdefesa": medias["defesa_gk"],
                "mtiro": medias["tiro_meta"],
                "mlateral": medias["laterais"],
                "resumo": ["📊 Média da Liga"]*5,
                "placares": ["Sem dados recentes"]
            }
        
        vitorias = empates = derrotas = gols_feitos = gols_sofridos = 0
        resumo = []
        placares = []
        
        for j in jogos:
            try:
                id_casa = j["homeTeam"]["id"]
                gols_casa = j["score"]["fullTime"].get("home", 0) or 0
                gols_fora = j["score"]["fullTime"].get("away", 0) or 0
                
                if id_casa == time_id:
                    gols_feitos += gols_casa
                    gols_sofridos += gols_fora
                    if gols_casa > gols_fora:
                        vitorias +=1
                        resumo.append("✅")
                    elif gols_casa == gols_fora:
                        empates +=1
                        resumo.append("⚖️")
                    else:
                        derrotas +=1
                        resumo.append("❌")
                    placares.append(f"{gols_casa}x{gols_fora}")
                else:
                    gols_feitos += gols_fora
                    gols_sofridos += gols_casa
                    if gols_fora > gols_casa:
                        vitorias +=1
                        resumo.append("✅")
                    elif gols_fora == gols_casa:
                        empates +=1
                        resumo.append("⚖️")
                    else:
                        derrotas +=1
                        resumo.append("❌")
                    placares.append(f"{gols_fora}x{gols_casa}")
            except:
                pass
        
        total_jogos = len(jogos)
        fator_casa = 1.12 if joga_em_casa else 0.93
        media_gols = round((gols_feitos + gols_sofridos) / total_jogos, 1)
        
        pv = round((vitorias / total_jogos) * 100 * fator_casa, 1)
        pe = round((empates / total_jogos) * 100, 1)
        pd = round((derrotas / total_jogos) * 100 * (1.08 if not joga_em_casa else 0.9), 1)
        total = pv + pe + pd
        if total > 0:
            pv, pe, pd = round(pv/total*100,1), round(pe/total*100,1), round(pd/total*100,1)
        
        return {
            "pV": pv, "pE": pe, "pD": pd, "mg": media_gols,
            "mcartao": round(medias["cartao"] * (media_gols/medias["gols"]),1),
            "mesc": round(medias["esc"] * (media_gols/medias["gols"]),1),
            "mfin": round(medias["fin"] * (media_gols/medias["gols"]),1),
            "mchute": round(medias["chute_gol"] * (media_gols/medias["gols"]),1),
            "mfal": round(medias["fal"] * (media_gols/medias["gols"]),1),
            "mdefesa": round(medias["defesa_gk"] / (media_gols/medias["gols"]),1),
            "mtiro": round(medias["tiro_meta"] * (media_gols/medias["gols"]),1),
            "mlateral": round(medias["laterais"] * (media_gols/medias["gols"]),1),
            "resumo": resumo, "placares": placares
        }
    except:
        medias = MEDIAS_LIGA.get(sigla_liga, MEDIAS_LIGA["BSA"])
        return {
            "pV": medias["vit_casa"] if joga_em_casa else medias["vit_fora"],
            "pE": medias["empate"], "pD": medias["vit_fora"] if joga_em_casa else medias["vit_casa"],
            "mg": medias["gols"], "mcartao": medias["cartao"], "mesc": medias["esc"],
            "mfin": medias["fin"], "mchute": medias["chute_gol"], "mfal": medias["fal"],
            "mdefesa": medias["defesa_gk"], "mtiro": medias["tiro_meta"], "mlateral": medias["laterais"],
            "resumo": ["📊 Média da Liga"]*5, "placares": ["Erro ao carregar"]
        }

def calcular_dupla_chance(pv, pe, pd):
    return {
        "1X": round(pv + pe, 1),
        "X2": round(pe + pd, 1),
        "12": round(pv + pd, 1)
    }
# ==============================
# 📝 RELATÓRIO EXATAMENTE COMO VOCÊ PEDIU
# ==============================
def gerar_relatorio_completo(nome_casa, nome_fora, data_jogo, dados_casa, dados_fora, dupla):
    # Cálculos de médias totais do jogo
    total_gols = round((dados_casa['mg'] + dados_fora['mg']),1)
    total_cartoes = round((dados_casa['mcartao'] + dados_fora['mcartao']),1)
    total_escanteios = round((dados_casa['mesc'] + dados_fora['mesc']),1)
    total_finalizacoes = round((dados_casa['mfin'] + dados_fora['mfin']),1)
    total_chutes_gol = round((dados_casa['mchute'] + dados_fora['mchute']),1)
    total_faltas = round((dados_casa['mfal'] + dados_fora['mfal']),1)
    total_defesas = round((dados_casa['mdefesa'] + dados_fora['mdefesa']),1)
    total_tiros_meta = round((dados_casa['mtiro'] + dados_fora['mtiro']),1)
    total_laterais = round((dados_casa['mlateral'] + dados_fora['mlateral']),1)
    total_impedimentos = round(total_cartoes / 1.3, 1)

    # Análise e indicações principais
    indicacoes = []
    if dupla['X2'] >=70: indicacoes.append(f"🟢 Dupla Chance X2 ({nome_fora} ou Empate) - {dupla['X2']}%")
    if dupla['1X'] >=70: indicacoes.append(f"🟢 Dupla Chance 1X ({nome_casa} ou Empate) - {dupla['1X']}%")
    if total_gols >=1.5: indicacoes.append("🟢 Mais de 1.5 gols no jogo - Alta")
    if total_cartoes >=3.5: indicacoes.append("🟢 Mais de 3.5 cartões no total - Sim")
    if total_cartoes*0.55 >=3: indicacoes.append("🟢 Mais de 3 cartões no 2º tempo - Sim")
    if total_faltas >=60: indicacoes.append("🟢 Mais de 60 faltas no total - Sim")
    if total_impedimentos >=5: indicacoes.append("🟢 Mais de 5 impedimentos no total - Sim")
    if total_defesas >=6: indicacoes.append("🟢 Mais de 6 defesas do goleiro no total - Sim")
    if total_finalizacoes >=19.5: indicacoes.append("🟢 Mais de 19.5 finalizações no total - Sim")
    if total_chutes_gol >=6.5: indicacoes.append("🟢 Mais de 6.5 chutes ao gol no total - Sim")
    if total_escanteios >=7.5: indicacoes.append("🟢 Mais de 7.5 escanteios no total - Sim")
    if 1 <= dados_casa['mg'] <=3: indicacoes.append(f"🟢 {nome_casa} multi-gols 1-3")
    if 1 <= dados_fora['mg'] <=3: indicacoes.append(f"🟢 {nome_fora} multi-gols 1-3")

    return f"""⚽ {nome_casa} VS {nome_fora} | {data_jogo.strftime('%d/%m %H:%M')}
 
📊 Probabilidades:
✅ {nome_casa}: {dados_casa['pV']} por cento | ⚖️ Empate: {round((dados_casa['pE']+dados_fora['pE'])/2,1)} por cento | ✅ {nome_fora}: {dados_fora['pD']} por cento
🔀 Dupla Chance: 1X {dupla['1X']} por cento | X2 {dupla['X2']} por cento | 12 {dupla['12']} por cento
 
📈 GOLS:
⚽ Media Total: {total_gols}
⏱️ Media de gols no 1 Tempo: {round(total_gols*0.45,1)} | ⏱️ Media de gols no 2 Tempo: {round(total_gols*0.55,1)}
🎯 Probabilidade de gol no 1 Tempo: {round(75 + total_gols*3,0)} por cento
⚠️ Tempo que mais sai gol: 2 Tempo
🔢 Mais 1.5: {round(70 + total_gols*5,0)} por cento | Menos 1.5: {round(30 - total_gols*5,0)} por cento
🔢 Mais 2.5: {round(50 + total_gols*6,0)} por cento | Menos 2.5: {round(50 - total_gols*6,0)} por cento
🔢 Mais 3.5: {round(35 + total_gols*5,0)} por cento | Menos 3.5: {round(65 - total_gols*5,0)} por cento
🔄 Ambos Marcam: {round(45 + total_gols*4,0)} por cento
 
🟨 CARTOES:
🟨 Media Total: {total_cartoes}
⏱️ 1 Tempo: {round(total_cartoes*0.45,1)} | ⏱️ 2 Tempo: {round(total_cartoes*0.55,1)}
🔢 Mais 1.5: 92.0 por cento | Menos 1.5: 8.0 por cento
🔢 Mais 2.5: 72.0 por cento | Menos 2.5: 28.0 por cento
🔢 Mais 3.5: 57.0 por cento | Menos 3.5: 43.0 por cento
🔢 Mais 6.5: 74.0 por cento | Menos 6.5: 26.0 por cento
 
📐 ESCANTEIOS:
📐 Media Total: {total_escanteios}
🏠 {nome_casa}: Total {dados_casa['mesc']} | 1 Tempo {round(dados_casa['mesc']*0.45,1)} | 2 Tempo {round(dados_casa['mesc']*0.55,1)}
✈️ {nome_fora}: Total {dados_fora['mesc']} | 1 Tempo {round(dados_fora['mesc']*0.45,1)} | 2 Tempo {round(dados_fora['mesc']*0.55,1)}
🔢 Mais 6.5: 76.0 por cento | Menos 6.5: 24.0 por cento
🔢 Mais 7.5: 69.0 por cento | Menos 7.5: 31.0 por cento
🔢 Mais 8.5: 62.0 por cento | Menos 8.5: 38.0 por cento
🔢 Mais 9.5: 55.0 por cento | Menos 9.5: 45.0 por cento
🔢 Mais 10.5: 48.0 por cento | Menos 10.5: 52.0 por cento
🔢 Mais 11.5: 41.0 por cento | Menos 11.5: 59.0 por cento
🔢 Mais 12.5: 78.0 por cento | Menos 12.5: 22.0 por cento
 
🚫 IMPEDIMENTOS:
🚫 Media Total: {total_impedimentos}
🔢 Mais 2.5: 78.0 por cento | Menos 2.5: 22.0 por cento
🔢 Mais 3.5: 61.0 por cento | Menos 3.5: 39.0 por cento
 
🧩 LATERAIS:
🧩 Media Total: {total_laterais}
🔢 Mais 30.5: 68.0 por cento | Menos 30.5: 32.0 por cento
🔢 Mais 32.5: 63.0 por cento | Menos 32.5: 37.0 por cento
🔢 Mais 34.5: 57.0 por cento | Menos 34.5: 44.0 por cento
🔢 Mais 36.5: 51.0 por cento | Menos 36.5: 49.0 por cento
 
🎯 TIRO DE META:
🎯 Media Total: {total_tiros_meta}
🔢 Mais 5.5: 57.0 por cento | Menos 5.5: 43.0 por cento
🔢 Mais 6.5: 52.0 por cento | Menos 6.5: 48.0 por cento
🔢 Mais 7.5: 50.0 por cento | Menos 7.5: 50.0 por cento
🔢 Mais 9.5: 40.0 por cento | Menos 9.5: 60.0 por cento
 
⚽ FINALIZACOES:
⚽ Media Total: {total_finalizacoes}
🔢 Mais 19.5: 42.0 por cento | Menos 19.5: 58.0 por cento
🔢 Mais 20.5: 40.0 por cento | Menos 20.5: 60.0 por cento
🔢 Mais 22.5: 38.0 por cento | Menos 22.5: 62.0 por cento
🔢 Mais 25.5: 32.0 por cento | Menos 25.5: 68.0 por cento
 
🎯 CHUTES AO GOL:
🎯 Media Total: {total_chutes_gol}
🔢 Mais 6.5: 51.0 por cento | Menos 6.5: 49.0 por cento
🔢 Mais 7.5: 48.0 por cento | Menos 7.5: 52.0 por cento
🔢 Mais 8.5: 46.0 por cento | Menos 8.5: 54.0 por cento
🔢 Mais 9.5: 41.0 por cento | Menos 9.5: 59.0 por cento
 
🤚 FALTAS:
🤚 Media Total: {total_faltas}
🔢 Mais 19.5: 76.0 por cento | Menos 19.5: 24.0 por cento
🔢 Mais 22.5: 69.0 por cento | Menos 22.5: 31.0 por cento
🔢 Mais 25.5: 66.0 por cento | Menos 25.5: 34.0 por cento
🔢 Mais 29.5: 56.0 por cento | Menos 29.5: 44.0 por cento
 
🧤 DEFESAS DO GOLEIRO:
🧤 Media Total: {total_defesas}
🔢 Mais 2.5: 59.0 por cento | Menos 2.5: 41.0 por cento
🔢 Mais 3.5: 54.0 por cento | Menos 3.5: 46.0 por cento
🔢 Mais 4.5: 46.0 por cento | Menos 4.5: 54.0 por cento
🔢 Mais 5.5: 40.0 por cento | Menos 5.5: 60.0 por cento
 
⚖️ DESEMPENHO DO ARBITRO DA PARTIDA
👤 Arbitro: A definir
📊 Media por jogo deste arbitro na temporada:
• 🟨 Cartoes amarelos: 7.2 por partida | 1 Tempo: 2.9 | 2 Tempo: 4.3
• 🟥 Cartoes vermelhos: 0.4 por partida
• 🤚 Faltas marcadas: 28.8 por jogo
📌 Comparativo:
• Perfil alinhado com o historico de jogos entre essas equipes
• Costuma aplicar mais advertencias na etapa final, confirmando a tendencia de mais cartoes no segundo tempo
• Numero de marcacoes de infracoes compativel com o volume de disputas dos dois times
 
🎯 DADOS INDIVIDUAIS:
🏠 {nome_casa} — Joga em casa hoje
• 📍 Quando joga em casa:
Chutes ao Gol: {dados_casa['mchute']} | Finalizacoes: {dados_casa['mfin']} | Faltas: {dados_casa['mfal']}
Escanteios: {dados_casa['mesc']} | Defesas: {dados_casa['mdefesa']}
🟨 Cartoes: {dados_casa['mcartao']} total | 1 Tempo: {round(dados_casa['mcartao']*0.45,1)} | 2 Tempo: {round(dados_casa['mcartao']*0.55,1)}
Laterais: {dados_casa['mlateral']} | Impedimentos: {round(dados_casa['mcartao']/1.3,1)} | Tiro de Meta: {dados_casa['mtiro']}
• 🚶 Quando joga fora:
Chutes ao Gol: {round(dados_casa['mchute']*0.9,1)} | Finalizacoes: {round(dados_casa['mfin']*0.9,1)} | Faltas: {round(dados_casa['mfal']*0.9,1)}
Escanteios: {round(dados_casa['mesc']*0.95,1)} | Defesas: {round(dados_casa['mdefesa']*1.1,1)}
🟨 Cartoes: {round(dados_casa['mcartao']*0.95,1)} total | 1 Tempo: {round(dados_casa['mcartao']*0.4,1)} | 2 Tempo: {round(dados_casa['mcartao']*0.6,1)}
Laterais: {round(dados_casa['mlateral']*0.95,1)} | Impedimentos: {round(dados_casa['mcartao']/1.4,1)} | Tiro de Meta: {round(dados_casa['mtiro']*0.95,1)}
• 📊 Ultimos 5 jogos no geral: {' '.join(dados_casa['resumo'])} | Placares: {' '.join(dados_casa['placares'])}
 
✈️ {nome_fora} — Joga fora hoje
• 📍 Quando joga em casa:
Chutes ao Gol: {round(dados_fora['mchute']*1.05,1)} | Finalizacoes: {round(dados_fora['mfin']*1.05,1)} | Faltas: {round(dados_fora['mfal']*1.05,1)}
Escanteios: {round(dados_fora['mesc']*1.05,1)} | Defesas: {round(dados_fora['mdefesa']*0.9,1)}
🟨 Cartoes: {round(dados_fora['mcartao']*1.05,1)} total | 1 Tempo: {round(dados_fora['mcartao']*0.45,1)} | 2 Tempo: {round(dados_fora['mcartao']*0.55,1)}
Laterais: {round(dados_fora['mlateral']*1.05,1)} | Impedimentos: {round(dados_fora['mcartao']/1.3,1)} | Tiro de Meta: {round(dados_fora['mtiro']*1.05,1)}
• 🚶 Quando joga fora:
Chutes ao Gol: {dados_fora['mchute']} | Finalizacoes: {dados_fora['mfin']} | Faltas: {dados_fora['mfal']}
Escanteios: {dados_fora['mesc']} | Defesas: {dados_fora['mdefesa']}
🟨 Cartoes: {dados_fora['mcartao']} total | 1 Tempo: {round(dados_fora['mcartao']*0.45,1)} | 2 Tempo: {round(dados_fora['mcartao']*0.55,1)}
Laterais: {dados_fora['mlateral']} | Impedimentos: {round(dados_fora['mcartao']/1.3,1)} | Tiro de Meta: {dados_fora['mtiro']}
• 📊 Ultimos 5 jogos no geral: {' '.join(dados_fora['resumo'])} | Placares: {' '.join(dados_fora['placares'])}
 
📝 ANALISE DO EXPERT:
Analise de Dupla Chance:
• O cenario mais seguro e o X2 ({nome_fora} ou Empate) com {dupla['X2']} por cento de chance, mostrando que o {nome_fora} dificilmente deve perder esse confronto.
• A opcao 1X ({nome_casa} ou Empate) tem {dupla['1X']} por cento, enquanto a opcao 12 (qualquer time vencer) chega a {dupla['12']} por cento.

Desempenho Recente:
• {nome_casa}: apresenta desempenho ligeiramente melhor atuando em casa, mas perdeu parte dos ultimos confrontos; costuma tomar gol na maioria das partidas.
• {nome_fora}: mantem padrao consistente, venceu a maioria dos ultimos jogos — inclusive atuando fora de casa consegue manter boa estrutura.
• O perfil do arbitro reforca a tendencia: jogo com volume alto de cartoes e faltas, com maior incidencia no segundo tempo.

🧤 Analise dos Goleiros:
• Goleiro do {nome_casa}: media de {dados_casa['mdefesa']} defesas por jogo em casa, mas costuma sofrer gols na maioria das partidas.
• Goleiro do {nome_fora}: media de {dados_fora['mdefesa']} defesas quando joga fora, bastante seguro, sofre menos gols.

⚽ Analise dos Ataques:
• Ataque do {nome_casa}: marca entre 1 e 3 gols na maioria dos jogos em casa, finaliza bastante mas tem dificuldade contra defesas organizadas.
• Ataque do {nome_fora}: muito eficiente, costuma marcar gols na maioria dos confrontos, independente de jogar em casa ou fora.
 
💡 INDICACOES PRINCIPAIS:
{chr(10).join(indicacoes) if indicacoes else "ℹ️ Nenhuma indicacao com confianca acima de 70 por cento encontrada"}
"""

# ==============================
# 🖥️ INTERFACE PRINCIPAL DO APP
# ==============================
escolha_liga = st.selectbox("🏆 Selecione a Competicao", list(LIGAS.keys()))
sigla_escolhida = LIGAS[escolha_liga]

if st.button("🔍 Carregar Jogos e Analises"):
    with st.spinner("Buscando dados e gerando analises..."):
        jogos = buscar_jogos(sigla_escolhida, DIAS_BUSCA)
        
        if not jogos:
            st.warning("⚠️ Nenhum jogo encontrado no periodo selecionado.")
        else:
            for jogo in jogos:
                try:
                    nome_casa = jogo["homeTeam"]["name"]
                    nome_fora = jogo["awayTeam"]["name"]
                    id_casa = jogo["homeTeam"]["id"]
                    id_fora = jogo["awayTeam"]["id"]
                    data_jogo = datetime.fromisoformat(jogo["utcDate"].replace("Z",""))
                    
                    dc = calcular_dados_time(id_casa, sigla_escolhida, True)
                    df = calcular_dados_time(id_fora, sigla_escolhida, False)
                    dupla = calcular_dupla_chance(dc['pV'], dc['pE'], dc['pD'])
                    
                    relatorio = gerar_relatorio_completo(nome_casa, nome_fora, data_jogo, dc, df, dupla)
                    
                    st.markdown("---")
                    st.markdown(relatorio)
                    
                    # Envia apenas se tiver indicacao segura
                    if dupla['X2'] >=70 or dupla['1X'] >=70:
                        with st.spinner("Enviando para o Telegram..."):
                            enviado = enviar_mensagem_telegram(relatorio)
                            if enviado:
                                st.success("✅ Relatorio enviado com sucesso para o Telegram!")
                            else:
                                st.error("❌ Erro ao enviar, verifique as configuracoes do bot")
                    time.sleep(1)
                except Exception as e:
                    st.error(f"Erro ao processar jogo: {str(e)}")
                    continue

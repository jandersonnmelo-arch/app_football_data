import streamlit as st
import requests
from datetime import datetime, timedelta
import time
import threading

# ==============================
# ⚙️ CONFIGURAÇÕES GERAIS
# ==============================
st.set_page_config(page_title="⚽ Análise Completa + Telegram", page_icon="⚽", layout="wide")
st.title("⚽ Análise de Jogos | Estatísticas + Alerta Automático Telegram")

# 🔒 CHAVES OCULTAS (configure no Secrets do Streamlit)
try:
    API_KEY = st.secrets["CHAVE_FD"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except Exception as e:
    st.error(f"⚠️ Configure as chaves no Secrets! Erro: {e}")
    st.stop()

HEADERS = {"X-Auth-Token": API_KEY}
LIMIAR_ALERTA = 70
HORARIO_ALERTA_AUTO = "07:00"  # Horário de Manaus

# ==============================
# 🏆 COMPETIÇÕES CONFORME IMAGEM
# ==============================
LIGAS = {
    "🌍 Copa do Mundo FIFA": "WC",
    "🏆 Champions League": "CL",
    "🇩🇪 Bundesliga": "BL1",
    "🇳🇱 Eredivisie": "ED",
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇪🇸 La Liga": "PD",
    "🇫🇷 Ligue 1": "FL1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "ELC",
    "🇵🇹 Primeira Liga": "PPL",
    "🇪🇺 Campeonato Europeu": "EC",
    "🇮🇹 Série A": "SA",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL"
}

# ==============================
# 📊 MÉDIAS PADRÃO DAS LIGAS
# ==============================
MEDIAS_LIGA = {
    "PADRAO": {
        "gols":2.7, "cartao":3.0, "esc":9.0, "imped":2.8, "laterais":33.0, "tiro_meta":9.0,
        "fin":10.5, "chute_gol":4.5, "fal":25.0, "defesa_gk":3.8,
        "vit_casa":46, "vit_fora":30, "empate":24,
        "mais15":80, "mais25":60, "mais35":42,
        "mais15cartao":92, "mais25cartao":72, "mais35cartao":50, "mais65cartao":26,
        "mais65esc":78, "mais75esc":69, "mais85esc":58, "mais95esc":45, "mais105esc":38, "mais115esc":30,
        "mais25imp":78, "mais35imp":62,
        "mais305lat":68, "mais325lat":55, "mais345lat":42, "mais365lat":28,
        "mais55tm":72, "mais65tm":60, "mais75tm":48, "mais95tm":30,
        "mais195fin":68, "mais205fin":60, "mais225fin":45, "mais255fin":25,
        "mais65cg":70, "mais75cg":55, "mais85cg":40, "mais95cg":46,
        "mais195fal":78, "mais225fal":62, "mais255fal":48, "mais295fal":32,
        "mais25def":80, "mais35def":54, "mais45def":38, "mais55def":30
    }
}

# ==============================
# 🔍 FUNÇÕES DE BUSCA E CÁLCULO
# ==============================
@st.cache_data(ttl=1800)
def buscar_jogos(sigla, dias):
    time.sleep(0.3)
    hoje = datetime.now() - timedelta(hours=4)
    lista = []
    try:
        r = requests.get(f"https://api.football-data.org/v4/competitions/{sigla}/matches", headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
        if r.status_code == 200:
            for j in r.json().get("matches", []):
                try:
                    dt = datetime.fromisoformat(j["utcDate"].replace("Z","")) - timedelta(hours=4)
                    if dt.date() <= hoje.date() + timedelta(days=dias):
                        lista.append(j)
                except: pass
    except: pass
    return lista

@st.cache_data(ttl=1800)
def ultimos_5(time_id):
    time.sleep(0.2)
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches", headers=HEADERS, params={"status":"FINISHED","limit":5}, timeout=15)
        return r.json().get("matches", [])
    except: return []

def calcular_dados(time_id, eh_casa=False):
    try:
        jogos = ultimos_5(time_id)
        med = MEDIAS_LIGA["PADRAO"]
        if not jogos:
            return med.copy()
        
        v=e=d=gf=gs=amb=0
        resumo=[]; placares=[]
        for j in jogos:
            try:
                cid = j["homeTeam"]["id"]
                gc = j["score"]["fullTime"].get("home",0) or 0
                ga = j["score"]["fullTime"].get("away",0) or 0
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
        
        res = {"pV":pv,"pE":pe,"pD":pd,"mg":round(media_gols,1),"amb":round((amb/t)*100,0),"resumo":resumo,"placares":placares}
        for chave in med:
            if chave not in res:
                res[chave] = round(med[chave]*fator,1)
        return res
    except: return MEDIAS_LIGA["PADRAO"].copy()

def dupla_chance(v,e,d):
    return {"1X":round(v+e,1),"X2":round(e+d,1),"12":round(v+d,1)}

def enviar_telegram(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id":CHAT_ID,"text":texto,"parse_mode":"Markdown"}, timeout=10)
        return True, "✅ Enviado ao Telegram!"
    except Exception as e: return False, f"❌ Erro: {str(e)}"

# ==============================
# 📨 MENSAGEM PADRONIZADA (CORRIGIDA)
# ==============================
def montar_mensagem(casa, fora, dt, dc, df, dup):
    def m(a,b): return round((a+b)/2,1)
    return f"""⚽ {casa} 🆚 {fora} | {dt.strftime('%d/%m %H:%M')}

📊 PROBABILIDADES:
✅ {casa}: {dc['pV']}% | ⚖️ Empate: {m(dc['pE'],df['pE'])}% | ✅ {fora}: {df['pD']}%
🔀 Dupla Chance: 1X {dup['1X']}% | X2 {dup['X2']}% | 12 {dup['12']}%

📈 GOLS:
⚽ Média: {m(dc['mg'],df['mg'])}
🔢 Mais 1.5: {m(dc['mais15'],df['mais15'])}% | Menos 1.5: {round(100 - m(dc['mais15'],df['mais15']),1)}%
🔢 Mais 2.5: {m(dc['mais25'],df['mais25'])}% | Menos 2.5: {round(100 - m(dc['mais25'],df['mais25']),1)}%
🔢 Mais 3.5: {m(dc['mais35'],df['mais35'])}% | Menos 3.5: {round(100 - m(dc['mais35'],df['mais35']),1)}%
🔄 Ambos Marcam: {m(dc['amb'],df['amb'])}%

🟨 CARTÕES:
🟨 Média: {m(dc['cartao'],df['cartao'])}
🔢 Mais 1.5: {m(dc['mais15cartao'],df['mais15cartao']))}% | Menos 1.5: {round(100 - m(dc['mais15cartao'],df['mais15cartao']),1)}%
🔢 Mais 2.5: {m(dc['mais25cartao'],df['mais25cartao']))}% | Menos 2.5: {round(100 - m(dc['mais25cartao'],df['mais25cartao']),1)}%
🔢 Mais 3.5: {m(dc['mais35cartao'],df['mais35cartao']))}% | Menos 3.5: {round(100 - m(dc['mais35cartao'],df['mais35cartao']),1)}%
🔢 Mais 6.5: {m(dc['mais65cartao'],df['mais65cartao']))}% | Menos 6.5: {round(100 - m(dc['mais65cartao'],df['mais65cartao']),1)}%

📐 ESCANTEIOS:
📐 Média: {m(dc['esc'],df['esc'])}
🔢 Mais 6.5: {m(dc['mais65esc'],df['mais65esc']))}% | Menos 6.5: {round(100 - m(dc['mais65esc'],df['mais65esc']),1)}%
🔢 Mais 7.5: {m(dc['mais75esc'],df['mais75esc']))}% | Menos 7.5: {round(100 - m(dc['mais75esc'],df['mais75esc']),1)}%
🔢 Mais 8.5: {m(dc['mais85esc'],df['mais85esc']))}% | Menos 8.5: {round(100 - m(dc['mais85esc'],df['mais85esc']),1)}%
🔢 Mais 9.5: {m(dc['mais95esc'],df['mais95esc']))}% | Menos 9.5: {round(100 - m(dc['mais95esc'],df['mais95esc']),1)}%
🔢 Mais 10.5: {m(dc['mais105esc'],df['mais105esc']))}% | Menos 10.5: {round(100 - m(dc['mais105esc'],df['mais105esc']),1)}%
🔢 Mais 11.5: {m(dc['mais115esc'],df['mais115esc']))}% | Menos 11.5: {round(100 - m(dc['mais115esc'],df['mais115esc']),1)}%

🚫 IMPEDIMENTOS:
🚫 Média Total: {m(dc['imped'],df['imped'])}
🔢 Mais 2.5: {m(dc['mais25imp'],df['mais25imp']))}% | Menos 2.5: {round(100 - m(dc['mais25imp'],df['mais25imp']),1)}%
🔢 Mais 3.5: {m(dc['mais35imp'],df['mais35imp']))}% | Menos 3.5: {round(100 - m(dc['mais35imp'],df['mais35imp']),1)}%

🧩 LATERAIS:
🧩 Média Total: {m(dc['laterais'],df['laterais'])}
🔢 Mais 30.5: {m(dc['mais305lat'],df['mais305lat']))}% | Menos 30.5: {round(100 - m(dc['mais305lat'],df['mais305lat']),1)}%
🔢 Mais 32.5: {m(dc['mais325lat'],df['mais325lat']))}% | Menos 32.5: {round(100 - m(dc['mais325lat'],df['mais325lat']),1)}%
🔢 Mais 34.5: {m(dc['mais345lat'],df['mais345lat']))}% | Menos 34.5: {round(100 - m(dc['mais345lat'],df['mais345lat']),1)}%
🔢 Mais 36.5: {m(dc['mais365lat'],df['mais365lat']))}% | Menos 36.5: {round(100 - m(dc['mais365lat'],df['mais365lat']),1)}%

🎯 TIRO DE META:
🎯 Média Total: {m(dc['tiro_meta'],df['tiro_meta'])}
🔢 Mais 5.5: {m(dc['mais55tm'],df['mais55tm']))}% | Menos 5.5: {round(100 - m(dc['mais55tm'],df['mais55tm']),1)}%
🔢 Mais 6.5: {m(dc['mais65tm'],df['mais65tm']))}% | Menos 6.5: {round(100 - m(dc['mais65tm'],df['mais65tm']),1)}%
🔢 Mais 7.5: {m(dc['mais75tm'],df['mais75tm']))}% | Menos 7.5: {round(100 - m(dc['mais75tm'],df['mais75tm']),1)}%
🔢 Mais 9.5: {m(dc['mais95tm'],df['mais95tm']))}% | Menos 9.5: {round(100 - m(dc['mais95tm'],df['mais95tm']),1)}%

⚽ FINALIZAÇÕES:
⚽ Média: {m(dc['fin'],df['fin'])}
🔢 Mais 19.5: {m(dc['mais195fin'],df['mais195fin']))}% | Menos 19.5: {round(100 - m(dc['mais195fin'],df['mais195fin']),1)}%
🔢 Mais 20.5: {m(dc['mais205fin'],df['mais205fin']))}% | Menos 20.5: {round(100 - m(dc['mais205fin'],df['mais205fin']),1)}%
🔢 Mais 22.5: {m(dc['mais225fin'],df['mais225fin']))}% | Menos 22.5: {round(100 - m(dc['mais225fin'],df['mais225fin']),1)}%
🔢 Mais 25.5: {m(dc['mais255fin'],df['mais255fin']))}% | Menos 25.5: {round(100 - m(dc['mais255fin'],df['mais255fin']),1)}%

🎯 CHUTES AO GOL:
🎯 Média: {m(dc['chute_gol'],df['chute_gol'])}
🔢 Mais 6.5: {m(dc['mais65cg'],df['mais65cg']))}% | Menos 6.5: {round(100 - m(dc['mais65cg'],df['mais65cg']),1)}%
🔢 Mais 7.5: {m(dc['mais75cg'],df['mais75cg']))}% | Menos 7.5: {round(100 - m(dc['mais75cg'],df['mais75cg']),1)}%
🔢 Mais 8.5: {m(dc['mais85cg'],df['mais85cg']))}% | Menos 8.5: {round(100 - m(dc['mais85cg'],df['mais85cg']),1)}%
🔢 Mais 9.5: {m(dc['mais95cg'],df['mais95cg']))}% | Menos 9.5: {round(100 - m(dc['mais95cg'],df['mais95cg']),1)}%

🤚 FALTAS:
🤚 Média: {m(dc['fal'],df['fal'])}
🔢 Mais 19.5: {m(dc['mais195fal'],df['mais195fal']))}% | Menos 19.5: {round(100 - m(dc['mais195fal'],df['mais195fal']),1)}%
🔢 Mais 22.5: {m(dc['mais225fal'],df['mais225fal']))}% | Menos 22.5: {round(100 - m(dc['mais225fal'],df['mais225fal']),1)}%
🔢 Mais 25.5: {m(dc['mais255fal'],df['mais255fal']))}% | Menos 25.5: {round(100 - m(dc['mais255fal'],df['mais255fal']),1)}%
🔢 Mais 29.5: {m(dc['mais295fal'],df['mais295fal']))}% | Menos 29.5: {round(100 - m(dc['mais295fal'],df['mais295fal']),1)}%

🧤 DEFESAS GOLEIRO:
🧤 Média: {m(dc['defesa_gk'],df['defesa_gk'])}
🔢 Mais 2.5: {m(dc['mais25def'],df['mais25def']))}% | Menos 2.5: {round(100 - m(dc['mais25def'],df['mais25def']),1)}%
🔢 Mais 3.5: {m(dc['mais35def'],df['mais35def']))}% | Menos 3.5: {round(100 - m(dc['mais35def'],df['mais35def']),1)}%
🔢 Mais 4.5: {m(dc['mais45def'],df['mais45def']))}% | Menos 4.5: {round(100 - m(dc['mais45def'],df['mais45def']),1)}%
🔢 Mais 5.5: {m(dc['mais55def'],df['mais55def']))}% | Menos 5.5: {round(100 - m(dc['mais55def'],df['mais55def']),1)}%

🎯 DADOS INDIVIDUAIS:
🏠 {casa}:
  • Vitória: {dc['pV']}% | Empate: {dc['pE']}% | Derrota: {dc['pD']}%
  • Chutes ao Gol: {dc['chute_gol']} | Finalizações: {dc['fin']} | Faltas: {dc['fal']}
  • Escanteios: {dc['esc']} | Defesas: {dc['defesa_gk']} | Cartões: {dc['cartao']}
  • Laterais: {dc['laterais']} | Impedimentos: {dc['imped']} | Tiro de Meta: {dc['tiro_meta']}
  • Últimos 5: {' '.join(dc['resumo'])} | Placares: {', '.join(dc['placares'])}

✈️ {fora}:
  • Vitória: {df['pD']}% | Empate: {df['pE']}% | Derrota: {df['pV']}%
  • Chutes ao Gol: {df['chute_gol']} | Finalizações: {df['fin']} | Faltas: {df['fal']}
  • Escanteios: {df['esc']} | Defesas: {df['defesa_gk']} | Cartões: {df['cartao']}
  • Laterais: {df['laterais']} | Impedimentos: {df['imped']} | Tiro de Meta: {df['tiro_meta']}
  • Últimos 5: {' '.join(df['resumo'])} | Placares: {', '.join(df['placares'])}
"""

# ==============================
# ⏰ ROTINA AUTOMÁTICA TELEGRAM
# ==============================
def rotina_alerta():
    if 'ultimo_envio' not in st.session_state:
        st.session_state['ultimo_envio'] = None
    while True:
        agora = datetime.now() - timedelta(hours=4)
        hora_atual = agora.strftime("%H:%M")
        
        if hora_atual == HORARIO_ALERTA_AUTO and st.session_state.get('ultimo_envio') != agora.date():
            st.session_state['ultimo_envio'] = agora.date()
            mensagem_inicio = f"📢 ALERTA DIÁRIO AUTOMÁTICO | {agora.strftime('%d/%m/%Y')}\n🔍 Analisando jogos com confiança ≥ {LIMIAR_ALERTA}%..."
            enviar_telegram(mensagem_inicio)
            
            for sigla in LIGAS.values():
                jogos = buscar_jogos(sigla, 1)
                for jogo in jogos:
                    try:
                        casa = jogo["homeTeam"]["name"]
                        fora = jogo["awayTeam"]["name"]
                        id_casa = jogo["homeTeam"]["id"]
                        id_fora = jogo["awayTeam"]["id"]
                        dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","")) - timedelta(hours=4)
                        
                        dc = calcular_dados(id_casa, eh_casa=True)
                        df = calcular_dados(id_fora, eh_casa=False)
                        dup = dupla_chance(dc["pV"], dc["pE"], dc["pD"])
                        
                        conf_max = max(dc['pV'], dc['pE'], dc['pD'], dup['1X'], dup['X2'], dup['12'])
                        if conf_max >= LIMIAR_ALERTA:
                            texto = montar_mensagem(casa, fora, dt, dc, df, dup)
                            enviar_telegram(texto)
                            time.sleep(2)
                    except: pass
            enviar_telegram("✅ Fim da análise diária automática!")
        
        time.sleep(60)

# Iniciar rotina uma vez só
if 'rotina_iniciada' not in st.session_state:
    st.session_state['rotina_iniciada'] = True
    threading.Thread(target=rotina_alerta, daemon=True).start()

# ==============================
# 🖥️ INTERFACE PRINCIPAL
# ==============================
col1, col2, col3 = st.columns(3)
with col1: liga_escolhida = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
with col2: dias_busca = st.slider("Buscar jogos para quantos dias?", min_value=1, max_value=14, value=7)
with col3: modo_visualizacao = st.radio("Modo de visualização", ["Todos os jogos", "Escolher jogo específico"])

sigla = LIGAS[liga_escolhida]

if st.button("🔍 Carregar Jogos e Análises"):
    with st.spinner("Buscando dados e calculando estatísticas..."):
        jogos = buscar_jogos(sigla, dias_busca)
        if not jogos:
            st.warning("⚠️ Nenhum jogo encontrado no período selecionado.")
            st.stop()
        
        st.success(f"✅ Encontrados {len(jogos)} jogos em {liga_escolhida}!")
        lista_jogos = [f"{j['homeTeam']['name']} 🆚 {j['awayTeam']['name']} | {datetime.fromisoformat(j['utcDate'].replace('Z','')).strftime('%d/%m %H:%M')}" for j in jogos]
        
        jogos_mostrar = jogos
        if modo_visualizacao == "Escolher jogo específico":
            escolha = st.selectbox("Selecione o jogo:", lista_jogos)
            idx = lista_jogos.index(escolha)
            jogos_mostrar = [jogos[idx]]
        
        for jogo in jogos_mostrar:
            try:
                casa = jogo["homeTeam"]["name"]
                fora = jogo["awayTeam"]["name"]
                id_casa = jogo["homeTeam"]["id"]
                id_fora = jogo["awayTeam"]["id"]
                dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","")) - timedelta(hours=4)
                
                dc = calcular_dados(id_casa, eh_casa=True)
                df = calcular_dados(id_fora, eh_casa=False)
                dup = dupla_chance(dc["pV"], dc["pE"], dc["pD"])
                
                st.subheader(f"⚽ {casa} 🆚 {fora} | {dt.strftime('%d/%m/%Y %H:%M')}")
                texto_final = montar_mensagem(casa, fora, dt, dc, df, dup)
                st.markdown(texto_final)
                
                conf_max = max(dc['pV'], dc['pE'], dc['pD'], dup['1X'], dup['X2'], dup['12'])
                if conf_max >= LIMIAR_ALERTA:
                    st.info(f"🔔 ALERTA: Confiança principal de {conf_max:.0f}% (limite: {LIMIAR_ALERTA}%)")
                    if st.button(f"📤 Enviar para Telegram", key=f"env_{id_casa}_{id_fora}"):
                        ok, msg = enviar_telegram(texto_final)
                        if ok: st.success(msg)
                        else: st.error(msg)
                st.divider()
            except Exception as e:
                st.error(f"❌ Erro no jogo: {str(e)}")

st.caption(f"⚽ Competições solicitadas | Período: até {dias_busca} dias | Alerta automático: {HORARIO_ALERTA_AUTO} Manaus | Limiar: ≥ {LIMIAR_ALERTA}%")
    

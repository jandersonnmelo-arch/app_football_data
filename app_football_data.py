import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# ==============================
# CONFIGURAÇÃO + CACHE
# ==============================
st.set_page_config(page_title="Análise Completa + Probabilidades", page_icon="⚽", layout="wide")
st.title("⚽ Análise + Desempenho + Estimativa Total do Jogo")

API_KEY = st.secrets["CHAVE_FD"]
HEADERS = {"X-Auth-Token": API_KEY}

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

# ==============================
# FUNÇÕES COM CACHE
# ==============================
@st.cache_data(ttl=3600)
def buscar_jogos(sigla):
    time.sleep(0.5)
    hoje = datetime.utcnow().date()
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{sigla}/matches",
            headers=HEADERS,
            params={"status":"SCHEDULED"},
            timeout=15
        )
        if r.status_code == 429:
            st.warning("⏳ Limite temporário — aguarde alguns minutos...")
            return []
        return [j for j in r.json().get("matches",[]) 
                if datetime.fromisoformat(j["utcDate"].replace("Z","")).date() <= hoje + timedelta(days=7)]
    except:
        return []

@st.cache_data(ttl=3600)
def ultimos_5_jogos(time_id, sigla):
    time.sleep(0.3)
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{time_id}/matches",
            headers=HEADERS,
            params={"competitions":sigla,"status":"FINISHED","limit":5},
            timeout=15
        )
        return r.json().get("matches", [])
    except:
        return []

def calcular_base(time_id, sigla):
    jogos = ultimos_5_jogos(time_id, sigla)
    medias = MEDIAS_LIGA.get(sigla, MEDIAS_LIGA["BSA"])
    if not jogos:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,
                "esc":medias["esc"],"laterais":medias["laterais"],"tiro_meta":medias["tiro_meta"],
                "fin":medias["fin"],"chute_gol":medias["chute_gol"],"fal":medias["fal"],"defesa":medias["defesa"],"resumo":[]}
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

# ✅ CÁLCULO NOVO E MAIS REALISTA
def prob_estatistica(valor, media):
    if valor <= 0 or media <= 0:
        return 50
    # Diferença percentual suave
    dif = (valor / media) - 1
    # Variação pequena: em vez de ir de 10 a 95, fica entre 30 e 80
    prob = 50 + (dif * 25)
    return max(30, min(80, round(prob, 0)))

# ==============================
# INTERFACE PRINCIPAL
# ==============================
try:
    escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
    sigla = LIGAS[escolha]
    medias_base = MEDIAS_LIGA[sigla]

    jogos = buscar_jogos(sigla)
    if not jogos:
        st.info("ℹ️ Aguardando dados ou limite temporário — aguarde alguns minutos.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        for jogo in jogos:
            casa = jogo.get("homeTeam",{})
            fora = jogo.get("awayTeam",{})
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            
            st.markdown("---")
            st.subheader(f"⚽ {casa.get('name')} 🆚 {fora.get('name')} | {dt.strftime('%d/%m %H:%M')}")

            dc = calcular_base(casa.get("id"), sigla)
            df = calcular_base(fora.get("id"), sigla)
            dup = dupla_chance(dc["pV"],dc["pE"],dc["pD"])

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Probabilidades Gerais")
                st.write(f"✅ {casa.get('name')}: {dc['pV']}%")
                st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
                st.write(f"✅ {fora.get('name')}: {df['pD']}%")
                st.divider()
                st.subheader("🔀 Dupla Chance")
                st.write(f"1X: {round((dup['1X']+dupla_chance(df['pV'],df['pE'],df['pD'])['1X'])/2,1)}%")
                st.write(f"X2: {round((dup['X2']+dupla_chance(df['pV'],df['pE'],df['pD'])['X2'])/2,1)}%")
                st.write(f"12: {round((dup['12']+dupla_chance(df['pV'],df['pE'],df['pD'])['12'])/2,1)}%")
                st.divider()
                st.subheader("📊 Últimos 5 Jogos")
                st.write(f"🟢 {casa.get('name')}: {' '.join(dc['resumo']) if dc['resumo'] else 'Sem dados'}")
                st.write(f"🔴 {fora.get('name')}: {' '.join(df['resumo']) if df['resumo'] else 'Sem dados'}")

            with col2:
                st.subheader("📐 Estatísticas por Equipe")
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown(f"🏠 {casa.get('name')}")
                    st.write(f"Escanteios: {dc['esc']}")
                    st.write(f"Laterais: {dc['laterais']}")
                    st.write(f"Tiro de Meta: {dc['tiro_meta']}")
                    st.write(f"Finalizações: {dc['fin']}")
                    st.write(f"Chute a Gol: {dc['chute_gol']}")
                    st.write(f"Faltas: {dc['fal']}")
                with c2:
                    st.markdown(f"🚩 {fora.get('name')}")
                    st.write(f"Escanteios: {df['esc']}")
                    st.write(f"Laterais: {df['laterais']}")
                    st.write(f"Tiro de Meta: {df['tiro_meta']}")
                    st.write(f"Finalizações: {df['fin']}")
                    st.write(f"Chute a Gol: {df['chute_gol']}")
                    st.write(f"Faltas: {df['fal']}")

            # ==============================
            # ESTIMATIVA COM % AJUSTADA
            # ==============================
            st.markdown("---")
            st.subheader("📊 ESTIMATIVA GERAL DO JOGO + CHANCE DE ACONTECER")
            total_esc = round((dc['esc'] + df['esc'])/2,1)
            total_lat = round((dc['laterais'] + df['laterais'])/2,1)
            total_tm = round((dc['tiro_meta'] + df['tiro_meta'])/2,1)
            total_fin = round((dc['fin'] + df['fin'])/2,1)
            total_cg = round((dc['chute_gol'] + df['chute_gol'])/2,1)
            total_fal = round((dc['fal'] + df['fal'])/2,1)
            total_def = round((dc['defesa'] + df['defesa'])/2,1)
            media_gols = round((dc['mg'] + df['mg'])/2,2)
            prob_mais25 = round((dc['ma25'] + df['ma25'])/2,0)
            prob_ambos = round((dc['amb'] + df['amb'])/2,0)

            pe = prob_estatistica(total_esc, medias_base['esc'])
            pl = prob_estatistica(total_lat, medias_base['laterais'])
            ptm = prob_estatistica(total_tm, medias_base['tiro_meta'])
            pfin = prob_estatistica(total_fin, medias_base['fin'])
            pcg = prob_estatistica(total_cg, medias_base['chute_gol'])
            pfal = prob_estatistica(total_fal, medias_base['fal'])
            pdef = prob_estatistica(total_def, medias_base['defesa'])

            t1, t2, t3 = st.columns(3)
            with t1:
                st.write(f"📐 Escanteios: **{total_esc}**  ({pe}%)")
                st.write(f"↔️ Laterais: **{total_lat}**  ({pl}%)")
                st.write(f"🚩 Tiro de Meta: **{total_tm}**  ({ptm}%)")
            with t2:
                st.write(f"👟 Finalizações: **{total_fin}**  ({pfin}%)")
                st.write(f"🎯 Chutes a Gol: **{total_cg}**  ({pcg}%)")
                st.write(f"👟 Faltas: **{total_fal}**  ({pfal}%)")
            with t3:
                st.write(f"🧤 Defesas: **{total_def}**  ({pdef}%)")
                st.write(f"⚽ Média Gols: **{media_gols}**")
                st.write(f"🔢 Mais 2.5 Gols: **{prob_mais25}%**")
                st.write(f"🔄 Ambos Marcam: **{prob_ambos}%**")

            if max(dc['pV'], df['pD']) >=75:
                st.error("🚨 ALTA CONFIANÇA ACIMA DE 75%!")

except Exception as e:
    st.error(f"Aguarde ou recarregue: {str(e)}")
    

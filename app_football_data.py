import streamlit as st
import requests
from datetime import datetime, timedelta

# ==============================
# CONFIGURAÇÃO
# ==============================
st.set_page_config(page_title="Análise Completa", page_icon="⚽", layout="wide")
st.title("⚽ Análise + Dupla Chance + Últimos 5 Jogos")

API_KEY = st.secrets["CHAVE_FD"]
HEADERS = {"X-Auth-Token": API_KEY}
TEMPORADA = 2025

# ==============================
# LIGAS E MÉDIAS POR COMPETIÇÃO
# ==============================
LIGAS = {
    "🇧🇷 Brasileirão Série A": "BSA",
    "🇧🇷 Brasileirão Série B": "BRB",
    "🏆 Libertadores": "CLI",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA"
}

MEDIAS = {
    "BSA": {
        "casa": {"esc":9.5,"tiro_meta":4.2,"laterais":7.8,"fin":11.2,"chute_gol":4.8,"fal":28.5,"defesa_gol":3.1},
        "fora": {"esc":8.5,"tiro_meta":5.1,"laterais":9.2,"fin":8.7,"chute_gol":3.2,"fal":24.8,"defesa_gol":4.5}
    },
    "BRB": {
        "casa": {"esc":9.0,"tiro_meta":4.5,"laterais":8.2,"fin":10.5,"chute_gol":4.2,"fal":29.0,"defesa_gol":3.5},
        "fora": {"esc":8.0,"tiro_meta":5.5,"laterais":9.8,"fin":8.0,"chute_gol":2.8,"fal":25.5,"defesa_gol":5.0}
    },
    "CLI": {
        "casa": {"esc":10.2,"tiro_meta":3.8,"laterais":6.5,"fin":12.5,"chute_gol":5.5,"fal":25.0,"defesa_gol":2.8},
        "fora": {"esc":8.8,"tiro_meta":4.8,"laterais":8.0,"fin":9.5,"chute_gol":3.8,"fal":22.0,"defesa_gol":4.0}
    },
    "PL": {
        "casa": {"esc":11.0,"tiro_meta":3.5,"laterais":6.0,"fin":13.0,"chute_gol":6.0,"fal":24.0,"defesa_gol":2.5},
        "fora": {"esc":9.5,"tiro_meta":4.5,"laterais":7.5,"fin":10.0,"chute_gol":4.2,"fal":20.0,"defesa_gol":3.8}
    },
    "PD": {
        "casa": {"esc":9.8,"tiro_meta":4.0,"laterais":7.0,"fin":11.8,"chute_gol":5.2,"fal":26.0,"defesa_gol":2.9},
        "fora": {"esc":8.7,"tiro_meta":5.0,"laterais":8.5,"fin":9.2,"chute_gol":3.5,"fal":22.5,"defesa_gol":4.2}
    },
    "BL1": {
        "casa": {"esc":10.5,"tiro_meta":3.2,"laterais":5.8,"fin":14.0,"chute_gol":6.5,"fal":23.0,"defesa_gol":2.2},
        "fora": {"esc":9.0,"tiro_meta":4.2,"laterais":7.2,"fin":10.5,"chute_gol":4.5,"fal":19.0,"defesa_gol":3.5}
    },
    "SA": {
        "casa": {"esc":9.2,"tiro_meta":4.5,"laterais":8.5,"fin":10.8,"chute_gol":4.5,"fal":27.0,"defesa_gol":3.3},
        "fora": {"esc":8.2,"tiro_meta":5.5,"laterais":10.0,"fin":8.3,"chute_gol":3.0,"fal":23.5,"defesa_gol":4.8}
    }
}

# ==============================
# FUNÇÕES
# ==============================
def buscar_jogos(sigla):
    hoje = datetime.utcnow().date()
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{sigla}/matches",
            headers=HEADERS,
            params={"status":"SCHEDULED"},
            timeout=15
        )
        r.raise_for_status()
        return [
            j for j in r.json().get("matches",[])
            if datetime.fromisoformat(j["utcDate"].replace("Z","")).date() <= hoje + timedelta(days=7)
        ]
    except Exception as e:
        st.error(f"Erro ao buscar jogos: {str(e)}")
        return []

def ultimos_5_jogos(time_id, sigla):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{time_id}/matches",
            headers=HEADERS,
            params={"competitions":sigla,"status":"FINISHED","limit":5},
            timeout=15
        )
        r.raise_for_status()
        return r.json().get("matches", [])
    except:
        return []

def calcular_principais(time_id, sigla):
    jogos = ultimos_5_jogos(time_id, sigla)
    if not jogos:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"fA":1,"fD":1,"resumo":[]}
    v=e=d=gf=gs=amb=0
    resumo = []
    for j in jogos:
        cid = j.get("homeTeam",{}).get("id")
        placar = j.get("score",{}).get("fullTime",{})
        gc = placar.get("home", 0) or 0
        ga = placar.get("away", 0) or 0
        if cid == time_id:
            gf += gc; gs += ga
            if gc>ga: v+=1; resumo.append("✅ Vitória")
            elif gc==ga: e+=1; resumo.append("⚖️ Empate")
            else: d+=1; resumo.append("❌ Derrota")
        else:
            gf += ga; gs += gc
            if ga>gc: v+=1; resumo.append("✅ Vitória")
            elif ga==gc: e+=1; resumo.append("⚖️ Empate")
            else: d+=1; resumo.append("❌ Derrota")
        if gc>0 and ga>0: amb+=1
    t=len(jogos)
    return {
        "pV":round((v/t)*100,1), "pE":round((e/t)*100,1), "pD":round((d/t)*100,1),
        "mg":round((gf+gs)/t,2), "ma25":round(70 if (gf+gs)/t>2.5 else 45,0),
        "amb":round((amb/t)*100,0), "fA":round((gf/t)/1.5,2), "fD":round((gs/t)/1.5,2),
        "resumo":resumo
    }

def dupla_chance(pV,pE,pD):
    return {
        "1X": round(pV + pE,1),
        "X2": round(pE + pD,1),
        "12": round(pV + pD,1)
    }

# ==============================
# INTERFACE PRINCIPAL
# ==============================
try:
    escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
    sigla = LIGAS[escolha]
    medias = MEDIAS.get(sigla, MEDIAS["BSA"])

    jogos = buscar_jogos(sigla)
    if not jogos:
        st.warning("ℹ️ Nenhum jogo agendado para os próximos 7 dias.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        for jogo in jogos:
            casa = jogo.get("homeTeam", {})
            fora = jogo.get("awayTeam", {})
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            
            st.markdown("---")
            st.subheader(f"⚽ {casa.get('name','Time Casa')} 🆚 {fora.get('name','Time Fora')} | {dt.strftime('%d/%m %H:%M')}")

            dc = calcular_principais(casa.get("id"), sigla)
            df = calcular_principais(fora.get("id"), sigla)
            dc_dupla = dupla_chance(dc["pV"],dc["pE"],dc["pD"])
            df_dupla = dupla_chance(df["pV"],df["pE"],df["pD"])

            # 3 COLUNAS: PROBABILIDADES | ÚLTIMOS JOGOS | ESTATÍSTICAS
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Probabilidades")
                st.write(f"✅ {casa.get('name')}: {dc['pV']}%")
                st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
                st.write(f"✅ {fora.get('name')}: {df['pD']}%")
                st.divider()
                st.subheader("🔀 Dupla Chance")
                st.write(f"1X (Casa/Empate): {round((dc_dupla['1X']+df_dupla['1X'])/2,1)}%")
                st.write(f"X2 (Empate/Fora): {round((dc_dupla['X2']+df_dupla['X2'])/2,1)}%")
                st.write(f"12 (Casa/Fora): {round((dc_dupla['12']+df_dupla['12'])/2,1)}%")
                st.divider()
                st.subheader("📊 Últimos 5 Jogos")
                st.write(f"🟢 {casa.get('name')}: {' '.join(dc['resumo']) if dc['resumo'] else 'Sem dados'}")
                st.write(f"🔴 {fora.get('name')}: {' '.join(df['resumo']) if df['resumo'] else 'Sem dados'}")
                st.divider()
                st.write(f"📊 Média Gols: {round((dc['mg']+df['mg'])/2,2)}")
                st.write(f"🔢 Mais 2.5: {round((dc['ma25']+df['ma25'])/2,0)}%")
                st.write(f"🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%")

            with col2:
                st.subheader("📐 Estatísticas Separadas")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"🏠 **{casa.get('name')}**")
                    st.write(f"📐 Escanteios: {medias['casa']['esc']}")
                    st.write(f"↔️ Laterais: {medias['casa']['laterais']}")
                    st.write(f"🚩 Tiro de Meta: {medias['casa']['tiro_meta']}")
                    st.write(f"👟 Finalizações: {medias['casa']['fin']}")
                    st.write(f"🎯 Chute a Gol: {medias['casa']['chute_gol']}")
                    st.write(f"👟 Faltas: {medias['casa']['fal']}")
                    st.write(f"🧤 Defesa Goleiro: {medias['casa']['defesa_gol']}")
                with c2:
                    st.markdown(f"🚩 **{fora.get('name')}**")
                    st.write(f"📐 Escanteios: {medias['fora']['esc']}")
                    st.write(f"↔️ Laterais: {medias['fora']['laterais']}")
                    st.write(f"🚩 Tiro de Meta: {medias['fora']['tiro_meta']}")
                    st.write(f"👟 Finalizações: {medias['fora']['fin']}")
                    st.write(f"🎯 Chute a Gol: {medias['fora']['chute_gol']}")
                    st.write(f"👟 Faltas: {medias['fora']['fal']}")
                    st.write(f"🧤 Defesa Goleiro: {medias['fora']['defesa_gol']}")

            if max(dc['pV'], df['pD']) >=75:
                st.error("🚨 ALTA CONFIANÇA ACIMA DE 75%!")

except Exception as geral:
    st.error(f"Erro: {str(geral)}")
    st.info("Recarregue ou tente novamente em instantes.")

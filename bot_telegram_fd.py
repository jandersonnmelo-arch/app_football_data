import requests
import time
from datetime import datetime, timedelta

# ==============================================
# 🔴 COLOQUE SEUS DADOS AQUI!
# ==============================================
API_KEY = "51d62042229e4f4a9532b6376203e602"       # Sua chave do football-data.org
BOT_TOKEN = "8289316862:AAFIhpQqoc2kRlW6B6I5zk5pqmecXaPMpmw"    # Do @BotFather
SEU_CHAT_ID = "1100260912"       # Que você já tem
LIMITE_ALERTA = 75
# ==============================================

HEADERS = {"X-Auth-Token": API_KEY}

# Ligas e médias estatísticas (igual ao app)
COMPETICOES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA",
    "🇫🇷 Ligue 1": "FL1",
    "🏆 Champions League": "CL",
    "🇧🇷 Brasileirão Série A": "BSA"
}

MEDIAS_LIGAS = {
    "PL": {"escanteios":10.5, "cartoes":3.8, "faltas":22, "finalizacoes":12},
    "PD": {"escanteios":9.2, "cartoes":4.2, "faltas":24, "finalizacoes":11},
    "BL1": {"escanteios":9.8, "cartoes":3.5, "faltas":21, "finalizacoes":13},
    "SA": {"escanteios":8.7, "cartoes":4.5, "faltas":25, "finalizacoes":10},
    "FL1": {"escanteios":8.5, "cartoes":3.9, "faltas":23, "finalizacoes":11},
    "CL": {"escanteios":9.5, "cartoes":3.6, "faltas":22, "finalizacoes":12},
    "BSA": {"escanteios":9.0, "cartoes":4.3, "faltas":26, "finalizacoes":10}
}

# --------------------------
# FUNÇÕES AUXILIARES
# --------------------------
def enviar(texto):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={
        "chat_id": SEU_CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }, timeout=15)

def buscar_jogos(sigla):
    url = f"https://api.football-data.org/v4/competitions/{sigla}/matches"
    try:
        r = requests.get(url, headers=HEADERS, params={"status":"SCHEDULED"}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

def buscar_historico(time_id, sigla):
    url = f"https://api.football-data.org/v4/teams/{time_id}/matches?competitions={sigla}&status=FINISHED&limit=10"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

def calcular_dados(time_id, sigla):
    jogos = buscar_historico(time_id, sigla)
    if not jogos:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"ambos":50,"fatA":1,"fatD":1}
    v=e=d=gf=gs=amb=0
    for j in jogos:
        cid = j["homeTeam"]["id"]
        gc = j["score"]["fullTime"]["home"] or 0
        ga = j["score"]["fullTime"]["away"] or 0
        if cid == time_id:
            gf += gc; gs += ga
            if gc>ga: v+=1
            elif gc==ga: e+=1
            else: d+=1
        else:
            gf += ga; gs += gc
            if ga>gc: v+=1
            elif ga==gc: e+=1
            else: d+=1
        if gc>0 and ga>0: amb+=1
    t = len(jogos)
    return {
        "pV":round((v/t)*100,1), "pE":round((e/t)*100,1), "pD":round((d/t)*100,1),
        "mg":round((gf+gs)/t,2), "ma25":round(70 if (gf+gs)/t>2.5 else 45,0),
        "ambos":round((amb/t)*100,0),
        "fatA":round((gf/t)/1.5,2), "fatD":round((gs/t)/1.5,2)
    }

def estimar(dc, df, sigla):
    m = MEDIAS_LIGAS[sigla]
    esc = round(m["escanteios"] * ((dc["fatA"]+df["fatA"])/2),1)
    car = round(m["cartoes"] * ((dc["fatD"]+df["fatD"])/2),1)
    fal = round(m["faltas"] * ((dc["fatD"]+df["fatD"])/2),1)
    fin = round(m["finalizacoes"] * ((dc["fatA"]+df["fatA"])/2),1)
    return {
        "esc":esc, "car":car, "fal":fal, "fin":fin,
        "maisc95":round(70 if esc>9.5 else 45,0),
        "maisc35":round(65 if car>3.5 else 40,0),
        "maisF225":round(60 if fal>22.5 else 45,0),
        "maisFi115":round(65 if fin>11.5 else 40,0)
    }

# --------------------------
# EXECUÇÃO PRINCIPAL
# --------------------------
if __name__ == "__main__":
    enviar("⚽ *ANÁLISE COMPLETA - FOOTBALL-DATA.ORG* ⚽\n📊 Probabilidades + Estimativas + Mercados\n🚨 Alerta acima de 75%")
    time.sleep(1)

    for nome_liga, sigla in COMPETICOES.items():
        jogos = buscar_jogos(sigla)
        if not jogos: continue
        enviar(f"\n🏆 *{nome_liga}*")
        time.sleep(0.5)

        for jogo in jogos:
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            if dt.date() > (datetime.utcnow() + timedelta(days=7)).date(): continue
            casa = jogo["homeTeam"]
            fora = jogo["awayTeam"]
            dc = calcular_dados(casa["id"], sigla)
            df = calcular_dados(fora["id"], sigla)
            est = estimar(dc, df, sigla)

            msg = f"""
⚽ {casa['name']} 🆚 {fora['name']}
📅 {dt.strftime('%d/%m %H:%M')}

📈 *Probabilidades:*
✅ {casa['name']}: {dc['pV']}%
⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%
✅ {fora['name']}: {df['pD']}%
📊 Média Gols: {round((dc['mg']+df['mg'])/2,2)}
🔢 Mais 2.5: {round((dc['ma25']+df['ma25'])/2,0)}%
🔄 Ambos Marcam: {round((dc['ambos']+df['ambos'])/2,0)}%

📊 *Estimativas:*
📐 Escanteios: {est['esc']} | +9.5: {est['maisc95']}%
🟨 Cartões: {est['car']} | +3.5: {est['maisc35']}%
👟 Faltas: {est['fal']} | +22.5: {est['maisF225']}%
🎯 Finalizações: {est['fin']} | +11.5: {est['maisFi115']}%
            """
            enviar(msg.strip())
            time.sleep(0.8)

            # ALERTA ESPECIAL
            maior = max(dc['pV'], df['pD'])
            if maior >= LIMITE_ALERTA:
                enviar(f"""
🚨 *ALERTA DE ALTA CONFIANÇA!* 🚨
🔹 {casa['name']} vs {fora['name']}
🔹 Probabilidade: {maior}%
🔹 Favorito: {casa['name'] if dc['pV']>df['pD'] else fora['name']}
                """.strip())
                time.sleep(0.5)

    enviar("\n✅ Análise finalizada! Bons greens! 🍀")
  

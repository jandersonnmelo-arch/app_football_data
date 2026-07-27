import requests
import time
from datetime import datetime, timedelta

# ==============================================
# 🔴 SEUS DADOS
# ==============================================
CHAVE_FOOTBALL_DATA = "51d62042229e4f4a9532b6376203e602"
TOKEN_BOT_NOVO = "8289316862:AAFIhpQqoc2kRlW6B6I5zk5pqmecXaPMpmw"
SEU_ID_TELEGRAM = "1100260912"
LIMITE_ALERTA = 75
# ==============================================

CABECALHO = {"X-Auth-Token": CHAVE_FOOTBALL_DATA}

TODAS_LIGAS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA",
    "🇫🇷 Ligue 1": "FL1",
    "🏆 Champions League": "CL",
    "🇧🇷 Brasileirão Série A": "BSA"
}

MEDIAS = {
    "PL": {"esc":10.5,"car":3.8,"fal":22,"fin":12},
    "PD": {"esc":9.2,"car":4.2,"fal":24,"fin":11},
    "BL1": {"esc":9.8,"car":3.5,"fal":21,"fin":13},
    "SA": {"esc":8.7,"car":4.5,"fal":25,"fin":10},
    "FL1": {"esc":8.5,"car":3.9,"fal":23,"fin":11},
    "CL": {"esc":9.5,"car":3.6,"fal":22,"fin":12},
    "BSA": {"esc":9.0,"car":4.3,"fal":26,"fin":10}
}

def enviar(texto):
    url = f"https://api.telegram.org/bot{TOKEN_BOT_NOVO}/sendMessage"
    requests.get(url, params={
        "chat_id": SEU_ID_TELEGRAM,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }, timeout=15)

def buscar_todos_jogos_do_dia():
    hoje_utc = datetime.utcnow().date()
    todos = []
    for nome_liga, sigla in TODAS_LIGAS.items():
        try:
            r = requests.get(f"https://api.football-data.org/v4/competitions/{sigla}/matches",
                            headers=CABECALHO, params={"status":"SCHEDULED"}, timeout=15)
            jogos = r.json().get("matches", [])
            for j in jogos:
                try:
                    data_j = datetime.fromisoformat(j["utcDate"].replace("Z","")).date()
                    if data_j == hoje_utc:
                        j["liga_nome"] = nome_liga
                        j["liga_sigla"] = sigla
                        todos.append(j)
                except:
                    continue
        except:
            continue
    # Ordena por horário do jogo
    todos.sort(key=lambda x: x["utcDate"])
    return todos

def historico(time_id, sigla):
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=CABECALHO, params={"competitions":sigla,"status":"FINISHED","limit":10}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

def calc(time_id, sigla):
    j = historico(time_id, sigla)
    if not j: return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"fA":1,"fD":1}
    v=e=d=gf=gs=amb=0
    for x in j:
        cid = x["homeTeam"]["id"]
        gc = x["score"]["fullTime"]["home"] or 0
        ga = x["score"]["fullTime"]["away"] or 0
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
    t = len(j)
    return {
        "pV":round((v/t)*100,1), "pE":round((e/t)*100,1), "pD":round((d/t)*100,1),
        "mg":round((gf+gs)/t,2), "ma25":round(70 if (gf+gs)/t>2.5 else 45,0),
        "amb":round((amb/t)*100,0),
        "fA":round((gf/t)/1.5,2), "fD":round((gs/t)/1.5,2)
    }

def estima(dc, df, sigla):
    m = MEDIAS[sigla]
    return {
        "esc": round(m["esc"]*((dc["fA"]+df["fA"])/2),1),
        "car": round(m["car"]*((dc["fD"]+df["fD"])/2),1),
        "fal": round(m["fal"]*((dc["fD"]+df["fD"])/2),1),
        "fin": round(m["fin"]*((dc["fA"]+df["fA"])/2),1)
    }

# --------------------------
# EXECUÇÃO
# --------------------------
if __name__ == "__main__":
    enviar("⚽ *JOGOS DE HOJE - TODAS AS LIGAS* ⚽\nLista completa + Análises")
    time.sleep(1)

    jogos_do_dia = buscar_todos_jogos_do_dia()
    if not jogos_do_dia:
        enviar("ℹ️ Nenhum jogo agendado para hoje nas competições selecionadas.")
    else:
        enviar(f"✅ Encontrados {len(jogos_do_dia)} jogos para hoje!")
        time.sleep(1)

        for jogo in jogos_do_dia:
            casa = jogo["homeTeam"]
            fora = jogo["awayTeam"]
            dt = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            dc = calc(casa["id"], jogo["liga_sigla"])
            df = calc(fora["id"], jogo["liga_sigla"])
            est = estima(dc, df, jogo["liga_sigla"])

            msg = f"""
{jogo['liga_nome']}
⚽ {casa['name']} 🆚 {fora['name']}
⏰ {dt.strftime('%H:%M')}

📈 Probabilidades:
✅ {casa['name']}: {dc['pV']}%
⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%
✅ {fora['name']}: {df['pD']}%
📊 Média Gols: {round((dc['mg']+df['mg'])/2,2)}

📊 Estimativas:
📐 Escanteios: {est['esc']}
🟨 Cartões: {est['car']}
👟 Faltas: {est['fal']} | 🎯 Finalizações: {est['fin']}
            """
            enviar(msg.strip())
            time.sleep(0.8)

            if max(dc['pV'], df['pD']) >= LIMITE_ALERTA:
                enviar(f"""
🚨 *ALERTA ACIMA DE 75%!* 🚨
{jogo['liga_nome']} | {casa['name']} vs {fora['name']}
Chance: {max(dc['pV'], df['pD'])}%
                """.strip())
                time.sleep(0.5)

    enviar("\n✅ Fim da lista de hoje! Bons greens! 🍀")
    
         

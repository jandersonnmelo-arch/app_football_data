import requests
import time
from datetime import datetime, timedelta

# ==============================================
# 🔴 COLOQUE AQUI SEUS DADOS NOVOS
# ==============================================
CHAVE_FOOTBALL_DATA = "51d62042229e4f4a9532b6376203e602"
TOKEN_BOT_NOVO = "8289316862:AAFIhpQqoc2kRlW6B6I5zk5pqmecXaPMpmw"
SEU_ID_TELEGRAM = "1100260912"
LIMITE_ALERTA = 75
# ==============================================

CABECALHO = {"X-Auth-Token": CHAVE_FOOTBALL_DATA}

LIGAS = {
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

# --------------------------
# FUNÇÃO DE ENVIAR MENSAGEM
# --------------------------
def msg(texto):
    url = f"https://api.telegram.org/bot{TOKEN_BOT_NOVO}/sendMessage"
    try:
        requests.get(url, params={
            "chat_id": SEU_ID_TELEGRAM,
            "text": texto,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }, timeout=15)
    except Exception as e:
        print(f"Erro: {e}")

# --------------------------
# BUSCAR JOGOS E HISTÓRICO
# --------------------------
def jogos(sigla):
    try:
        r = requests.get(f"https://api.football-data.org/v4/competitions/{sigla}/matches",
                        headers=CABECALHO, params={"status":"SCHEDULED"}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

def historico(time_id, sigla):
    try:
        r = requests.get(f"https://api.football-data.org/v4/teams/{time_id}/matches",
                        headers=CABECALHO, params={"competitions":sigla,"status":"FINISHED","limit":10}, timeout=15)
        return r.json().get("matches", [])
    except:
        return []

# --------------------------
# CÁLCULOS
# --------------------------
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
        "fin": round(m["fin"]*((dc["fA"]+df["fA"])/2),1),
        "maisc95": round(70 if m["esc"]>9.5 else 45,0),
        "maisc35": round(65 if m["car"]>3.5 else 40,0)
    }

# --------------------------
# EXECUÇÃO PRINCIPAL
# --------------------------
if __name__ == "__main__":
    msg("⚽ *NOVO BOT - FOOTBALL-DATA.ORG* ⚽\nTudo integrado do zero!")
    time.sleep(1)

    for nome_liga, sigla in LIGAS.items():
        lista = jogos(sigla)
        if not lista: continue
        msg(f"\n🏆 *{nome_liga}*")
        time.sleep(0.5)

        for jogo in lista:
            data_jogo = datetime.fromisoformat(jogo["utcDate"].replace("Z","-04:00"))
            if data_jogo.date() > (datetime.utcnow() + timedelta(days=7)).date(): continue
            casa = jogo["homeTeam"]
            fora = jogo["awayTeam"]
            dc = calc(casa["id"], sigla)
            df = calc(fora["id"], sigla)
            est = estima(dc, df, sigla)

            texto = f"""
⚽ {casa['name']} 🆚 {fora['name']}
📅 {data_jogo.strftime('%d/%m %H:%M')}

📈 Probabilidades:
✅ {casa['name']}: {dc['pV']}%
⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%
✅ {fora['name']}: {df['pD']}%
📊 Média Gols: {round((dc['mg']+df['mg'])/2,2)}
🔢 Mais 2.5: {round((dc['ma25']+df['ma25'])/2,0)}%
🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%

📊 Estimativas:
📐 Escanteios: {est['esc']} | +9.5: {est['maisc95']}%
🟨 Cartões: {est['car']} | +3.5: {est['maisc35']}%
👟 Faltas / Finalizações: {est['fal']} / {est['fin']}
            """
            msg(texto.strip())
            time.sleep(0.7)

            # ALERTA
            maior = max(dc['pV'], df['pD'])
            if maior >= LIMITE_ALERTA:
                msg(f"""
🚨 *ALERTA ACIMA DE 75%!* 🚨
{casa['name']} vs {fora['name']}
Chance: {maior}%
Favorito: {casa['name'] if dc['pV']>df['pD'] else fora['name']}
                """.strip())
                time.sleep(0.5)

    msg("\n✅ Concluído! Bons greens! 🍀")
         

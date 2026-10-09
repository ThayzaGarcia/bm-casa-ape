#!/usr/bin/env python3
"""Tempo de uso do WhatsApp pelo comercial, por dia útil (horário de Brasília).

Tempo ativo estimado = união das janelas [envio - N min, envio] de cada mensagem enviada
por uma pessoa (a saudação automática não conta). N padrão = 2 min (sensibilidade 1 e 3).
Ocioso = expediente (07:30–17:00) - ativo.
Ocioso com paciente esperando = minutos do expediente sem atividade em que havia ao menos
um paciente com mensagem sem resposta há mais de 5 min.
"""
import json, re, sqlite3, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
D = Path(__file__).parent / "dados"
db = sqlite3.connect(D / (sys.argv[1] if len(sys.argv) > 1 else "whatsapp.db"))
AUTO = "Seja Bem-vindo(a) a Clínica CLINMED"
INI, FIM = 7 * 60 + 30, 17 * 60
sys.path.insert(0, str(Path(__file__).parent))
from classificacao import NAO_PACIENTE

rows = db.execute("SELECT chatid, ts_ms, de_mim, texto, raw FROM mensagens ORDER BY ts_ms").fetchall()

ACK = re.compile(r"^\W*(ok+|okay|obrigad[oa]|obg|grat[oa]|t[aá] (bom|bem|certo|ok)|certo|beleza|blz|sim|perfeito|entendi|tendi|de nada|amém)\W*$", re.I)
def encerramento(txt, m):
    t = (txt or "").strip()
    return m.get("messageType") in ("StickerMessage", "call") or (t and ACK.match(t)) or (len(t) <= 3 and m.get("messageType") == "Conversation")

def minuto(ts):
    d = datetime.fromtimestamp(ts / 1000, BRT)
    return d.date(), d.hour * 60 + d.minute + d.second / 60

def eh_paciente(c):
    return not c.endswith("@g.us") and c.split("@")[0] not in NAO_PACIENTE

envios = defaultdict(list)        # dia -> [(min, paciente?)]
pend = defaultdict(list)          # dia -> intervalos [ini, fim] com paciente esperando
ultima_cli = {}                   # chat -> ts da 1ª msg do cliente ainda sem resposta
for c, ts, eu, txt, raw in rows:
    m = json.loads(raw)
    humano = eu and AUTO not in (txt or "") and m.get("source") != "call_log"
    if eu and humano:
        dia, mi = minuto(ts)
        envios[dia].append((mi, eh_paciente(c)))
        if c in ultima_cli:
            t0 = ultima_cli.pop(c)
            d0, m0 = minuto(t0 + 5 * 60000)
            if d0 == dia and mi > m0:
                pend[dia].append((m0, mi))
            elif d0 < dia:
                pend[d0].append((m0, FIM))
                pend[dia].append((INI, mi))
    elif not eu and eh_paciente(c) and not encerramento(txt, m):
        ultima_cli.setdefault(c, ts)

def uniao(iv):
    out = []
    for a, b in sorted(iv):
        a, b = max(a, INI), min(b, FIM)
        if b <= a: continue
        if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out

def total(iv): return sum(b - a for a, b in iv)

def intersec(x, y):
    i = j = 0; out = []
    while i < len(x) and j < len(y):
        a, b = max(x[i][0], y[j][0]), min(x[i][1], y[j][1])
        if a < b: out.append([a, b])
        if x[i][1] < y[j][1]: i += 1
        else: j += 1
    return out

def complemento(iv):
    out, cur = [], INI
    for a, b in iv:
        if a > cur: out.append([cur, a])
        cur = max(cur, b)
    if cur < FIM: out.append([cur, FIM])
    return out

dias = []
for dia in sorted(envios):
    if dia.weekday() >= 5: continue
    msgs = envios[dia]
    lin = {"dia": dia.strftime("%a %d/%m"), "msgs_enviadas": len(msgs),
           "msgs_pacientes": sum(p for _, p in msgs)}
    for n in (1, 2, 3):
        lin[f"ativo_min_n{n}"] = round(total(uniao([(mi - n, mi) for mi, _ in msgs])))
    ativo = uniao([(mi - 2, mi) for mi, _ in msgs])
    ocioso = complemento(ativo)
    lin["ocioso_min"] = round(total(ocioso))
    lin["ocioso_com_paciente_esperando_min"] = round(total(intersec(ocioso, uniao(pend[dia]))))
    lin["maior_pausa_min"] = round(max((b - a for a, b in ocioso), default=0))
    hrs = [mi for mi, _ in msgs if INI <= mi < FIM]
    lin["primeiro_envio"] = f"{int(min(hrs)//60):02d}:{int(min(hrs)%60):02d}" if hrs else "-"
    lin["ultimo_envio"] = f"{int(max(hrs)//60):02d}:{int(max(hrs)%60):02d}" if hrs else "-"
    # perfil por hora: minutos ativos em cada hora do expediente
    lin["ativo_por_hora"] = {h: round(total(intersec(ativo, [[h * 60, h * 60 + 60]]))) for h in range(7, 17)}
    dias.append(lin)

res = {"expediente_min": FIM - INI, "metodo": __doc__.strip(), "dias": dias}
(D / "uso_diario.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str))
for d in dias:
    print(d["dia"], "| envios", d["msgs_enviadas"], "| ativo", d["ativo_min_n1"], d["ativo_min_n2"], d["ativo_min_n3"],
          "| ocioso", d["ocioso_min"], "| ocioso c/ espera", d["ocioso_com_paciente_esperando_min"],
          "| maior pausa", d["maior_pausa_min"], "|", d["primeiro_envio"], "-", d["ultimo_envio"])

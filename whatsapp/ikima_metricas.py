#!/usr/bin/env python3
"""Métricas da Ikima (capilar/harmonização) a partir de dados-ikima/whatsapp.db. Horário de Brasília."""
import json, re, sqlite3, collections, statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
D = Path(__file__).parent / "dados-ikima"
db = sqlite3.connect(D / "whatsapp.db")
dt = lambda ms: datetime.fromtimestamp(ms / 1000, BRT)
GRUPO = "120363373170843644@g.us"

rows = db.execute("SELECT chatid, ts_ms, de_mim, texto, raw FROM mensagens WHERE ts_ms >= ? ORDER BY ts_ms",
                  (int(datetime(2026, 11, 3, tzinfo=BRT).timestamp() * 1000),)).fetchall()
ch = collections.defaultdict(list)
for c, ts, eu, txt, raw in rows:
    ch[c].append((ts, bool(eu), txt or "", json.loads(raw)))

def anuncio(m):
    return "externalAdReply" in str(m.get("content", ""))
def origem(m):
    s = str(m.get("content", ""))
    r = re.search(r"'(?:sourceURL|sourceUrl)': '([^']+)'", s)
    return r.group(1) if r else "?"
def humano(x):  # resposta escrita por pessoa (exclui auto-resposta da Meta, source=unknown)
    return x[1] and x[3].get("source") in ("web", "android", "ios")

res = {}
leads = {c: m for c, m in ch.items() if c != GRUPO and any(anuncio(x[3]) and not x[1] for x in m)}
res["conversas_total_com_msgs"] = len(ch)
res["conversas_de_anuncio"] = len(leads)

# leads por dia (1ª msg com anúncio)
por_dia = collections.Counter(); chegada = {}
for c, m in leads.items():
    t0 = min(x[0] for x in m if anuncio(x[3]) and not x[1]); chegada[c] = t0
    por_dia[dt(t0).strftime("%d/%m")] += 1
res["leads_anuncio_por_dia_whatsapp"] = sorted(por_dia.items())
res["origem_anuncios"] = collections.Counter(origem(x[3]) for m in leads.values() for x in m if anuncio(x[3]) and not x[1]).most_common()

# velocidade da 1ª resposta humana
esp, fora = [], 0
cat = collections.Counter()
for c, m in leads.items():
    t0 = chegada[c]; h = [x for x in m if humano(x) and x[0] >= t0]
    d0 = dt(t0)
    util = d0.weekday() < 5 and 8 <= d0.hour < 18
    if not util: fora += 1
    if not h: cat["sem resposta"] += 1; continue
    mins = (h[0][0] - t0) / 60000; esp.append((mins, util))
    cat["até 5 min" if mins <= 5 else "até 1 h" if mins <= 60 else "mesmo dia" if mins <= 1440 and dt(h[0][0]).date() == d0.date() else "dia seguinte ou mais"] += 1
res["leads_chegaram_fora_do_expediente"] = fora
res["primeira_resposta_faixas"] = dict(cat)
v = sorted(m for m, _ in esp)
res["primeira_resposta_mediana_min"] = round(st.median(v), 1) if v else None
res["primeira_resposta_mediana_expediente_min"] = round(st.median([m for m, u in esp if u]), 1) if any(u for _, u in esp) else None
res["primeira_resposta_mediana_fora_min"] = round(st.median([m for m, u in esp if not u]), 1) if any(not u for _, u in esp) else None
res["leads_com_resposta_automatica_meta"] = sum(any(x[1] and x[3].get("source") == "unknown" for x in m) for m in leads.values())

# funil dos leads de anúncio
f = collections.Counter()
for c, m in leads.items():
    cli = [x for x in m if not x[1] and not anuncio(x[3])]
    cli_txt = " ".join(x[2].lower() for x in cli)
    f["1. lead de anúncio"] += 1
    if any(humano(x) for x in m): f["2. recebeu resposta humana"] += 1
    if cli: f["3. respondeu / continuou a conversa"] += 1
    if re.search(r"valor|quanto|custa|preço|investimento", cli_txt): f["4. perguntou valor"] += 1
    if re.search(r"dia \d|\d{1,2}/\d{1,2}|às \d|horário|sábado|agendar", " ".join(x[2].lower() for x in m if humano(x))) and cli:
        f["5. recebeu proposta de data/horário"] += 1
res["funil_leads_anuncio"] = dict(sorted(f.items()))
res["leads_sem_nenhuma_msg_alem_do_anuncio"] = sum(1 for m in leads.values() if not [x for x in m if not x[1] and not anuncio(x[3])])
res["perguntaram_cidade_ou_distancia"] = sum(bool(re.search(r"de qual cidade|onde fica|clinica é aonde|sou de|moro", " ".join(x[2].lower() for x in m if not x[1]))) for m in leads.values())

# relatórios diários do grupo
rel = {}
for ts, eu, txt, m in ch[GRUPO]:
    mm = re.search(r"Relat[óo]rio Di[áa]rio-\s*\[(\d\d)/(\d\d)/2026\]", txt)
    if not mm: continue
    dia = f"{mm.group(1)}/{mm.group(2)}"
    h = re.search(r"harmoniza[çc][ãa]o.*?Leads do dia:\s*(\d+).*?Agendamentos Pacientes Novos:\s*(\d*)", txt, re.S | re.I)
    c_ = re.search(r"Capilar.*?Leads do dia:\s*(\d+).*?Agendamentos Pacientes Novos:\s*(\d*)", txt, re.S | re.I)
    rel[dia] = {"harm_leads": int(h.group(1)) if h else None, "harm_agend": int(h.group(2) or 0) if h else None,
                "cap_leads": int(c_.group(1)) if c_ else None, "cap_agend": int(c_.group(2) or 0) if c_ else None}
res["relatorios_do_grupo"] = rel
res["totais_relatorios"] = {k: sum(v[k] or 0 for v in rel.values()) for k in ("harm_leads", "harm_agend", "cap_leads", "cap_agend")}

# volume geral
cl = sum(1 for m in ch.values() for x in m if not x[1]); cx = sum(1 for m in ch.values() for x in m if x[1])
res["msgs_recebidas"], res["msgs_enviadas"] = cl, cx
dia_msgs = collections.defaultdict(lambda: [0, 0])
for c, m in ch.items():
    if c == GRUPO: continue
    for x in m: dia_msgs[dt(x[0]).strftime("%d/%m")][int(x[1])] += 1
res["msgs_por_dia_(recebidas,enviadas)"] = sorted(dia_msgs.items())
res["chats_so_com_msgs_da_clinica"] = sum(1 for c, m in ch.items() if c != GRUPO and all(x[1] for x in m))
res["confirmacoes_de_agenda_enviadas"] = sum(1 for m in ch.values() for x in m if x[1] and re.search(r"confirmar seu agendamento|confirmar sua presen", x[2]))
res["mensagens_da_clinica_por_origem"] = collections.Counter(x[3].get("source") for m in ch.values() for x in m if x[1]).most_common()
# envios em lote (mesma mensagem em 3+ chats no mesmo minuto)
lote = collections.Counter()
for c, m in leads.items():
    for x in m:
        if humano(x) and re.search(r"vou te enviar algumas fotos|vou te enviar alguns casos|fotos de casos", x[2]): lote[dt(x[0]).strftime("%d/%m %H:%M")[:11]] += 1
res["envio_de_fotos_de_casos_por_dia_hora"] = sorted(lote.items())
(D / "ikima_metricas.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(json.dumps(res, ensure_ascii=False, indent=1))

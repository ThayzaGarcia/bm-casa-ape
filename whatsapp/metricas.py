#!/usr/bin/env python3
"""Métricas de atendimento a partir de dados/whatsapp.db (horário de Brasília)."""
import json, sqlite3, statistics as st, collections, re
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
D = Path(__file__).parent / "dados"
db = sqlite3.connect(D / "whatsapp.db")

# Conversas que não são de pacientes (equipe, médicos, fornecedores, spam) — classificadas na leitura manual
NAO_PACIENTE = {
    "559891691855": "Dr Tomaz (médico)", "559891263337": "Dra Walquiria (médica)", "559896038258": "Dr Clóvis (médico)",
    "559884138885": "Isabel (gestão)", "559884252900": "Keila (pessoal)", "559882020241": "próprio número",
    "559886027839": "Adailton (laudos)", "559892171010": "Click Laudos", "559892339540": "fornecedor raio-x",
    "5511999210621": "Claro", "556140040001": "Banco do Brasil", "559888184218": "divulgação cursos",
    "559881636003": "oferta Google Maps", "553190078143": "oferta software", "559881357791": "currículo",
}
AUTO = "Ola , Seja Bem-vindo(a) a Clínica CLINMED"
TEMPLATES = {
    "saudacao_automatica": AUTO,
    "apresentacao_keila": "Sou Keila  e darei continuidade",
    "combo_mulher": "combo da mulher em valor promocional",
    "combo_homem": "combo  promocional  súde do homem",
    "preco_morfologica": "a  morfologica do segundo trimestre com doppler",
    "endereco": "Ficamos localizados : Av. do Mercado Central",
    "confirmacao_agendamento": "Tudo confirmado!",
    "orcamento_sistema": "ORÇAMENTO DE PROCEDIMENTOS",
    "follow_up_marcar": "gostaria de est",
}

def dt(ms): return datetime.fromtimestamp(ms / 1000, BRT)
def util(d): return d.weekday() < 5 and (7 * 60 + 30) <= d.hour * 60 + d.minute < 17 * 60

rows = db.execute("SELECT chatid, ts_ms, de_mim, tipo, texto, raw FROM mensagens ORDER BY chatid, ts_ms").fetchall()
chats = collections.defaultdict(list)
for cid, ts, eu, tipo, txt, raw in rows:
    chats[cid].append((ts, eu, tipo, txt or "", json.loads(raw)))

pac = {c: m for c, m in chats.items() if not c.endswith("@g.us") and c.split("@")[0] not in NAO_PACIENTE}
res = {"total_conversas_com_msgs": len(chats), "grupos": sum(c.endswith("@g.us") for c in chats),
       "nao_pacientes": sorted(NAO_PACIENTE.values()), "conversas_pacientes": len(pac)}

# origem por anúncio
ads = collections.Counter(); chats_ad = set()
for c, ms in pac.items():
    for ts, eu, tipo, txt, m in ms:
        ci = str(m.get("content", ""))
        if "externalAdReply" in ci:
            u = re.search(r"'(?:sourceURL|sourceUrl)': '([^']+)'", ci)
            ads[u.group(1) if u else "?"] += 1; chats_ad.add(c)
res["conversas_vindas_de_anuncio"] = len(chats_ad)
res["anuncios"] = ads.most_common()

# 1ª resposta humana (ignora saudação automática) a partir da 1ª msg do cliente
prim, prim_util, sem_resp = [], [], []
for c, ms in pac.items():
    cli = [x for x in ms if not x[1]]
    if not cli: continue
    t0 = cli[0][0]
    hum = [x for x in ms if x[1] and x[0] >= t0 and AUTO not in x[3]]
    if not hum:
        sem_resp.append(c); continue
    mins = (hum[0][0] - t0) / 60000
    prim.append(mins)
    if util(dt(t0)): prim_util.append(mins)

# todas as esperas do cliente (bloco de msgs do cliente -> próxima msg humana da clínica)
esperas, esperas_util = [], []
for c, ms in pac.items():
    i = 0
    while i < len(ms):
        if not ms[i][1]:
            t0 = ms[i][0]
            j = i
            while j < len(ms) and not (ms[j][1] and AUTO not in ms[j][3]): j += 1
            if j < len(ms):
                w = (ms[j][0] - t0) / 60000; esperas.append(w)
                if util(dt(t0)): esperas_util.append(w)
            i = j + 1
        else: i += 1

def resumo(v):
    v = sorted(v)
    if not v: return {}
    return {"n": len(v), "mediana_min": round(st.median(v), 1), "media_min": round(st.mean(v), 1),
            "p90_min": round(v[int(len(v) * .9) - 1], 1), "ate_5min_%": round(100 * sum(x <= 5 for x in v) / len(v)),
            "mais_1h_%": round(100 * sum(x > 60 for x in v) / len(v)), "mais_24h": sum(x > 1440 for x in v)}

res["primeira_resposta_humana"] = resumo(prim)
res["primeira_resposta_humana_horario_comercial"] = resumo(prim_util)
res["todas_as_esperas"] = resumo(esperas)
res["todas_as_esperas_horario_comercial"] = resumo(esperas_util)
res["conversas_cliente_sem_nenhuma_resposta_humana"] = sem_resp

# mensagens de clientes fora do horário
fora = [x for ms in pac.values() for x in ms if not x[1] and not util(dt(x[0]))]
res["msgs_cliente_fora_horario"] = len(fora)
res["msgs_cliente_total"] = sum(1 for ms in pac.values() for x in ms if not x[1])

# uso dos textos padrão
uso = {k: sum(1 for ms in pac.values() for x in ms if x[1] and v in x[3]) for k, v in TEMPLATES.items()}
uso["follow_up_marcar"] = sum(1 for ms in pac.values() for x in ms if x[1] and re.search(r"gostaria de (est|marca|agend|deixar)", x[3], re.I))
res["uso_textos_padrao"] = uso

# nome pedido duas vezes (saudação automática + apresentação Keila) / nome já informado antes da apresentação
dup = ja_tinha = 0
for ms in pac.values():
    txts = [(x[1], x[3]) for x in ms]
    a = any(eu and AUTO in t for eu, t in txts); k = [i for i, (eu, t) in enumerate(txts) if eu and "Sou Keila" in t]
    if a and k:
        dup += 1
        if any(not eu for eu, t in txts[:k[0]]): ja_tinha += 1
res["nome_pedido_2x"] = dup
res["apresentacao_apos_cliente_ja_ter_escrito"] = ja_tinha

# tipos de mídia enviados pela clínica
res["clinica_por_tipo"] = collections.Counter(x[2] for ms in pac.values() for x in ms if x[1]).most_common()
res["audios_clinica"] = sum(1 for ms in pac.values() for x in ms if x[1] and x[2] == "AudioMessage")
res["msgs_por_dia_semana"] = collections.Counter(dt(x[0]).strftime("%a") for ms in pac.values() for x in ms if not x[1]).most_common()
res["msgs_cliente_por_hora"] = sorted(collections.Counter(dt(x[0]).hour for ms in pac.values() for x in ms if not x[1]).items())

(D / "metricas.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(json.dumps(res, ensure_ascii=False, indent=1))

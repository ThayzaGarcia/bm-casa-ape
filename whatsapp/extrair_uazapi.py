#!/usr/bin/env python3
"""Extrai dados da instância Uazapi (WhatsApp) e salva para consulta futura.

Uso:
    export UAZAPI_URL=https://free.uazapi.com
    export UAZAPI_TOKEN=<token da instância>
    python3 whatsapp/extrair_uazapi.py --dias 7

Saída (em whatsapp/dados/):
    raw/*.json          respostas brutas da API (status, contatos, etiquetas, respostas rápidas, chats)
    raw/mensagens/*.json mensagens brutas por conversa
    whatsapp.db         SQLite com tabelas `chats` e `mensagens` (consultável com qualquer cliente SQLite)
    conversas.md        transcrição legível das conversas do período
"""
import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = os.environ.get("UAZAPI_URL", "https://free.uazapi.com").rstrip("/")
TOKEN = os.environ.get("UAZAPI_TOKEN")
OUT = Path(__file__).parent / "dados"
TZ = timezone(timedelta(hours=-3))  # horário de Brasília


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"token": TOKEN, "Content-Type": "application/json", "Accept": "application/json"},
    )
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode() or "null")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and tentativa < 3:
                time.sleep(2 ** tentativa)
                continue
            print(f"  ! {method} {path} -> HTTP {e.code}: {e.read()[:200]!r}", file=sys.stderr)
            return None


def salvar(nome, obj):
    p = OUT / "raw" / nome
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def ts(v):
    """Normaliza timestamp (s ou ms) para epoch em segundos."""
    if not v:
        return 0
    v = int(v)
    return v // 1000 if v > 10**11 else v


def lista(resp, *chaves):
    if isinstance(resp, list):
        return resp
    for k in chaves:
        if isinstance(resp, dict) and isinstance(resp.get(k), list):
            return resp[k]
    return []


def texto(m):
    for k in ("text", "content", "caption", "body"):
        v = m.get(k)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, dict):
            for kk in ("text", "caption", "conversation"):
                if isinstance(v.get(kk), str):
                    return v[kk]
    return f"[{m.get('messageType') or m.get('type') or 'mídia'}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=7)
    args = ap.parse_args()
    if not TOKEN:
        sys.exit("Defina UAZAPI_TOKEN no ambiente.")
    corte = int((datetime.now(timezone.utc) - timedelta(days=args.dias)).timestamp())

    print("Status da instância…")
    salvar("status.json", api("GET", "/instance/status"))
    for nome, path in [("contatos.json", "/contacts"), ("etiquetas.json", "/labels"),
                       ("respostas_rapidas.json", "/quickreply/showall")]:
        print(f"Baixando {nome}…")
        salvar(nome, api("GET", path))

    print("Listando conversas…")
    chats, offset = [], 0
    while True:
        resp = api("POST", "/chat/find", {"operator": "AND", "sort": "-wa_lastMsgTimestamp",
                                          "limit": 100, "offset": offset})
        pag = lista(resp, "chats", "data", "results")
        if not pag:
            break
        chats += pag
        offset += len(pag)
        if ts(pag[-1].get("wa_lastMsgTimestamp")) < corte or len(pag) < 100:
            break
    salvar("chats.json", chats)
    recentes = [c for c in chats if ts(c.get("wa_lastMsgTimestamp")) >= corte]
    print(f"  {len(chats)} conversas no total, {len(recentes)} com atividade nos últimos {args.dias} dias")

    db = sqlite3.connect(OUT / "whatsapp.db")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS chats (chatid TEXT PRIMARY KEY, nome TEXT, is_grupo INTEGER,
        ultima_msg INTEGER, etiquetas TEXT, raw TEXT);
    CREATE TABLE IF NOT EXISTS mensagens (id TEXT PRIMARY KEY, chatid TEXT, timestamp INTEGER,
        data_hora TEXT, from_me INTEGER, remetente TEXT, tipo TEXT, texto TEXT, raw TEXT);
    CREATE INDEX IF NOT EXISTS idx_msg_chat ON mensagens(chatid, timestamp);
    """)

    md = [f"# Conversas WhatsApp — últimos {args.dias} dias\n",
          f"Extraído em {datetime.now(TZ):%d/%m/%Y %H:%M} (horário de Brasília)\n"]
    for i, c in enumerate(recentes, 1):
        chatid = c.get("wa_chatid") or c.get("chatid") or c.get("id")
        nome = c.get("wa_name") or c.get("wa_contactName") or c.get("name") or chatid
        print(f"  [{i}/{len(recentes)}] {nome}")
        msgs, offset = [], 0
        while True:
            resp = api("POST", "/message/find", {"chatid": chatid, "limit": 200, "offset": offset})
            pag = lista(resp, "messages", "data", "results")
            if not pag:
                break
            msgs += pag
            offset += len(pag)
            if min(ts(m.get("messageTimestamp")) for m in pag) < corte or len(pag) < 200:
                break
        msgs = sorted((m for m in msgs if ts(m.get("messageTimestamp")) >= corte),
                      key=lambda m: ts(m.get("messageTimestamp")))
        salvar(f"mensagens/{chatid.replace('@', '_')}.json", msgs)

        db.execute("INSERT OR REPLACE INTO chats VALUES (?,?,?,?,?,?)",
                   (chatid, nome, int("@g.us" in chatid), ts(c.get("wa_lastMsgTimestamp")),
                    json.dumps(c.get("wa_label") or c.get("labels"), ensure_ascii=False),
                    json.dumps(c, ensure_ascii=False)))
        md.append(f"\n## {nome} ({chatid})\n")
        for m in msgs:
            t = ts(m.get("messageTimestamp"))
            quando = datetime.fromtimestamp(t, TZ)
            quem = "EMPRESA" if m.get("fromMe") else (m.get("senderName") or "Cliente")
            db.execute("INSERT OR REPLACE INTO mensagens VALUES (?,?,?,?,?,?,?,?,?)",
                       (m.get("messageid") or m.get("id"), chatid, t, quando.isoformat(),
                        int(bool(m.get("fromMe"))), quem, m.get("messageType"), texto(m),
                        json.dumps(m, ensure_ascii=False)))
            md.append(f"- `{quando:%d/%m %H:%M}` **{quem}:** {texto(m)}")
    db.commit()
    (OUT / "conversas.md").write_text("\n".join(md))
    print(f"Pronto. Dados em {OUT}")


if __name__ == "__main__":
    main()

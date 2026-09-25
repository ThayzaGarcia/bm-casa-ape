#!/usr/bin/env python3
"""Extrai chats e mensagens da instância Uazapi e salva em SQLite + JSON.

Uso:
    export UAZAPI_URL=https://free.uazapi.com
    export UAZAPI_TOKEN=<token da instância>
    python3 whatsapp/extrair_uazapi.py --dias 7

Saída (em whatsapp/dados/):
    whatsapp.db         banco SQLite (tabelas chats e mensagens) para consultas futuras
    bruto/AAAA-MM-DD/   JSON cru devolvido pela API, por chat
"""
import argparse, json, os, sqlite3, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = os.environ.get("UAZAPI_URL", "https://free.uazapi.com").rstrip("/")
TOKEN = os.environ["UAZAPI_TOKEN"]
OUT = Path(__file__).parent / "dados"


def api(method, path, body=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"token": TOKEN, "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def ts_ms(v):
    v = int(v or 0)
    return v if v > 10**12 else v * 1000


def listar_chats(desde_ms):
    chats, offset = [], 0
    while True:
        r = api("POST", "/chat/find", {"sort": "-wa_lastMsgTimestamp", "limit": 100, "offset": offset})
        lote = r.get("chats", r if isinstance(r, list) else [])
        if not lote:
            break
        chats += lote
        if ts_ms(lote[-1].get("wa_lastMsgTimestamp")) < desde_ms:
            break
        offset += len(lote)
    return [c for c in chats if ts_ms(c.get("wa_lastMsgTimestamp")) >= desde_ms]


def listar_mensagens(chatid, desde_ms):
    msgs, offset = [], 0
    while True:
        r = api("POST", "/message/find", {"chatid": chatid, "limit": 200, "offset": offset})
        lote = r.get("messages", r if isinstance(r, list) else [])
        if not lote:
            break
        msgs += lote
        if min(ts_ms(m.get("messageTimestamp")) for m in lote) < desde_ms or not r.get("hasMore", True):
            break
        offset += len(lote)
        time.sleep(0.3)
    return [m for m in msgs if ts_ms(m.get("messageTimestamp")) >= desde_ms]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=7)
    a = ap.parse_args()
    desde = datetime.now(timezone.utc) - timedelta(days=a.dias)
    desde_ms = int(desde.timestamp() * 1000)

    OUT.mkdir(exist_ok=True)
    bruto = OUT / "bruto" / datetime.now().strftime("%Y-%m-%d")
    bruto.mkdir(parents=True, exist_ok=True)
    (bruto / "status.json").write_text(json.dumps(api("GET", "/instance/status"), ensure_ascii=False, indent=2))

    db = sqlite3.connect(OUT / "whatsapp.db")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS chats (chatid TEXT PRIMARY KEY, nome TEXT, is_grupo INTEGER,
        ultima_msg_ms INTEGER, raw TEXT);
    CREATE TABLE IF NOT EXISTS mensagens (id TEXT PRIMARY KEY, chatid TEXT, ts_ms INTEGER,
        data_hora TEXT, de_mim INTEGER, remetente TEXT, tipo TEXT, texto TEXT, raw TEXT);
    CREATE INDEX IF NOT EXISTS ix_msg_chat_ts ON mensagens(chatid, ts_ms);
    """)

    chats = listar_chats(desde_ms)
    print(f"{len(chats)} chats com atividade desde {desde:%d/%m/%Y}")
    for c in chats:
        cid = c.get("wa_chatid") or c.get("id")
        db.execute("INSERT OR REPLACE INTO chats VALUES (?,?,?,?,?)", (
            cid, c.get("wa_contactName") or c.get("wa_name") or c.get("name"),
            int(bool(c.get("wa_isGroup"))), ts_ms(c.get("wa_lastMsgTimestamp")),
            json.dumps(c, ensure_ascii=False)))
        msgs = listar_mensagens(cid, desde_ms)
        (bruto / f"{cid.replace('@', '_')}.json").write_text(json.dumps(msgs, ensure_ascii=False, indent=2))
        for m in msgs:
            t = ts_ms(m.get("messageTimestamp"))
            db.execute("INSERT OR REPLACE INTO mensagens VALUES (?,?,?,?,?,?,?,?,?)", (
                m.get("messageid") or m.get("id"), cid, t,
                datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                int(bool(m.get("fromMe"))), m.get("senderName") or m.get("sender"),
                m.get("messageType"), m.get("text") or "", json.dumps(m, ensure_ascii=False)))
        print(f"  {cid}: {len(msgs)} mensagens")
        db.commit()
    db.close()


if __name__ == "__main__":
    main()

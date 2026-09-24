#!/usr/bin/env python3
"""Exporta chats, mensagens, respostas rápidas e etiquetas de uma instância uazapi.

Uso:
    export UAZAPI_URL=https://free.uazapi.com
    export UAZAPI_TOKEN=<token da instância>
    python3 whatsapp/export_uazapi.py --days 7      # só conversas dos últimos 7 dias
    python3 whatsapp/export_uazapi.py --days 0      # histórico completo

Saída (em whatsapp/data/):
    raw/*.json          respostas brutas da API (para reprocessar depois)
    whatsapp.db         SQLite com tabelas chats, messages, quick_replies, labels
"""
import argparse, json, os, sqlite3, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

BASE = os.environ.get("UAZAPI_URL", "https://free.uazapi.com").rstrip("/")
TOKEN = os.environ.get("UAZAPI_TOKEN")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"token": TOKEN, "Content-Type": "application/json", "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt); continue
            print(f"[{e.code}] {method} {path}: {e.read()[:300]!r}", file=sys.stderr)
            return None


def ts_ms(v):
    """uazapi devolve timestamps em ms (às vezes em s); normaliza para ms."""
    try:
        v = int(v or 0)
    except (TypeError, ValueError):
        return 0
    return v * 1000 if 0 < v < 10**11 else v


def save_raw(name, data):
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    with open(os.path.join(OUT, "raw", name), "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def fetch_chats(cutoff):
    chats, offset = [], 0
    while True:
        r = call("POST", "/chat/find", {"operator": "AND", "sort": "-wa_lastMsgTimestamp",
                                        "limit": 100, "offset": offset})
        page = (r or {}).get("chats") or []
        chats += page
        if not page or (cutoff and ts_ms(page[-1].get("wa_lastMsgTimestamp")) < cutoff):
            break
        offset += len(page)
    if cutoff:
        chats = [c for c in chats if ts_ms(c.get("wa_lastMsgTimestamp")) >= cutoff]
    return chats


def fetch_messages(chatid, cutoff):
    msgs, offset = [], 0
    while True:
        r = call("POST", "/message/find", {"chatid": chatid, "limit": 200, "offset": offset})
        page = (r or {}).get("messages") or []
        msgs += page
        oldest = min((ts_ms(m.get("messageTimestamp")) for m in page), default=0)
        if not page or not (r or {}).get("hasMore", len(page) == 200) or (cutoff and oldest < cutoff):
            break
        offset = r.get("nextOffset") or offset + len(page)
    return msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="janela em dias (0 = tudo)")
    a = ap.parse_args()
    if not TOKEN:
        sys.exit("Defina UAZAPI_TOKEN")
    cutoff = int((time.time() - a.days * 86400) * 1000) if a.days else 0

    status = call("GET", "/instance/status"); save_raw("instance_status.json", status)
    quick = call("GET", "/quickreply/showall"); save_raw("quick_replies.json", quick)
    labels = call("GET", "/labels"); save_raw("labels.json", labels)
    chats = fetch_chats(cutoff); save_raw("chats.json", chats)
    print(f"{len(chats)} chats")

    db = sqlite3.connect(os.path.join(OUT, "whatsapp.db"))
    db.executescript("""
      CREATE TABLE IF NOT EXISTS chats(chatid TEXT PRIMARY KEY, name TEXT, is_group INT,
        last_msg_ts INT, labels TEXT, raw TEXT);
      CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, chatid TEXT, ts INT, dt TEXT,
        from_me INT, sender TEXT, sender_name TEXT, type TEXT, text TEXT, raw TEXT);
      CREATE INDEX IF NOT EXISTS ix_msg_chat_ts ON messages(chatid, ts);
      CREATE TABLE IF NOT EXISTS quick_replies(id TEXT PRIMARY KEY, shortcut TEXT, text TEXT, raw TEXT);
      CREATE TABLE IF NOT EXISTS labels(id TEXT PRIMARY KEY, name TEXT, raw TEXT);
    """)
    for q in (quick if isinstance(quick, list) else (quick or {}).get("quickReplies") or []):
        db.execute("INSERT OR REPLACE INTO quick_replies VALUES(?,?,?,?)",
                   (str(q.get("id")), q.get("shortCut") or q.get("shortcut"), q.get("text"), json.dumps(q, ensure_ascii=False)))
    for l in (labels if isinstance(labels, list) else (labels or {}).get("labels") or []):
        db.execute("INSERT OR REPLACE INTO labels VALUES(?,?,?)",
                   (str(l.get("id") or l.get("labelid")), l.get("name"), json.dumps(l, ensure_ascii=False)))

    all_msgs = {}
    for i, c in enumerate(chats, 1):
        cid = c.get("wa_chatid") or c.get("id")
        db.execute("INSERT OR REPLACE INTO chats VALUES(?,?,?,?,?,?)",
                   (cid, c.get("wa_contactName") or c.get("wa_name") or c.get("name"),
                    int(bool(c.get("wa_isGroup"))), ts_ms(c.get("wa_lastMsgTimestamp")),
                    json.dumps(c.get("wa_label"), ensure_ascii=False), json.dumps(c, ensure_ascii=False)))
        msgs = fetch_messages(cid, cutoff)
        all_msgs[cid] = msgs
        for m in msgs:
            t = ts_ms(m.get("messageTimestamp"))
            db.execute("INSERT OR REPLACE INTO messages VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (m.get("messageid") or m.get("id"), cid, t,
                        datetime.fromtimestamp(t / 1000, timezone.utc).isoformat() if t else None,
                        int(bool(m.get("fromMe"))), m.get("sender"), m.get("senderName"),
                        m.get("messageType"), m.get("text") or (m.get("content") or {}).get("text") if isinstance(m.get("content"), dict) else m.get("text"),
                        json.dumps(m, ensure_ascii=False)))
        print(f"  [{i}/{len(chats)}] {cid}: {len(msgs)} msgs")
    db.commit()
    save_raw("messages.json", all_msgs)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()

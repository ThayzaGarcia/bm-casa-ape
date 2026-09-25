#!/usr/bin/env python3
"""Gera transcrições legíveis (horário de Brasília) a partir de dados/whatsapp.db."""
import ast, json, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
D = Path(__file__).parent / "dados"
db = sqlite3.connect(D / "whatsapp.db")


def conteudo(m):
    c = m.get("content")
    if isinstance(c, str):
        try:
            c = ast.literal_eval(c)
        except Exception:
            try: c = json.loads(c)
            except Exception: c = {}
    return c if isinstance(c, dict) else {}


def descrever(m):
    t, c = m.get("messageType"), conteudo(m)
    txt = (m.get("text") or "").strip()
    if t == "call":
        e = c.get("event", {})
        return f"[LIGAÇÃO {'vídeo' if e.get('callType') else 'voz'} · {m.get('status')} · {e.get('duration', 0)}s]"
    extra = {"AudioMessage": "[ÁUDIO]", "ImageMessage": "[IMAGEM]", "DocumentMessage": f"[DOCUMENTO {c.get('fileName') or c.get('title') or ''}]",
             "StickerMessage": "[FIGURINHA]", "ContactMessage": "[CONTATO]", "LocationMessage": "[LOCALIZAÇÃO]",
             "AlbumMessage": "[ÁLBUM]", "VideoMessage": "[VÍDEO]"}.get(t, "")
    ad = (c.get("contextInfo") or {}).get("externalAdReply") or {}
    if ad:
        extra += f" [ANÚNCIO: {ad.get('title') or ''} | {ad.get('sourceURL') or ad.get('sourceUrl') or ''}]"
    cap = c.get("caption") or ""
    return " ".join(x for x in [extra, cap if cap and cap != txt else "", txt] if x).strip()


out = []
chats = db.execute("SELECT chatid, nome, is_grupo FROM chats ORDER BY ultima_msg_ms DESC").fetchall()
for cid, nome, grupo in chats:
    msgs = db.execute("SELECT raw FROM mensagens WHERE chatid=? ORDER BY ts_ms", (cid,)).fetchall()
    if not msgs:
        continue
    out.append(f"\n===== CHAT {cid} | {nome or '-'}{' | GRUPO' if grupo else ''} | {len(msgs)} msgs =====")
    for (r,) in msgs:
        m = json.loads(r)
        dt = datetime.fromtimestamp(int(m["messageTimestamp"]) / 1000, BRT)
        quem = "CLÍNICA" if m.get("fromMe") else "CLIENTE"
        if m.get("fromMe") and m.get("source"):
            quem += f"({m['source']})"
        out.append(f"[{dt:%a %d/%m %H:%M}] {quem}: {descrever(m)}")
(D / "transcricoes.txt").write_text("\n".join(out))
print(len(out), "linhas")

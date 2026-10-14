"""Baixa todas as conversas de uma instância Uazapi e monta um banco SQLite consultável.

Uso:
    UAZAPI_TOKEN=<token da instância> python3 extrair.py [pasta_saida]

Gera em pasta_saida (padrão: ../whatsapp, ignorada pelo git):
    raw/chats.json, raw/messages.json  -> dados brutos da API
    whatsapp.db                        -> tabelas chats, messages e idmap
    transcripts/<chatid>.txt           -> uma transcrição legível por conversa
"""
import datetime, glob, json, os, re, sqlite3, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

SERVER = os.environ.get("UAZAPI_SERVER", "https://free.uazapi.com")
TOKEN = os.environ.get("UAZAPI_TOKEN") or sys.exit("Defina UAZAPI_TOKEN")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "whatsapp")
TZ = datetime.timezone(datetime.timedelta(hours=-3))


def post(path, body):
    for a in range(6):
        try:
            r = urllib.request.Request(SERVER + path, data=json.dumps(body).encode(),
                                       headers={"token": TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(r, timeout=120))
        except Exception as e:
            print("tentando de novo", path, e, file=sys.stderr)
            time.sleep(2 ** a)
    print("FALHOU", body, file=sys.stderr)
    return {}


def baixar_chats():
    chats, off = [], 0
    while True:
        d = post("/chat/find", {"limit": 500, "offset": off, "sort": "-wa_lastMsgTimestamp"})
        page = d.get("chats", [])
        chats += page
        if len(page) < 500:
            return chats
        off += 500


def baixar_mensagens(chats):
    # A paginação global de /message/find para em 2000; por isso buscamos também conversa a conversa.
    msgs, off = {}, 0
    while True:
        page = post("/message/find", {"limit": 1000, "offset": off}).get("messages", [])
        for m in page:
            msgs[m["id"]] = m
        if not page:
            break
        off += len(page)

    def por_chat(cid):
        out, off = [], 0
        while True:
            d = post("/message/find", {"chatid": cid, "limit": 1000, "offset": off})
            page = d.get("messages", [])
            out += page
            if not d.get("hasMore") or not page:
                return out
            off = d.get("nextOffset", off + len(page))

    alvos = {c[k] for c in chats for k in ("wa_chatid", "wa_chatlid") if c.get(k)}
    with ThreadPoolExecutor(6) as ex:
        for res in ex.map(por_chat, sorted(alvos)):
            for m in res:
                msgs[m["id"]] = m
    return sorted(msgs.values(), key=lambda m: m["messageTimestamp"])


def montar_db(chats, msgs):
    path = os.path.join(OUT, "whatsapp.db")
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.executescript("""
    create table chats(chatid text, chatlid text, name text, contact_name text, wa_name text, phone text,
                       is_group int, labels text, last_msg_ts int, unread int, archived int, raw text);
    create table messages(id text primary key, chatid text, ts int, dt text, from_me int, is_group int,
                          sender text, sender_name text, type text, text text, source text, status text,
                          quoted text, raw text);
    create table idmap(chatid text primary key, contact text);""")
    for c in chats:
        db.execute("insert into chats values(?,?,?,?,?,?,?,?,?,?,?,?)", (
            c["wa_chatid"], c.get("wa_chatlid"), c.get("name"), c.get("wa_contactName"), c.get("wa_name"),
            c.get("phone"), int(c["wa_isGroup"]), json.dumps(c["wa_label"]), c.get("wa_lastMsgTimestamp"),
            c.get("wa_unreadCount"), int(c.get("wa_archived", False)), json.dumps(c, ensure_ascii=False)))
    for m in msgs:
        content = m.get("content") if isinstance(m.get("content"), dict) else {}
        dt = datetime.datetime.fromtimestamp(m["messageTimestamp"] / 1000, TZ).isoformat()
        db.execute("insert or replace into messages values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            m["id"], m["chatid"], m["messageTimestamp"], dt, int(m["fromMe"]), int(m["isGroup"]), m.get("sender"),
            m.get("senderName"), m["messageType"], m.get("text") or content.get("caption", ""), m.get("source"),
            m.get("status"), m.get("quoted"), json.dumps(m, ensure_ascii=False)))
    # Um mesmo contato pode aparecer como telefone (@s.whatsapp.net) e como @lid; idmap unifica os dois.
    lid2phone = {lid: cid for cid, lid in db.execute("select chatid, chatlid from chats where coalesce(chatlid,'')!=''")}
    for (cid,) in db.execute("select distinct chatid from messages").fetchall():
        db.execute("insert into idmap values(?,?)", (cid, lid2phone.get(cid, cid)))
    db.execute("create index i_msg_chat on messages(chatid, ts)")
    db.commit()
    return db


def transcricoes(db):
    os.makedirs(os.path.join(OUT, "transcripts"), exist_ok=True)
    nomes = {}
    for cid, lid, n, cn, wn, ph in db.execute("select chatid, chatlid, name, contact_name, wa_name, phone from chats"):
        for k in (cid, lid):
            if k:
                nomes[k] = n or cn or wn or ph or cid
    rotulo = {"AudioMessage": "[áudio]", "ImageMessage": "[imagem]", "VideoMessage": "[vídeo]",
              "StickerMessage": "[figurinha]", "DocumentMessage": "[documento]", "call": "[ligação]"}
    for (cid,) in db.execute("select distinct chatid from messages").fetchall():
        linhas = [f"# {nomes.get(cid, cid)} ({cid})"]
        for dt, fm, sn, ty, tx in db.execute(
                "select dt, from_me, sender_name, type, text from messages where chatid=? order by ts", (cid,)):
            corpo = tx or ""
            if ty not in ("Conversation", "ExtendedTextMessage"):
                corpo = (rotulo.get(ty, f"[{ty}]") + " " + corpo).strip()
            linhas.append(f"{dt[:16]} | {'CLÍNICA' if fm else (sn or 'contato')}: {corpo}")
        nome = re.sub(r"[^\w@.-]", "_", cid)
        open(os.path.join(OUT, "transcripts", nome + ".txt"), "w").write("\n".join(linhas))


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    chats = baixar_chats()
    print(len(chats), "conversas")
    msgs = baixar_mensagens(chats)
    print(len(msgs), "mensagens")
    json.dump(chats, open(os.path.join(OUT, "raw", "chats.json"), "w"), ensure_ascii=False)
    json.dump(msgs, open(os.path.join(OUT, "raw", "messages.json"), "w"), ensure_ascii=False)
    transcricoes(montar_db(chats, msgs))
    print("Pronto:", os.path.abspath(OUT))

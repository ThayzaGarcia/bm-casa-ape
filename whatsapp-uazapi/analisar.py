import sqlite3,collections,re,json,datetime,statistics as st
import os,sys
BASE=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),"..","whatsapp")
db=sqlite3.connect(os.path.join(BASE,"whatsapp.db"))
TZ=datetime.timezone(datetime.timedelta(hours=-3)); D=lambda t:datetime.datetime.fromtimestamp(t,TZ)
ts_=lambda *a:datetime.datetime(*a,tzinfo=TZ).timestamp()
# Lacuna do histórico sincronizado (17/07 a 01/10/2026 só tem registros de ligação). Ajuste se a nova extração não tiver lacuna.
GAP=(ts_(2026,7,16,12),ts_(2026,10,2)); END=db.execute("select max(ts) from messages").fetchone()[0]/1000
AUTO=("Oieee, sua mensagem já chegou aqui","Olá!!\n\nÉ um prazer ter você aqui","Oieee, tudo bem? ✨")
isauto=lambda m: m["ty"] in("ButtonsMessage","TemplateMessage","NativeFlowMessage") or m["tx"].startswith(AUTO)
# Conversas internas (ex.: número pessoal da Dra.) a excluir da análise de leads: NUMEROS_INTERNOS=5577...,5577...
INTERNAL={n.strip()+"@s.whatsapp.net" for n in os.environ.get("NUMEROS_INTERNOS","").split(",") if n.strip()}
VENDOR=r"pedido|entrega|estoque|promoç|receita já está|prescriç|grupo foca|papelaria|seja bem-vindo|fornecedor|boleto vence|nota fiscal"
C=collections.defaultdict(list)
for contact,ts,fm,ty,tx,raw in db.execute("select i.contact,ts,from_me,type,text,raw from messages m join idmap i on i.chatid=m.chatid where is_group=0 order by ts"):
    C[contact].append(dict(ts=ts/1000,fm=fm,ty=ty,tx=tx or "",ad='externalAdReply' in raw,raw=raw if ty=="call" else ""))
M={}
# volumes
M["total_msgs"]=db.execute("select count(*) from messages").fetchone()[0]
M["chats_total"]=db.execute("select count(*) from chats").fetchone()[0]
M["chats_with_msgs"]=len(C)+db.execute("select count(distinct chatid) from messages where is_group=1").fetchone()[0]
M["groups_with_msgs"]=db.execute("select count(distinct chatid) from messages where is_group=1").fetchone()[0]
M["by_month"]=db.execute("select substr(dt,1,7),sum(case when is_group=0 and from_me=0 then 1 else 0 end),sum(case when is_group=0 and from_me=1 then 1 else 0 end),sum(is_group) from messages where type!='call' group by 1").fetchall()
M["internal_doc_msgs"]=sum(1 for c in INTERNAL for _ in db.execute("select 1 from messages m join idmap i on i.chatid=m.chatid where i.contact=?",(c,)))
M["types"]=db.execute("select type,count(*) from messages group by 1 order by 2 desc").fetchall()
a=db.execute("select count(*),sum(json_extract(raw,'$.content.seconds')) from messages where from_me=1 and is_group=0 and type='AudioMessage'").fetchone(); M["audio_out"]=a
M["audio_in"]=db.execute("select count(*),sum(json_extract(raw,'$.content.seconds')) from messages where from_me=0 and is_group=0 and type='AudioMessage'").fetchone()
# calls
calls=[json.loads(r[0]) for r in db.execute("select raw from messages where type='call' and from_me=0")]
ev=[c["content"].get("event",{}) for c in calls]
M["calls_in"]=len(ev); M["calls_in_missed"]=sum(1 for e in ev if e.get("callResult",0)!=0 or not e.get("duration"))
M["calls_result"]=collections.Counter(e.get("callResult") for e in ev).most_common()
LEADS=[]; heat=collections.Counter(); bursts=[]
for k,ms in C.items():
    if k in INTERNAL: continue
    msn=[m for m in ms if m["ty"]!="call"]
    if not msn: continue
    inb=[m for m in msn if not m["fm"]]
    for i,m in enumerate(msn):
        if not m["fm"] and (i==0 or msn[i-1]["fm"] or msn[i]["ts"]-msn[i-1]["ts"]>3600*6):
            d=D(m["ts"]); heat[(d.weekday(),d.hour)]+=1
            nxt=next((x for x in msn[i+1:] if x["fm"] and not isauto(x)),None)
            w=(nxt["ts"]-m["ts"])/60 if nxt else None
            ok = m["ts"]+86400<min(END, GAP[0]) or (m["ts"]>GAP[1] and m["ts"]+86400<END)
            bursts.append(dict(k=k,ts=m["ts"],wd=d.weekday(),h=d.hour,w=w,ok=ok))
    if not inb: continue
    it=" ".join(m["tx"].lower() for m in inb); ct=" ".join(m["tx"].lower() for m in msn if m["fm"])
    entry=next((m for m in inb[:4] if m["ad"] or m["tx"].startswith(("Olá, vim do instagram","Olá! Quero agendar","Olá, vim do site"))),None)
    new=not msn[0]["fm"] and msn[0]["ts"]>ts_(2025,10,21)
    interest=re.search(r"valor|preço|quanto|agendar|marcar|consulta|avalia|procedimento|botox|preench|harmoniza|papada|full ?face|olheira|l[áa]bio|bioestim",it)
    if not (entry or (new and interest)) or re.search(VENDOR,it[:400]): continue
    first=inb[0]; hum=[m for m in msn if m["fm"] and not isauto(m)]
    fr=next((m for m in hum if m["ts"]>=first["ts"]),None)
    pi=[i for i,m in enumerate(msn) if m["fm"] and re.search(r"pix/cnpj|pagamento antecipado|pay\.infinitepay",m["tx"].lower())]
    paid=bool(re.search(r"comprovante|paguei|fiz o pix|pix feito|transferi|já paguei|ja paguei",it)) or bool(pi and any((not m["fm"]) and m["ty"] in("ImageMessage","DocumentMessage") for m in msn[pi[0]:]))
    src="Anúncio (Click-to-WhatsApp)" if any(m["ad"] for m in inb[:4]) else ("Link do Instagram (bio/direct)" if entry and entry["tx"].startswith("Olá, vim do instagram") else ("Link 'Quero agendar'" if entry and entry["tx"].startswith("Olá! Quero agendar") else ("Site" if entry else "Contato direto")))
    d=D(first["ts"])
    LEADS.append(dict(month=d.strftime("%Y-%m"),src=src,wd=d.weekday(),h=d.hour,
        bh=(d.weekday()<5 and 8<=d.hour<18) or (d.weekday()==5 and 8<=d.hour<12),
        fr=(fr["ts"]-first["ts"])/60 if fr else None, fr_ok=first["ts"]+86400<min(END,GAP[0]) or (first["ts"]>GAP[1] and first["ts"]+86400<END),
        engaged=any((not m["fm"]) for m in msn if fr and m["ts"]>fr["ts"]),
        price=bool(re.search(r"valor|preço|preco|quanto (custa|fica|é|e|ta|tá)|investimento",it)),
        price_text=bool(re.search(r"r\$ ?\d|1\.300|1\.400|1\.500|250,00|250 reais|\b250\b",ct)),
        audio=sum(1 for m in msn if m["fm"] and m["ty"]=="AudioMessage"),
        slot=bool(re.search(r"consigo (um encaixe|às|as|dia|pra)|daria certo|fica confortável|manhã ou (à |a )?tarde",ct)),
        payreq=bool(pi),paid=paid,
        stall=bool(re.search(r"vou ver|vou pensar|vou analisar|vou me organizar|depois (eu )?(te )?(falo|chamo|retorno)|mais pra frente|volto a falar|te aviso|já te falo|vou verificar",it)),
        followup_tpl=any(m["fm"] and m["ty"]=="TemplateMessage" or re.search(r"Às vezes a gente deixa|Só queria deixar esse lembrete|Tem algo aí dentro",m["tx"]) for m in msn if m["fm"]),
        city=next((v for c,v in [("maring","Maringá"),("brumado","Brumado"),("conquista","Vitória da Conquista"),("vca","Vitória da Conquista"),("porto seguro","Porto Seguro"),("jequi","Jequié"),("anag","Anagé"),("itapetinga","Itapetinga"),("barra da estiva","Barra da Estiva"),("belo campo","Belo Campo"),("salvador","Salvador"),("divisa","Divisa Alegre"),("cândido sales","Cândido Sales"),("candido sales","Cândido Sales"),("guanambi","Guanambi"),("poções","Poções")] if c in it),"Não informado"),
        procs=[p for p,rx in {"Full face":r"full ?face","Botox / toxina":r"botox|toxina","Lábios":r"l[áa]bio|labial","Olheiras":r"olheira","Bigode chinês":r"bigode","Mandíbula / mento / queixo":r"mand[íi]bula|\bmento\b|queixo","Papada / lipo de papada":r"papada|lipo","Bioestimulador / colágeno":r"bioestimulador|sculptra|radiesse|col[áa]geno","Nariz / rino":r"nariz|\brino","Remoção de ácido":r"tira(m|r)? (o )?ácido|remo(ver|ção)|hialuronidase","Harmonização (genérico)":r"harmoniza"}.items() if re.search(rx,it)],
        objections=[o for o,rx in {"Preço / 'caro'":r"\bcaro\b|\bcara\b|muito alto|sem condi|não tenho condi|nao tenho condi|desconto|não tenho como","Distância / agenda":r"não moro|nao moro|moro em|distância|distancia|só posso|so posso|não consigo (ir|nesse)|horário (de|no) (sábado|sabado)|final de semana","Medo / insegurança":r"\bmedo\b|receio|insegur|artificial|exager|natural","Dor / recuperação":r"\bdói\b|\bdoi\b|\bdor\b|recupera|inchad|roxo","Quer pensar / adiar":r"vou ver|vou pensar|vou analisar|mais pra frente|me organizar"}.items() if re.search(rx,it)],
        last_clinic=msn[-1]["fm"]==1,
    ))
M["leads_n"]=len(LEADS)
M["leads_month"]=sorted(collections.Counter(l["month"] for l in LEADS).items())
M["leads_src"]=collections.Counter(l["src"] for l in LEADS).most_common()
M["leads_src_month"]={m:dict(collections.Counter(l["src"] for l in LEADS if l["month"]==m)) for m,_ in M["leads_month"]}
f=lambda key: sum(1 for l in LEADS if l[key])
M["funnel"]=dict(leads=len(LEADS),responded=sum(1 for l in LEADS if l["fr"] is not None),engaged=f("engaged"),price=f("price"),slot=f("slot"),payreq=f("payreq"),paid=f("paid"))
M["leads_extra"]=dict(price_text=f("price_text"),audio_any=sum(1 for l in LEADS if l["audio"]),stall=f("stall"),followup_tpl=f("followup_tpl"),last_clinic=f("last_clinic"))
pr=[l for l in LEADS if l["price"]]
M["price_askers"]=dict(n=len(pr),got_text_price=sum(l["price_text"] for l in pr),got_audio=sum(1 for l in pr if l["audio"]),slot=sum(l["slot"] for l in pr),paid=sum(l["paid"] for l in pr))
def summ(v):
    v=sorted(v); n=len(v)
    return dict(n=n,med=round(st.median(v),1),p75=round(v[int(.75*n)],1),p90=round(v[int(.9*n)],1),le5=round(100*sum(x<=5 for x in v)/n),le15=round(100*sum(x<=15 for x in v)/n),le60=round(100*sum(x<=60 for x in v)/n))
LR=[l for l in LEADS if l["fr_ok"]]
M["lead_first_resp_bh"]=summ([l["fr"] for l in LR if l["bh"] and l["fr"] is not None])
M["lead_first_resp_off"]=summ([l["fr"] for l in LR if not l["bh"] and l["fr"] is not None])
M["lead_no_resp_24h"]=dict(n=len(LR),none=sum(1 for l in LR if l["fr"] is None or l["fr"]>1440))
M["lead_off_hours_share"]=round(100*sum(not l["bh"] for l in LEADS)/len(LEADS))
B=[b for b in bursts if b["ok"]]
bh=lambda b:(b["wd"]<5 and 8<=b["h"]<18) or (b["wd"]==5 and 8<=b["h"]<12)
M["all_resp_bh"]=summ([b["w"] for b in B if bh(b) and b["w"] is not None])
M["all_noresp_24h"]=dict(n=len(B),none=sum(1 for b in B if b["w"] is None or b["w"]>1440))
M["bursts_month"]={m:summ([b["w"] for b in B if bh(b) and b["w"] is not None and D(b["ts"]).strftime("%Y-%m")==m]) for m in sorted(set(D(b["ts"]).strftime("%Y-%m") for b in B)) if sum(1 for b in B if D(b["ts"]).strftime("%Y-%m")==m)>30}
M["heat"]=[[heat[(wd,h)] for h in range(24)] for wd in range(7)]
M["procs"]=collections.Counter(p for l in LEADS for p in l["procs"]).most_common()
M["cities"]=collections.Counter(l["city"] for l in LEADS).most_common()
M["objections"]=collections.Counter(o for l in LEADS for o in l["objections"]).most_common()
M["leads_by_src_funnel"]={s:dict(n=sum(1 for l in LEADS if l["src"]==s),engaged=sum(1 for l in LEADS if l["src"]==s and l["engaged"]),slot=sum(1 for l in LEADS if l["src"]==s and l["slot"]),paid=sum(1 for l in LEADS if l["src"]==s and l["paid"])) for s,_ in M["leads_src"]}
json.dump(M,open(os.path.join(BASE,"metrics.json"),"w"),ensure_ascii=False,indent=1)
for k,v in M.items():
    if k not in("heat","types"): print(k,":",v)

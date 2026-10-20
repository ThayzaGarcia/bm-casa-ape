import json,html
import os,sys
BASE=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),"..","whatsapp")
M=json.load(open(os.path.join(BASE,"metrics.json")))
OUT=os.path.join(BASE,"relatorio.html")
MES={"01":"jan","02":"fev","03":"mar","04":"abr","05":"mai","06":"jun","07":"jul","08":"ago","09":"set","10":"out","11":"nov","12":"dez"}
lab=lambda ym: MES[ym[5:]]+("/"+ym[2:4] if ym[5:] in("01","10") else "")
fmt=lambda n: f"{n:,}".replace(",",".")

# ---- chart 1: monthly 1:1 messages (inbound+outbound), gap months hatched
def monthly():
    rows=M["by_month"]; W,H,pl,pb,pt=640,220,44,28,14
    vals=[r[1]+r[2] for r in rows]; mx=5000
    bw=(W-pl-8)/len(rows); s=[]
    for t in range(0,mx+1,1000):
        y=pt+(H-pt-pb)*(1-t/mx)
        s.append(f'<line x1="{pl}" x2="{W-4}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/><text x="{pl-6}" y="{y+4:.1f}" class="ax" text-anchor="end">{fmt(t)}</text>')
    for i,(r,v) in enumerate(zip(rows,vals)):
        x=pl+i*bw+bw*0.18; w=bw*0.64; gap=r[0] in("2026-08","2026-09")
        h=(H-pt-pb)*v/mx; y=H-pb-h
        if gap:
            s.append(f'<rect x="{x:.1f}" y="{pt}" width="{w:.1f}" height="{H-pt-pb}" class="gapbox"><title>{lab(r[0])}: sem histórico sincronizado (só registros de ligação)</title></rect>')
        else:
            s.append(f'<path d="M{x:.1f},{H-pb} v{-(h-4):.1f} q0,-4 4,-4 h{w-8:.1f} q4,0 4,4 v{h-4:.1f} z" class="bar"><title>{lab(r[0])}: {fmt(v)} mensagens em conversas individuais ({fmt(r[1])} recebidas, {fmt(r[2])} enviadas)</title></path>')
            if r[0] in("2026-06","2026-01","2026-10"):
                s.append(f'<text x="{x+w/2:.1f}" y="{y-6:.1f}" class="vl" text-anchor="middle">{fmt(v)}</text>')
        s.append(f'<text x="{x+w/2:.1f}" y="{H-pb+16}" class="ax" text-anchor="middle">{lab(r[0])}</text>')
    xg=pl+10*bw+bw*0.18
    s.append(f'<text x="{xg+bw*0.82:.1f}" y="{pt+44}" class="note" text-anchor="middle">sem</text><text x="{xg+bw*0.82:.1f}" y="{pt+58}" class="note" text-anchor="middle">dados</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Mensagens por mês em conversas individuais">{"".join(s)}</svg>'

def leadsmonth():
    rows=[r for r in M["leads_month"]]
    allm=["2025-10","2025-11","2025-12","2026-01","2026-02","2026-03","2026-04","2026-05","2026-06","2026-07","2026-08","2026-09","2026-10"]
    d=dict(rows); W,H,pl,pb,pt=640,200,36,28,18; mx=80; bw=(W-pl-8)/len(allm); s=[]
    for t in range(0,81,20):
        y=pt+(H-pt-pb)*(1-t/mx); s.append(f'<line x1="{pl}" x2="{W-4}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/><text x="{pl-6}" y="{y+4:.1f}" class="ax" text-anchor="end">{t}</text>')
    for i,m in enumerate(allm):
        x=pl+i*bw+bw*0.18; w=bw*0.64
        if m in("2026-08","2026-09"):
            s.append(f'<rect x="{x:.1f}" y="{pt}" width="{w:.1f}" height="{H-pt-pb}" class="gapbox"><title>sem histórico</title></rect>')
        else:
            v=d.get(m,0); h=(H-pt-pb)*v/mx; y=H-pb-h
            s.append(f'<path d="M{x:.1f},{H-pb} v{-(h-4):.1f} q0,-4 4,-4 h{w-8:.1f} q4,0 4,4 v{h-4:.1f} z" class="bar{" bar-hi" if m=="2026-10" else ""}"><title>{lab(m)}: {v} leads{" (só 7 a 14/10)" if m=="2026-10" else ""}</title></path>')
            s.append(f'<text x="{x+w/2:.1f}" y="{y-6:.1f}" class="vl" text-anchor="middle">{v}</text>')
        s.append(f'<text x="{x+w/2:.1f}" y="{H-pb+16}" class="ax" text-anchor="middle">{lab(m)}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Novos leads por mês">{"".join(s)}</svg>'

def funnel():
    F=M["funnel"]; steps=[("Leads que chegaram",F["leads"]),("Receberam resposta de uma pessoa",F["responded"]),("Responderam de volta",F["engaged"]),("Receberam proposta de horário",F["slot"]),("Receberam pedido de sinal (R$ 250)",F["payreq"]),("Sinal pago (comprovante)",F["paid"])]
    out=[]
    for i,(n,v) in enumerate(steps):
        p=100*v/F["leads"]
        out.append(f'<div class="frow"><div class="flab">{n}</div><div class="ftrack"><div class="fbar{" fdrop" if i==3 else ""}" style="width:{p:.1f}%"></div></div><div class="fval"><b>{v}</b> <span>{p:.0f}%</span></div></div>')
    return "".join(out)

def hbars(items,total=None,maxv=None):
    maxv=maxv or max(v for _,v in items); out=[]
    for n,v in items:
        out.append(f'<div class="hrow"><div class="hlab">{html.escape(n)}</div><div class="htrack"><div class="hbar" style="width:{100*v/maxv:.1f}%"></div></div><div class="hval">{v}</div></div>')
    return "".join(out)

def heat():
    H=M["heat"]; days=["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]; hrs=list(range(6,23)); mx=max(max(r) for r in H)
    cw,ch,pl,pt=32,24,40,22; W=pl+cw*len(hrs)+4; Ht=pt+ch*7+4; s=[]
    for j,h in enumerate(hrs): s.append(f'<text x="{pl+j*cw+cw/2}" y="{pt-8}" class="ax" text-anchor="middle">{h}h</text>')
    for i,d in enumerate(days):
        s.append(f'<text x="{pl-8}" y="{pt+i*ch+ch/2+4}" class="ax" text-anchor="end">{d}</text>')
        for j,h in enumerate(hrs):
            v=H[i][h]; a=0.06+0.94*(v/mx)**0.8 if v else 0
            open_=(i<5 and 8<=h<18) or (i==5 and 8<=h<12)
            s.append(f'<rect x="{pl+j*cw+1}" y="{pt+i*ch+1}" width="{cw-2}" height="{ch-2}" rx="3" class="cell{"" if open_ else " closed"}" style="fill-opacity:{a:.2f}"><title>{d} {h}h: {v} conversas iniciadas{"" if open_ else " (fora do horário)"}</title></rect>')
    return f'<div class="scroll"><svg viewBox="0 0 {W} {Ht}" style="min-width:560px" role="img" aria-label="Mapa de calor de mensagens recebidas por dia e hora">{"".join(s)}</svg></div>'

F=M["funnel"]; lb=M["lead_first_resp_bh"]; lo=M["lead_first_resp_off"]; nr=M["lead_no_resp_24h"]
src=M["leads_by_src_funnel"]
srcrows="".join(f'<tr><td>{html.escape(k)}</td><td class="n">{v["n"]}</td><td class="n">{v["engaged"]}</td><td class="n">{v["slot"]}</td><td class="n">{v["paid"]}</td></tr>' for k,v in src.items())

SS={r["key"]:r for r in M["script_steps"]}
st=lambda k: SS[k]["pct"]
FA=M["followup_auto"]
cmp_rows="".join(f'<tr><td>{SS[k]["name"]}</td><td class="n">{SS[k]["n"]}</td><td class="n hi">{SS[k]["conv_with"]}%</td><td class="n">{SS[k]["conv_without"]}%</td></tr>' for k in ("periodo","horario","preco"))
ws_rows=hbars(M["written_scripts"],maxv=max(5,max(n for _,n in M["written_scripts"])))
doc=f'''<title>Raio-X WhatsApp Nader Beauty</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Instrument+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: relatório de leitura em coluna única (~720px), seções numeradas só onde há sequência real (plano de ação) */
:root{{
 --bg:#fbf8f7; --surface:#ffffff; --ink:#221a1d; --ink2:#5f5357; --muted:#8c8084; --line:#ebe3e4;
 --accent:#8a3557; --accent-soft:#f3e4ea; --gapfill:#efe9ea;
 --good:#2f7d4f; --warn:#b06a00; --crit:#b3261e;
 --display:"Fraunces",Georgia,"Times New Roman",serif; --body:"Instrument Sans",system-ui,-apple-system,"Segoe UI",sans-serif; --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#171214;--surface:#211a1d;--ink:#f3ecee;--ink2:#c7bbbf;--muted:#9a8d91;--line:#3a3034;--accent:#e08aab;--accent-soft:#3b2530;--gapfill:#2a2226;--good:#6cc28f;--warn:#e0a03a;--crit:#f07a72;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#171214;--surface:#211a1d;--ink:#f3ecee;--ink2:#c7bbbf;--muted:#9a8d91;--line:#3a3034;--accent:#e08aab;--accent-soft:#3b2530;--gapfill:#2a2226;--good:#6cc28f;--warn:#e0a03a;--crit:#f07a72;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6}}
.wrap{{max-width:760px;margin:0 auto;padding-block:40px 80px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:56px}}
h1,h2,h3{{font-family:var(--display);font-weight:600;text-wrap:balance;line-height:1.2;margin:0}}
h1{{font-size:clamp(2rem,5vw,2.8rem);letter-spacing:-.01em}}
h2{{font-size:1.6rem}} h3{{font-size:1.1rem;font-family:var(--body)}}
p{{margin:0}} section{{display:flex;flex-direction:column;gap:18px}}
.eyebrow{{font-family:var(--mono);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}}
.lede{{font-size:1.12rem;color:var(--ink2);max-width:62ch}}
.meta{{display:flex;flex-wrap:wrap;gap:8px 20px;font-family:var(--mono);font-size:.78rem;color:var(--muted)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.kpi{{background:var(--surface);padding:16px;display:flex;flex-direction:column;gap:4px;min-width:0}}
.kpi b{{font-family:var(--display);font-size:1.9rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}}
.kpi span{{font-size:.85rem;color:var(--ink2);line-height:1.35}}
.find{{display:flex;flex-direction:column;gap:14px;margin:0;padding:0;list-style:none}}
.find li{{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:start}}
.tag{{font-family:var(--mono);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:99px;border:1px solid currentColor;white-space:nowrap;margin-top:3px}}
.t-crit{{color:var(--crit)}} .t-warn{{color:var(--warn)}} .t-good{{color:var(--good)}}
.fig{{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:18px;display:flex;flex-direction:column;gap:12px;min-width:0}}
.fig h3{{font-size:1rem}} .cap{{font-size:.85rem;color:var(--muted)}}
svg{{width:100%;height:auto;display:block}}
.grid{{stroke:var(--line);stroke-width:1}} .ax{{fill:var(--muted);font-family:var(--mono);font-size:11px}} .vl{{fill:var(--ink);font-family:var(--mono);font-size:11px;font-weight:500}}
.note{{fill:var(--muted);font-family:var(--body);font-size:11px}}
.bar{{fill:var(--accent);fill-opacity:.55}} .bar:hover,.bar-hi{{fill-opacity:1}}
.gapbox{{fill:var(--gapfill)}}
.cell{{fill:var(--accent)}} .cell.closed{{stroke:var(--ink2);stroke-width:1;stroke-dasharray:2 2}}
.frow,.hrow{{display:grid;grid-template-columns:minmax(0,15rem) 1fr 4.5rem;gap:12px;align-items:center;font-size:.9rem}}
.hrow{{grid-template-columns:minmax(0,13rem) 1fr 2.5rem}}
.ftrack,.htrack{{height:14px;background:var(--gapfill);border-radius:4px;overflow:hidden}}
.fbar,.hbar{{height:100%;background:var(--accent);border-radius:0 4px 4px 0}}
.fdrop{{background:var(--crit)}}
.fval,.hval{{font-family:var(--mono);font-size:.85rem;text-align:right;font-variant-numeric:tabular-nums}} .fval span{{color:var(--muted)}}
@media (max-width:560px){{.frow,.hrow{{grid-template-columns:1fr 3.6rem}} .flab,.hlab{{grid-column:1/-1}} .ftrack,.htrack{{grid-column:1}} }}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}} th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}} th{{font-family:var(--mono);font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}} td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono)}}
blockquote{{margin:0;padding:10px 14px;border-left:3px solid var(--accent);background:var(--accent-soft);border-radius:0 8px 8px 0;font-size:.92rem;color:var(--ink)}}
blockquote small{{display:block;color:var(--ink2);font-size:.8rem;margin-top:4px}}
.plan{{display:flex;flex-direction:column;gap:22px}}
.phase{{display:grid;grid-template-columns:7rem 1fr;gap:16px}} @media (max-width:560px){{.phase{{grid-template-columns:1fr;gap:6px}}}}
.phase>div:first-child{{font-family:var(--mono);font-size:.78rem;color:var(--accent);text-transform:uppercase;letter-spacing:.06em;padding-top:3px}}
.phase ol{{margin:0;padding-left:1.2rem;display:flex;flex-direction:column;gap:8px}}
ul.plain{{margin:0;padding-left:1.2rem;display:flex;flex-direction:column;gap:8px}}
.small{{font-size:.88rem;color:var(--ink2)}}
.steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:0;counter-reset:st}}
.step{{display:grid;grid-template-columns:2.2rem 1fr;gap:14px;padding-block:14px;border-top:1px solid var(--line)}}
.step:first-child{{border-top:0}}
.step .num{{font-family:var(--display);font-size:1.4rem;color:var(--accent);line-height:1}}
.step .body{{display:flex;flex-direction:column;gap:8px;min-width:0}}
.step .head{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 12px;align-items:baseline}}
.step .head b{{font-size:1rem}}
.use{{font-family:var(--mono);font-size:.8rem;color:var(--ink2);font-variant-numeric:tabular-nums}}
.use.low{{color:var(--crit)}}
.msg{{background:var(--accent-soft);border-radius:4px 12px 12px 12px;padding:8px 12px;font-size:.88rem;white-space:pre-line;max-width:52ch}}
.msg.auto{{background:var(--gapfill)}}
.compare td.hi{{color:var(--good);font-weight:600}}
.recipe{{counter-reset:r;list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:14px}}
.recipe li{{display:flex;flex-direction:column;gap:6px}}
.recipe li>b{{font-size:.95rem}}

code{{font-family:var(--mono);font-size:.85em;background:var(--gapfill);padding:1px 5px;border-radius:4px}}
</style>
<div class="wrap">
<header style="display:flex;flex-direction:column;gap:16px">
 <div class="eyebrow">Análise de atendimento · WhatsApp comercial</div>
 <h1>Raio-X do WhatsApp da Nader Beauty</h1>
 <p class="lede">Um ano de conversas do número de atendimento da Dra. Carolina Nader, lidas e medidas para mostrar onde o atendimento converte e onde os leads se perdem.</p>
 <div class="meta"><span>Número 55 77 9154-9301</span><span>14/out/2025 → 14/out/2026</span><span>Extraído via Uazapi em 14/out/2026</span></div>
</header>

<section>
 <div class="kpis">
  <div class="kpi"><b>{fmt(M["total_msgs"])}</b><span>mensagens analisadas</span></div>
  <div class="kpi"><b>{F["leads"]}</b><span>leads novos identificados</span></div>
  <div class="kpi"><b>{lb["med"]:.0f} min</b><span>1ª resposta mediana em horário comercial</span></div>
  <div class="kpi"><b>{100*F["slot"]/F["leads"]:.0f}%</b><span>dos leads receberam proposta de horário</span></div>
 </div>
</section>

<section>
 <div class="eyebrow">Resumo</div>
 <h2>O que mais pesa</h2>
 <ul class="find">
  <li><span class="tag t-crit">Crítico</span><div><b>A conversa para antes do agendamento.</b> 76% dos leads respondem à secretária, mas só 21% recebem uma proposta concreta de dia e horário. E é justamente essa etapa que decide a venda: 40% de quem recebe horário paga o sinal, contra 5% de quem não recebe.</div></li>
  <li><span class="tag t-crit">Crítico</span><div><b>Lead pago sem resposta.</b> 8 de 33 conversas vindas de anúncio (24%) nunca receberam uma mensagem humana, e das que vieram de anúncio só 1 recebeu proposta de horário. Nenhuma chegou ao sinal pago.</div></li>
  <li><span class="tag t-warn">Atenção</span><div><b>40% dos leads chegam fora do horário</b> e esperam em média 12 horas pela primeira resposta. No total, {nr["none"]} de {nr["n"]} leads ({100*nr["none"]/nr["n"]:.0f}%) ficaram mais de 24h sem resposta humana.</div></li>
  <li><span class="tag t-warn">Atenção</span><div><b>O preço vai em áudio.</b> 103 leads perguntaram valor; {M["price_askers"]["got_audio"]} receberam a explicação em áudio e só {M["price_askers"]["got_text_price"]} receberam algum valor por escrito. Quem pergunta no trabalho ou no ônibus não ouve, e some.</div></li>
  <li><span class="tag t-warn">Atenção</span><div><b>71% das conversas de lead terminam com a clínica falando sozinha</b> e só 11% receberam alguma mensagem de retomada. Não há rotina de follow-up.</div></li>
  <li><span class="tag t-good">Funciona</span><div><b>Em horário comercial, a resposta é rápida:</b> mediana de {lb["med"]:.1f} min para o 1º contato e 92% respondidos em até 1 hora. O roteiro de qualificação (procedimento anterior → queixa → cidade → manhã ou tarde) é bom quando é seguido até o fim.</div></li>
 </ul>
</section>

<section>
 <div class="eyebrow">A base</div>
 <h2>O que foi extraído e onde está guardado</h2>
 <p>Foram baixadas da instância todas as {fmt(M["chats_total"])} conversas cadastradas e {fmt(M["total_msgs"])} mensagens (texto, áudio, imagem, documento, ligação). {M["chats_with_msgs"]} conversas têm mensagens no período: {M["chats_with_msgs"]-M["groups_with_msgs"]} individuais e {M["groups_with_msgs"]} grupos internos. Tudo foi organizado num banco consultável (SQLite) e em uma transcrição de texto por conversa.</p>
 <div class="fig">
  <h3>Mensagens por mês em conversas individuais</h3>
  {monthly()}
  <p class="cap">Agosto e setembro de 2026 não vieram no histórico: de 17/07 a 06/10 a instância só tem registros de ligação. É uma lacuna da sincronização do WhatsApp, não queda de movimento: mensagens de outubro citam mensagens anteriores que não vieram na extração. Janeiro baixo coincide com o afastamento da Dra. (retorno em fevereiro). Outubro/26 cobre só 8 dias (7 a 14/10).</p>
 </div>
 <p class="small">Uma conversa sozinha concentra {fmt(M["internal_doc_msgs"])} mensagens (27% de tudo): o canal entre a Dra. e a secretária. A operação da agenda passa quase inteira por ela, o que torna a Dra. um gargalo e mistura assuntos pessoais com o canal comercial.</p>
</section>

<section>
 <div class="eyebrow">Aquisição</div>
 <h2>De onde vêm os leads</h2>
 <div class="fig">
  <h3>Leads novos por mês</h3>
  {leadsmonth()}
  <p class="cap">O volume salta em junho/26, quando entram o link pré-preenchido do Instagram e os anúncios de clique para WhatsApp. Outubro/26 já tem 39 leads em 8 dias, o maior ritmo do ano.</p>
 </div>
 <div class="fig">
  <h3>Origem e avanço por canal</h3>
  <div class="scroll"><table><thead><tr><th>Origem</th><th class="n">Leads</th><th class="n">Responderam</th><th class="n">Horário proposto</th><th class="n">Sinal pago</th></tr></thead><tbody>{srcrows}</tbody></table></div>
  <p class="cap">"Contato direto" é quem escreveu sem mensagem padrão, geralmente por indicação. É o canal que mais converte (13 sinais em 75 leads). O anúncio traz volume, mas a conversa não avança.</p>
 </div>
 <blockquote>"Olá! Quero agendar com a Dra Carol! Poderia me passar mais informações?" — mensagem do anúncio<small>Resposta frequente: "Oie bom dia, tudo bem? Como posso te ajudar hoje?". A pessoa já disse que quer agendar; a resposta ideal oferece dois horários.</small></blockquote>
</section>

<section>
 <div class="eyebrow">Conversão</div>
 <h2>Onde o funil vaza</h2>
 <div class="fig">
  <h3>Funil dos {F["leads"]} leads novos</h3>
  <div style="display:flex;flex-direction:column;gap:10px">{funnel()}</div>
  <p class="cap">Etapas detectadas pelo texto das conversas. "Sinal pago" conta o envio de comprovante depois do pedido de PIX; pagamentos feitos na recepção ou combinados por ligação não aparecem, então a conversão real pode ser um pouco maior.</p>
 </div>
 <p>A queda de 76% para 21% acontece depois que a lead já está conversando. O padrão que se repete: a secretária pergunta "posso te mandar um áudio?", envia áudio e uma arte com o valor da consulta, a lead responde "ok, obrigada" ou "vou ver", e a conversa termina com "qualquer coisa estamos à disposição". </p>
 <blockquote>Entre as leads que receberam uma proposta de horário, <b>40% pagaram o sinal</b> (19 de 48). Entre as que conversaram mas não receberam proposta, <b>5%</b> (6 de 127).<small>Oferecer horário cedo é a ação de maior impacto deste relatório.</small></blockquote>

</section>

<section id="roteiro">
 <div class="eyebrow">Roteiro de atendimento</div>
 <h2>Existe um roteiro, mas ele raramente vai até o fim</h2>
 <p>Encontrei dois roteiros. O primeiro é o que a equipe pratica: uma sequência de mensagens que se repete nas conversas, muitas vezes com o mesmo texto. O segundo foi escrito pela Dra. no grupo interno "COMO RESPONDER", com respostas para dúvidas e objeções. A porcentagem ao lado de cada etapa mostra em quantas das {F["leads"]} conversas de lead ela aparece.</p>
 <div class="fig">
  <h3>O roteiro praticado, na ordem em que aparece</h3>
  <ol class="steps">
   <li class="step"><div class="num">1</div><div class="body"><div class="head"><b>Mensagem automática de entrada</b><span class="use">{st("auto")}% das leads</span></div>
    <div class="msg auto">Oieee, tudo bem? ✨
Aqui é Mai, faço parte da equipe da Nader Beauty!
Poderia me falar seu nome completo por gentileza?</div>
    <p class="small">Usada de out/25 a jul/26, junto com "Oieee, sua mensagem já chegou aqui!". Em out/26 foi trocada por "Olá!! É um prazer ter você aqui…" seguida de um menu com três botões: <i>Já sou cliente</i>, <i>Quero agendar</i> e <i>Tirar dúvidas</i>.</p></div></li>
   <li class="step"><div class="num">2</div><div class="body"><div class="head"><b>Saudação pelo nome</b><span class="use">{st("saud")}%</span></div>
    <div class="msg">Oie [nome], bom dia! Tudo bem? 🤍</div></div></li>
   <li class="step"><div class="num">3</div><div class="body"><div class="head"><b>Qualificação</b><span class="use low">{st("proc")}% · {st("cidade")}% · {st("queixa")}%</span></div>
    <div class="msg">Você já realizou algum procedimento estético?</div>
    <div class="msg">Você é de qual cidade, amor?</div>
    <div class="msg">Qual seria sua queixa? O que mais te incomoda?</div>
    <p class="small">As três perguntas são boas, mas aparecem em poucas conversas. Em {st("ajuda")}% das conversas a secretária pergunta "Como posso te ajudar?", mesmo quando a lead já escreveu "quero agendar".</p></div></li>
   <li class="step"><div class="num">4</div><div class="body"><div class="head"><b>Explicação da consulta, em áudio</b><span class="use">áudio em {st("audio")}% · imagem em {st("arte")}%</span></div>
    <div class="msg">Posso te mandar um áudio explicando melhor sobre nossa consulta?</div>
    <p class="small">Em seguida vão um áudio de 20 a 40 segundos e uma imagem com as informações da consulta. A versão por escrito ("A consulta é um momento mais importante de todo o planejamento…") só aparece em {st("consulta")}% das conversas, e algum valor por escrito em {st("preco")}%.</p></div></li>
   <li class="step"><div class="num">5</div><div class="body"><div class="head"><b>Fechamento: período e horário</b><span class="use low">{st("periodo")}% · {st("horario")}%</span></div>
    <div class="msg">Me conta, pra você ficaria mais confortável no período da manhã ou à tarde?</div>
    <div class="msg">Consigo um encaixe pra você segunda-feira dia 15 às 10:00 horas, daria certo?</div>
    <p class="small">É a etapa que mais converte e uma das que menos aparecem.</p></div></li>
   <li class="step"><div class="num">6</div><div class="body"><div class="head"><b>Sinal de R$ 250 e PIX</b><span class="use">{st("sinal")}%</span></div>
    <div class="msg">Para conseguirmos reservar seu horário de agendamento, nós estamos pedindo o pagamento antecipado dos R$ 250,00 reais, tudo bem?
A forma de pagamento pode ser pix ou link, qual seria a melhor opção para você?
Como reservamos um horário especialmente para você esse valor não poderá ser devolvido caso não consiga comparecer.
Poderemos remarcar mais uma única vez seu horário.</div>
    <p class="small">Logo depois vão o PIX/CNPJ da Nader Beauty e o pedido de comprovante. A consulta não é descontada do procedimento.</p></div></li>
   <li class="step"><div class="num">7</div><div class="body"><div class="head"><b>Endereço</b><span class="use">{st("endereco")}%</span></div>
    <div class="msg">Nós estamos localizados na rua Arthur Seixas, no edifício Candeias Prime Green… Se vier de uber, põe na localização: arte fina papelaria que é aqui ao lado. ✨</div></div></li>
   <li class="step"><div class="num">8</div><div class="body"><div class="head"><b>Retomada de quem parou de responder</b><span class="use low">{st("follow")}%</span></div>
    <div class="msg auto">Oi! [nome], passando só pra dizer que estamos por aqui, viu? Se quiser continuar nossa conversa ou tirar dúvidas, vai ser um prazer te ajudar 💬</div>
    <p class="small">Até julho não havia retomada. A partir de 07/10 entraram quatro mensagens automáticas desse tipo: {FA["sent"]} envios para {FA["chats"]} conversas, com {FA["answered48h"]} respostas em até 48 horas. Por serem genéricas, quase ninguém responde.</p></div></li>
  </ol>
  <p class="cap">{M["script_empty"]} conversas de lead ({100*M["script_empty"]//F["leads"]}%) não passaram por nenhuma etapa escrita além da automação, de áudios e de imagens.</p>
 </div>
 <div class="fig">
  <h3>As etapas de fechamento acompanham o pagamento do sinal</h3>
  <div class="scroll"><table class="compare"><thead><tr><th>Etapa</th><th class="n">Leads com a etapa</th><th class="n">Sinal pago, com a etapa</th><th class="n">Sinal pago, sem a etapa</th></tr></thead><tbody>{cmp_rows}</tbody></table></div>
  <p class="cap">Essas etapas costumam aparecer em conversas que já estavam avançando, então a diferença não é toda efeito do roteiro. Mas mostra o caminho: quem recebe período e horário paga o sinal muito mais.</p>
 </div>
 <div class="fig">
  <h3>O roteiro escrito pela Dra. (grupo "COMO RESPONDER")</h3>
  <p class="small">Respostas prontas para {len(M["written_scripts"])} situações, escritas entre fev e jul/26. Ao lado, quantas vezes cada uma aparece por escrito nas conversas com pacientes e leads.</p>
  <div style="display:flex;flex-direction:column;gap:8px">{ws_rows}</div>
  <p class="cap">Em maio a Dra. perguntou no grupo "Mai, vc está usando essas msgs?", e a resposta foi "As de cima sim". O uso em áudio não aparece aqui.</p>
 </div>
 <div class="fig">
  <h3>Roteiro recomendado</h3>
  <p class="small">Junta o que já funciona no roteiro praticado com as respostas da Dra. Cada passo tem um texto pronto para virar resposta rápida do WhatsApp Business.</p>
  <ol class="recipe">
   <li><b>1. Entrada (automática).</b><div class="msg auto">Oi! Aqui é a Mai, da equipe da Dra. Carol Nader 🤍 Pra eu te ajudar mais rápido, escolhe uma opção:
[Quero agendar] [Já sou paciente] [Tirar dúvidas]</div></li>
   <li><b>2. Qualificação em duas perguntas.</b><div class="msg">Que bom te ver aqui, [nome]! Você já fez algum procedimento estético? E é de Conquista ou de outra cidade?</div></li>
   <li><b>3. Consulta explicada por escrito, áudio como opção.</b><div class="msg">A consulta com a Dra. é o momento em que ela entende o que te incomoda e monta seu plano dentro do que você pode investir hoje. O valor é R$ 250 e ela atende presencial ou on-line. Quer que eu te explique melhor por áudio também?</div></li>
   <li><b>4. Se pedirem valor do procedimento:</b> usar a resposta da Dra. para "Qual a média de valor?" e passar a referência da tabela única, sempre com a mesma faixa para toda a equipe.</li>
   <li><b>5. Fechamento na mesma mensagem.</b><div class="msg">Tenho [dia] às [hora] ou [dia] às [hora]. Qual fica melhor pra você?</div></li>
   <li><b>6. Sinal, PIX e endereço.</b> Manter os textos atuais. Eles são claros e explicam a regra de remarcação.</li>
   <li><b>7. Objeções.</b> Usar as respostas da Dra. como atalhos ("Está caro", "Estou pesquisando outros profissionais", "Moro em outra cidade", "Tenho medo de ficar artificial"), sempre terminando com uma proposta de horário.</li>
   <li><b>8. Retomada que cita a conversa.</b><div class="msg">D+1: [nome], fiquei pensando no que você me contou sobre [queixa]. Consegui um horário na [dia] às [hora], quer que eu reserve?
D+3: Separei um resultado de [procedimento] parecido com o que você quer. Posso te mandar?
D+7: Vou liberar os horários desta semana. Se quiser, ainda consigo [dia] às [hora] pra você.</div></li>
  </ol>
 </div>
</section>

<section>
 <div class="eyebrow">Velocidade</div>
 <h2>Tempo de resposta</h2>
 <div class="kpis">
  <div class="kpi"><b>{lb["med"]:.1f} min</b><span>mediana da 1ª resposta a lead, horário comercial</span></div>
  <div class="kpi"><b>{lb["le5"]}%</b><span>respondidos em até 5 min (horário comercial)</span></div>
  <div class="kpi"><b>{lo["med"]/60:.0f} h</b><span>mediana da 1ª resposta fora do horário</span></div>
  <div class="kpi"><b>{M["calls_in_missed"]} de {M["calls_in"]}</b><span>ligações recebidas não atendidas</span></div>
 </div>
 <div class="fig">
  <h3>Quando as pessoas escrevem</h3>
  {heat()}
  <p class="cap">Conversas iniciadas por contatos, por dia e hora (cor mais forte = mais conversas). Contorno tracejado = fora do horário de atendimento (seg–sex 8h–18h, sáb 8h–12h). Os picos são 9h–11h e 14h–16h. Fins de tarde e noites somam um volume relevante de leads novos.</p>
 </div>
 <p class="small">O atendimento melhorou ao longo do ano: em out/25, 10% das mensagens esperavam mais de 2 horas em horário comercial; em out/26, esse corte caiu para 27 minutos.</p>
</section>

<section>
 <div class="eyebrow">Demanda</div>
 <h2>O que as leads querem e o que as trava</h2>
 <div class="two">
  <div class="fig"><h3>Procedimentos citados pelas leads</h3><div style="display:flex;flex-direction:column;gap:8px">{hbars(M["procs"])}</div></div>
  <div class="fig"><h3>Objeções e receios</h3><div style="display:flex;flex-direction:column;gap:8px">{hbars(M["objections"])}</div>
  <h3 style="margin-top:8px">Cidades citadas</h3><div style="display:flex;flex-direction:column;gap:8px">{hbars([c for c in M["cities"] if c[0]!="Não informado"][:6])}</div>
  <p class="cap">{dict(M["cities"])["Não informado"]} das {F["leads"]} leads não informaram a cidade.</p></div>
 </div>
 <ul class="plain">
  <li><b>Toxina botulínica e papada lideram.</b> Papada é o produto-assinatura (Método PZ). Leads chegam comparando com clínicas que vendem enzimas e laser; a secretária explica bem a diferença, e isso pode virar conteúdo.</li>
  <li><b>Distância e agenda pesam.</b> Leads de Porto Seguro, Jequié, Brumado e cidades vizinhas pedem encaixe no dia. Quando não há horário, não existe lista de espera e a conversa morre.</li>
  <li><b>Maringá já aparece</b>: a etiqueta tem 25 conversas e há leads de lá em out/26. Vale ter roteiro, endereço e agenda próprios para a cidade.</li>
 </ul>
</section>

<section>
 <div class="eyebrow">Qualidade</div>
 <h2>Achados do atendimento</h2>
 <h3>O que já funciona</h3>
 <ul class="plain">
  <li>Boas perguntas de qualificação: "Você já realizou algum procedimento estético?", "Você é de qual cidade?" e "manhã ou à tarde?". O problema é a frequência de uso, detalhada na seção de roteiro.</li>
  <li>Prova social com fotos de antes e depois e explicações didáticas (full face, olheiras, papada).</li>
  <li>Pós-procedimento ativo: mensagens de "como você está?" e orientação sobre inchaço.</li>
  <li>Ações de relacionamento: cashback de aniversário e pedido de avaliação no Google. As duas pararam (a última em dez/25 e abr/26).</li>
 </ul>
 <h3>O que trava</h3>
 <ul class="plain">
  <li><b>Até julho, duas mensagens automáticas disparavam juntas</b> ("sua mensagem já chegou" e "aqui é Mai… qual seu nome completo?"), em {M["auto_overlap_chats"]} conversas. A segunda chegava também para pacientes antigas. Em outubro entrou um menu com botões no lugar, o que resolve a duplicidade.</li>
  <li><b>Preço sem padrão.</b> Para a mesma pergunta, uma lead recebe "1 ml fica R$ 1.300 à vista ou R$ 1.400 em 4x", outra recebe "valores só na consulta" e outra "o ml fica em média R$ 1.500". A lead percebe a diferença.</li>
  <li><b>Os roteiros da Dra. não chegaram ao atendimento.</b> O grupo "COMO RESPONDER" tem respostas para objeções ("caro comparado a quê?", "vou pesquisar com outros profissionais", "medo de ficar artificial"). Por escrito, {sum(1 for _,n in M["written_scripts"] if n)} dos {len(M["written_scripts"])} roteiros aparecem nas conversas, {sum(n for _,n in M["written_scripts"])} vezes no total. A secretária disse no grupo que usa alguns, provavelmente em áudio.</li>
  <li><b>Muito áudio:</b> {fmt(M["audio_out"][0])} áudios enviados ({M["audio_out"][1]/3600:.1f} horas). O áudio cria proximidade, mas não pode ser lido, buscado ou padronizado, e esconde a informação que a lead pediu.</li>
  <li><b>Etiquetas pouco usadas:</b> 47 de {fmt(M["chats_total"])} conversas têm etiqueta, e "Aguardando pagamento" tem só 2. Não há como saber, pelo WhatsApp, quem está em que etapa.</li>
 </ul>
</section>

<section>
 <div class="eyebrow">Plano de ação</div>
 <h2>Prioridades</h2>
 <div class="plan">
  <div class="phase"><div>Esta semana</div><ol>
   <li>Responder hoje toda lead sem retorno humano (etapa "1. Sem resposta humana" na planilha de leads).</li>
   <li>Manter só o menu de outubro como automação de entrada, sem pedir nome completo para quem já é paciente.</li>
   <li>Regra de ouro: toda resposta a "quero agendar" ou "qual o valor" termina com dois horários concretos.</li>
  </ol></div>
  <div class="phase"><div>30 dias</div><ol>
   <li>Tabela de preços de referência por escrito, igual para toda a equipe (consulta R$ 250, que não é descontada do procedimento; ml; toxina; papada parcelada). O áudio vem depois, como complemento.</li>
   <li>Trocar a retomada automática genérica por uma cadência D+1, D+3 e D+7 que cite o que a lead pediu e ofereça horário.</li>
   <li>Levar as respostas do "COMO RESPONDER" para respostas rápidas do WhatsApp Business, com atalho, e revisar semanalmente o uso.</li>
   <li>Etiquetas obrigatórias por etapa: Lead novo → Qualificado → Horário proposto → Aguardando sinal → Agendado → Paciente.</li>
  </ol></div>
  <div class="phase"><div>90 dias</div><ol>
   <li>Cobertura fora do horário (até 21h e sábado à tarde), por plantão ou por um assistente de primeiro atendimento que qualifica e oferece horários.</li>
   <li>Lista de espera para encaixes e para os dias de Brumado e Maringá.</li>
   <li>Atender as ligações ou devolver em até 1h (54% não atendidas hoje).</li>
   <li>Retomar cashback e pedido de avaliação no Google como rotina mensal.</li>
   <li>Repetir este raio-x mensalmente com os mesmos indicadores.</li>
  </ol></div>
 </div>
</section>

<section>
 <div class="eyebrow">Método</div>
 <h2>Como os números foram calculados</h2>
 <ul class="plain small">
  <li><b>Lead novo:</b> contato cuja primeira mensagem é a do link do Instagram, do anúncio ou do site, ou contato novo no período que perguntou sobre valor, consulta, agendamento ou procedimento. Fornecedores e notificações foram excluídos.</li>
  <li><b>Tempo de resposta:</b> do primeiro texto da lead até a primeira mensagem escrita por uma pessoa da clínica. Mensagens automáticas não contam. Janelas que caem na lacuna de ago–set foram descartadas.</li>
  <li><b>Etapas do funil, objeções e procedimentos</b> foram detectados por palavras-chave no texto. O conteúdo dos áudios não foi transcrito, então parte das negociações não aparece.</li>
  <li>Nomes e telefones de pacientes foram omitidos deste relatório.</li>
 </ul>
</section>
</div>'''
open(OUT,"w").write(doc); print(len(doc))

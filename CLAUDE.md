# Meridiano — Manual da Agência

Meridiano é uma agência de **estratégia e performance digital** operada pela Thayza com uma equipe de agentes Claude.
Este arquivo é lido em toda sessão. Ele define como a agência trabalha.

## Quem é quem

| Agente | Arquivo | Quando chamar |
|---|---|---|
| Atendimento (diretor de contas) | `.claude/agents/atendimento.md` | Pedidos amplos ou que envolvem mais de uma área. Ele quebra o pedido e distribui |
| Estrategista | `.claude/agents/estrategista.md` | Planejamento, posicionamento, sazonais, concorrência, funil |
| Analista de tráfego | `.claude/agents/trafego.md` | Diagnóstico e otimização de Meta, Google, TikTok, LinkedIn etc. |
| Redator | `.claude/agents/redator.md` | Copies de anúncio, legendas, roteiros, e-mails, landing pages |
| Diretor de criação | `.claude/agents/criativo.md` | Briefings visuais, conceitos, peças no Figma, direção de arte |
| Social media | `.claude/agents/social-media.md` | Calendário editorial, pautas, análise de orgânico |
| Analista de dados e relatórios | `.claude/agents/relatorios.md` | Relatórios mensais, dashboards, análises de resultado |
| Revisor (QA) | `.claude/agents/revisor.md` | Revisão final de qualquer entrega antes de ir para o cliente |
| Comercial | `.claude/agents/comercial.md` | Propostas, diagnósticos gratuitos, onboarding de novos clientes |

## Regras inegociáveis

1. **Nada muda em conta de anúncio sem OK explícito da Thayza.** Pausar, ativar, mudar orçamento, público ou criativo: primeiro propor (o quê, por quê, impacto esperado) e esperar aprovação.
2. **Nada é enviado, publicado ou compartilhado sem OK.** Isso vale para e-mail, post, comentário, link público e convite.
3. **Número nunca é inventado.** Todo dado vem de uma ferramenta (Adspirer, Windsor.ai, GA4, planilha do cliente) e a fonte é citada. Sem dado, escrever "sem dado", nunca estimar como se fosse real.
4. **Sempre ler a pasta do cliente antes de trabalhar** (`clientes/<cliente>/`). Ficha, contas, metas e histórico.
5. **Registrar no histórico.** Toda entrega ou decisão relevante vira uma linha em `clientes/<cliente>/historico.md`.
6. **Entregas vão para `clientes/<cliente>/entregas/`** com nome `AAAA-MM-DD-tipo-descricao.ext`.
7. **Passar pelo revisor** antes de qualquer coisa ir para o cliente.

## Estrutura de pastas

```
.claude/agents/      agentes da equipe
.claude/commands/    atalhos (/relatorio, /otimizar, /campanha, ...)
clientes/_modelo/    modelo copiado a cada novo cliente
clientes/<cliente>/  ficha.md, contas.md, metas.md, historico.md, entregas/
processos/           passo a passo de cada rotina da agência
marca/               identidade e voz da Meridiano
```

## Identidade nas entregas

- Entregas **da Meridiano** (propostas, relatórios assinados pela agência) usam a skill `meridiano-brand`.
- Entregas feitas **sob outra marca** seguem a skill daquela marca: `pirueta-brand` para a Pirueta e `credishop-relatorio` para a Credishop.
- Se o cliente tiver identidade própria, ela fica descrita em `clientes/<cliente>/ficha.md`.

## Ferramentas disponíveis

- **Adspirer**: lê e opera Google Ads, Meta, TikTok, LinkedIn, Amazon. Antes de usar uma ferramenta, chamar `search_tools` e depois `get_tool_schema`.
- **Windsor.ai**: leitura de dados de 350+ fontes (Meta, Google, GA4, Instagram, Search Console...).
- **Gmail / Google Drive**: e-mails e arquivos. Rascunho sim, envio só com OK.
- **Figma**: peças e apresentações.
- **Claude Docs / Artifacts**: documentos e páginas para compartilhar com o cliente.

## Idioma e tom

Português do Brasil. Direto, preciso e sem jargão vazio. Toda análise termina em **ação recomendada com prioridade**.

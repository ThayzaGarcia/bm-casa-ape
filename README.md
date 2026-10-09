# Meridiano · Estratégia e Performance Digital

Agência operada pela Thayza com uma equipe de agentes Claude.

## Como usar

Abra uma sessão do Claude Code neste repositório e peça em linguagem natural ("como está a BM Casa Apê?") ou use um atalho:

| Atalho | O que faz |
|---|---|
| `/status <cliente \| todos>` | Visão geral e saúde das contas |
| `/otimizar <cliente \| todos>` | Diagnóstico e lista de otimizações (nada é alterado sem seu OK) |
| `/relatorio <cliente> [período]` | Relatório de performance revisado |
| `/campanha <cliente> <objetivo>` | Campanha completa: estratégia, copy, criativo e montagem pausada |
| `/conteudo <cliente> <mês>` | Calendário de conteúdo orgânico |
| `/copy <cliente> <pedido>` | Textos e roteiros, já revisados |
| `/proposta <prospect>` | Diagnóstico gratuito e proposta comercial |
| `/novo-cliente <nome>` | Cadastra um cliente a partir do modelo |

## A equipe

Atendimento, Estrategista, Tráfego, Redator, Criação, Social media, Relatórios, Revisor e Comercial. Os detalhes estão em [`CLAUDE.md`](CLAUDE.md) e em `.claude/agents/`.

## Clientes

- [`clientes/bm-casa-ape`](clientes/bm-casa-ape): imobiliária de alto padrão, Imperatriz-MA
- [`clientes/credishop`](clientes/credishop): varejo e crédito (via Pirueta)
- Para adicionar um cliente: `/novo-cliente`

## Ajustando a equipe

Cada agente é um arquivo `.md` em `.claude/agents/`. Para mudar o comportamento de um agente, basta editar o texto, ou pedir: "ajusta o redator para…".

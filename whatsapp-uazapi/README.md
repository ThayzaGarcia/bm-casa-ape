# Análise do WhatsApp via Uazapi

Scripts para extrair as conversas de uma instância [Uazapi](https://docs.uazapi.com/) e medir o atendimento comercial (funil de leads, tempo de resposta, objeções, procedimentos).

**Nenhum dado de conversa fica neste repositório.** O repositório é público e as conversas têm dados de pacientes. Os dados vão para a pasta `whatsapp/`, que o git ignora.

## Como usar

```bash
# 1. Baixar tudo da instância (cerca de 3 minutos para 40 mil mensagens)
UAZAPI_TOKEN=<token da instância> python3 whatsapp-uazapi/extrair.py

# 2. Calcular os indicadores (gera whatsapp/metrics.json)
NUMEROS_INTERNOS=<número pessoal da Dra., só dígitos> python3 whatsapp-uazapi/analisar.py

# 3. Gerar o relatório HTML (whatsapp/relatorio.html)
python3 whatsapp-uazapi/gerar_relatorio.py
```

`UAZAPI_SERVER` muda o servidor (padrão: `https://free.uazapi.com`).

## O que é gerado

| Arquivo | Conteúdo |
|---|---|
| `whatsapp/whatsapp.db` | SQLite com as tabelas `chats`, `messages` e `idmap` (une o ID por telefone e o ID `@lid` do mesmo contato) |
| `whatsapp/transcripts/*.txt` | Uma transcrição legível por conversa |
| `whatsapp/raw/*.json` | Respostas brutas da API |
| `whatsapp/metrics.json` | Indicadores usados no relatório |

Exemplos de consulta:

```sql
-- mensagens de um contato, em ordem
select dt, from_me, type, text from messages m join idmap i on i.chatid = m.chatid
where i.contact = '5577XXXXXXXXX@s.whatsapp.net' order by ts;

-- leads que chegaram pelo link do Instagram no mês
select chatid, dt from messages where from_me = 0 and text like 'Olá, vim do instagram%' and dt like '2026-10%';
```

## Observações sobre os dados

- A paginação global de `/message/find` para em 2.000 mensagens. Por isso, o `extrair.py` busca também conversa por conversa.
- Na extração de 14/10/2026, o histórico de 17/07 a 06/10/2026 veio só com registros de ligação (lacuna da sincronização do WhatsApp). O `analisar.py` ignora essa janela ao medir o tempo de resposta. Ajuste a constante `GAP` numa nova extração.
- As etapas do funil e as objeções são detectadas por palavras-chave no texto. Os áudios não são transcritos.
- O texto do relatório em `gerar_relatorio.py` foi escrito para a extração de out/2026. Os números são atualizados a partir do `metrics.json`, mas a parte narrativa precisa de revisão a cada nova extração.

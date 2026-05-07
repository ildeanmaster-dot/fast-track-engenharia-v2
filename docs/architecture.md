# Arquitetura

## Visão geral

```
        +-----------+        +-----------+        +-----------+
  API   |  Bronze   |        |  Silver   |        |   Gold    |
  ----> |  JSONL    |  --->  |  Schema   |  --->  | Star+Mart |
        |  + Delta  |        |  + Dedup  |        |           |
        +-----------+        +-----------+        +-----------+
```

Padrão medalhão clássico, três camadas. Cada camada tem propósito bem
definido — Bronze não transforma dados; Silver normaliza; Gold materializa
modelos analíticos.

## Bronze

- **Formato local**: JSONL em `data/samples/`. Mantido pequeno (15 páginas
  total) para iteração rápida.
- **Formato Databricks**: Delta Lake em
  `/Volumes/workspace/ftkeng_v2/lakehouse/bronze/<endpoint>`.
- **Auditoria**: cada registro recebe um campo `_audit` com `ingest_ts`,
  `endpoint` e `source_url`. Rastreabilidade desde a fonte.
- **Chave primária**: definida no catálogo YAML, não no código.

## Silver

- Rename para `snake_case`.
- Tipagem explícita de colunas temporais (`pd.to_datetime` com `utc=True`
  em timestamps).
- Deduplicação pela chave primária (`drop_duplicates(subset=pk, keep="last")`).
- Tratamento especial: `votacao_votos` tem objeto `deputado_` aninhado que
  é achatado em colunas `id_deputado`, `nome_deputado`, etc.

## Gold

Star schema:

- **Dimensões**: `dim_deputado`, `dim_partido`, `dim_frente`, `dim_orgao`,
  `dim_evento`, `dim_data`.
- **Fatos**: `fato_voto`, `fato_presenca`, `fato_despesa`.

Tabelas analíticas (`gold_*`) materializam um entregável cada. Não há JOIN
em runtime — a consulta lê parquet direto.

## Estratégias incrementais

Cada endpoint declara sua estratégia em `conf/endpoints.yaml`:

| Estratégia    | Uso                                              |
|---------------|--------------------------------------------------|
| `snapshot`    | Lista pequena/estável (partidos, deputados)      |
| `append`      | Eventos novos (votações, votos, presenças)       |
| `watermark`   | Por data de documento (despesas)                 |
| `scd2`        | Histórico relevante (tramitações de PL)          |

Na V2 isso fica registrado mas a execução real só varia entre `snapshot` e
`append` — implementação mais elaborada de SCD2 fica em iteração futura.

## Fluxo de dependência

A coleta respeita ordem topológica:

1. Listas base sem fanout: `partidos`, `deputados`, `frentes`, `orgaos`,
   `eventos`, `votacoes`, `proposicoes`, `legislaturas`.
2. Fanouts dependem de IDs do pai: `frente_membros` (de frentes),
   `votacao_votos` (de votações), `deputado_despesas` (de deputados),
   etc.

## Auditoria e replay

- Bronze é idempotente: rodar 2x sobrescreve com mesmo conteúdo (a menos
  que a API tenha mudado).
- Silver e Gold são determinísticos a partir do Bronze.
- Reprocessar uma data específica = re-rodar Bronze do(s) endpoint(s) e
  re-rodar Silver/Gold.

## Diagrama relacional simplificado

```
dim_deputado ──┬── fato_voto ──── dim_data (via id_votacao)
               ├── fato_presenca ── dim_evento
               └── fato_despesa
                                    
gold_atlas_frentes ──── dim_frente
                  └──── dim_deputado
```

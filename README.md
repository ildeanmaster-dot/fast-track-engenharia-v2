# Câmara Pipeline — Upskill Tiller T2

Pipeline de dados ponta-a-ponta sobre a [API da Câmara dos Deputados](https://dadosabertos.camara.leg.br/).
Projeto final do programa Upskill Tiller — Engenharia de Dados, Turma 2.

## Visão geral

Arquitetura medalhão clássica (Bronze → Silver → Gold) rodando no Databricks
com Unity Catalog Volumes. Para iteração rápida, o pipeline também roda
localmente em pandas — útil para validar transformações sem subir cluster.

A camada Gold materializa os 6 entregáveis obrigatórios + CDC de tramitação
(opcional).

## Arquitetura

```
        +-----------+        +-----------+        +-----------+
  API   |  Bronze   |        |  Silver   |        |   Gold    |
  ----> |  JSONL +  |  --->  | Schema +  |  --->  |  Star +   |
        |   Delta   |        |  SCD-like |        |  Analytics|
        +-----------+        +-----------+        +-----------+
```

- **Bronze**: payload JSON exatamente como veio da API + colunas de auditoria
  (`ingest_ts`, `run_id`, `endpoint`).
- **Silver**: rename para `snake_case`, tipagem, deduplicação por chave
  primária, parse de timestamps em UTC.
- **Gold**: dimensões + fatos + 1 tabela analítica por entregável.

Detalhes em [docs/architecture.md](docs/architecture.md). Decisões
arquiteturais em [docs/decisions/](docs/decisions/).

## Entregáveis

Os 6 obrigatórios:

1. **Atlas das frentes** — HHI por frente, sobreposição, perfil
2. **Calendário de eventos** — taxa de presença, densidade semanal
3. **Correlação frente × votação** — comparativo de alinhamento
4. **Raio-X CEAP** — z-score por categoria, ranking de fornecedores
5. **Auditoria de CPIs** — catálogo + duração vs. prazo regimental
6. **Engajamento parlamentar** — score composto + percentil

Opcional implementado:

- **CDC de tramitação de PLs** — SCD2 com `valid_from`/`valid_to`/`is_current`

## Quickstart local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.pipelines.run_local
```

Tests:

```bash
pytest tests/ -v
```

## Quickstart Databricks

1. Importar este repo como Git folder.
2. Rodar os notebooks na ordem:
   - `00_setup.py`     — cria schema/volume
   - `01_bronze.py`    — JSONL → Delta
   - `02_silver.py`    — transforms
   - `03_gold.py`      — dimensões + fatos + entregáveis
   - `04_analytics.py` — queries SQL representativas

Schema: `workspace.ftkeng_v2`. Volume: `workspace.ftkeng_v2.lakehouse`.

## Estrutura

```
.
├── conf/endpoints.yaml         # catálogo de endpoints
├── src/
│   ├── ingestion/              # cliente HTTP + bronze
│   ├── transforms/             # silver + gold
│   ├── analytics/              # 6 entregáveis
│   ├── pipelines/              # orquestradores locais
│   └── utils/                  # carregamento de config
├── notebooks/                  # versão Databricks
├── tests/unit/                 # pytest
└── docs/
    ├── architecture.md
    └── decisions/              # ADRs
```

## Por que a ingestão fica fora do cluster

Em arquiteturas reais, a coleta da API não roda dentro do cluster Databricks.
Razões:

- **Custo**: cluster ligado custa $$/h. Bater em API leva segundos.
- **Segurança**: clusters serverless têm egress de internet restrito por
  default — princípio de least-privilege em multi-tenant.
- **Acoplamento**: se a API cair, cluster fica retentando e pagando compute
  parado.
- **Observabilidade**: ingestão num orquestrador (Airflow, Lambda, Cron)
  tem dashboards e alertas próprios.

A separação que uso aqui reflete essa prática:

```
[ Worker leve ]      [ Object Storage ]      [ Cluster pesado ]
src/ingestion/  ──►  Volume UC samples  ──►  Notebooks 02-04
(bate na API)        (entrega zone)           (Bronze->Gold)
```

Pra reproduzir essa demonstração ao vivo, use `scripts/live_demo.py`:
limpa samples, bate na API ao vivo (você vê o terminal), sobe pro Volume
e dispara o pipeline no Databricks.

## Sobre

Desenvolvido com auxílio de IA (Claude). Decisões e revisões são minhas.

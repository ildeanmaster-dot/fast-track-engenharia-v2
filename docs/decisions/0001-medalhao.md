# 0001 - Arquitetura medalhão (Bronze/Silver/Gold)

## Contexto

O desafio pede explicitamente arquitetura medalhão e cita Delta Lake +
Time Travel. Avaliei outras opções antes de fechar.

## Opções consideradas

1. **Medalhão (Bronze/Silver/Gold)** — padrão Databricks, separação clara.
2. **ELT direto** — ingere e transforma na mesma camada.
3. **Data Vault 2.0** — hub+link+sat, mais complexo.

## Decisão

Medalhão.

## Justificativa

- **Idempotência**: Bronze preserva o payload bruto. Reprocessar Silver/Gold
  é seguro a qualquer momento sem voltar à API.
- **Auditoria natural**: cada camada tem suas próprias colunas de auditoria.
  Rastrear linhagem de uma linha é trivial.
- **Compatível com Delta**: SCD2 e Time Travel são operações nativas.
- **Recomendado pelo desafio**: alinhamento direto.

Data Vault foi descartado por ser pesado para o volume e cadência deste
desafio. ELT direto perde a separação que dá idempotência.

## Consequências

- 3 áreas de storage (bronze/silver/gold) por ambiente (local + Databricks).
- Caminhos abstraídos via configuração (Volume UC no Databricks, `data/`
  local).
- Reprocesso "replay" é feito re-rodando do Bronze pra frente.

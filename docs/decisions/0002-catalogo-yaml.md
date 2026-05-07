# 0002 - Catálogo de endpoints declarativo em YAML

## Contexto

A API da Câmara tem dezenas de endpoints. Adicionar/remover endpoints sem
mexer em código Python deixa a manutenção mais previsível e a configuração
auditável.

## Opções consideradas

1. **YAML declarativo em `conf/endpoints.yaml`**
2. **Dict Python em `conf/config.py`** — mais simples mas menos amigável
   pra editar / revisar.
3. **JSON** — sem comentários, formato pior pra config humana.
4. **Variáveis de ambiente** — não escala.

## Decisão

YAML.

## Justificativa

- Endpoints são metadata, não comportamento. Devem ficar separados do código.
- Permite comentários explicando estratégia de cada endpoint.
- Loader Python (`src/utils/config_loader.py`) converte para dataclasses
  tipadas, mantendo type checking nas chamadas downstream.
- Adicionar um novo endpoint = adicionar bloco no YAML, sem alterar
  cliente HTTP nem ingestão.

## Consequências

- Dependência do `pyyaml` (já é dependência comum em projetos Python).
- Validação de schema do YAML é leve — confia no `dataclass` quando faltam
  campos obrigatórios.
- Tests do `config_loader` garantem que toda entrada tem PK e estratégia
  válida.

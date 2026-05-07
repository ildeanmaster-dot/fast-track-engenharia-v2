# Databricks notebook source
# MAGIC %md # 02 — Silver (rename + dedup)

# COMMAND ----------

LAKEHOUSE = "/Volumes/workspace/ftkeng_v2/lakehouse"

def read_bronze(name):
    return spark.read.format("delta").load(f"{LAKEHOUSE}/bronze/{name}")

def write_silver(name, df):
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
          .save(f"{LAKEHOUSE}/silver/{name}")
    n = df.count()
    print(f"  silver.{name:<25s} {n:>5d} rows")
    return n

# COMMAND ----------

# MAGIC %md ## Listas base

# COMMAND ----------

write_silver("deputados", read_bronze("deputados").selectExpr(
    "id as id_deputado", "nome", "siglaPartido as sigla_partido",
    "siglaUf as sigla_uf", "idLegislatura as id_legislatura", "uri",
).dropDuplicates(["id_deputado"]))

write_silver("partidos", read_bronze("partidos").selectExpr(
    "id as id_partido", "sigla as sigla_partido", "nome as nome_partido",
).dropDuplicates(["id_partido"]))

write_silver("legislaturas", read_bronze("legislaturas").selectExpr(
    "id as id_legislatura", "to_date(dataInicio) as data_inicio",
    "to_date(dataFim) as data_fim",
).dropDuplicates(["id_legislatura"]))

write_silver("frentes", read_bronze("frentes").selectExpr(
    "id as id_frente", "titulo as nome_frente", "idLegislatura as id_legislatura",
).dropDuplicates(["id_frente"]))

# orgaos pode ter dataInicio/Fim opcionais
orgs_bronze = read_bronze("orgaos")
selects = ["id as id_orgao", "sigla as sigla_orgao", "nome as nome_orgao",
           "tipoOrgao as tipo_orgao", "codTipoOrgao as cod_tipo_orgao"]
if "dataInicio" in orgs_bronze.columns:
    selects.append("to_date(dataInicio) as data_inicio")
if "dataFim" in orgs_bronze.columns:
    selects.append("to_date(dataFim) as data_fim")
write_silver("orgaos", orgs_bronze.selectExpr(*selects).dropDuplicates(["id_orgao"]))

write_silver("eventos", read_bronze("eventos").selectExpr(
    "id as id_evento", "to_timestamp(dataHoraInicio) as data_hora_inicio",
    "to_timestamp(dataHoraFim) as data_hora_fim",
    "descricaoTipo as descricao_tipo", "situacao",
).dropDuplicates(["id_evento"]))

write_silver("votacoes", read_bronze("votacoes").selectExpr(
    "id as id_votacao", "to_timestamp(dataHoraRegistro) as data_hora_registro",
    "descricao",
).dropDuplicates(["id_votacao"]))

write_silver("proposicoes", read_bronze("proposicoes").selectExpr(
    "id as id_proposicao", "siglaTipo as sigla_tipo", "ementa",
    "to_date(dataApresentacao) as data_apresentacao",
).dropDuplicates(["id_proposicao"]))

# COMMAND ----------

# MAGIC %md ## Fanouts

# COMMAND ----------

write_silver("frente_membros", read_bronze("frente_membros").selectExpr(
    "_parent_id as id_frente", "id as id_deputado",
    "siglaPartido as sigla_partido", "siglaUf as sigla_uf",
).dropDuplicates(["id_frente", "id_deputado"]))

write_silver("evento_deputados", read_bronze("evento_deputados").selectExpr(
    "_parent_id as id_evento", "id as id_deputado",
    "siglaPartido as sigla_partido", "siglaUf as sigla_uf",
).dropDuplicates(["id_evento", "id_deputado"]))

write_silver("votacao_votos", read_bronze("votacao_votos").selectExpr(
    "_parent_id as id_votacao", "deputado_.id as id_deputado",
    "deputado_.siglaPartido as sigla_partido",
    "deputado_.siglaUf as sigla_uf", "tipoVoto as tipo_voto",
).dropDuplicates(["id_votacao", "id_deputado"]))

write_silver("deputado_despesas", read_bronze("deputado_despesas").selectExpr(
    "_parent_id as id_deputado", "ano", "mes",
    "tipoDespesa as tipo_despesa", "codDocumento as cod_documento",
    "valorLiquido as valor_liquido",
    "nomeFornecedor as nome_fornecedor",
    "cnpjCpfFornecedor as cnpj_fornecedor",
    "to_timestamp(dataDocumento) as data_documento",
).dropDuplicates(["id_deputado", "cod_documento"]))

write_silver("proposicao_tramitacoes", read_bronze("proposicao_tramitacoes").selectExpr(
    "_parent_id as id_proposicao", "sequencia",
    "to_timestamp(dataHora) as data_hora",
    "siglaOrgao as sigla_orgao",
    "descricaoSituacao as descricao_situacao",
    "descricaoTramitacao as descricao_tramitacao",
).dropDuplicates(["id_proposicao", "sequencia"]))

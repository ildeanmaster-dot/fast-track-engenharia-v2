# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Analytics: queries SQL dos entregáveis

# COMMAND ----------

# MAGIC %md ## 1. Atlas: top 10 frentes mais diversas (HHI mais baixo)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_frente, nome_frente, n_membros, n_partidos, hhi
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_frente_diversidade`
# MAGIC ORDER BY hhi ASC LIMIT 10

# COMMAND ----------

# MAGIC %md ## 2. Calendário: top 10 deputados por presença

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_deputado, nome, sigla_partido, sigla_uf, taxa_presenca
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_taxa_presenca_deputado`
# MAGIC ORDER BY taxa_presenca DESC LIMIT 10

# COMMAND ----------

# MAGIC %md ## 3. Frentes mais alinhadas

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_frente, nome_frente, alinhamento_medio, qtd_votacoes
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_resumo_alinhamento_frente`
# MAGIC ORDER BY alinhamento_medio DESC LIMIT 10

# COMMAND ----------

# MAGIC %md ## 4. CEAP: outliers (z-score > 3)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_deputado, nome, sigla_uf, tipo_despesa, valor_liquido,
# MAGIC        media_grupo, std_grupo, z_score
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_ceap_anomalias`
# MAGIC WHERE outlier = true
# MAGIC ORDER BY z_score DESC LIMIT 20

# COMMAND ----------

# MAGIC %md ## 5. CPIs

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_orgao, sigla_orgao, nome_orgao, data_inicio, data_fim,
# MAGIC        duracao_dias, excedeu_prazo
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_cpi_catalogo`
# MAGIC ORDER BY data_inicio DESC

# COMMAND ----------

# MAGIC %md ## 6. Top 10 mais engajados

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_deputado, nome, sigla_partido, n_presencas, n_votos,
# MAGIC        engajamento, percentil
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_engajamento_deputado`
# MAGIC ORDER BY engajamento DESC LIMIT 10

# COMMAND ----------

# MAGIC %md ## Opcional: estado atual de cada PL (SCD2)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT id_proposicao, sequencia, sigla_orgao,
# MAGIC        descricao_situacao, valid_from
# MAGIC FROM delta.`/Volumes/workspace/ftkeng_v2/lakehouse/gold/gold_pl_estado_atual`
# MAGIC ORDER BY valid_from DESC LIMIT 20

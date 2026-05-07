# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Setup
# MAGIC
# MAGIC Cria schema, volume e copia samples do repo para o Volume UC.

# COMMAND ----------

import os
import shutil

REPO_PATH = "/Workspace/Users/developer@yottaflow.com.br/FAST-TRACK-ENGENHARIA-V2"

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.ftkeng_v2")
spark.sql("CREATE VOLUME IF NOT EXISTS workspace.ftkeng_v2.lakehouse")

LAKEHOUSE = "/Volumes/workspace/ftkeng_v2/lakehouse"
SAMPLES = f"{LAKEHOUSE}/samples"
for sub in ("samples", "bronze", "silver", "gold"):
    dbutils.fs.mkdirs(f"{LAKEHOUSE}/{sub}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Copia JSONL do repo para o Volume

# COMMAND ----------

src_dir = f"{REPO_PATH}/data/samples"
copied = 0
if os.path.exists(src_dir):
    for fname in os.listdir(src_dir):
        if fname.endswith(".jsonl"):
            src = f"{src_dir}/{fname}"
            if os.path.getsize(src) > 0:
                shutil.copy(src, f"{SAMPLES}/{fname}")
                copied += 1

print(f"copiados {copied} JSONL para {SAMPLES}")

# COMMAND ----------

print("Arquivos no Volume:")
for f in dbutils.fs.ls(SAMPLES):
    print(f"  {f.name}  ({f.size} bytes)")

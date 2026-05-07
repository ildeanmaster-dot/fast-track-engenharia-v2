"""Pipeline local: bronze -> silver -> gold em pandas, sem Spark."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.analytics import (
    atlas_frentes,
    calendario,
    cdc_tramitacao,
    ceap,
    correlacao,
    cpis,
    engajamento,
)
from src.ingestion.bronze import collect_all
from src.transforms import gold as gold_mod
from src.transforms.silver import to_silver_all
from src.utils.config_loader import load as load_config

GOLD_DIR = Path("data/gold")


def _save(df: pd.DataFrame | None, name: str) -> None:
    if df is None or df.empty:
        print(f"  [skip] {name} (vazio)")
        return
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    out = GOLD_DIR / f"{name}.parquet"
    df.to_parquet(out, index=False)
    print(f"  [ok]   {name:<40s} {len(df):>5d}")


def main(skip_bronze: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()

    if not skip_bronze:
        print("\n=== Bronze (API -> JSONL) ===")
        results = collect_all(cfg, max_pages_simple=2)
        print(f"\nTotal bronze: {sum(results.values())} registros")

    print("\n=== Silver ===")
    silver = to_silver_all()
    for name, df in silver.items():
        print(f"  {name:<25s} {len(df):>5d}")

    print("\n=== Gold - dimensoes e fatos ===")
    _save(gold_mod.dim_deputado(silver), "dim_deputado")
    _save(gold_mod.dim_partido(silver), "dim_partido")
    _save(gold_mod.dim_frente(silver), "dim_frente")
    _save(gold_mod.dim_orgao(silver), "dim_orgao")
    _save(gold_mod.dim_evento(silver), "dim_evento")
    _save(gold_mod.dim_data(silver), "dim_data")
    _save(gold_mod.fato_voto(silver), "fato_voto")
    _save(gold_mod.fato_presenca(silver), "fato_presenca")
    _save(gold_mod.fato_despesa(silver), "fato_despesa")

    modules = [
        ("atlas frentes", atlas_frentes.build),
        ("calendario", calendario.build),
        ("correlacao", correlacao.build),
        ("ceap", ceap.build),
        ("cpis", cpis.build),
        ("engajamento", engajamento.build),
        ("CDC tramitacao", cdc_tramitacao.build),
    ]

    for label, builder in modules:
        print(f"\n=== Gold - {label} ===")
        try:
            tables = builder(silver)
            for name, df in tables.items():
                _save(df, name)
        except Exception as e:
            print(f"  [erro] {label}: {e}")

    print(f"\nFinalizado. Resultados em {GOLD_DIR.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-bronze", action="store_true",
                        help="reutiliza JSONLs existentes em data/samples/")
    args = parser.parse_args()
    main(skip_bronze=args.skip_bronze)

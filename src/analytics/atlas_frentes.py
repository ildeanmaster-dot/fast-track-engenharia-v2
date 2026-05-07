"""Entregavel 1 — Atlas das frentes parlamentares."""
from __future__ import annotations

import pandas as pd


def atlas_frentes(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Membros das frentes enriquecidos com partido/UF do deputado."""
    fr = silver["frentes"][["id_frente", "nome_frente", "id_legislatura"]]
    fm = silver["frente_membros"][["id_frente", "id_deputado"]]
    dep = silver["deputados"][["id_deputado", "nome", "sigla_partido", "sigla_uf"]]
    return (fm.merge(dep, on="id_deputado", how="left")
              .merge(fr, on="id_frente", how="left"))


def hhi_por_frente(atlas: pd.DataFrame) -> pd.DataFrame:
    """Indice de Herfindahl por frente. Baixo = mais diverso."""
    rows: list[dict] = []
    for fid, grp in atlas.groupby("id_frente"):
        total = len(grp)
        if total == 0:
            continue
        partidos = grp["sigla_partido"].fillna("?").value_counts()
        share = partidos / total
        rows.append({
            "id_frente": fid,
            "nome_frente": grp["nome_frente"].iloc[0],
            "n_membros": int(total),
            "n_partidos": int((partidos > 0).sum()),
            "n_ufs": grp["sigla_uf"].fillna("?").nunique(),
            "hhi": float((share ** 2).sum()),
        })
    return pd.DataFrame(rows).sort_values("hhi").reset_index(drop=True)


def deputados_em_n_frentes(atlas: pd.DataFrame, top: int = 30) -> pd.DataFrame:
    return (atlas.groupby(["id_deputado", "nome", "sigla_partido", "sigla_uf"])
                 .size()
                 .reset_index(name="n_frentes")
                 .sort_values("n_frentes", ascending=False)
                 .head(top)
                 .reset_index(drop=True))


def sobreposicao_frentes(atlas: pd.DataFrame, min_overlap: int = 5) -> pd.DataFrame:
    """Pares de frentes com membros em comum acima de min_overlap."""
    membros_por_frente = atlas.groupby("id_frente")["id_deputado"].apply(set).to_dict()
    nomes = atlas.set_index("id_frente")["nome_frente"].to_dict()

    pares: list[dict] = []
    fids = sorted(membros_por_frente.keys())
    for i, a in enumerate(fids):
        for b in fids[i + 1:]:
            inter = len(membros_por_frente[a] & membros_por_frente[b])
            if inter >= min_overlap:
                pares.append({
                    "frente_a": a, "nome_a": nomes.get(a),
                    "frente_b": b, "nome_b": nomes.get(b),
                    "membros_comum": inter,
                })
    return pd.DataFrame(pares).sort_values("membros_comum", ascending=False).reset_index(drop=True)


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    atlas = atlas_frentes(silver)
    return {
        "gold_atlas_frentes": atlas,
        "gold_frente_diversidade": hhi_por_frente(atlas),
        "gold_deputados_em_n_frentes": deputados_em_n_frentes(atlas),
        "gold_sobreposicao_frentes": sobreposicao_frentes(atlas),
    }

"""CRISP-DM 2.1 — Coleta dos dados iniciais.

Não há download de uma base pública: a
camada bruta já é o resultado do scraping da OLX (`Software/coleta/`),
materializada uma única vez em ``data/raw/``. Esta ingestão faz duas coisas:

1. lê `anuncios_detalhados.csv`, tratado como imutável;
2. mescla o valor de FIPE — a OLX só traz FIPE em 90,7% dos anúncios
   (`valor_fipe_olx`); o resto foi resolvido à parte via API pública da
   Tabela FIPE, gravado em `fipe_fallback.csv`
   (`Software/coleta/preenche_fipe_faltantes.py`).

A mesma lógica é usada no notebook `01-analise-exploratoria` (escrita ali
célula a célula, para narrar a decisão) e aqui (como função, para que
`preparacao.construir_base_curada` não precise duplicá-la).
"""

from __future__ import annotations

import pandas as pd

from src import config


def carregar_bruto() -> pd.DataFrame:
    """Lê a base bruta e mescla o valor de FIPE (OLX + API pública).

    Returns:
        As 23 colunas originais mais `valor_fipe_final` (FIPE mesclada) e
        `fonte_fipe` (`"OLX"`, `"API pública (fallback)"` ou
        `"não encontrada"`).
    """
    bruto = pd.read_csv(config.ARQUIVO_BRUTO)

    fallback = pd.read_csv(config.ARQUIVO_FIPE_FALLBACK)
    # Um link aparece duas vezes no fallback (reprocessamento pontual); fica
    # a última tentativa — mesmo tratamento do notebook 01.
    fallback_valor = fallback.drop_duplicates("link", keep="last").set_index("link")[
        "valor_fipe_api"
    ]

    bruto["valor_fipe_final"] = bruto["valor_fipe_olx"].fillna(bruto["link"].map(fallback_valor))
    bruto["fonte_fipe"] = pd.Series("não encontrada", index=bruto.index, dtype="object")
    bruto.loc[bruto["valor_fipe_final"].notna(), "fonte_fipe"] = "API pública (fallback)"
    bruto.loc[bruto["valor_fipe_olx"].notna(), "fonte_fipe"] = "OLX"

    return bruto

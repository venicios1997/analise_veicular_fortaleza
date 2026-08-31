"""Preenche o valor de FIPE (via API pública) apenas para os anúncios do
dataset que ficaram sem `valor_fipe_olx` (a OLX não trouxe a FIPE na página).

Resumível: grava incrementalmente em dados/fipe_fallback.csv (por link) e
pula quem já foi resolvido em execuções anteriores. Só chama a API para as
linhas que ainda faltam, respeitando um delay entre chamadas por causa do
limite de requisições da API pública da FIPE (parallelum.com.br).
"""

from __future__ import annotations

import csv
import random
import time
from pathlib import Path

import matcher
import pandas as pd
from scraper import Anuncio

DIR_DADOS = Path(__file__).parent / "dados"
CSV_DETALHADOS = DIR_DADOS / "anuncios_detalhados.csv"
CSV_FALLBACK = DIR_DADOS / "fipe_fallback.csv"

DELAY_MIN = 1.0
DELAY_MAX = 2.5

CAMPOS_FALLBACK = [
    "link",
    "titulo",
    "marca_fipe",
    "modelo_fipe",
    "ano_fipe",
    "valor_fipe_api",
    "diferenca_pct_api",
    "status_fipe_api",
]


def carrega_ja_resolvidos() -> set[str]:
    if not CSV_FALLBACK.exists():
        return set()
    df = pd.read_csv(CSV_FALLBACK)
    return set(df["link"].dropna())


def anuncio_de_linha(linha: pd.Series) -> Anuncio:
    def _val(campo, default=None):
        v = linha.get(campo, default)
        if pd.isna(v):
            return default
        return v

    return Anuncio(
        titulo=str(linha["titulo"]),
        preco=int(linha["preco"]),
        localizacao=str(_val("localizacao", "")),
        km=_val("km"),
        cor=_val("cor"),
        motor=_val("motor"),
        tipo=_val("tipo"),
        ano=int(linha["ano"]) if not pd.isna(linha["ano"]) else None,
        link=str(linha["link"]),
    )


def main() -> None:
    df = pd.read_csv(CSV_DETALHADOS)
    faltantes = df[df["valor_fipe_olx"].isna()].copy()
    ja_resolvidos = carrega_ja_resolvidos()
    faltantes = faltantes[~faltantes["link"].isin(ja_resolvidos)]

    total = len(faltantes)
    print(f"Faltando FIPE-OLX: {df['valor_fipe_olx'].isna().sum()} anúncios")
    print(f"Já resolvidos em execuções anteriores: {len(ja_resolvidos)}")
    print(f"A processar agora via API: {total}")

    if total == 0:
        print("Nada a fazer.")
        return

    novo_arquivo = not CSV_FALLBACK.exists()
    with open(CSV_FALLBACK, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_FALLBACK)
        if novo_arquivo:
            writer.writeheader()

        for i, (_, linha) in enumerate(faltantes.iterrows(), start=1):
            anuncio = anuncio_de_linha(linha)
            try:
                avaliacao = matcher.avaliar_anuncio(anuncio)
                registro = {
                    "link": anuncio.link,
                    "titulo": anuncio.titulo,
                    "marca_fipe": avaliacao.marca_fipe,
                    "modelo_fipe": avaliacao.modelo_fipe,
                    "ano_fipe": avaliacao.ano_fipe,
                    "valor_fipe_api": avaliacao.valor_fipe,
                    "diferenca_pct_api": avaliacao.diferenca_pct,
                    "status_fipe_api": avaliacao.status,
                }
            except Exception as exc:
                registro = {
                    "link": anuncio.link,
                    "titulo": anuncio.titulo,
                    "marca_fipe": None,
                    "modelo_fipe": None,
                    "ano_fipe": None,
                    "valor_fipe_api": None,
                    "diferenca_pct_api": None,
                    "status_fipe_api": f"erro: {exc}",
                }

            writer.writerow(registro)
            f.flush()
            print(f"[{i}/{total}] {registro['status_fipe_api']} — {anuncio.titulo[:60]}")

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    print("Concluído.")


if __name__ == "__main__":
    main()

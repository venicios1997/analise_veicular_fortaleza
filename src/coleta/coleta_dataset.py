"""Script de coleta em lote para o dataset de clusterização (projeto de MBA).

Roda fora do Streamlit (é demorado — cada anúncio detalhado exige abrir uma
página nova no navegador). Funciona em duas fases, cada uma salvando em CSV
incrementalmente, para que dê pra interromper e retomar sem perder trabalho:

  1. Listagem: varre várias faixas de preço em Fortaleza e salva os anúncios
     encontrados (dados básicos do card) em `dados/anuncios_listagem.csv`.
  2. Detalhamento: para cada anúncio da listagem que ainda não foi
     detalhado, abre a página dele e extrai marca, modelo, câmbio,
     combustível, carroceria, bairro, tipo de vendedor e valor de FIPE-OLX,
     salvando em `dados/anuncios_detalhados.csv`.

Uso:
    .venv\\Scripts\\python.exe coleta_dataset.py listagem
    .venv\\Scripts\\python.exe coleta_dataset.py detalhes
    .venv\\Scripts\\python.exe coleta_dataset.py tudo
"""
from __future__ import annotations

import csv
import dataclasses
import random
import sys
import time
from pathlib import Path

from scraper import Anuncio, buscar_anuncios, enriquecer_com_detalhes

LOCALIZACAO = "Fortaleza, CE"
PASTA_DADOS = Path(__file__).parent / "dados"
CSV_LISTAGEM = PASTA_DADOS / "anuncios_listagem.csv"
CSV_DETALHADO = PASTA_DADOS / "anuncios_detalhados.csv"

# faixas de preço para contornar o limite de páginas por busca da OLX e
# conseguir um volume maior de anúncios distintos em Fortaleza
FAIXAS_PRECO = [
    (5_000, 15_000),
    (15_000, 25_000),
    (25_000, 35_000),
    (35_000, 45_000),
    (45_000, 55_000),
    (55_000, 70_000),
    (70_000, 90_000),
    (90_000, 120_000),
    (120_000, 160_000),
    (160_000, 250_000),
]
MAX_PAGINAS_POR_FAIXA = 5  # 50 anúncios/página -> até 250 por faixa (reduzido p/ não sobrecarregar o IP)

CAMPOS = [f.name for f in dataclasses.fields(Anuncio)]


def _ler_links_existentes(caminho: Path) -> set[str]:
    if not caminho.exists():
        return set()
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return {linha["link"] for linha in csv.DictReader(f)}


def _gravar_anuncios(caminho: Path, anuncios: list[Anuncio]) -> None:
    PASTA_DADOS.mkdir(exist_ok=True)
    novo = not caminho.exists()
    with caminho.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            writer.writeheader()
        for a in anuncios:
            writer.writerow(dataclasses.asdict(a))


def coletar_listagem() -> None:
    links_existentes = _ler_links_existentes(CSV_LISTAGEM)
    print(f"{len(links_existentes)} anúncios já coletados anteriormente.")

    for preco_min, preco_max in FAIXAS_PRECO:
        print(f"\n== Faixa R$ {preco_min:,} - R$ {preco_max:,} ==".replace(",", "."))

        def progresso(pagina, total, n_anuncios):
            print(f"  página {pagina}/{total} — {n_anuncios} anúncios nesta faixa", end="\r")

        anuncios = buscar_anuncios(
            preco_min=preco_min,
            preco_max=preco_max,
            localizacao=LOCALIZACAO,
            max_paginas=MAX_PAGINAS_POR_FAIXA,
            progresso=progresso,
        )
        print()

        novos = [a for a in anuncios if a.link not in links_existentes]
        links_existentes.update(a.link for a in novos)
        _gravar_anuncios(CSV_LISTAGEM, novos)
        print(f"  {len(anuncios)} anúncios na faixa, {len(novos)} novos (total acumulado: {len(links_existentes)}).")

        # pausa entre faixas de preço (cada faixa já abre seu próprio navegador),
        # pra não manter um ritmo constante de requisições por muito tempo seguido
        time.sleep(random.uniform(15.0, 30.0))

    print(f"\nListagem concluída. Total de anúncios únicos: {len(links_existentes)}")
    print(f"Salvo em: {CSV_LISTAGEM}")


def detalhar_anuncios() -> None:
    if not CSV_LISTAGEM.exists():
        print("Nenhuma listagem encontrada. Rode a fase 'listagem' primeiro.")
        return

    ja_detalhados = _ler_links_existentes(CSV_DETALHADO)
    print(f"{len(ja_detalhados)} anúncios já detalhados anteriormente.")

    with CSV_LISTAGEM.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))

    pendentes = [linha for linha in linhas if linha["link"] not in ja_detalhados]
    print(f"{len(pendentes)} anúncios pendentes de detalhamento.")
    if not pendentes:
        return

    def para_anuncio(linha: dict) -> Anuncio:
        campos_int = {"preco", "km", "ano"}
        kwargs = {}
        for campo in CAMPOS:
            valor = linha.get(campo) or None
            if valor is not None and campo in campos_int:
                valor = int(float(valor))
            kwargs[campo] = valor
        return Anuncio(**kwargs)

    # processa em lotes pequenos, gravando a cada lote (resumível se cair no meio)
    TAMANHO_LOTE = 25
    for i in range(0, len(pendentes), TAMANHO_LOTE):
        lote = [para_anuncio(linha) for linha in pendentes[i : i + TAMANHO_LOTE]]

        def progresso(j, total):
            print(f"  lote {i // TAMANHO_LOTE + 1} — {j}/{total}", end="\r")

        enriquecer_com_detalhes(lote, progresso=progresso)
        _gravar_anuncios(CSV_DETALHADO, lote)
        print(f"\n  {min(i + TAMANHO_LOTE, len(pendentes))}/{len(pendentes)} anúncios detalhados no total.")

        # pausa entre lotes (além da pausa a cada 25 anúncios já feita dentro
        # de enriquecer_com_detalhes), pra espaçar ainda mais as requisições
        if i + TAMANHO_LOTE < len(pendentes):
            time.sleep(random.uniform(20.0, 40.0))

    print(f"\nDetalhamento concluído. Salvo em: {CSV_DETALHADO}")


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if fase in ("listagem", "tudo"):
        coletar_listagem()
    if fase in ("detalhes", "tudo"):
        detalhar_anuncios()
    if fase not in ("listagem", "detalhes", "tudo"):
        print("Uso: python coleta_dataset.py [listagem|detalhes|tudo]")

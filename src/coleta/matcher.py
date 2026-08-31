"""Cruza os anúncios da OLX com a Tabela FIPE para achar as melhores oportunidades."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz, process

import fipe_api
from scraper import Anuncio

# apelidos comuns que a busca por similaridade de texto erraria sozinha
ALIASES_MARCA = {
    "vw": "VW - VolksWagen",
    "volkswagen": "VW - VolksWagen",
    "gm": "GM - Chevrolet",
    "chevrolet": "GM - Chevrolet",
    "mercedes": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "citroen": "CITROEN",
    "land rover": "LAND ROVER",
    "landrover": "LAND ROVER",
    "big": "BIG",
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return texto.lower().strip()


@dataclass
class Avaliacao:
    anuncio: Anuncio
    marca_fipe: str | None = None
    modelo_fipe: str | None = None
    ano_fipe: int | None = None
    valor_fipe: float | None = None
    diferenca_pct: float | None = None
    status: str = "não encontrado na FIPE"


def _match_marca(primeira_palavra: str, marcas: list[dict]) -> dict | None:
    chave = _normalizar(primeira_palavra)
    alvo = ALIASES_MARCA.get(chave)
    if alvo:
        for m in marcas:
            if m["nome"].lower() == alvo.lower():
                return m

    nomes = [m["nome"] for m in marcas]
    resultado = process.extractOne(
        primeira_palavra, nomes, scorer=fuzz.WRatio, score_cutoff=70
    )
    if not resultado:
        return None
    nome_encontrado, _score, idx = resultado
    return marcas[idx]


def _match_modelo(texto_restante: str, modelos: list[dict]) -> dict | None:
    palavras = texto_restante.split()
    if not palavras:
        return None

    # o nome do modelo na FIPE quase sempre começa com o nome "core" do carro
    # (ex.: "ONIX HATCH LT..."), então exigimos que a primeira palavra do
    # anúncio apareça no nome do modelo — evita casar carros diferentes
    # (ex.: "Onix" virar "Joy") só por causa de tokens genéricos em comum.
    nucleo = _normalizar(palavras[0])
    candidatos = [
        m for m in modelos if nucleo and nucleo in _normalizar(m["nome"]).split()
    ]
    if not candidatos:
        candidatos = modelos

    nomes = [m["nome"] for m in candidatos]
    resultado = process.extractOne(
        texto_restante, nomes, scorer=fuzz.token_set_ratio, score_cutoff=45
    )
    if not resultado:
        return None
    _nome, _score, idx = resultado
    return candidatos[idx]


def _match_ano_codigo(anos: tuple[dict, ...], ano_alvo: int) -> str | None:
    for candidato in (ano_alvo, ano_alvo - 1, ano_alvo + 1):
        for ano in anos:
            if ano["nome"].startswith(str(candidato)):
                return ano["codigo"]
    return None


def avaliar_anuncio(anuncio: Anuncio) -> Avaliacao:
    resultado = Avaliacao(anuncio=anuncio)

    if not anuncio.ano:
        resultado.status = "ano não identificado no título"
        return resultado

    palavras = anuncio.titulo.split()
    if not palavras:
        return resultado

    marcas = fipe_api.get_marcas()
    marca = _match_marca(palavras[0], marcas)
    if not marca:
        resultado.status = "marca não identificada"
        return resultado
    resultado.marca_fipe = marca["nome"]

    modelos = list(fipe_api.get_modelos(marca["codigo"]))
    texto_restante = " ".join(palavras[1:])
    modelo = _match_modelo(texto_restante, modelos)
    if not modelo:
        resultado.status = "modelo não identificado"
        return resultado
    resultado.modelo_fipe = modelo["nome"]

    anos = fipe_api.get_anos(marca["codigo"], modelo["codigo"])
    ano_codigo = _match_ano_codigo(anos, anuncio.ano)
    if not ano_codigo:
        resultado.status = "ano não disponível na FIPE"
        return resultado

    preco = fipe_api.get_valor(marca["codigo"], modelo["codigo"], ano_codigo)
    if not preco:
        resultado.status = "preço FIPE indisponível"
        return resultado

    valor_fipe = fipe_api.parse_valor_brl(preco["Valor"])
    if not valor_fipe:
        resultado.status = "preço FIPE indisponível"
        return resultado

    resultado.ano_fipe = preco.get("AnoModelo")
    resultado.valor_fipe = valor_fipe
    resultado.diferenca_pct = round((valor_fipe - anuncio.preco) / valor_fipe * 100, 1)
    resultado.status = "ok"
    return resultado


def avaliar_anuncios(anuncios: list[Anuncio], progresso=None) -> list[Avaliacao]:
    avaliacoes = []
    for i, anuncio in enumerate(anuncios, start=1):
        try:
            avaliacoes.append(avaliar_anuncio(anuncio))
        except Exception:
            avaliacoes.append(Avaliacao(anuncio=anuncio, status="erro ao consultar FIPE"))
        if progresso:
            progresso(i, len(anuncios))
    return avaliacoes

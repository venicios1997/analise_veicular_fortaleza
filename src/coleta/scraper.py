"""Scraper de anúncios de carros na OLX usando Playwright (navegador real,
necessário porque a OLX bloqueia requisições HTTP simples sem navegador)."""
from __future__ import annotations

import asyncio
import contextlib
import html
import json
import random
import re
import sys
import time
from dataclasses import dataclass, field

from playwright.sync_api import sync_playwright

BASE_SEARCH_URL = "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@contextlib.contextmanager
def _event_loop_policy_para_playwright():
    """No Windows, servidores baseados em Tornado (como o do Streamlit) trocam
    a política global do asyncio para uma que não sabe criar subprocessos —
    e o Playwright precisa disso para abrir o navegador. Troca só durante a
    chamada e devolve a política original em seguida."""
    if sys.platform != "win32":
        yield
        return
    original = asyncio.get_event_loop_policy()
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(original)


@dataclass
class Anuncio:
    titulo: str
    preco: int
    localizacao: str
    km: int | None
    cor: str | None
    motor: str | None
    tipo: str | None
    ano: int | None
    link: str
    valor_fipe_olx: float | None = None
    # campos abaixo só são preenchidos após enriquecer_com_detalhes(), que
    # visita a página do anúncio (não vêm no card da listagem)
    marca: str | None = None
    modelo: str | None = None
    versao: str | None = None
    cambio: str | None = None
    combustivel: str | None = None
    carroceria: str | None = None
    portas: str | None = None
    bairro: str | None = None
    municipio: str | None = None
    vendedor_tipo: str | None = None  # "profissional" ou "particular"
    aceita_troca: str | None = None
    unico_dono: str | None = None
    data_coleta: str | None = None


class LocalizacaoNaoEncontrada(Exception):
    pass


def _resolve_location_path(page, texto_local: str) -> dict:
    """Usa a API de autocomplete da própria OLX (chamada de dentro do navegador,
    já autenticado por cookies de sessão) para achar o path de URL da localização."""
    query_js = json.dumps(texto_local)
    resultado = page.evaluate(
        f"""
        fetch('https://location-autocomplete.olx.com.br/location?q=' + encodeURIComponent({query_js}))
            .then(r => r.ok ? r.json() : [])
            .catch(() => [])
        """
    )
    if not resultado:
        raise LocalizacaoNaoEncontrada(
            f"Não encontrei nenhuma localização correspondente a '{texto_local}' na OLX."
        )
    return resultado[0]


def _parse_preco(texto: str) -> int | None:
    numeros = re.sub(r"[^\d]", "", texto or "")
    return int(numeros) if numeros else None


def _parse_km(aria_label: str | None) -> int | None:
    if not aria_label:
        return None
    m = re.search(r"([\d.]+)\s*quil", aria_label)
    if not m:
        return None
    return int(m.group(1).replace(".", ""))


def _parse_ano(titulo: str) -> int | None:
    anos = re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", titulo)
    if not anos:
        return None
    return int(anos[-1])


def _parse_card(card) -> Anuncio | None:
    link_el = card.query_selector('a[data-testid="adcard-link"]')
    if not link_el:
        return None
    titulo = (link_el.get_attribute("title") or "").strip()
    href = link_el.get_attribute("href") or ""

    # usa text_content() (le o textContent do DOM) em vez de inner_text()
    # (que respeita renderizacao/visibilidade): a OLX usa `content-visibility:
    # auto` nos cards fora da tela, o que faz inner_text() retornar vazio
    # pra cards ainda nao rolados ate a viewport, mesmo com o texto ja
    # presente no DOM. Descoberto porque so ~11 de 50 cards por pagina
    # estavam sendo aproveitados.
    preco_el = card.query_selector(".olx-adcard__price")
    preco = _parse_preco(preco_el.text_content()) if preco_el else None
    if preco is None:
        return None

    loc_el = card.query_selector(".olx-adcard__location")
    localizacao = loc_el.text_content().strip() if loc_el else ""

    km = cor = motor = tipo = None
    for detail in card.query_selector_all(".olx-adcard__detail"):
        label = detail.get_attribute("aria-label") or ""
        if "quil" in label:
            km = _parse_km(label)
        elif label.startswith("Cor "):
            cor = label.replace("Cor ", "").strip()
        elif label.startswith("Motor "):
            motor = label.replace("Motor ", "").strip()
        elif "tipo" in label:
            tipo = label.split("tipo", 1)[-1].strip()

    return Anuncio(
        titulo=titulo,
        preco=preco,
        localizacao=localizacao,
        km=km,
        cor=cor,
        motor=motor,
        tipo=tipo,
        ano=_parse_ano(titulo),
        link=href,
    )


def buscar_anuncios(
    preco_min: int,
    preco_max: int,
    localizacao: str,
    max_paginas: int = 3,
    headless: bool = True,
    progresso=None,
) -> list[Anuncio]:
    """Busca anúncios de carros na OLX dentro da faixa de preço e localização informadas.

    progresso: callback opcional chamado como progresso(pagina_atual, total_paginas, n_anuncios)
    """
    anuncios: list[Anuncio] = []

    with _event_loop_policy_para_playwright(), sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT, locale="pt-BR")
        page = context.new_page()

        # precisa estar numa página do domínio olx.com.br antes de chamar a API
        # de autocomplete (mesma origem / cookies de sessão)
        page.goto(f"{BASE_SEARCH_URL}?ps={preco_min}&pe={preco_max}",
                   wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)

        local = _resolve_location_path(page, localizacao)
        path = local["path"]
        titulo_local = local.get("title", localizacao)

        for pagina in range(1, max_paginas + 1):
            url = f"{BASE_SEARCH_URL}/{path}?ps={preco_min}&pe={preco_max}&o={pagina}"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)

            cards = page.query_selector_all("section.olx-adcard")
            if not cards:
                break

            for card in cards:
                anuncio = _parse_card(card)
                if anuncio:
                    anuncios.append(anuncio)

            if progresso:
                progresso(pagina, max_paginas, len(anuncios))

            if len(cards) < 50:
                break  # última página

            time.sleep(random.uniform(3.0, 6.0))  # educado com o servidor da OLX

        browser.close()

    return anuncios


def _extrair_fipe_olx(conteudo_pagina: str) -> float | None:
    """A página de cada anúncio individual traz um valor de FIPE calculado
    pela própria OLX, embutido como JSON dentro de um atributo HTML
    (escapado com &quot;). Precisa desescapar antes de procurar o campo."""
    texto = html.unescape(conteudo_pagina)
    m = re.search(r'"fipePrice"\s*:\s*(\d+)', texto)
    if not m:
        return None
    return float(m.group(1))


def _extrair_bloco_datalayer(conteudo_pagina: str) -> dict | None:
    """A página de cada anúncio embute `window.dataLayer = [...]` com um
    objeto `page.adDetail` já estruturado (marca, modelo, câmbio,
    combustível, bairro, tipo de vendedor etc.) — muito mais confiável do
    que tentar adivinhar essas informações a partir do título do anúncio."""
    marcador = "window.dataLayer = "
    inicio = conteudo_pagina.find(marcador)
    if inicio == -1:
        return None
    inicio += len(marcador)

    profundidade = 0
    dentro_string = False
    escapando = False
    fim = None
    for i in range(inicio, len(conteudo_pagina)):
        c = conteudo_pagina[i]
        if dentro_string:
            if escapando:
                escapando = False
            elif c == "\\":
                escapando = True
            elif c == '"':
                dentro_string = False
            continue
        if c == '"':
            dentro_string = True
        elif c == "[":
            profundidade += 1
        elif c == "]":
            profundidade -= 1
            if profundidade == 0:
                fim = i + 1
                break
    if fim is None:
        return None

    try:
        dados = json.loads(conteudo_pagina[inicio:fim])
        return dados[0]["page"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


def _preencher_detalhes(anuncio: Anuncio, conteudo_pagina: str) -> None:
    anuncio.valor_fipe_olx = _extrair_fipe_olx(conteudo_pagina)
    anuncio.data_coleta = time.strftime("%Y-%m-%d")

    page_data = _extrair_bloco_datalayer(conteudo_pagina)
    detalhe = (page_data or {}).get("adDetail") or {}
    if not detalhe:
        return

    anuncio.marca = detalhe.get("brand")
    anuncio.modelo = detalhe.get("model")
    anuncio.versao = detalhe.get("version")
    anuncio.cambio = detalhe.get("gearbox")
    anuncio.combustivel = detalhe.get("fuel")
    anuncio.carroceria = detalhe.get("cartype")
    anuncio.portas = detalhe.get("doors")
    anuncio.bairro = detalhe.get("neighbourhood")
    anuncio.municipio = detalhe.get("municipality")
    anuncio.aceita_troca = detalhe.get("exchange")
    anuncio.unico_dono = detalhe.get("owner")
    # professionalAd vem vazio ("") para pessoa física e preenchido para lojas
    anuncio.vendedor_tipo = "profissional" if detalhe.get("professionalAd") else "particular"

    # a FIPE-OLX pode vir vazia do regex acima (às vezes o widget carrega
    # via chamada assíncrona à parte); o dataLayer tem um segundo lugar
    # onde o mesmo valor aparece, então usamos como reforço se faltar
    if anuncio.valor_fipe_olx is None:
        ref = (page_data or {}).get("detail", {}).get("abuyFipePrice") or {}
        preco_fipe = ref.get("fipePrice")
        if preco_fipe:
            anuncio.valor_fipe_olx = float(preco_fipe)


def enriquecer_com_detalhes(
    anuncios: list[Anuncio],
    headless: bool = True,
    progresso=None,
) -> list[Anuncio]:
    """Abre a página de cada anúncio e preenche marca, modelo, câmbio,
    combustível, carroceria, bairro, tipo de vendedor e valor de FIPE-OLX
    (exige uma requisição extra por anúncio).

    progresso: callback opcional chamado como progresso(i, total)
    """
    # cada anúncio precisa de um `browser.new_context()` novo — reaproveitar
    # o mesmo contexto entre anúncios faz o widget de "Referência de preço"
    # (que traz a FIPE) parar de carregar dados depois do primeiro acesso
    # (visto empiricamente). Os demais campos (dataLayer) não têm essa
    # limitação, mas manter contexto novo não tem custo extra relevante.
    with _event_loop_policy_para_playwright(), sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        for i, anuncio in enumerate(anuncios, start=1):
            if anuncio.link:
                context = browser.new_context(user_agent=USER_AGENT, locale="pt-BR")
                try:
                    page = context.new_page()
                    page.goto(anuncio.link, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                    _preencher_detalhes(anuncio, page.content())
                except Exception:
                    pass
                finally:
                    context.close()

            if progresso:
                progresso(i, len(anuncios))

            time.sleep(random.uniform(2.5, 5.0))  # educado com o servidor da OLX

            # pausa mais longa a cada bloco de anúncios, pra não manter um
            # ritmo constante de requisições por muito tempo seguido
            if i % 25 == 0:
                time.sleep(random.uniform(20.0, 40.0))

        browser.close()

    return anuncios


# mantido por compatibilidade com código existente que só precisa da FIPE
enriquecer_com_fipe_olx = enriquecer_com_detalhes

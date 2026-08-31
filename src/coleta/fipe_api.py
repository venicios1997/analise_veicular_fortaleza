"""Cliente para a API pública da Tabela FIPE (parallelum.com.br/fipe)."""

from __future__ import annotations

import re
from functools import lru_cache

import requests

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"
_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ComparadorFIPE/1.0)"})


def parse_valor_brl(valor: str) -> float | None:
    """Converte 'R$ 55.000,00' em 55000.0"""
    if not valor:
        return None
    numero = re.sub(r"[^\d,]", "", valor).replace(",", ".")
    try:
        return float(numero)
    except ValueError:
        return None


@lru_cache(maxsize=1)
def get_marcas() -> list[dict]:
    resp = _session.get(f"{BASE_URL}/marcas", timeout=15)
    resp.raise_for_status()
    return resp.json()


@lru_cache(maxsize=256)
def get_modelos(marca_codigo: str) -> tuple[dict, ...]:
    resp = _session.get(f"{BASE_URL}/marcas/{marca_codigo}/modelos", timeout=15)
    resp.raise_for_status()
    return tuple(resp.json().get("modelos", []))


@lru_cache(maxsize=1024)
def get_anos(marca_codigo: str, modelo_codigo: str) -> tuple[dict, ...]:
    resp = _session.get(
        f"{BASE_URL}/marcas/{marca_codigo}/modelos/{modelo_codigo}/anos", timeout=15
    )
    resp.raise_for_status()
    return tuple(resp.json())


@lru_cache(maxsize=2048)
def get_valor(marca_codigo: str, modelo_codigo: str, ano_codigo: str) -> dict | None:
    resp = _session.get(
        f"{BASE_URL}/marcas/{marca_codigo}/modelos/{modelo_codigo}/anos/{ano_codigo}",
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json()

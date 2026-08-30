"""Hook do MkDocs: publica os notebooks executados dentro do site.

Os notebooks versionados em ``notebooks/`` são gravados sem saída (`nbstripout`
roda no pre-commit). As versões **com saída** ficam em ``reports/notebooks/``,
gravadas por ``src.utils.executar_notebooks``.

Como a ``nav`` do MkDocs só enxerga arquivos dentro de ``docs_dir``, este hook
copia as versões executadas para ``docs/notebooks/`` antes de cada build — é o
que faz o plugin ``mkdocs-jupyter`` ter o que renderizar. O destino é ignorado
pelo git: o original continua sendo ``reports/notebooks/``.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "reports" / "notebooks"
DESTINO = RAIZ / "docs" / "notebooks"

log = logging.getLogger("mkdocs.hooks.publicar_notebooks")


def on_pre_build(config) -> None:  # noqa: ARG001 — assinatura fixada pelo MkDocs
    """Copia `reports/notebooks/*.ipynb` para `docs/notebooks/`."""
    if not ORIGEM.is_dir():
        log.warning(
            "%s não existe — rode `uv run invoke notebooks` para gerar as "
            "versões executadas. O site será publicado sem a seção Notebooks.",
            ORIGEM.relative_to(RAIZ),
        )
        return

    DESTINO.mkdir(parents=True, exist_ok=True)
    copiados = 0
    for caderno in sorted(ORIGEM.glob("*.ipynb")):
        shutil.copy2(caderno, DESTINO / caderno.name)
        copiados += 1

    log.info("publicar_notebooks: %d notebooks copiados para docs/notebooks/", copiados)

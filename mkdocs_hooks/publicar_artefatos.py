"""Hook do MkDocs: leva os artefatos gerados para dentro do site.

Dois diretórios do projeto ficam **fora** de ``docs_dir`` e, por isso, não são
enxergados nem pela ``nav`` nem por um caminho relativo dentro de um `.md`:

* ``reports/notebooks/`` — as versões **executadas** dos notebooks. As
  versionadas em ``notebooks/`` são gravadas sem saída (`nbstripout` roda no
  pre-commit), então é daqui que sai o que o `mkdocs-jupyter` renderiza;
* ``reports/figures/`` — as figuras da análise, gravadas junto com o CSV que
  originou cada uma (``src.utils.io.salvar_figura``).

Este hook copia os dois para dentro de ``docs/`` antes de cada build. Os
destinos são ignorados pelo git: o original continua sendo ``reports/``, que é
onde os notebooks gravam. Nas páginas, as figuras são referenciadas por
``imagens/figuras/<secao>/<nome>.png``.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

NOTEBOOKS_ORIGEM = RAIZ / "reports" / "notebooks"
NOTEBOOKS_DESTINO = RAIZ / "docs" / "notebooks"

FIGURAS_ORIGEM = RAIZ / "reports" / "figures"
FIGURAS_DESTINO = RAIZ / "docs" / "imagens" / "figuras"

log = logging.getLogger("mkdocs.hooks.publicar_artefatos")


def _copiar(origem: Path, destino: Path, padrao: str, rotulo: str) -> None:
    if not origem.is_dir():
        log.warning(
            "%s não existe — rode `uv run invoke notebooks` para gerar os artefatos. "
            "O site será publicado sem %s.",
            origem.relative_to(RAIZ),
            rotulo,
        )
        return

    copiados = 0
    for arquivo in sorted(origem.rglob(padrao)):
        alvo = destino / arquivo.relative_to(origem)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arquivo, alvo)
        copiados += 1

    log.info("publicar_artefatos: %d %s copiados para %s", copiados, rotulo, destino.name)


def on_pre_build(config) -> None:  # noqa: ARG001 — assinatura fixada pelo MkDocs
    """Copia notebooks executados e figuras para dentro de ``docs/``."""
    _copiar(NOTEBOOKS_ORIGEM, NOTEBOOKS_DESTINO, "*.ipynb", "notebooks")
    _copiar(FIGURAS_ORIGEM, FIGURAS_DESTINO, "*.png", "figuras")

"""Configuração central do projeto.

Concentra caminhos, semente aleatória, paleta e parâmetros que precisam ser
idênticos entre notebooks, scripts de pipeline e aplicação Streamlit. Nenhum
outro módulo deve montar caminho na mão.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Caminhos
# --------------------------------------------------------------------------- #

RAIZ = Path(__file__).resolve().parents[1]

DATA = RAIZ / "data"
DATA_RAW = DATA / "raw"
DATA_PROCESSED = DATA / "processed"
DATA_EXTERNAL = DATA / "external"

MODELS = RAIZ / "models"
REPORTS = RAIZ / "reports"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"
REFERENCES = RAIZ / "references"

# --------------------------------------------------------------------------- #
# Fonte dos dados
# --------------------------------------------------------------------------- #

# Anúncios de carros usados de Fortaleza-CE, coletados por scraping da OLX
# (o coletor é uma ferramenta separada, fora deste repositório — ver
# `docs/fonte-dados.md`). Não há download de origem externa: a camada
# bruta já é o resultado da coleta, materializado uma única vez em
# `data/raw/` e tratado como imutável a partir daqui.
ARQUIVO_BRUTO = DATA_RAW / "anuncios_detalhados.csv"
ARQUIVO_BRUTO_LISTAGEM = DATA_RAW / "anuncios_listagem.csv"
#: Complemento de FIPE via API pública, para os anúncios sem FIPE-OLX.
ARQUIVO_FIPE_FALLBACK = DATA_RAW / "fipe_fallback.csv"

BASE_CURADA = DATA_PROCESSED / "anuncios_curados.parquet"
MATRIZ_MODELAGEM = DATA_PROCESSED / "matriz_modelagem.parquet"
#: Base curada com a coluna `segmento` já atribuída. Gravada pelo notebook 03.
BASE_SEGMENTADA = DATA_PROCESSED / "anuncios_segmentados.parquet"

#: Pipeline treinado (pré-processador + modelo) que a aplicação consome. Nome
#: fixo, independente de qual algoritmo venceu a seleção — a aplicação não
#: precisa saber se foi K-Means, Birch etc. Gravado pelo notebook 03.
PACOTE_APLICACAO = MODELS / "modelo-segmentacao.joblib"
#: Catálogo dos segmentos (perfil, métricas, parâmetros), publicado pela mesma fase.
CATALOGO_DE_SEGMENTOS = MODELS / "catalogo_de_segmentos.json"

# --------------------------------------------------------------------------- #
# Reprodutibilidade
# --------------------------------------------------------------------------- #

SEMENTE = 42

#: Ano de referência para calcular a idade dos veículos (`idade_veiculo`,
#: `km_por_ano`). A coleta foi feita em 2026-08-21 (ver `data_coleta`), e o
#: projeto roda em 2026 — usar o ano civil da coleta, não `datetime.now()`,
#: mantém o cálculo reprodutível independente de quando o notebook é rodado.
ANO_REFERENCIA = 2026

# --------------------------------------------------------------------------- #
# Regras de negócio vindas do Canvas do Problema
# --------------------------------------------------------------------------- #

#: Teto de linhas de produto que uma pequena revenda consegue operar.
K_MAXIMO_NEGOCIO = 8
#: Abaixo de dois grupos não existe segmentação.
K_MINIMO_NEGOCIO = 4
#: Silhueta mínima aceita no critério técnico do projeto.
SILHUETA_MINIMA = 0.40
#: Percentual máximo de anúncios que podem cair como ruído em métodos de densidade.
RUIDO_MAXIMO = 0.10

# --------------------------------------------------------------------------- #
# Identidade visual
# --------------------------------------------------------------------------- #

AZUL_PROFUNDO = "#1B4965"
AZUL_COBALTO = "#2A6F97"
AZUL_CLARO = "#62B6CB"
VERDE = "#74C69D"
AMARELO = "#F4D35E"
CORAL = "#EE6C4D"
ROXO = "#8E7DBE"
LARANJA = "#F49D6E"
ROSA = "#F2A6A6"
CINZA = "#8A9BA8"

PALETA = [AZUL_PROFUNDO, CORAL, VERDE, AMARELO, ROXO, AZUL_CLARO, LARANJA, ROSA]
PALETA_SEGMENTOS = [AZUL_PROFUNDO, CORAL, VERDE, AMARELO, ROXO, AZUL_CLARO, LARANJA, ROSA]

DPI = 150


def garantir_diretorios() -> None:
    """Cria os diretórios de saída caso ainda não existam."""
    for caminho in (
        DATA_RAW,
        DATA_PROCESSED,
        DATA_EXTERNAL,
        MODELS,
        FIGURES,
        TABLES,
        REFERENCES,
    ):
        caminho.mkdir(parents=True, exist_ok=True)

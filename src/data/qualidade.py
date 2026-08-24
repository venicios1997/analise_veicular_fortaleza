"""CRISP-DM 2.2 e 2.4 — Descrição dos dados e verificação de qualidade.

Produz o perfil que sustenta o notebook de ajustes: tipos, volume, ausentes,
cardinalidade, colunas constantes, duplicidades e plausibilidade do domínio.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


def perfil_colunas(dados: pd.DataFrame) -> pd.DataFrame:
    """Monta o perfil coluna a coluna do conjunto de dados.

    Returns:
        Tabela com tipo, contagem de nulos, percentual de nulos, cardinalidade,
        percentual do valor mais frequente e amostra de valores.
    """
    total = len(dados)
    linhas = []
    for coluna in dados.columns:
        serie = dados[coluna]
        nulos = int(serie.isna().sum())
        preenchida = serie.dropna()
        moda = preenchida.mode()
        valor_frequente = moda.iloc[0] if len(moda) else np.nan
        freq_relativa = float((preenchida == valor_frequente).mean()) if len(preenchida) else np.nan
        linhas.append(
            {
                "coluna": coluna,
                "tipo": str(serie.dtype),
                "nulos": nulos,
                "pct_nulos": round(100 * nulos / total, 2),
                "distintos": int(serie.nunique(dropna=True)),
                "valor_mais_frequente": valor_frequente,
                "pct_valor_mais_frequente": round(100 * freq_relativa, 2)
                if freq_relativa == freq_relativa
                else np.nan,
            }
        )
    perfil = pd.DataFrame(linhas).set_index("coluna")
    return perfil.sort_values("pct_nulos", ascending=False)


def colunas_constantes(dados: pd.DataFrame, limiar: float = 99.0) -> pd.DataFrame:
    """Colunas com um único valor ou quase — variância nula quebra a padronização.

    Args:
        dados: conjunto a inspecionar.
        limiar: percentual de concentração acima do qual a coluna é sinalizada.
    """
    perfil = perfil_colunas(dados)
    alvo = perfil[(perfil["distintos"] <= 1) | (perfil["pct_valor_mais_frequente"] >= limiar)]
    return alvo[["distintos", "valor_mais_frequente", "pct_valor_mais_frequente"]]


def diagnostico_duplicidade(dados: pd.DataFrame, chave: str) -> dict:
    """Verifica se a chave declarada identifica de fato cada registro."""
    return {
        "linhas": int(len(dados)),
        "chaves_distintas": int(dados[chave].nunique()),
        "linhas_duplicadas_completas": int(dados.duplicated().sum()),
        "chave_unica": bool(dados[chave].is_unique),
    }


def resumo_numericas(dados: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Estatística descritiva estendida, com assimetria e curtose.

    Assimetria alta é o sinal de que a variável precisa de transformação antes
    de qualquer algoritmo baseado em distância.
    """
    resumo = dados[colunas].describe().T
    resumo["assimetria"] = dados[colunas].skew()
    resumo["curtose"] = dados[colunas].kurtosis()
    resumo["zeros"] = (dados[colunas] == 0).sum()
    resumo["pct_zeros"] = round(100 * (dados[colunas] == 0).mean(), 2)
    resumo["cv"] = resumo["std"] / resumo["mean"].replace(0, np.nan)
    return resumo.round(3)


#: Regras de plausibilidade do domínio de veículos usados: nome, colunas
#: exigidas e o teste. Nenhuma
#: regra aqui tem uma autoridade externa citável para justificar remoção
#: automática — por isso `valores_implausiveis` é usada só para **registrar**
#: o achado; a decisão de remover (ou não) é tomada à parte, com evidência
#: própria, no notebook `02-ajustes-dados`.
CHECAGENS: list[tuple[str, list[str], object]] = [
    (
        "km negativa",
        ["km"],
        lambda d: d["km"] < 0,
    ),
    (
        "ano fora de uma faixa plausível (antes de 1950 ou mais de 1 ano à frente da coleta)",
        ["ano"],
        lambda d: (d["ano"] < 1950) | (d["ano"] > config.ANO_REFERENCIA + 1),
    ),
    (
        "km muito alta para a idade do veículo (> 100.000 km/ano)",
        ["km", "idade_veiculo"],
        lambda d: d["km"] / d["idade_veiculo"].clip(lower=1) > 100_000,
    ),
    (
        "quilometragem zero em veículo com mais de 2 anos",
        ["km", "idade_veiculo"],
        lambda d: (d["km"] == 0) & (d["idade_veiculo"] > 2),
    ),
    (
        "preço muito abaixo da FIPE (menos de 30% do valor de referência)",
        ["preco", "valor_fipe_final"],
        lambda d: d["valor_fipe_final"].notna() & (d["preco"] < 0.3 * d["valor_fipe_final"]),
    ),
]


def valores_implausiveis(dados: pd.DataFrame) -> pd.DataFrame:
    """Regras de plausibilidade específicas do domínio de veículos usados.

    Cada regra devolve quantos registros a violam. Regra sem violação também
    aparece — é evidência de que a checagem foi feita.

    A regra cuja coluna não existe no conjunto recebido aparece como *não
    aplicável*, e não desaparece do relatório: checagem omitida em silêncio é
    checagem que ninguém percebe que deixou de rodar.
    """
    linhas = []
    for nome, exigidas, teste in CHECAGENS:
        if not set(exigidas) <= set(dados.columns):
            ausentes = ", ".join(c for c in exigidas if c not in dados.columns)
            linhas.append(
                {
                    "regra": nome,
                    "registros": pd.NA,
                    "pct": pd.NA,
                    "situacao": f"não aplicável — sem {ausentes}",
                }
            )
            continue
        mascara = teste(dados)
        linhas.append(
            {
                "regra": nome,
                "registros": int(mascara.sum()),
                "pct": round(100 * mascara.mean(), 2),
                "situacao": "verificada",
            }
        )
    return pd.DataFrame(linhas).set_index("regra")

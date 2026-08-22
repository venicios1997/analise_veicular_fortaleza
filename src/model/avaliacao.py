"""Métricas de avaliação para clusterização (CRISP-DM 4 e 5).

Precisa viver em `src`, não dentro do notebook: o pipeline final
(`models/modelo-segmentacao.joblib`) é um `GridSearchCV` cujo parâmetro
`scoring` é `silhouette_scorer`. O `joblib`/`pickle` grava só o caminho do
módulo e o nome da função — se ela estivesse definida no notebook (módulo
`__main__` daquela sessão), carregar o modelo em qualquer outro script (a
aplicação Streamlit, por exemplo) falharia com
``AttributeError: Can't get attribute 'silhouette_scorer'``.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline


def obter_rotulos(estimador, dados):
    """Extrai a matriz transformada e os rótulos de cluster.

    Funciona tanto para um `Pipeline` completo (pré-processador + modelo)
    quanto para o modelo isolado (dentro de um `GridSearchCV`).
    """
    if isinstance(estimador, Pipeline):
        dados_transformados = estimador[:-1].transform(dados)
        rotulos = estimador[-1].predict(dados_transformados)
    else:
        dados_transformados = dados
        rotulos = estimador.predict(dados_transformados)
    return dados_transformados, rotulos


def silhouette_scorer(estimador, dados, y=None) -> float:
    """Silhueta como *scorer* do scikit-learn — não depende de rótulo (`y`).

    Devolve -1 (pior valor possível) quando o ajuste degenera num único
    cluster, para que o `GridSearchCV` descarte essa combinação de
    hiperparâmetros em vez de falhar.
    """
    dados_transformados, rotulos = obter_rotulos(estimador, dados)
    if len(np.unique(rotulos)) < 2:
        return -1.0
    return silhouette_score(dados_transformados, rotulos)

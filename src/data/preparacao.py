"""CRISP-DM 3 — Preparação dos dados.

Transforma a camada bruta imutável em duas saídas:

* ``data/processed/anuncios_curados.parquet`` — base curada, em unidades
  originais, legível por gente de negócio;
* ``data/processed/matriz_modelagem.parquet`` — recorte com as variáveis do
  espaço de atributos, sem os rótulos reservados.

Toda regra de limpeza vem com o motivo registrado em :data:`REGRAS_LIMPEZA`,
que o notebook `02-ajustes-dados` narra célula a célula. Regra sem motivo é
removida na primeira refatoração e o problema volta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    MinMaxScaler,
    OneHotEncoder,
    RobustScaler,
    StandardScaler,
)

from src import config
from src.data import dicionario as dic
from src.data.ingestao import carregar_bruto

# --------------------------------------------------------------------------- #
# Limiares da limpeza
# --------------------------------------------------------------------------- #

#: Múltiplo do IQR que define o valor extremo em `ano`/`km`. O 1,5 de Tukey
#: marca 3,5%/2,4% da base — incluindo o segmento de alto padrão e de alta
#: quilometragem que a segmentação precisa isolar, não descartar; o 3
#: alcança só a anomalia genuína.
FATOR_EXTREMO = 3.0

#: Concentração num único valor a partir da qual a coluna não informa nada.
LIMIAR_CONCENTRACAO = 99.0

#: Colunas que a regra de concentração não remove: são o esqueleto da base
#: curada e da matriz de modelagem.
COLUNAS_PROTEGIDAS = set(
    dic.IDENTIFICADORES
    + dic.ESPACO_MISTO
    + [dic.ROTULO_RESERVADO, dic.RESERVADA_VALIDACAO, dic.RESERVADA_FIPE]
)

#: Valor sentinela observado em `km` — um único registro com 999.998,
#: visivelmente um preenchimento de sistema/erro de digitação (posição
#: 10⁶ − 2), não uma quilometragem real. Ver notebook `02-ajustes-dados`,
#: bloco 4.
KM_SENTINELA = 999_998

#: Quilometragem abaixo da qual o hodômetro não é crível num carro já rodado.
#: Combinado com :data:`IDADE_MINIMA_PARA_KM`: um carro com mais de 5 anos e
#: menos de 1.000 km declarados é, quase sempre, quilometragem digitada em
#: milhares ("120" para 120.000 km) ou campo não preenchido. Ver notebook
#: `02-ajustes-dados`, bloco 5.
KM_MINIMA_PLAUSIVEL = 1_000

#: Idade a partir da qual a regra acima passa a valer. Abaixo dela, km baixa é
#: legítima (seminovo de vitrine, zero-km) e precisa continuar na base — é o
#: que a variável `zero_km` marca.
IDADE_MINIMA_PARA_KM = 5

#: Desconto/ágio máximo (em módulo, %) aceito como leitura de mercado.
#: `desconto_fipe_pct` é uma razão sem limite inferior: quando o casamento de
#: FIPE por similaridade de texto erra o modelo, o valor explode (a base chega
#: a −1.249%). Acima deste limiar o número diz mais sobre o casamento do que
#: sobre o anúncio.
DESCONTO_MAXIMO_PLAUSIVEL = 60.0

# --------------------------------------------------------------------------- #
# Regras de limpeza — narradas no notebook 02-ajustes-dados
# --------------------------------------------------------------------------- #

REGRAS_LIMPEZA: list[dict[str, str]] = [
    {
        "regra": "Remover anúncios com `link` duplicado (mesmo anúncio coletado duas vezes)",
        "motivo": (
            "5 links aparecem duas vezes na base bruta — falha pontual na dedupe "
            "incremental da coleta (retomada após queda de conexão/energia), não "
            "dois anúncios distintos."
        ),
    },
    {
        "regra": "Remover anúncios com falha total do bloco `dataLayer` da OLX",
        "motivo": (
            "62 anúncios têm marca, câmbio, combustível, carroceria, portas, tipo de "
            "vendedor e município vazios ao mesmo tempo — falha de captura do "
            "scraper (o bloco não carregou), não ausência de informação do anúncio. "
            "Sem essas colunas não há como caracterizar o veículo."
        ),
    },
    {
        "regra": "Remover o anúncio sem `ano`",
        "motivo": (
            "Um único registro; `ano` é a variável mais central da caracterização "
            "e não tem substituto plausível."
        ),
    },
    {
        "regra": f"Remover o registro com `km` = {KM_SENTINELA:,}".replace(",", "."),
        "motivo": (
            "Valor isolado, muito acima de qualquer outro na base e sugestivamente "
            "próximo de 10⁶ − 2 — padrão típico de valor de preenchimento/erro de "
            "digitação, não de uma quilometragem real."
        ),
    },
    {
        "regra": "Rotular como `NaoInformado` a ausência real e opcional (câmbio, combustível, "
        "carroceria, portas, aceita_troca, único_dono, bairro)",
        "motivo": (
            "Ausência real e legítima (o vendedor não preencheu o campo), em volume "
            "baixo o bastante (até 25% em `aceita_troca`, a maioria abaixo de 7%) "
            "para não justificar descartar linha ou coluna. Vira categoria "
            "explícita — nenhum valor numérico é inventado."
        ),
    },
    {
        "regra": "Derivar `idade_veiculo`, `km_por_ano`, `zero_km` e `desconto_fipe_pct`",
        "motivo": (
            "Idade na data da coleta separa veículos melhor que o ano absoluto; "
            "quilometragem por ano mede intensidade de uso, informação que `km` e "
            "`ano` sozinhos não capturam. `desconto_fipe_pct` deriva das reservadas "
            "e só entra na avaliação a posteriori."
        ),
    },
    {
        "regra": (
            f"Remover anúncios com `km` < {KM_MINIMA_PLAUSIVEL:,} em veículos com mais de "
            f"{IDADE_MINIMA_PARA_KM} anos"
        ).replace(",", "."),
        "motivo": (
            "Hodômetro implausível: 34 anúncios declaram menos de 1.000 km em carros "
            "de 6 a 44 anos — inclusive uma Belina 1982 com 100 km e um Civic 2007 "
            "com 1.000 km anunciado a R$ 10 mil contra FIPE de R$ 43 mil. O padrão "
            "é quilometragem digitada em milhares ou campo não preenchido, não uma "
            "frota preservada: a mediana do grupo dá 14 km rodados por ano. Sem a "
            "regra, esses registros formam um segmento inteiro na clusterização — "
            "um artefato de captura promovido a leitura de mercado. Zero-km e "
            "seminovos ficam, protegidos pelo corte de idade."
        ),
    },
    {
        "regra": (
            f"Anular `desconto_fipe_pct` quando |desconto| > {DESCONTO_MAXIMO_PLAUSIVEL:.0f}%"
        ),
        "motivo": (
            "A coluna é uma razão sem limite inferior e a FIPE que a alimenta vem, "
            "em 6,4% dos anúncios, de casamento por similaridade de texto — quando "
            "o casamento erra o modelo, o desconto explode (mínimo observado: "
            "−1.249%). São 2,7% da base e eles sozinhos dominam qualquer média. "
            "Aqui só o **valor** é descartado, não o anúncio: `desconto_fipe_pct` é "
            "reservada, não entra no espaço de atributos, e remover a linha "
            "tiraria da segmentação um veículo cujo defeito está na referência de "
            "preço, não nas características que agrupam."
        ),
    },
    {
        "regra": f"Remover os valores extremos além de {FATOR_EXTREMO:.0f}×IQR em `ano`/`km`",
        "motivo": (
            "A cerca clássica de Tukey (1,5×IQR) alcançaria carros antigos e de "
            "alta quilometragem genuínos — exatamente o extremo que a segmentação "
            "precisa isolar, não descartar. O fator 3 marca só a anomalia."
        ),
    },
    {
        "regra": "Descartar as colunas concentradas acima de 99% num único valor",
        "motivo": (
            "Coluna em que 99% dos anúncios dizem a mesma coisa não separa "
            "ninguém e entra como ruído com o mesmo peso de uma variável que "
            "discrimina. Nenhuma coluna do espaço de atributos passa desse "
            "limiar nesta base — o maior valor ali é 89,7% (`município` e "
            "`portas`). A única que passa é `data_coleta` (a coleta é de um "
            "único dia), e ela já não fazia parte do espaço de atributos."
        ),
    },
]


# --------------------------------------------------------------------------- #
# Camada curada
# --------------------------------------------------------------------------- #


def _remover_duplicados_reais(dados: pd.DataFrame) -> pd.DataFrame:
    """Remove anúncios com `link` repetido — o mesmo anúncio coletado 2×."""
    return dados.drop_duplicates(subset="link", keep="first")


def _remover_falha_dataLayer(dados: pd.DataFrame) -> pd.DataFrame:
    """Remove anúncios em que o bloco `dataLayer` inteiro falhou ao carregar."""
    falha_total = dados[dic.NUCLEO_DATALAYER].isna().all(axis=1)
    return dados[~falha_total]


def _remover_km_sentinela(dados: pd.DataFrame) -> pd.DataFrame:
    """Remove o registro com o valor de preenchimento em `km`."""
    return dados[dados["km"] != KM_SENTINELA]


def _rotular_ausencia_opcional(dados: pd.DataFrame) -> pd.DataFrame:
    """Converte a ausência real e legítima em categoria explícita `NaoInformado`."""
    dados = dados.copy()
    for coluna in dic.AUSENCIA_OPCIONAL:
        if coluna in dados.columns:
            dados[coluna] = dados[coluna].fillna("NaoInformado")
    return dados


def _derivar(dados: pd.DataFrame) -> pd.DataFrame:
    """Constrói os atributos derivados (CRISP-DM 3.3)."""
    dados = dados.copy()
    dados["idade_veiculo"] = (config.ANO_REFERENCIA - dados["ano"]).clip(lower=0)
    dados["km_por_ano"] = dados["km"] / dados["idade_veiculo"].clip(lower=1)
    dados["zero_km"] = (dados["km"] == 0).astype("int8")

    # Derivada das reservadas: entra apenas na avaliação a posteriori.
    dados["desconto_fipe_pct"] = np.where(
        dados["valor_fipe_final"].notna(),
        (dados["valor_fipe_final"] - dados["preco"]) / dados["valor_fipe_final"] * 100,
        np.nan,
    )
    return dados


def _remover_km_implausivel(dados: pd.DataFrame) -> pd.DataFrame:
    """Remove veículos rodados com hodômetro incompatível com a idade.

    Roda depois de :func:`_derivar`, que é quem constrói ``idade_veiculo``.
    Ver a regra correspondente em :data:`REGRAS_LIMPEZA`.
    """
    implausivel = (dados["km"] < KM_MINIMA_PLAUSIVEL) & (
        dados["idade_veiculo"] > IDADE_MINIMA_PARA_KM
    )
    return dados[~implausivel]


def _aparar_desconto_implausivel(dados: pd.DataFrame) -> pd.DataFrame:
    """Anula `desconto_fipe_pct` fora da faixa plausível, mantendo o anúncio.

    O anúncio continua na base e na segmentação; o que sai é só a leitura de
    desconto, que naquele ponto reflete um erro de casamento de FIPE.
    """
    dados = dados.copy()
    fora_da_faixa = dados["desconto_fipe_pct"].abs() > DESCONTO_MAXIMO_PLAUSIVEL
    dados.loc[fora_da_faixa, "desconto_fipe_pct"] = np.nan
    return dados


def _remover_extremos(dados: pd.DataFrame) -> pd.DataFrame:
    """Remove valores além de :data:`FATOR_EXTREMO`×IQR em `ano`/`km`."""
    fora_da_cerca = pd.Series(False, index=dados.index)
    for coluna in dic.NUMERICAS:
        q1, q3 = dados[coluna].quantile([0.25, 0.75])
        iqr = q3 - q1
        limites = (q1 - FATOR_EXTREMO * iqr, q3 + FATOR_EXTREMO * iqr)
        fora_da_cerca |= (dados[coluna] < limites[0]) | (dados[coluna] > limites[1])
    return dados[~fora_da_cerca]


def _remover_colunas_sem_informacao(dados: pd.DataFrame) -> pd.DataFrame:
    """Descarta coluna concentrada acima de :data:`LIMIAR_CONCENTRACAO` num valor.

    As colunas declaradas em :data:`COLUNAS_PROTEGIDAS` ficam mesmo quando
    passam do limiar.
    """
    concentracao = {}
    for coluna in dados.columns:
        preenchida = dados[coluna].dropna()
        if not len(preenchida):
            continue
        concentracao[coluna] = 100 * preenchida.value_counts(normalize=True).iloc[0]

    descartar = [
        coluna
        for coluna, pct in concentracao.items()
        if pct >= LIMIAR_CONCENTRACAO and coluna not in COLUNAS_PROTEGIDAS
    ]
    return dados.drop(columns=descartar)


def construir_base_curada(salvar: bool = True) -> pd.DataFrame:
    """Executa a preparação completa e devolve a base curada.

    A ordem dos passos é a do notebook `02-ajustes-dados`, que narra cada
    decisão. Os dois precisam produzir a mesma tabela.

    Args:
        salvar: quando ``True``, grava o parquet em ``data/processed/``.
    """
    bruto = carregar_bruto()
    curada = _remover_duplicados_reais(bruto)
    curada = _remover_falha_dataLayer(curada)
    curada = curada[curada["ano"].notna()]
    curada = _remover_km_sentinela(curada)
    curada = _rotular_ausencia_opcional(curada)
    curada = _derivar(curada)
    curada = _remover_km_implausivel(curada)
    curada = _aparar_desconto_implausivel(curada)
    curada = _remover_extremos(curada)
    curada = _remover_colunas_sem_informacao(curada)

    curada = curada.reset_index(drop=True)
    if salvar:
        config.garantir_diretorios()
        curada.to_parquet(config.BASE_CURADA, index=False)
    return curada


def construir_matriz_modelagem(curada: pd.DataFrame, salvar: bool = True) -> pd.DataFrame:
    """Recorta a matriz de modelagem — sem os rótulos reservados."""
    colunas = (
        dic.IDENTIFICADORES
        + dic.ESPACO_MISTO
        + [dic.RESERVADA_VALIDACAO, dic.ROTULO_RESERVADO, dic.RESERVADA_FIPE]
    )
    matriz = curada[[c for c in colunas if c in curada.columns]].copy()
    if salvar:
        matriz.to_parquet(config.MATRIZ_MODELAGEM, index=False)
    return matriz


def carregar_curada() -> pd.DataFrame:
    """Lê a base curada, construindo-a se ainda não existir."""
    if not config.BASE_CURADA.exists():
        return construir_base_curada()
    return pd.read_parquet(config.BASE_CURADA)


# --------------------------------------------------------------------------- #
# Espaços de atributos — CRISP-DM 3.5 (formatação e escala)
# --------------------------------------------------------------------------- #


def aplicar_log1p(matriz: np.ndarray, indices: list[int]) -> np.ndarray:
    """Aplica `log1p` às colunas indicadas pelos índices.

    Precisa ser uma função de módulo, e não uma função interna: o pipeline é
    serializado com `joblib` para a aplicação, e closure não é serializável.
    """
    saida = np.asarray(matriz, dtype=float).copy()
    if indices:
        saida[:, indices] = np.log1p(saida[:, indices])
    return saida


def _log1p_seletivo(colunas: list[str]) -> FunctionTransformer:
    """Aplica `log1p` apenas onde a assimetria medida na EDA justifica."""
    indices = [colunas.index(c) for c in dic.ASSIMETRICAS if c in colunas]
    return FunctionTransformer(
        aplicar_log1p, kw_args={"indices": indices}, feature_names_out="one-to-one"
    )


ESCALADORES = {
    "sem_escala": "passthrough",
    "minmax": MinMaxScaler(),
    "padrao": StandardScaler(),
    "robusto": RobustScaler(),
}


def construir_preprocessador(
    escalador: str = "padrao", com_nominais: bool = False
) -> Pipeline | ColumnTransformer:
    """Monta o pré-processador do espaço euclidiano.

    Args:
        escalador: uma das chaves de :data:`ESCALADORES`.
        com_nominais: quando ``True``, acrescenta as nominais em *one-hot* —
            usado para demonstrar a diluição do espaço euclidiano.
    """
    if escalador not in ESCALADORES:
        raise ValueError(f"Escalador desconhecido: {escalador}. Use {list(ESCALADORES)}.")

    numericas = dic.NUMERICAS + dic.BINARIAS
    passos_numericos = [("log", _log1p_seletivo(numericas))]
    escala = ESCALADORES[escalador]
    if escala != "passthrough":
        # Cada chamada precisa de uma instância própria: o mesmo objeto
        # reaproveitado guardaria as estatísticas do ajuste anterior.
        passos_numericos.append(("escala", type(escala)()))
    ramo_numerico = Pipeline(passos_numericos)

    if not com_nominais:
        return ColumnTransformer(
            [("num", ramo_numerico, numericas)], verbose_feature_names_out=False
        )

    return ColumnTransformer(
        [
            ("num", ramo_numerico, numericas),
            (
                "nom",
                OneHotEncoder(drop="if_binary", handle_unknown="ignore", sparse_output=False),
                dic.NOMINAIS,
            ),
        ],
        verbose_feature_names_out=False,
    )


def preparar_espaco(
    matriz: pd.DataFrame, escalador: str = "padrao", com_nominais: bool = False
) -> tuple[np.ndarray, list[str]]:
    """Aplica o pré-processador e devolve a matriz numérica e os nomes."""
    preprocessador = construir_preprocessador(escalador, com_nominais)
    transformada = preprocessador.fit_transform(matriz)
    nomes = list(preprocessador.get_feature_names_out())
    return np.asarray(transformada, dtype=float), nomes


if __name__ == "__main__":
    base = construir_base_curada()
    modelo = construir_matriz_modelagem(base)
    print(f"Base curada:         {base.shape[0]} x {base.shape[1]}")
    print(f"Matriz de modelagem: {modelo.shape[0]} x {modelo.shape[1]}")
    nulos = int(modelo[dic.ESPACO_MISTO].isna().sum().sum())
    print(f"Nulos na matriz (fora das reservadas): {nulos}")

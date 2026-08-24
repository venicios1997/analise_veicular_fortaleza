"""Aplicação Streamlit — Segmentação do mercado de veículos usados de Fortaleza.

Consome o pipeline treinado em `models/modelo-segmentacao.joblib`, o catálogo
de segmentos em `models/catalogo_de_segmentos.json` e a base classificada em
`data/processed/anuncios_segmentados.parquet` (todos gravados pelo notebook
`03-modelagem`). Não retreina nada — só classifica e explora o resultado.

Cinco abas: Sobre o projeto, Classificar anúncio (com comparação de margem
contra um preço de compra opcional), Catálogo de segmentos (filtrável, com
exportação em CSV), Oportunidades comerciais (com detalhamento por marca e
carroceria) e Mapa preço x km (também filtrável).

Execute com `uv run invoke app` ou `uv run streamlit run src/deployment/app.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import config  # noqa: E402
from src.utils import io  # noqa: E402


@st.cache_resource
def carregar_modelo():
    return joblib.load(config.PACOTE_APLICACAO)


@st.cache_data
def carregar_catalogo() -> dict:
    return io.ler_json(config.CATALOGO_DE_SEGMENTOS)


@st.cache_data
def carregar_base_segmentada() -> pd.DataFrame:
    return pd.read_parquet(config.BASE_SEGMENTADA)


def cartao_segmento(segmento: str, perfil: dict) -> None:
    st.metric("Segmento", segmento)
    col1, col2, col3 = st.columns(3)
    col1.metric("Preço mediano", f"R$ {perfil['preco_mediano']:,.0f}".replace(",", "."))
    col2.metric("Km mediana", f"{perfil['km_mediano']:,.0f} km".replace(",", "."))
    col3.metric("Idade mediana", f"{perfil['idade_mediana']:.0f} anos")

    col4, col5 = st.columns(2)
    col4.metric("Marca mais comum", perfil["marca_mais_comum"])
    col5.metric("Carroceria mais comum", perfil["carroceria_mais_comum"])

    desconto = perfil["desconto_fipe_medio_pct"]
    rotulo_desconto = "Desconto médio vs. FIPE" if desconto >= 0 else "Ágio médio vs. FIPE"
    st.metric(rotulo_desconto, f"{abs(desconto):.1f}%")
    resumo = f"{perfil['anuncios']:,} anúncios · {perfil['participacao_pct']:.1f}% da base"
    st.caption(resumo.replace(",", "."))


def grafico_distribuicao_segmento(
    base: pd.DataFrame, segmento: int, referencia: dict | None = None
):
    """Histogramas de preço e km do segmento, com marcador opcional de referência."""
    io.configurar_estilo()
    cor = config.PALETA_SEGMENTOS[segmento % len(config.PALETA_SEGMENTOS)]
    dados_segmento = base[base["segmento"] == segmento]

    fig, (ax_preco, ax_km) = plt.subplots(1, 2, figsize=(11, 4))

    sns.histplot(dados_segmento["preco"], bins=25, color=cor, ax=ax_preco)
    ax_preco.set_xlabel("Preço (R$)")
    ax_preco.set_title("Distribuição de preço")
    if referencia and "preco" in referencia:
        ax_preco.axvline(referencia["preco"], color=config.CORAL, ls="dashed", lw=2)

    sns.histplot(dados_segmento["km"], bins=25, color=cor, ax=ax_km)
    ax_km.set_xlabel("Quilometragem")
    ax_km.set_title("Distribuição de km")
    if referencia and "km" in referencia:
        ax_km.axvline(referencia["km"], color=config.CORAL, ls="dashed", lw=2)

    fig.tight_layout()
    return fig


def pagina_sobre(catalogo: dict, base: pd.DataFrame) -> None:
    st.header("Sobre o projeto")
    st.markdown(
        "**A dor:** uma pequena revenda de veículos usados tem capital limitado e "
        "precisa decidir quais carros comprar para revender. Essa decisão costuma "
        "ser baseada em experiência pessoal e preferência por marca — o que pode "
        "levar a capital parado em veículos de baixa procura e perda de "
        "oportunidades em segmentos com maior potencial."
    )
    st.markdown(
        "**A pergunta central:** quais segmentos de veículos usados existem no "
        "mercado de Fortaleza, e como usar essa segmentação para apoiar a decisão "
        "de composição de estoque de uma pequena revenda?"
    )

    st.divider()
    st.subheader("O modelo por trás do app")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Algoritmo", catalogo["algoritmo"])
    col2.metric("Segmentos", catalogo["n_segmentos"])
    col3.metric("Silhueta", f"{catalogo['silhueta']:.3f}")
    col4.metric("Anúncios na base", f"{len(base):,}".replace(",", "."))
    st.caption(
        "Segmentação por K-Means sobre `ano`, `km` e `zero_km` — o espaço "
        "numérico enxuto separou os grupos bem melhor do que incluir marca, "
        "câmbio e carroceria via one-hot (ver aba **Classificar anúncio**). "
        "Dados coletados via scraping da OLX em 21/08/2026."
    )

    st.divider()
    st.subheader("O que cada aba responde")
    st.markdown(
        "- **Classificar anúncio** — a que perfil de mercado pertence um carro "
        "com este ano/km específico?\n"
        "- **Catálogo de segmentos** — quais perfis existem e como cada um se "
        "comporta (preço, km, idade, marca típica)?\n"
        "- **Oportunidades comerciais** — qual segmento está, em média, mais "
        "abaixo da FIPE — ou seja, onde comprar relativamente barato?\n"
        "- **Mapa preço x km** — onde a oferta se concentra, com filtros por "
        "marca/carroceria/câmbio/preço."
    )
    st.caption(
        "Documentação completa (Canvas do Problema, EDA, preparação, avaliação) "
        "em `docs/` — sirva localmente com `uv run invoke docs`."
    )


def pagina_classificar(modelo, catalogo: dict, base: pd.DataFrame) -> None:
    st.header("Classificar um anúncio")
    st.write(
        "O modelo agrupa veículos por **ano** e **quilometragem** — as duas "
        "características que, isoladas de marca/câmbio/carroceria, produziram a "
        "segmentação com melhor separação (silhueta 0,54, contra ~0,10 quando as "
        "categóricas entravam em one-hot; ver notebook `03-modelagem`, seção "
        "*Sensibilidade ao espaço de atributos*)."
    )

    col1, col2 = st.columns(2)
    ano = col1.number_input("Ano do veículo", min_value=1950, max_value=2030, value=2020, step=1)
    km = col2.number_input(
        "Quilometragem", min_value=0, max_value=1_000_000, value=50_000, step=1000
    )
    preco_compra = st.number_input(
        "Preço de compra (opcional)",
        min_value=0,
        value=0,
        step=500,
        help="Se preenchido, compara com o preço mediano de venda do segmento.",
    )

    if st.button("Classificar", type="primary"):
        entrada = pd.DataFrame({"ano": [ano], "km": [km], "zero_km": [int(km == 0)]})
        segmento = int(modelo.predict(entrada)[0])
        perfil = catalogo["segmentos"][str(segmento)]

        st.divider()
        cartao_segmento(str(segmento), perfil)

        if preco_compra > 0:
            st.subheader("Comparação com o preço de venda do segmento")
            preco_venda_mediano = perfil["preco_mediano"]
            margem = preco_venda_mediano - preco_compra
            margem_pct = margem / preco_compra * 100

            col_a, col_b = st.columns(2)
            col_a.metric(
                "Margem estimada",
                f"R$ {margem:,.0f}".replace(",", "."),
                f"{margem_pct:+.1f}% sobre a compra",
            )
            venda_fmt = f"R$ {preco_venda_mediano:,.0f}".replace(",", ".")
            col_b.metric("Preço mediano de venda no segmento", venda_fmt)

            compra_fmt = f"R$ {preco_compra:,.0f}".replace(",", ".")
            if margem > 0:
                st.success(
                    f"Comprando por {compra_fmt} e vendendo pela mediana do "
                    f"segmento ({venda_fmt}), a margem estimada é de {margem_pct:.1f}%."
                )
            else:
                st.warning(
                    f"O preço de compra ({compra_fmt}) está acima da mediana de "
                    f"venda do segmento ({venda_fmt})"
                    " — margem estimada negativa."
                )
            st.caption(
                "Comparação com a mediana de venda do segmento inteiro, não com um "
                "anúncio específico — use a tabela de anúncios parecidos abaixo para "
                "uma referência mais próxima deste ano/km."
            )

        st.subheader("Onde o anúncio cai na distribuição do segmento")
        st.caption("A linha tracejada marca a quilometragem informada.")
        st.pyplot(grafico_distribuicao_segmento(base, segmento, referencia={"km": km}))

        st.subheader("Anúncios parecidos no mesmo segmento")
        parecidos = (
            base[base["segmento"] == segmento]
            .assign(diferenca_km=lambda d: (d["km"] - km).abs())
            .sort_values("diferenca_km")
            .head(10)
        )
        st.dataframe(
            parecidos[["titulo", "marca", "modelo", "ano", "km", "preco", "carroceria", "cambio"]],
            hide_index=True,
            width="stretch",
        )


COLUNAS_LISTA_ANUNCIOS = [
    "titulo",
    "marca",
    "modelo",
    "ano",
    "km",
    "preco",
    "carroceria",
    "cambio",
    "desconto_fipe_pct",
    "segmento",
    "link",
]


def botao_download_anuncios(df: pd.DataFrame, nome_arquivo: str, label: str) -> None:
    """Botão de download da lista de anúncios em CSV (separador ; para abrir bem no Excel PT-BR)."""
    colunas = [c for c in COLUNAS_LISTA_ANUNCIOS if c in df.columns]
    csv = df[colunas].to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(label, data=csv, file_name=nome_arquivo, mime="text/csv")


def tabela_catalogo(catalogo: dict) -> pd.DataFrame:
    linhas = [{"segmento": seg, **perfil} for seg, perfil in catalogo["segmentos"].items()]
    tabela = pd.DataFrame(linhas).sort_values("desconto_fipe_medio_pct", ascending=False)
    return tabela.rename(
        columns={
            "segmento": "Segmento",
            "anuncios": "Anúncios",
            "participacao_pct": "% da base",
            "preco_mediano": "Preço mediano",
            "km_mediano": "Km mediana",
            "idade_mediana": "Idade mediana",
            "desconto_fipe_medio_pct": "Desconto vs. FIPE (%)",
            "marca_mais_comum": "Marca mais comum",
            "carroceria_mais_comum": "Carroceria mais comum",
        }
    )


def pagina_catalogo(catalogo: dict, base: pd.DataFrame, base_filtrada: pd.DataFrame) -> None:
    st.header("Catálogo de segmentos")
    st.write(
        f"Modelo **{catalogo['algoritmo']}**, {catalogo['n_segmentos']} segmentos — "
        f"silhueta **{catalogo['silhueta']:.3f}**, Davies-Bouldin "
        f"**{catalogo['davies_bouldin']:.3f}**."
    )

    tabela = tabela_catalogo(catalogo)
    st.dataframe(tabela, hide_index=True, width="stretch")

    st.divider()
    st.subheader("Quantos anúncios filtrados caem em cada segmento?")
    st.caption(
        "Responde aos filtros da barra lateral — útil para ver onde um perfil de "
        "veículo se concentra."
    )
    if base_filtrada.empty:
        st.warning("Nenhum anúncio corresponde aos filtros selecionados.")
    else:
        contagem = base_filtrada["segmento"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(9, 3.5))
        cores = [config.PALETA_SEGMENTOS[s % len(config.PALETA_SEGMENTOS)] for s in contagem.index]
        ax.bar(contagem.index.astype(str), contagem.values, color=cores)
        ax.set_xlabel("Segmento")
        ax.set_ylabel("Anúncios no filtro")
        st.pyplot(fig)
        resumo_filtro = f"{len(base_filtrada):,} de {len(base):,} anúncios passam pelo filtro atual"
        st.caption(resumo_filtro.replace(",", "."))
        botao_download_anuncios(
            base_filtrada,
            "anuncios-filtrados.csv",
            "Baixar lista de anúncios do filtro atual (CSV)",
        )

    st.divider()
    st.subheader("Explorar a distribuição de um segmento")
    segmentos_disponiveis = sorted(base["segmento"].unique())
    escolhido = st.selectbox(
        "Segmento", segmentos_disponiveis, format_func=lambda s: f"Segmento {s}"
    )
    st.pyplot(grafico_distribuicao_segmento(base, escolhido))


MIN_ANUNCIOS_GRUPO = 5


def pagina_oportunidades(catalogo: dict, base: pd.DataFrame) -> None:
    st.header("Oportunidades comerciais")
    st.write(
        "Segmentos ordenados pelo **desconto médio sobre a FIPE** — quanto maior, "
        "mais a oferta está, em média, abaixo do valor de referência de mercado "
        "(potencial de compra vantajosa para revenda)."
    )

    tabela = tabela_catalogo(catalogo)
    melhor = tabela.iloc[0]
    st.success(
        f"**Melhor oportunidade:** segmento {melhor['Segmento']} — "
        f"desconto médio de {melhor['Desconto vs. FIPE (%)']:.1f}% sobre a FIPE, "
        f"{melhor['Anúncios']} anúncios ({melhor['% da base']:.1f}% da base)."
    )

    io.configurar_estilo()
    fig, ax = plt.subplots(figsize=(9, 4))
    cores = [
        config.PALETA_SEGMENTOS[int(s) % len(config.PALETA_SEGMENTOS)] for s in tabela["Segmento"]
    ]
    ax.barh(tabela["Segmento"].astype(str), tabela["Desconto vs. FIPE (%)"], color=cores)
    ax.axvline(0, color=config.CINZA, lw=1)
    ax.set_xlabel("Desconto médio vs. FIPE (%) — negativo é ágio")
    ax.set_ylabel("Segmento")
    ax.invert_yaxis()
    st.pyplot(fig)

    st.dataframe(
        tabela[
            [
                "Segmento",
                "Anúncios",
                "% da base",
                "Preço mediano",
                "Km mediana",
                "Idade mediana",
                "Desconto vs. FIPE (%)",
                "Marca mais comum",
                "Carroceria mais comum",
            ]
        ],
        hide_index=True,
        width="stretch",
    )

    st.divider()
    with st.expander("Detalhar por marca e carroceria dentro de um segmento"):
        st.caption(
            "O desconto médio do segmento inteiro esconde variação por marca/carroceria — "
            f"aqui o recorte é mais fino (mínimo de {MIN_ANUNCIOS_GRUPO} anúncios por grupo, "
            "para não destacar combinações raras demais para confiar)."
        )
        segmentos_disponiveis = sorted(base["segmento"].unique())
        escolhido = st.selectbox(
            "Segmento",
            segmentos_disponiveis,
            format_func=lambda s: f"Segmento {s}",
            key="segmento_oportunidades",
        )

        dados_segmento = base[base["segmento"] == escolhido]
        ranking = (
            dados_segmento.groupby(["marca", "carroceria"], observed=True)
            .agg(
                anuncios=("preco", "size"),
                desconto_medio_pct=("desconto_fipe_pct", "mean"),
                preco_mediano=("preco", "median"),
            )
            .query("anuncios >= @MIN_ANUNCIOS_GRUPO")
            .sort_values("desconto_medio_pct", ascending=False)
            .reset_index()
        )

        if ranking.empty:
            st.info(
                "Nenhuma combinação de marca/carroceria com pelo menos "
                f"{MIN_ANUNCIOS_GRUPO} anúncios neste segmento."
            )
        else:
            tabela_ranking = ranking.rename(
                columns={
                    "marca": "Marca",
                    "carroceria": "Carroceria",
                    "anuncios": "Anúncios",
                    "desconto_medio_pct": "Desconto vs. FIPE (%)",
                    "preco_mediano": "Preço mediano",
                }
            )
            st.dataframe(tabela_ranking, hide_index=True, width="stretch")
            botao_download_anuncios(
                dados_segmento,
                f"anuncios-segmento-{escolhido}.csv",
                f"Baixar lista de anúncios do segmento {escolhido} (CSV)",
            )


def pagina_mapa(base_filtrada: pd.DataFrame) -> None:
    st.header("Mapa preço x quilometragem")
    st.write(
        "Cada ponto é um anúncio; a cor é o segmento atribuído pelo modelo. "
        "Use os filtros na barra lateral."
    )

    if base_filtrada.empty:
        st.warning("Nenhum anúncio corresponde aos filtros selecionados.")
        return

    io.configurar_estilo()
    fig, ax = plt.subplots(figsize=(9, 5))
    ordem = sorted(base_filtrada["segmento"].unique())
    sns.scatterplot(
        data=base_filtrada,
        x="km",
        y="preco",
        hue="segmento",
        hue_order=ordem,
        palette=[config.PALETA_SEGMENTOS[s % len(config.PALETA_SEGMENTOS)] for s in ordem],
        alpha=0.6,
        s=25,
        ax=ax,
    )
    ax.set_xlabel("Quilometragem")
    ax.set_ylabel("Preço (R$)")
    ax.legend(title="Segmento", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig)
    st.caption(f"{len(base_filtrada):,} anúncios exibidos".replace(",", "."))


def filtros_sidebar(base: pd.DataFrame) -> pd.DataFrame:
    """Filtros globais (marca, carroceria, câmbio, faixa de preço) do mapa e do catálogo."""
    st.sidebar.header("Filtros")
    st.sidebar.caption("Afetam apenas as abas **Catálogo de segmentos** e **Mapa preço x km**.")
    marcas = st.sidebar.multiselect("Marca", sorted(base["marca"].unique()))
    carrocerias = st.sidebar.multiselect("Carroceria", sorted(base["carroceria"].unique()))
    cambios = st.sidebar.multiselect("Câmbio", sorted(base["cambio"].unique()))

    preco_min, preco_max = int(base["preco"].min()), int(base["preco"].max())
    faixa_preco = st.sidebar.slider(
        "Faixa de preço (R$)", preco_min, preco_max, (preco_min, preco_max), step=1000
    )

    filtrada = base
    if marcas:
        filtrada = filtrada[filtrada["marca"].isin(marcas)]
    if carrocerias:
        filtrada = filtrada[filtrada["carroceria"].isin(carrocerias)]
    if cambios:
        filtrada = filtrada[filtrada["cambio"].isin(cambios)]
    filtrada = filtrada[filtrada["preco"].between(*faixa_preco)]

    if marcas or carrocerias or cambios or faixa_preco != (preco_min, preco_max):
        resumo = f"{len(filtrada):,} de {len(base):,} anúncios no filtro"
        st.sidebar.caption(resumo.replace(",", "."))

    return filtrada


def main() -> None:
    st.set_page_config(
        page_title="Segmentação de veículos — Fortaleza",
        page_icon="🚗",
        layout="wide",
    )
    st.title("Segmentação do mercado de veículos usados de Fortaleza")
    st.caption(
        "Apoio à decisão de composição de estoque para pequenas revendas — "
        "MBA em Ciência de Dados, aprendizado não supervisionado."
    )

    if not config.PACOTE_APLICACAO.exists():
        st.error(
            f"Modelo não encontrado em `{config.PACOTE_APLICACAO}`. "
            "Rode o notebook `03-modelagem.ipynb` antes de abrir a aplicação."
        )
        st.stop()

    modelo = carregar_modelo()
    catalogo = carregar_catalogo()
    base = carregar_base_segmentada()
    base_filtrada = filtros_sidebar(base)

    aba_sobre, aba_classificar, aba_catalogo, aba_oportunidades, aba_mapa = st.tabs(
        [
            "Sobre o projeto",
            "Classificar anúncio",
            "Catálogo de segmentos",
            "Oportunidades comerciais",
            "Mapa preço x km",
        ]
    )
    with aba_sobre:
        pagina_sobre(catalogo, base)
    with aba_classificar:
        pagina_classificar(modelo, catalogo, base)
    with aba_catalogo:
        pagina_catalogo(catalogo, base, base_filtrada)
    with aba_oportunidades:
        pagina_oportunidades(catalogo, base)
    with aba_mapa:
        pagina_mapa(base_filtrada)


if __name__ == "__main__":
    main()

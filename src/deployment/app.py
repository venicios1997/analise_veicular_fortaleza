"""Aplicação Streamlit — Segmentação do mercado de veículos usados de Fortaleza.

Consome o pipeline treinado em `models/modelo-segmentacao.joblib` (gravado pelo
notebook `03-modelagem`) e o catálogo de segmentos em
`models/catalogo_de_segmentos.json`. Não retreina nada — só classifica.

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

from src import config
from src.utils import io


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
    st.caption(f"{perfil['anuncios']:,} anúncios · {perfil['participacao_pct']:.1f}% da base".replace(",", "."))


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
    km = col2.number_input("Quilometragem", min_value=0, max_value=1_000_000, value=50_000, step=1000)

    if st.button("Classificar", type="primary"):
        entrada = pd.DataFrame({"ano": [ano], "km": [km], "zero_km": [int(km == 0)]})
        segmento = int(modelo.predict(entrada)[0])
        perfil = catalogo["segmentos"][str(segmento)]

        st.divider()
        cartao_segmento(str(segmento), perfil)

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


def pagina_catalogo(catalogo: dict) -> None:
    st.header("Catálogo de segmentos")
    st.write(
        f"Modelo **{catalogo['algoritmo']}**, {catalogo['n_segmentos']} segmentos — "
        f"silhueta **{catalogo['silhueta']:.3f}**, Davies-Bouldin "
        f"**{catalogo['davies_bouldin']:.3f}**."
    )

    linhas = [
        {"segmento": seg, **perfil} for seg, perfil in catalogo["segmentos"].items()
    ]
    tabela = pd.DataFrame(linhas).sort_values("desconto_fipe_medio_pct", ascending=False)
    tabela = tabela.rename(
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
    st.dataframe(tabela, hide_index=True, width="stretch")

    melhor = tabela.iloc[0]
    st.success(
        f"**Melhor oportunidade comercial:** segmento {melhor['Segmento']} — "
        f"desconto médio de {melhor['Desconto vs. FIPE (%)']:.1f}% sobre a FIPE, "
        f"{melhor['Anúncios']} anúncios ({melhor['% da base']:.1f}% da base)."
    )


def pagina_mapa(base: pd.DataFrame) -> None:
    st.header("Mapa preço x quilometragem")
    st.write("Cada ponto é um anúncio; a cor é o segmento atribuído pelo modelo.")

    io.configurar_estilo()
    fig, ax = plt.subplots(figsize=(9, 5))
    ordem = sorted(base["segmento"].unique())
    sns.scatterplot(
        data=base, x="km", y="preco", hue="segmento", hue_order=ordem,
        palette=config.PALETA_SEGMENTOS[: len(ordem)], alpha=0.6, s=25, ax=ax,
    )
    ax.set_xlabel("Quilometragem")
    ax.set_ylabel("Preço (R$)")
    ax.legend(title="Segmento", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig)


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

    aba_classificar, aba_catalogo, aba_mapa = st.tabs(
        ["Classificar anúncio", "Catálogo de segmentos", "Mapa preço x km"]
    )
    with aba_classificar:
        pagina_classificar(modelo, catalogo, base)
    with aba_catalogo:
        pagina_catalogo(catalogo)
    with aba_mapa:
        pagina_mapa(base)


if __name__ == "__main__":
    main()

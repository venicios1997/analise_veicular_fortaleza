import pandas as pd
import streamlit as st
from matcher import avaliar_anuncios
from scraper import LocalizacaoNaoEncontrada, buscar_anuncios, enriquecer_com_fipe_olx

st.set_page_config(page_title="Carros OLX x FIPE", layout="wide")
st.title("Buscador de carros na OLX x Tabela FIPE")
st.caption(
    "Informe a faixa de preço e a localização. O app busca os anúncios na OLX "
    "e cruza cada carro com a Tabela FIPE para mostrar quais estão mais baratos "
    "em relação ao valor de referência (melhores oportunidades no topo). "
    "A comparação usa o valor de FIPE que a própria OLX mostra em cada anúncio "
    "(mais preciso); o valor da API pública da FIPE é exibido como referência extra."
)

with st.form("busca"):
    col1, col2 = st.columns(2)
    preco_min = col1.number_input("Preço mínimo (R$)", min_value=0, value=20000, step=1000)
    preco_max = col2.number_input("Preço máximo (R$)", min_value=0, value=50000, step=1000)
    localizacao = st.text_input("Localização (cidade, bairro ou estado)", value="Fortaleza, CE")
    max_paginas = st.slider(
        "Quantidade de páginas a buscar (50 anúncios por página)",
        min_value=1,
        max_value=10,
        value=3,
    )
    enviado = st.form_submit_button("Buscar")

if enviado:
    if preco_min > preco_max:
        st.error("O preço mínimo não pode ser maior que o preço máximo.")
        st.stop()

    status = st.empty()
    barra = st.progress(0.0)

    def progresso_scraper(pagina, total, n_anuncios):
        status.text(f"Buscando na OLX... página {pagina}/{total} ({n_anuncios} anúncios coletados)")
        barra.progress(pagina / total * 0.3)

    try:
        with st.spinner("Abrindo navegador e buscando na OLX..."):
            anuncios = buscar_anuncios(
                preco_min=int(preco_min),
                preco_max=int(preco_max),
                localizacao=localizacao,
                max_paginas=max_paginas,
                progresso=progresso_scraper,
            )
    except LocalizacaoNaoEncontrada as e:
        status.empty()
        barra.empty()
        st.error(str(e))
        st.stop()

    if not anuncios:
        status.empty()
        barra.empty()
        st.warning("Nenhum anúncio encontrado para esses filtros.")
        st.stop()

    def progresso_fipe_olx(i, total):
        status.text(f"Consultando FIPE da OLX em cada anúncio... {i}/{total}")
        barra.progress(0.3 + i / total * 0.4)

    with st.spinner("Abrindo cada anúncio para pegar o valor FIPE da OLX..."):
        anuncios = enriquecer_com_fipe_olx(anuncios, progresso=progresso_fipe_olx)

    def progresso_fipe_api(i, total):
        status.text(f"Consultando API pública da FIPE (referência extra)... {i}/{total}")
        barra.progress(0.7 + i / total * 0.3)

    with st.spinner("Consultando a API pública da FIPE..."):
        avaliacoes = avaliar_anuncios(anuncios, progresso=progresso_fipe_api)

    status.empty()
    barra.empty()

    linhas = []
    for av in avaliacoes:
        a = av.anuncio
        valor_principal = a.valor_fipe_olx if a.valor_fipe_olx else av.valor_fipe
        fonte = "OLX" if a.valor_fipe_olx else ("API" if av.valor_fipe else None)
        diferenca_pct = (
            round((valor_principal - a.preco) / valor_principal * 100, 1)
            if valor_principal
            else None
        )
        linhas.append(
            {
                "Anúncio": a.titulo,
                "Ano": a.ano,
                "Preço OLX (R$)": a.preco,
                "Valor FIPE (R$)": valor_principal,
                "Fonte FIPE": fonte,
                "Diferença vs FIPE (%)": diferenca_pct,
                "Valor FIPE OLX (R$)": a.valor_fipe_olx,
                "Valor FIPE API (R$)": av.valor_fipe,
                "KM": a.km,
                "Localização": a.localizacao,
                "Status FIPE (API)": av.status,
                "Link": a.link,
            }
        )

    def fmt_brl(v):
        return f"R$ {v:,.0f}".replace(",", ".") if pd.notna(v) else ""

    df = pd.DataFrame(linhas)
    for col in ["Valor FIPE (R$)", "Diferença vs FIPE (%)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # colunas de referência: formatadas como texto (NumberColumn exibe "None"
    # para células vazias quando a coluna tem NaN misturado com valores)
    df["Valor FIPE OLX (R$)"] = df["Valor FIPE OLX (R$)"].apply(fmt_brl)
    df["Valor FIPE API (R$)"] = df["Valor FIPE API (R$)"].apply(fmt_brl)

    df = df.sort_values(
        by="Diferença vs FIPE (%)", ascending=False, na_position="last"
    ).reset_index(drop=True)

    n_com_fipe = df["Diferença vs FIPE (%)"].notna().sum()
    n_com_fipe_olx = (df["Valor FIPE OLX (R$)"] != "").sum()
    st.success(
        f"{len(df)} anúncios encontrados — {n_com_fipe} com valor de FIPE "
        f"({n_com_fipe_olx} direto da OLX, o restante pela API pública)."
    )

    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Preço OLX (R$)": st.column_config.NumberColumn(format="R$ %.0f"),
            "Valor FIPE (R$)": st.column_config.NumberColumn(
                format="R$ %.0f",
                help="Valor usado para o ranking: prioriza a FIPE mostrada pela "
                "própria OLX no anúncio; usa a API pública como alternativa "
                "quando a OLX não mostra FIPE para aquele anúncio.",
            ),
            "Diferença vs FIPE (%)": st.column_config.NumberColumn(
                format="%.1f%%",
                help="Positivo = anúncio mais barato que a FIPE (bom negócio). "
                "Negativo = anúncio mais caro que a FIPE.",
            ),
            "Valor FIPE OLX (R$)": st.column_config.TextColumn(),
            "Valor FIPE API (R$)": st.column_config.TextColumn(),
            "Link": st.column_config.LinkColumn(display_text="Ver anúncio"),
        },
        hide_index=True,
    )

    st.download_button(
        "Baixar CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name="carros_olx_fipe.csv",
        mime="text/csv",
    )

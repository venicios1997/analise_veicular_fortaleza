# Análise exploratória

Esta página resume **o desenho** da análise exploratória: quais notebooks existem, o que cada
um responde e as decisões metodológicas que valem para todos. Os resultados em si ficam nas
figuras de `reports/figures/eda-exploratoria/` e nas tabelas de `reports/tables/eda-exploratoria/`.

## Mapa dos notebooks

| Notebook | Objetivo | Recorte | Saída principal |
|:---|:-:|:---|:---|
| `00-dicionario-dados.ipynb` | 1, 2 | as 23 colunas brutas | `data/processed/dicionario.csv` |
| `01-analise-exploratoria.ipynb` | 1, 2 | espaço de atributos + reservadas (14 colunas) | figuras e tabelas de `reports/*/eda-exploratoria/` |

A coluna **Objetivo** referencia a numeração dos [critérios de sucesso](criterios-sucesso.md).

## Desenho da EDA

O notebook `01-analise-exploratoria.ipynb` segue um roteiro de **8 etapas**, aplicado
sobre `ano`, `km`, as 9 nominais do espaço de atributos e as 3 reservadas (`preco`,
`bairro`, `valor_fipe_final`) — a mesma coluna que a análise de negócio usa depois,
sem recorte adicional (a base bruta já tem só 23 colunas).

| Seção | Técnica | O que responde |
|:---|:---|:---|
| Distribuição/perfil | contagens de nulos, duplicados, cardinalidade | como a base se compõe antes de qualquer ajuste? |
| Univariada — nominais | frequência das categorias mais comuns | quais categorias concentram carteira? |
| Univariada — numéricas | extremos, histograma, dispersão, caixa | como `ano`/`km`/`preco`/`valor_fipe_final` se distribuem? |
| Bivariada | média por categoria (marca, carroceria, câmbio, vendedor) | quais eixos de negócio separam preço/km/ano? |
| Multivariada | análise de correspondência (`prince.CA`) + empacotamento de círculos | quais categorias nominais andam juntas? |
| Valores ausentes | % de célula vazia por coluna | onde falta dado, e é falha de captura ou ausência real? |
| Valores discrepantes | critério de Tukey (IQR × 1,5) | há valor implausível em `preco`/`km`/`ano`/`valor_fipe_final`? |
| Correlação | Spearman (numérica×numérica), V de Cramér (nominal×nominal), η (nominal×numérica) | quais variáveis são redundantes? |

Duas etapas deste roteiro **não se
aplicam** aqui, e por isso ficam de fora: características **ordinais** (esta
base não declara nenhuma escala do tipo `Ex > Gd > TA`) e características de
**tempo** (a coleta é de um único dia — `data_coleta` tem 1 valor distinto).

## Escolhas metodológicas

- **Mesclagem da FIPE dentro da EDA, não na ingestão**: diferente de um projeto
  que consome uma base pública pronta, aqui a análise exploratória é também o
  lugar onde `valor_fipe_olx` (90,7% de cobertura) é mesclada com o resultado
  da API pública (`fipe_fallback.csv`), subindo a cobertura para 97,1% — decisão
  registrada porque a mesclagem já é, em si, um achado de qualidade de dado.
- **3 reservadas, não 1**: além do rótulo (`preco`) e da variável de validação
  externa (`bairro`), `valor_fipe_final` também fica reservada — é derivada de
  marca/modelo/ano e entraria na modelagem de forma redundante; serve só para
  medir desconto/oportunidade *a posteriori*.
- **Correspondência em vez de tabela de contingência bruta**: `marca` tem 41
  categorias e `carroceria`, 10 — a tabela cruzada seria dominada pelas
  combinações mais frequentes. A análise de correspondência projeta linhas e
  colunas num plano de 2 dimensões, com corte de inércia acumulada ≥ 80% para
  decidir se o plano é interpretável.
- **3×IQR fica para a fase de preparação**, não para a EDA: aqui só se
  **detecta** o discrepante (critério clássico de Tukey, 1,5×IQR); a decisão
  de remover ou não — e com qual fator — é tomada com evidência de negócio em
  `02-ajustes-dados.ipynb`.

## Coleção de insights

Os seis achados que a EDA deixou, com o número que sustenta cada um — é esta
lista que a fase de preparação (`02-ajustes-dados`) consome, e que gerou tabela
em `reports/tables/eda-exploratoria/insights.csv`.

1. **`km` tem um registro de 999.998** — muito acima do limite superior de
   Tukey (265.000) e visivelmente um valor de preenchimento/erro de digitação,
   não um carro real. Removido em `02-ajustes-dados`.
2. **`preco` e `valor_fipe_final` correlacionam em 0,98** (Spearman) — a FIPE
   mesclada é, por construção, quase um espelho do preço pedido. Confirma por
   que ela fica reservada da modelagem, e não descartada por redundância
   (ambas já são reservadas).
3. **Câmbio separa o mercado com força**, mesmo antes de qualquer
   clusterização: automático custa em média R$ 120 mil com 68 mil km
   rodados, contra R$ 42,5 mil e 113 mil km do manual.
4. **O desconto médio sobre a FIPE varia por marca**: Peugeot (13,3%),
   Citroën (8,3%) e Chery (8,2%) no topo; BYD é a única marca com desconto
   negativo (−9,3%, anunciada acima da FIPE) — primeira leitura de
   oportunidade comercial (Pergunta 5 do [Canvas do Problema](canvas-do-problema.md)).
5. **Lojas profissionais concentram veículos com menor km** (74 mil contra 130
   mil de particulares), mas desconto médio negativo sobre a FIPE (−2,0%);
   particulares vendem com desconto médio positivo (+1,9%) — menor km e
   melhor preço vs. FIPE não andam juntos no mesmo canal de venda.
6. **`aceita_troca` (27,4%) e `unico_dono` (18,7%) são as colunas com mais
   ausência** — esperado, dependem do anunciante informar. A mescla com a
   API pública reduz a ausência de FIPE de 9,3% para 2,9%.

## Reprodução

```bash
# executa os notebooks 00-03 em ordem e falha se algum quebrar
uv run invoke notebooks
```

Os notebooks são versionados **com saída** neste repositório (diferente da
convenção `nbstripout`) — cada figura relevante também é persistida em
`reports/figures/eda-exploratoria/` e a tabela que a originou em
`reports/tables/eda-exploratoria/`, gravadas juntas por
`src.utils.io.salvar_figura`, para que o dado nunca divirja do gráfico.

## Dados por trás de cada gráfico

Toda figura é salva por `io.salvar_figura(fig, secao, nome, dados)`, que grava
o `.png` em `reports/figures/<secao>/` e, quando `dados` é informado, o CSV de
origem em `reports/tables/<secao>/<nome>.csv` — separador `;`, decimal `,`
(abre direto no Excel em português).

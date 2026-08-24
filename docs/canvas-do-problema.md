# Canvas do Problema

Documento de planejamento do projeto — definido **antes** da coleta e da
análise, e mantido aqui sem retrospectiva: o que o modelo efetivamente entregou
está em [Avaliação dos resultados](avaliacao.md).

## 1. Contexto de negócio

**Organização:** mercado de revenda de veículos usados e seminovos de
Fortaleza-CE. O mercado é composto por lojas, revendedores independentes e
vendedores particulares que anunciam veículos em plataformas digitais.

A análise foi realizada sobre anúncios de veículos disponíveis para venda,
considerando características como preço, ano, quilometragem, marca, modelo,
motorização, carroceria, câmbio, combustível, localização e tipo de vendedor.

A decisão de negócio relacionada ao estudo é:

> **Quais tipos de veículos uma pequena revenda deveria priorizar para compra e
> revenda em Fortaleza?**

## 2. A dor

Uma pequena revenda possui recursos financeiros limitados e precisa decidir
quais veículos comprar para compor seu estoque. Essa decisão costuma ser
baseada em experiência pessoal, percepção do vendedor, preferência por
determinadas marcas, histórico individual de vendas e percepção sobre "o que
vende mais" — o que pode levar a capital parado em veículos de baixa procura,
dificuldade de venda, necessidade de reduzir preço, menor margem de lucro e
perda de oportunidades em segmentos com maior potencial.

**Quem sofre com isso:** pequenos revendedores, lojas independentes, vendedores
autônomos e investidores que compram veículos para revenda.

## 3. Objetivo de negócio

> **Identificar segmentos de veículos com características semelhantes no
> mercado de Fortaleza, permitindo que pequenas revendas direcionem melhor
> seus recursos para aquisição de veículos e composição de estoque.**

O objetivo é apoiar uma decisão de negócio: **melhorar a seleção dos veículos
que serão adquiridos para revenda**.

## 4. Critério de sucesso do negócio

O projeto seria considerado bem-sucedido se conseguisse identificar segmentos
de veículos claramente distintos e interpretáveis, utilizáveis para apoiar
decisões de aquisição e composição de estoque.

### Metas propostas

- [x] Identificar entre **4 e 8 segmentos** de veículos — obtido: **5**
- [x] Obter segmentos com características claramente diferenciadas
- [x] Permitir uma interpretação comercial para cada segmento
- [x] Identificar pelo menos **2 potenciais oportunidades comerciais** — obtido: segmentos 3 e 2 (ver [Avaliação dos resultados](avaliacao.md))

## 5. Meta de mineração

### Objetivo técnico

> **Identificar agrupamentos naturais de veículos existentes no mercado de
> Fortaleza a partir de suas características comerciais e técnicas.**

### Técnicas de aprendizado não supervisionado

Algoritmos candidatos: **K-Means**, **Hierarchical Clustering**, **DBSCAN**.
Também poderia ser utilizado **PCA** para redução de dimensionalidade e
visualização. Os grupos não foram definidos previamente — o algoritmo
identificou os padrões presentes nos próprios dados (ver
[Modelagem dos dados](modelagem.md)).

## 6. Critério de sucesso técnico

Obter uma solução de clusterização com número de grupos entre **4 e 8**, boa
separação entre os clusters e baixo grau de sobreposição.

### Métricas sugeridas

Silhouette Score, Davies-Bouldin Index e, eventualmente, Calinski-Harabasz
Index.

### Meta preliminar

- [x] Silhouette Score ≥ **0,40** — obtido: **0,542**
- [x] Nenhum cluster excessivamente pequeno — menor segmento: 60 anúncios
- [x] Clusters comercialmente interpretáveis
- [ ] Estabilidade razoável dos agrupamentos sob reamostragem — avaliada por
  `ShuffleSplit` na seleção do algoritmo, não como estabilidade formal
  (ex.: Índice de Rand Ajustado) do modelo final
- [x] Ausência de agrupamentos formados apenas por outliers ou ruído

## 7. Entidade de análise

A unidade de análise é:

> **Um anúncio de veículo usado ou seminovo disponível para venda em
> Fortaleza-CE.**

Cada linha da base representa um anúncio.

## 8. Fonte e volume dos dados

### Fontes

- **OLX** — fonte efetivamente usada (ver [Fonte dos dados](fonte-dados.md)).
- iCarros e outras plataformas foram consideradas no planejamento, mas não
  usadas — a OLX sozinha já atingiu a meta de volume.

### Variáveis desejadas

Identificação (marca, modelo, versão), características técnicas (ano,
quilometragem, motorização, câmbio, carroceria, combustível) e características
comerciais (preço, tipo de vendedor, localização/bairro, indicação de troca,
data de coleta) — todas coletadas. Detalhamento completo em
[Entendimento dos dados](entendimento-dados.md).

### Volume desejado

> **1.000 a 5.000 anúncios** — obtido: **2.565** anúncios brutos, **2.479**
> após a limpeza (ver [Preparação dos dados](preparacao.md)).

### Atenção metodológica

O projeto analisa principalmente **oferta/anúncios**, não demanda efetiva.
Quantidade de anúncios de determinado veículo não significa necessariamente
maior demanda por ele; preço anunciado não é necessariamente igual ao preço
efetivamente vendido. Essas limitações foram consideradas na interpretação dos
resultados (ver [Entendimento dos dados — Limitações](entendimento-dados.md#limitacoes)).

## 9. Perguntas orientadas a dados

### Pergunta 1

> Quais segmentos de veículos podem ser identificados automaticamente a partir
> das características dos anúncios de Fortaleza?

**Resposta:** 5 segmentos, obtidos por K-Means sobre `ano`/`km`/`zero_km`
(silhueta 0,542). Ver [Modelagem dos dados](modelagem.md).

### Pergunta 2

> Quais características são mais importantes para diferenciar os segmentos
> encontrados?

**Resposta:** ano e quilometragem (as variáveis usadas na clusterização), lidos
em conjunto com câmbio, marca e carroceria (que não entraram no algoritmo, mas
diferenciam os segmentos na leitura de negócio). Ver
[Modelagem dos dados — Interpretação do resultado](modelagem.md#interpretacao-do-resultado).

### Pergunta 3

> Quais segmentos concentram veículos de menor preço e maior quilometragem?

**Resposta:** o segmento 0 (populares antigos: R$ 15,0 mil, 163 mil km, 24 anos
de idade mediana). Ver [Avaliação dos resultados](avaliacao.md).

### Pergunta 4

> Quais segmentos apresentam maior concentração de veículos dentro de
> determinadas faixas de preço?

**Resposta:** os segmentos 2 e 3 concentram juntos 82,6% da base — seminovos
recentes (R$ 99,5 mil) e populares usados (R$ 41,9 mil). Ver
`reports/tables/modelagem/perfil-dos-segmentos.csv`.

### Pergunta 5

> Quais segmentos representam potenciais oportunidades para uma pequena
> revenda de veículos em Fortaleza?

**Resposta:** o segmento 3 (populares usados) tem desconto médio de **+3,0%**
sobre a FIPE — a única leitura de desconto positivo entre os 5 segmentos — e
41,5% da base, a maior participação de mercado. Ver
[Avaliação dos resultados](avaliacao.md) e a aba "Oportunidades comerciais" da
aplicação, que também detalha o desconto médio por marca e carroceria dentro
de cada segmento.

## 10. Restrições e riscos

### Qualidade dos dados

Anúncios podem estar duplicados, preços podem estar incorretos, anúncios podem
estar desatualizados, quilometragem pode não ser confiável, características
podem estar ausentes, vendedores podem usar padrões de descrição diferentes,
determinados modelos podem ter poucos registros. **Tratado** em
[Preparação dos dados](preparacao.md) — duplicados removidos, ausência
tratada por natureza, `km` com sentinela removido, marcas raras agrupadas.

### Riscos metodológicos

Escolha inadequada do número de clusters, variáveis com escalas muito
diferentes, influência excessiva de outliers, clusters pouco interpretáveis,
alta correlação entre variáveis, codificação inadequada de categóricas,
concentração excessiva de marcas/modelos. **Tratado** em
[Modelagem dos dados](modelagem.md) — a seção "Sensibilidade ao espaço de
atributos" é a resposta direta ao risco de codificação inadequada de
categóricas (o one-hot ingênuo derrubava a silhueta em ~5×).

### Riscos relacionados ao negócio

Preço anunciado não representa necessariamente preço de venda; número de
anúncios não representa necessariamente demanda; muitos anúncios podem
indicar concorrência elevada, não oportunidade; velocidade de venda não está
disponível; os resultados representam um recorte temporal do mercado (coleta
de 21/08/2026). **Registrado** como limitação declarada em
[Entendimento dos dados](entendimento-dados.md#limitacoes), não escondido nem
contornado.

## 11. Ação esperada por grupo

O resultado da clusterização apoia a **seleção de veículos para aquisição e
composição do estoque de uma pequena revenda**. Cada grupo recebeu uma
interpretação comercial — ver a tabela real (não mais hipotética) em
[Avaliação dos resultados](avaliacao.md).

## Proposta de análise

```text
Coleta dos anúncios
        ↓
Tratamento e limpeza dos dados
        ↓
Análise exploratória
        ↓
Seleção das variáveis
        ↓
Tratamento de variáveis categóricas
        ↓
Normalização/Padronização
        ↓
Tratamento de outliers
        ↓
K-Means / Hierárquico / Bisecting / Birch
        ↓
Avaliação dos clusters
        ↓
Interpretação comercial
        ↓
Identificação de oportunidades
        ↓
Recomendação para composição de estoque
```

Seguida integralmente — o único desvio foi não usar PCA (a comparação de
espaços de atributos mostrou que reduzir para 3 variáveis numéricas já bastava,
sem precisar de componentes principais) nem DBSCAN (não estava entre os 4
algoritmos comparados no notebook `03-modelagem`, que priorizou K-Means e
variantes por serem mais adequados a um espaço puramente numérico e de baixa
dimensão).

## Título e hipótese

## Segmentação do Mercado de Veículos Usados de Fortaleza por meio de Aprendizado de Máquina Não Supervisionado para Apoio à Decisão de Composição de Estoque

> **Pergunta central:** Quais segmentos de veículos usados apresentam
> características semelhantes no mercado de Fortaleza e como essa segmentação
> pode apoiar a decisão de aquisição de estoque de uma pequena revenda?

> **Hipótese de negócio:** a identificação de segmentos de veículos por meio de
> técnicas de aprendizado de máquina não supervisionado pode revelar padrões do
> mercado que auxiliem pequenas revendas a direcionar seus recursos para grupos
> de veículos mais adequados à sua estratégia de estoque.

Confirmada — ver [Avaliação dos resultados](avaliacao.md) para o confronto
completo com os critérios de aceite.

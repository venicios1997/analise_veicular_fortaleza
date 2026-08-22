# Modelagem dos dados

Esta página descreve **o desenho do experimento de modelagem**: qual problema o modelo
resolve, sobre que unidade de análise ele opera, quais variáveis entram, qual técnica foi
escolhida e como o resultado é avaliado.

O único objetivo que exige modelagem é o Objetivo 1 dos
[critérios de sucesso](criterios-sucesso.md) — segmentar a carteira de anúncios.
Os objetivos 2 e 3 (leitura comercial, aplicação) consomem o resultado, mas não
treinam nada de novo.

## Problema

Identificar agrupamentos naturais de veículos existentes no mercado de
Fortaleza a partir de suas características comerciais e técnicas — sem definir
os grupos previamente (aprendizado não supervisionado).

Implementado em `notebooks/03-modelagem.ipynb` e `src/data/preparacao.py`
(pré-processador) + `src/model/avaliacao.py` (métrica de seleção).

## Unidade de análise

Um registro por **anúncio de veículo usado** (`data/processed/anuncios_curados.parquet`).

É a mesma unidade de análise de toda a base — o Canvas do Problema já define
assim (cada linha é uma oferta de mercado), e agrupar por outra unidade (por
exemplo, por modelo de carro) descartaria a variação de preço e estado entre
anúncios do mesmo modelo, que é justamente parte do que o mercado revela.

## Variáveis

| Critério pede | Variável usada | Observação |
|:---|:---|:---|
| Preço | `preco` | **reservada** — rótulo, avaliação *a posteriori* |
| Ano | `ano` | espaço de atributos |
| Quilometragem | `km` | espaço de atributos |
| Marca, modelo | `marca` | espaço de atributos (nominal, agrupada — ver abaixo); `modelo` fica fora (224 categorias, granularidade excessiva) |
| Motorização | — | `motor` (texto livre do anúncio) não está no espaço de atributos; `cambio`/`combustivel` entram no lugar, estruturados |
| Carroceria | `carroceria` | espaço de atributos |
| Câmbio | `cambio` | espaço de atributos |
| Combustível | `combustivel` | espaço de atributos |
| Localização | `bairro` | **reservada** — proxy de geografia, usada só para validação externa dos segmentos |
| Tipo de vendedor | `vendedor_tipo` | espaço de atributos |
| — | `zero_km` | variável acrescentada: flag binária (`km == 0`) — "carro de vitrine" é uma categoria de negócio distinta, não só a ponta inferior da distribuição de `km` |
| — | `valor_fipe_final` | **reservada** — derivada de marca/modelo/ano, usada só para medir desconto/oportunidade comercial |

### Pré-processamento

- **Agrupamento de categorias raras em `Outras`**: `marca` (41 categorias) e
  `municipio` (27) têm cauda longa. Categoria com menos de 20 anúncios
  (≈0,8% da base) vira `Outras`, reduzindo `marca` a 16 categorias efetivas.
- **Ausência**: já resolvida na preparação (ver [Preparação dos dados](preparacao.md))
  — nenhuma célula vazia no espaço de atributos ao chegar na modelagem.
- **Transformação de escala**: `log1p` seletivo em `km` (assimetria 0,94, acima
  do limiar de 0,75), seguido de `MinMaxScaler` nas numéricas/binárias
  (`ano`, `km`, `zero_km`).
- **Codificação de categóricas**: `OneHotEncoder` — mas **não entram na
  modelagem final** (ver seção Técnica, abaixo). Ficam disponíveis para a
  leitura de negócio dos segmentos.

## Técnica

K-Means (e três concorrentes: MiniBatch K-Means, Bisecting K-Means, Birch),
escolhidos por serem algoritmos particionais/hierárquicos padrão para dados
predominantemente numéricos — o tipo de dado que a segunda etapa do desenho
(abaixo) mostrou ser a melhor leitura deste problema.

```mermaid
flowchart LR
    A["espaço de atributos<br/>12 variáveis"] --> B["sensibilidade<br/>numérico x misto (one-hot)"]
    B --> C["pré-processador<br/>log1p + MinMax"]
    C --> D["GridSearchCV<br/>4 algoritmos x grade de k"]
    D --> E["perfilagem<br/>leitura de negócio por segmento"]
```

### Sensibilidade ao espaço de atributos

Antes de fixar o desenho, duas leituras do espaço de atributos foram testadas
empiricamente (não presumidas):

| Espaço | Dimensões | Silhueta (k=4-8) |
|:---|---:|:---|
| Numérico enxuto (`ano`, `km`, `zero_km`) | 3 | 0,47 a 0,54 |
| Misto (+ one-hot das 9 nominais) | 106 | 0,10 a 0,14 |

O espaço misto dilui a silhueta: 103 das 106 dimensões são *dummies* quase
sempre zero, e a distância euclidiana passa a ser dominada por combinações
categóricas, não pelo perfil de uso do veículo. **Decisão: a modelagem usa o
espaço numérico enxuto** — as nominais continuam decisivas, mas na leitura
comercial dos segmentos, não como entrada do algoritmo.

### Seleção de algoritmo e hiperparâmetros

`GridSearchCV` (métrica: silhueta, a única que não depende de rótulo)
selecionando hiperparâmetros dentro de cada modelo, validado por
`ShuffleSplit` (5 reamostragens de 80/20) via `cross_validate` — um modelo que
só funciona numa fatia específica dos dados não serve para operação. `k`
(número de segmentos) varre exatamente o intervalo do Canvas do Problema (4 a
8). O ajuste final é refeito em toda a base (a validação cruzada serve para
escolher, não para o modelo entregue).

## Avaliação do modelo

| Métrica | Leitura |
|:---|:---|
| Silhueta | maior é melhor — separação entre clusters; critério de aceite ≥ 0,40 |
| Davies-Bouldin | menor é melhor — razão intra/entre-cluster |
| Calinski-Harabasz | maior é melhor — dispersão entre/dentro dos grupos |

!!! warning "Ressalva de métrica"
    A silhueta sobre o espaço misto (one-hot) chegava a apenas ~0,10 — não
    porque os grupos não existam, mas porque a distância euclidiana em espaço
    de alta dimensão esparsa engana. É por isso que a comparação de espaços
    (acima) faz parte do desenho do experimento, e não é um detalhe de
    implementação: métrica boa em espaço errado não vira modelo bom.

**Resultado:** K-Means venceu (`n_clusters=5`, `init=k-means++`) contra os
outros três candidatos. Silhueta **0,542**, Davies-Bouldin **0,543**,
Calinski-Harabasz **6.670**.

## Interpretação do resultado

Cada segmento é perfilado por mediana/moda das variáveis que **não** entraram
na clusterização (marca, carroceria, câmbio, tipo de vendedor) mais preço,
km e idade — é assim que o número do cluster vira persona de negócio. A
nomeação dos grupos ("populares antigos", "seminovos recentes"...) é manual,
feita a partir dessas medianas, não automática. Detalhe completo em
[Avaliação dos resultados](avaliacao.md).

## Saídas

| Arquivo | Conteúdo |
|:---|:---|
| `data/processed/anuncios_segmentados.parquet` | a base curada + coluna `segmento` |
| `models/modelo-segmentacao.joblib` | pipeline treinado (pré-processador + `GridSearchCV`), pronto para `.predict()` |
| `models/catalogo_de_segmentos.json` | métricas do modelo + perfil de cada segmento |
| `reports/figures/modelagem/*.png` | sensibilidade ao espaço de atributos, mapa preço × km |

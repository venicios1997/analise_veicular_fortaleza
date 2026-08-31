# Segmentação do mercado de veículos usados de Fortaleza

Aprendizado de máquina não supervisionado sobre 2.565 anúncios de carros usados
coletados da OLX em Fortaleza-CE e região metropolitana, para identificar
segmentos de veículos com características semelhantes e apoiar a decisão de
composição de estoque de uma pequena revenda. Projeto da disciplina
*Aprendizado de Máquina Não Supervisionado*, MBA em Ciência de Dados. Documentação
completa publicada com MkDocs (ver seção Utilização).

## Objetivos e resultados chave

- Segmentar a carteira de anúncios em grupos tecnicamente defensáveis
  - Identificar entre 4 e 8 segmentos, com silhueta ≥ 0,40 → **5 segmentos,
    silhueta 0,542** (K-Means, sobre `ano`/`km`/`zero_km`)
  - Testar (não presumir) qual espaço de atributos separa melhor os grupos —
    espaço misto com one-hot das categóricas ficou em ~0,10 de silhueta;
    espaço numérico enxuto, em 0,54
- Descrever cada segmento em linguagem de negócio
  - Perfil de preço, km, idade, marca e carroceria por segmento
  - Pelo menos 2 oportunidades comerciais identificadas via desconto médio
    sobre a FIPE
  - Validação externa contra `bairro`, variável que nunca entrou na modelagem
- Entregar em forma utilizável pela operação
  - Aplicação Streamlit que classifica um anúncio novo e mostra o catálogo de
    segmentos, sem precisar retreinar nada

Detalhamento completo, com critérios de aceite verificáveis, em
[`docs/criterios-sucesso.md`](docs/criterios-sucesso.md).

## Conteúdo

### Notebooks

| Notebook | Fase do CRISP-DM | O que faz |
|:---|:---|:---|
| `00-dicionario-dados` | 2.2 | Dicionário de dados das 23 colunas brutas |
| `01-analise-exploratoria` | 2.3 | Mescla a FIPE (OLX + API pública) e roda o roteiro de 8 etapas da EDA |
| `02-ajustes-dados` | 3 | Limpeza, tratamento de ausência e atributos derivados — grava a base curada |
| `03-modelagem` | 4, 5, 6 | Sensibilidade ao espaço de atributos, seleção de algoritmo, avaliação, perfil dos segmentos e implantação (modelagem + avaliação + implantação num único notebook) |

Os notebooks são versionados **com saída** — as figuras também ficam
persistidas em `reports/figures/` e as tabelas-fonte em `reports/tables/`.

### Documentação

O relatório completo é o site MkDocs em `docs/`, com 13 páginas encadeadas —
do [Canvas do Problema](docs/canvas-do-problema.md) ao
[Status do projeto](docs/status.md), passando por entendimento de negócio,
fonte e entendimento dos dados, análise exploratória, preparação, modelagem,
avaliação e implementação. Publique localmente com `uv run invoke docs`.

### A aplicação

```bash
uv run invoke app
```

Sobe em `http://localhost:8501`, roda inteiramente local (sem chamada de rede)
e lê o pipeline treinado (`models/modelo-segmentacao.joblib`), o catálogo de
segmentos (`models/catalogo_de_segmentos.json`) e a base classificada
(`data/processed/anuncios_segmentados.parquet`). Cinco abas:

- **Sobre o projeto** — a dor de negócio, a pergunta central e um resumo do modelo;
- **Classificar anúncio** — classifica um anúncio novo por ano/km, com histograma
  de onde ele cai na distribuição do segmento e, se informado um preço de
  compra, a margem estimada contra a mediana de venda do segmento;
- **Catálogo de segmentos** — os 5 segmentos, filtráveis por marca/carroceria/
  câmbio/faixa de preço (barra lateral), com exportação da lista filtrada em CSV;
- **Oportunidades comerciais** — segmentos ordenados por desconto médio vs.
  FIPE, com detalhamento por marca e carroceria dentro de cada segmento e
  exportação em CSV;
- **Mapa preço x km** — dispersão colorida por segmento, também filtrável.

## Utilização

Este projeto usa o [uv](https://docs.astral.sh/uv/) como gerenciador de
dependências e ambientes virtuais.

```bash
# Instalar o uv (caso ainda não tenha)
# https://docs.astral.sh/uv/getting-started/installation/

# Criar o ambiente virtual e instalar todas as dependências (usa o uv.lock)
uv sync

# Instalar os hooks de pre-commit (ruff)
uv run pre-commit install

# Listar as tarefas disponíveis do projeto
uv run invoke --list

# Tarefas
uv run invoke lab          # Abre o JupyterLab
uv run invoke app          # Executa a aplicação Streamlit
uv run invoke docs         # Serve a documentação localmente
uv run invoke notebooks    # Executa os notebooks 00-03 em ordem
uv run invoke preparacao   # Refaz a base curada a partir de data/raw
uv run invoke lint         # Verifica o código com o ruff
uv run invoke test         # Executa os testes com o pytest

# Adicionar uma nova dependência
uv add <pacote>
```

A versão do Python está fixada em [`.python-version`](.python-version); o `uv`
instala e usa essa versão automaticamente.

**Nota sobre a coleta:** os dados já vêm coletados em `data/raw/` (scraping da
OLX + API pública da Tabela FIPE). O coletor é uma ferramenta separada, não
incluída neste repositório — este projeto parte da camada bruta já
materializada e imutável.

## Desenvolvedores

- [Marcos Venicios de Andrade](https://github.com/venicios1997) — matrícula 2517819 — Coleta, análise, modelagem
- [Josue de Vasconcelos Silveira Moreira](https://github.com/josueVSM) — matrícula 2517534 — Implantação


## Organização de diretórios

```
.
├── .github/                # Templates de issues/PRs e CODEOWNERS
├── data/
│   ├── raw/                # 3 CSVs da coleta (imutáveis)
│   └── processed/          # base curada, matriz de modelagem, base segmentada
├── docs/                   # Documentação do projeto publicada com o MkDocs
├── models/                 # Pipeline treinado (.joblib) e catálogo de segmentos (.json)
├── notebooks/              # 00-dicionario-dados a 03-modelagem
├── references/             # Material exploratório complementar
├── reports/
│   ├── figures/             # Uma subpasta por notebook (eda-exploratoria, ajustes-dados, modelagem)
│   └── tables/               # Tabela-fonte de cada figura, mesma organização
├── src/
│   ├── config.py            # Caminhos, semente, paleta, critérios de sucesso do Canvas
│   ├── data/                # Ingestão, dicionário de dados, preparação, checagens de qualidade
│   ├── eda/                 # Medidas de associação e detecção de discrepantes
│   ├── model/                # Métrica de seleção de cluster (silhueta), usada pelo modelo salvo
│   ├── utils/                # Gravação padronizada de figuras/tabelas, execução em lote dos notebooks
│   └── deployment/           # Aplicação Streamlit
├── tests/                   # Testes automatizados executados com o pytest
├── .pre-commit-config.yaml  # Hooks de qualidade executados antes de cada commit
├── .python-version          # Versão do Python utilizada pelo uv
├── LICENSE
├── mkdocs.yml
├── pyproject.toml
├── uv.lock
├── README.md
└── tasks.py                 # Tarefas do invoke (lab, app, docs, notebooks, preparacao, lint, test)
```

# Entendimento de negócio

## Marcos negociais

???+ success "Fase 1: Preparação do ambiente"
    - [x] Criar repositório GitHub
    - [x] Instalar ferramentas do projeto (uv, JupyterLab, MkDocs)

???+ success "Fase 2: Entendimento de negócio"
    - [x] Elaborar projeto inicial (Canvas do Problema da disciplina)
    - [x] Produzir relatório de mineração dos dados (esta página)

???+ success "Fase 3: Entendimento dos dados"
    - [x] Gerar conjunto de dados (coleta OLX + FIPE)
    - [x] Produzir relatório de qualidade dos dados
    - [x] Realizar descrição dos dados (`00-dicionario-dados.ipynb`)
    - [x] Realizar análise exploratória (`01-analise-exploratoria.ipynb`)
    - [x] Produzir relatório do entendimento dos dados

???+ success "Fase 4: Preparação dos dados"
    - [x] Gerar script de limpeza dos dados (`src/data/preparacao.py`)
    - [x] Gerar conjunto de dados processado (`data/processed/anuncios_curados.parquet`)
    - [x] Produzir relatório de preparação dos dados

???+ success "Fase 5: Modelagem"
    - [x] Gerar desenho do experimento da modelagem
    - [x] Gerar script da modelagem (`03-modelagem.ipynb`)
    - [x] Produzir relatório com os resultados

???+ success "Fase 6: Avaliação"
    - [x] Produzir relatório da avaliação dos resultados
    - [x] Produzir relatório das próximas etapas

???+ success "Fase 7: Implementação"
    - [x] Gerar desenho da implementação
    - [x] Desenvolver script da implementação (`src/deployment/app.py`)
    - [ ] Produzir relatório de monitoramento e manutenção dos modelos
    - [x] Produzir relatório final contendo todas as fases anteriores

## Avaliar a situação

O projeto é individual, de escopo acadêmico, com recursos e riscos de porte bem
menor que um projeto corporativo — mesmo assim vale registrar os quatro pontos
que orientaram as decisões de escopo.

### Recursos

- **Humanos:** um único autor, acumulando os papéis de analista de negócio,
  engenheiro de dados e cientista de dados.
- **Tecnológicos:** Python 3.12, `uv` para gerência de ambiente, Playwright para
  o scraping (repositório separado, não versionado aqui), JupyterLab,
  scikit-learn, MkDocs Material para a documentação e Streamlit para a
  aplicação. Nenhum serviço pago — tudo roda localmente.
- **Financeiros:** nenhum orçamento dedicado; a única dependência externa é a
  API pública gratuita da Tabela FIPE (`parallelum.com.br`), usada com
  moderação (delay entre chamadas) por ter limite de requisições.

#### Equipe técnica

| Nome     | Cargo / Função                                         | E-mail                 |
| :------- | :------------------------------------------------------ | :----------------------- |
| Venicios | Coleta de dados, engenharia de dados, ciência de dados | venicios1997@gmail.com |

#### Especialistas de negócio

Não há especialista de negócio real consultado. O contexto de negócio (dor,
objetivo, critérios de sucesso) vem do Canvas do Problema fornecido pela
disciplina, que descreve o cenário de uma pequena revenda de veículos usados de
Fortaleza-CE — usado aqui como o "cliente" hipotético do projeto.

#### Equipe de infraestrutura

Não aplicável — projeto individual, sem infraestrutura compartilhada. Execução
local (notebook pessoal) e documentação publicada via GitHub Pages/MkDocs.

#### Recursos financeiros

Custo financeiro nulo: todas as ferramentas usadas são gratuitas e de código
aberto, e a coleta de dados não depende de nenhuma API paga.

### Requisitos do projeto

#### Necessidades de negócio

Uma pequena revenda de Fortaleza precisa de um critério além da intuição para
decidir quais veículos comprar para estoque — capital limitado não pode ficar
parado em carros de baixa procura.

#### Requisitos funcionais

- Coletar uma amostra representativa de anúncios de carros usados de Fortaleza
  (meta do Canvas: 1.000 a 5.000 anúncios — atingido: 2.565).
- Identificar entre 4 e 8 segmentos de veículos, com separação técnica
  defensável (silhueta ≥ 0,40).
- Descrever cada segmento em linguagem de negócio (perfil, preço, km, idade,
  marca/carroceria típicas).
- Apontar ao menos 2 oportunidades comerciais a partir dos segmentos
  encontrados.
- Disponibilizar uma forma de classificar um anúncio novo no segmento
  correspondente (aplicação Streamlit).

#### Requisitos técnicos

| Ferramenta                          | Descrição                                                        |
| :------------------------------------ | :------------------------------------------------------------------ |
| :simple-github: GitHub                | Controle de versão e hospedagem do repositório.                  |
| :simple-uv: uv                        | Gerenciamento de dependências e do ambiente virtual do projeto.  |
| :simple-python: Python 3.12           | Linguagem de todo o pipeline (coleta, análise, modelagem, app).  |
| :simple-jupyter: JupyterLab           | Ambiente dos notebooks 00–03.                                     |
| :simple-playwright: Playwright        | Scraping da OLX (repositório separado da coleta).                |
| :material-bookshelf: Bibliotecas      | pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, prince, circlify, joblib, streamlit. |
| :material-file-document: MkDocs Material | Publicação desta documentação.                                |

#### Requisitos de dados

Anúncios de veículos usados de Fortaleza-CE e municípios da região metropolitana,
com preço, ano, quilometragem, marca, modelo, câmbio, combustível, carroceria,
tipo de vendedor e localização — ver detalhamento em
[Fonte dos dados](fonte-dados.md).

### Riscos

Os riscos deste projeto são principalmente metodológicos e de qualidade de
dado, não organizacionais:

- **Oferta ≠ demanda:** o volume de anúncios de um modelo não significa que
  exista mais demanda por ele — apenas mais oferta (ou mais concorrência).
- **Preço anunciado ≠ preço vendido:** os dados capturam a intenção de venda,
  não a transação efetivada.
- **Recorte temporal:** a coleta foi feita num único dia (21/08/2026); os
  resultados retratam o mercado nesse momento, não uma tendência.
- **Qualidade do dado de scraping:** campos podem faltar quando a página do
  anúncio não carrega por completo — tratado explicitamente no notebook
  `02-ajustes-dados`.
- **Escolha do número de clusters e do espaço de atributos:** decisão sensível,
  documentada e testada empiricamente (seção *Sensibilidade ao espaço de
  atributos* do notebook `03-modelagem`).

### Análise custo-benefício

Custo: o tempo do autor (coleta, análise, modelagem, documentação) — sem custo
financeiro direto. Benefício: um critério de decisão de estoque baseado em
padrão real de mercado, em vez de intuição, replicável a qualquer momento
rodando a coleta e o pipeline novamente.

## Mineração de dados

Os dados brutos ficam em `data/raw/` (imutáveis) e a base curada em
`data/processed/` — sem Data Warehouse corporativo, dado o escopo do projeto.
Não há dado pessoal sensível: os anúncios são públicos e não trazem
identificação do comprador; a localização do vendedor é limitada a
bairro/município, informação já pública no próprio anúncio da OLX.

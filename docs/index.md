# Segmentação do mercado de veículos usados de Fortaleza

## Introdução

Uma pequena revenda de veículos usados em Fortaleza-CE decide o que comprar para
estoque com base em experiência pessoal, percepção do vendedor e histórico
individual de vendas — não em dados de mercado. Isso leva a capital parado em
veículos de baixa procura, dificuldade de venda e perda de oportunidades em
segmentos com maior potencial.

Este projeto aplica **aprendizado de máquina não supervisionado** (clusterização)
sobre 2.565 anúncios de carros usados coletados da OLX em Fortaleza e região
metropolitana, para identificar segmentos de veículos com características
semelhantes — e, a partir deles, apontar quais tipos de veículo uma pequena
revenda deveria priorizar na compra e revenda.

O resultado: **4 segmentos**, obtidos por K-Means sobre `ano`, `km` e `zero_km`
(silhueta 0,541), com leitura de negócio construída sobre marca, câmbio, carroceria,
tipo de vendedor e desconto em relação à Tabela FIPE — a métrica que aponta as
oportunidades comerciais de cada grupo:

| Segmento | Perfil | Anúncios | Preço mediano | Idade | Desconto mediano vs. FIPE |
|:-:|:---|--:|--:|--:|--:|
| 0 | Populares antigos | 255 (10,5%) | R$ 14.000 | 25 anos | **+7,7%** |
| 2 | Populares usados | 1.028 (42,5%) | R$ 39.900 | 12 anos | **+0,7%** |
| 1 | Seminovos recentes | 1.070 (44,3%) | R$ 97.990 | 2 anos | −0,9% |
| 3 | Zero-km e vitrine | 65 (2,7%) | R$ 175.990 | 0 anos | −9,6% |

Detalhes em [Modelagem dos dados](modelagem.md) e
[Avaliação dos resultados](avaliacao.md).

## Dados do projeto

Os dados são anúncios públicos de carros usados publicados na OLX
(`ce.olx.com.br`), coletados por scraping (Playwright) entre 21 e 22/08/2026 com
o coletor em [`src/coleta/`](fonte-dados.md#o-coletor), complementados com o
valor de referência da Tabela FIPE (via API pública `parallelum.com.br/fipe`,
para os anúncios em que a própria OLX não trazia essa informação). Ver
[Fonte dos dados](fonte-dados.md).

### Levantamento inicial

!!! info "Tipo do projeto"
    - [ ] Análise exploratória
    - [ ] Modelo preditivo
    - [ ] Modelo de classificação
    - [x] Modelo de agrupamento
    - [ ] Detecção de anomalias

### Nível de acesso

!!! warning "Confidencialidade"
    - [x] Público
    - [ ] Interno (toda a organização)
    - [ ] Restrito (apenas a área requisitante)

    Os dados são anúncios públicos de veículos, sem informação pessoal do
    anunciante além do que a própria OLX exibe publicamente (localização por
    bairro/município, tipo de vendedor).

### Objetivos de negócio

!!! quote ""
    Identificar segmentos de veículos com características semelhantes no mercado
    de Fortaleza, permitindo que pequenas revendas direcionem melhor seus
    recursos para aquisição de veículos e composição de estoque — respondendo a
    quais tipos de veículo uma pequena revenda deveria priorizar para compra e
    revenda em Fortaleza. Detalhes em [Critérios de sucesso](criterios-sucesso.md).

## Sobre o projeto

Projeto em equipe da disciplina **Aprendizado de Máquina Não Supervisionado**,
MBA em Ciência de Dados. Não há stakeholder externo real contratante: o "cliente"
— uma pequena revenda de veículos de Fortaleza — é o cenário de negócio definido
no Canvas do Problema da disciplina, e os papéis técnicos e de negócio abaixo são
exercidos pelos próprios integrantes.

### Histórico do documento

| Data       | Versão | Descrição                                     | Autor    |
| :--------- | :----- | :--------------------------------------------- | :------- |
| 2026-08-22 | 1.0    | Versão inicial da documentação (notebooks 00-03) | Venicios Andrade |
| 2026-08-30 | 1.1    | Regras de hodômetro implausível e de desconto fora de faixa; k passa de 5 para 4; ranking de oportunidade por mediana; segmentos nomeados | Equipe |
| 2026-08-31 | 1.2    | Coletor incorporado ao repositório (`src/coleta/`) e referenciado nas páginas; ver [Fonte dos dados — O coletor](fonte-dados.md#o-coletor) | Equipe |

### Dados do solicitante

``` mermaid
flowchart TD
    id1[Setor automotivo — revenda de veículos usados] --o id2[Pequena revenda de Fortaleza-CE, cenário do Canvas do Problema]
```

| Nome                    | Cargo / Função                          | E-mail                  |
| :----------------------- | :--------------------------------------- | :----------------------- |
| Pequena revenda (cenário) | Solicitante — decisão de composição de estoque | não aplicável (cenário acadêmico) |

### Dados da equipe técnica

| Nome | Cargo / Função |
| :--- | :--- |
| Venicios Andrade | Coleta, engenharia de dados e modelagem |
| Luis Helder | Revisão metodológica, preparação dos dados e implantação |
| Marcos Paulo | Análise exploratória e documentação |
| Josué Vasconcelos | Análise exploratória e documentação |
| Plínio Rodrigues | Avaliação dos resultados e leitura de negócio |

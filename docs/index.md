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

O resultado: **5 segmentos**, obtidos por K-Means sobre `ano` e `km` (silhueta
0,54), com leitura de negócio construída sobre marca, câmbio, carroceria, tipo de
vendedor e desconto médio em relação à Tabela FIPE — a métrica que aponta as
oportunidades comerciais de cada grupo. Detalhes em
[Modelagem dos dados](modelagem.md) e [Avaliação dos resultados](avaliacao.md).

## Dados do projeto

Os dados são anúncios públicos de carros usados publicados na OLX
(`ce.olx.com.br`), coletados por scraping (Playwright) entre 21 e 22/08/2026,
complementados com o valor de referência da Tabela FIPE (via API pública
`parallelum.com.br/fipe`, para os anúncios em que a própria OLX não trazia essa
informação). Ver [Fonte dos dados](fonte-dados.md).

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

Projeto individual da disciplina **Aprendizado de Máquina Não Supervisionado**,
MBA em Ciência de Dados. Não há stakeholder externo real contratante: o "cliente"
— uma pequena revenda de veículos de Fortaleza — é o cenário de negócio definido
no Canvas do Problema da disciplina, e todos os papéis técnicos e de negócio
abaixo são exercidos pelo mesmo autor.

### Histórico do documento

| Data       | Versão | Descrição                                     | Autor    |
| :--------- | :----- | :--------------------------------------------- | :------- |
| 2026-08-22 | 1.0    | Versão inicial da documentação (notebooks 00-03) | Venicios |
| 2026-08-30 | 1.1    | Versão atualizada (notebooks 00-03) | Josué V. |
### Dados do solicitante

``` mermaid
flowchart TD
    id1[Setor automotivo — revenda de veículos usados] --o id2[Pequena revenda de Fortaleza-CE, cenário do Canvas do Problema]
```

| Nome                    | Cargo / Função                          | E-mail                  |
| :----------------------- | :--------------------------------------- | :----------------------- |
| Pequena revenda (cenário) | Solicitante — decisão de composição de estoque | não aplicável (cenário acadêmico) |

### Dados da equipe técnica

| Nome     | Cargo / Função                                              | E-mail                  |
| :------- | :------------------------------------------------------------ | :----------------------- |
| Venicios | Coleta, análise, modelagem    | venicios1997@gmail.com  |
| Josue Vasconcelos | Implantação      | josuevasconceloss@gmail.com  |
# Critérios de sucesso

O sucesso do projeto é dado pela completude dos três objetivos de negócio a seguir,
derivados do Canvas do Problema da disciplina. Cada um está descrito no formato
**Como** / **Quero** / **Para** / **Objetivo**, com critérios de aceite verificáveis.

## Visão geral

| # | Objetivo de negócio | Solicitante (papel) | Entrega principal |
|:-:|:---|:---|:---|
| 1 | Segmentar a carteira de anúncios em grupos tecnicamente defensáveis | Pequena revenda (cenário do Canvas) | `03-modelagem.ipynb`, `models/modelo-segmentacao.joblib` |
| 2 | Descrever cada segmento em linguagem de negócio | Pequena revenda (cenário do Canvas) | Perfil dos segmentos, `models/catalogo_de_segmentos.json` |
| 3 | Entregar em forma utilizável pela operação | Pequena revenda (cenário do Canvas) | Aplicação Streamlit (`src/deployment/app.py`) |

---

## 1. Segmentar a carteira de anúncios em grupos tecnicamente defensáveis

???+ success "Segmentação técnica"
    **Como** pequena revenda de veículos de Fortaleza<br>
    **Quero** que os anúncios do mercado sejam agrupados por características
    semelhantes, sem que eu defina os grupos manualmente<br>
    **Para** ter uma leitura estruturada do mercado, e não só a minha experiência
    pessoal<br>
    **Objetivo** um número de segmentos operável, com separação estatística real
    entre eles

    **Critérios de aceite:**

    - [x] Entre 4 e 8 segmentos — obtido: **4**
    - [x] Silhueta ≥ 0,40 — obtido: **0,541**
    - [x] Nenhum segmento com menos de 50 anúncios (volume mínimo para leitura
      confiável) — obtido: **65** (menor segmento)
    - [x] A escolha do espaço de atributos é testada, não presumida — a seção
      *Sensibilidade ao espaço de atributos* do notebook `03-modelagem` compara
      o espaço numérico com o espaço misto (one-hot) antes de decidir

    **Entrega:** `notebooks/03-modelagem.ipynb`, seções "Seleção de algoritmo e
    hiperparâmetros" e "Ajuste final e avaliação técnica";
    `models/modelo-segmentacao.joblib`.

## 2. Descrever cada segmento em linguagem de negócio

???+ success "Leitura comercial dos segmentos"
    **Como** pequena revenda de veículos de Fortaleza<br>
    **Quero** saber o que cada segmento representa — preço típico, quilometragem,
    idade, marca e carroceria mais comuns<br>
    **Para** decidir, para cada grupo, se ele faz sentido para o meu estoque<br>
    **Objetivo** um perfil de negócio para cada um dos 4 segmentos, incluindo uma
    leitura de oportunidade comercial

    **Critérios de aceite:**

    - [x] Perfil (preço, km, idade, marca e carroceria dominantes) para os 4
      segmentos, cada um com **nome de negócio e condição verificável** —
      tabela `reports/tables/modelagem/perfil-dos-segmentos.csv`
    - [x] Pelo menos 2 oportunidades comerciais identificadas — o segmento 0
      (*populares antigos*, 10,5% da base) tem desconto mediano de **+7,7%**
      sobre a FIPE e o segmento 2 (*populares usados*, 42,5%) tem **+0,7%**.
      Os dois estão, no anúncio típico, abaixo da tabela — não é preciso contar
      um ágio como oportunidade, que era como este critério fechava antes da
      revisão do desconto (ver
      [Avaliação dos resultados](avaliacao.md#a-revisao-que-mudou-a-conclusao))
    - [x] Validação externa dos segmentos contra uma variável que **não** entrou
      na modelagem (`bairro`) — seção "Validação externa" do notebook
      `03-modelagem`

    **Entrega:** `models/catalogo_de_segmentos.json`;
    `reports/tables/modelagem/oportunidades-comerciais.csv`;
    `reports/figures/modelagem/segmentos-preco-x-km.png`.

## 3. Entregar em forma utilizável pela operação

???+ success "Aplicação de classificação"
    **Como** pequena revenda de veículos de Fortaleza<br>
    **Quero** classificar um anúncio novo (ou em análise de compra) no segmento
    correspondente sem precisar rodar notebook nenhum<br>
    **Para** usar a segmentação no dia a dia da operação, não só como relatório
    acadêmico<br>
    **Objetivo** uma aplicação local, simples, que reutiliza o modelo treinado

    **Critérios de aceite:**

    - [x] Aplicação Streamlit que carrega o modelo salvo e classifica um anúncio
      a partir de ano e quilometragem
    - [x] A aplicação mostra o catálogo dos 4 segmentos, pelo nome de negócio, e
      a leitura de oportunidade comercial
    - [x] A aplicação roda localmente sem retreinar nada (`uv run invoke app`)

    **Entrega:** `src/deployment/app.py`; `models/modelo-segmentacao.joblib`;
    `models/catalogo_de_segmentos.json`.

---

## Consolidado dos critérios de aceite

| Objetivo | Critérios de aceite | Concluídos | Observação |
|:---|:-:|:-:|:---|
| 1. Segmentação técnica | 4 | 4 | k=4 depois da regra de hodômetro implausível |
| 2. Leitura comercial | 3 | 3 | ranking por desconto mediano, com a média ao lado |
| 3. Aplicação | 3 | 3 | — |
| **Total** | **10** | **10** | |

## Pendências de dados

Nenhuma pendência bloqueia os critérios acima. Duas limitações registradas em
[Entendimento dos dados](entendimento-dados.md#limitacoes) não impedem o
objetivo do projeto, mas restringem a interpretação dos resultados:

| # | Pendência | Destrava |
|:-:|:---|:---|
| 1 | Preço de venda efetivo (só temos o preço anunciado) | Acesso a dados de transação real, que a OLX não publica |
| 2 | Série histórica de anúncios (coleta é de um único dia) | Coletas repetidas ao longo do tempo, fora do escopo deste projeto |

!!! info "Fonte"
    Critérios derivados do Canvas do Problema da disciplina de Aprendizado de
    Máquina Não Supervisionado (MBA em Ciência de Dados), seções 4 ("Critério de
    sucesso do negócio") e 6 ("Critério de sucesso técnico") — reproduzidas na
    íntegra em [Canvas do Problema](canvas-do-problema.md).

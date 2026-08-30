# Avaliação dos resultados

Enquanto a avaliação feita em [Modelagem dos dados](modelagem.md) é **técnica**, esta página
olha para o **projeto como um todo**: os resultados atendem aos objetivos de negócio, o
processo foi conduzido corretamente, e o que fazer em seguida.

## Confronto com os critérios de aceite

| Objetivo | Critério de aceite | Situação | Evidência |
|:---|:---|:---|:---|
| 1 | Entre 4 e 8 segmentos | atendido — 4 | `models/catalogo_de_segmentos.json` |
| 1 | Silhueta ≥ 0,40 | atendido — 0,541 | notebook `03-modelagem`, seção "Ajuste final" |
| 1 | Nenhum segmento com menos de 50 anúncios | atendido — mínimo 65 | `reports/tables/modelagem/criterios-de-sucesso.csv` |
| 1 | Espaço de atributos testado, não presumido | atendido | seção "Sensibilidade ao espaço de atributos" |
| 2 | Perfil de negócio para os 4 segmentos | atendido — todos nomeados, com condição verificável | `reports/tables/modelagem/perfil-dos-segmentos.csv` |
| 2 | ≥ 2 oportunidades comerciais identificadas | atendido — segmentos 0 e 2, os dois com desconto **mediano positivo** (+7,7% e +0,7% vs. FIPE) | `reports/tables/modelagem/oportunidades-comerciais.csv` |
| 2 | Validação externa contra variável fora da modelagem | atendido — `bairro` varia entre segmentos | seção "Validação externa" do notebook 03 |
| 3 | Aplicação classifica anúncio novo | atendido | `src/deployment/app.py`, página "Classificar anúncio" |
| 3 | Aplicação mostra catálogo, oportunidades e mapa | atendido | páginas "Catálogo de segmentos", "Oportunidades comerciais" e "Mapa preço x km" |
| 3 | Roda local sem retreinar | atendido | `uv run invoke app` carrega `models/modelo-segmentacao.joblib` |

### Os quatro segmentos

| Segmento | Perfil | Anúncios | Preço mediano | Idade | Desconto mediano | Desconto médio |
|:-:|:---|--:|--:|--:|--:|--:|
| 0 | Populares antigos | 255 (10,5%) | R$ 14.000 | 25 anos | **+7,7%** | +8,6% |
| 2 | Populares usados | 1.028 (42,5%) | R$ 39.900 | 12 anos | **+0,7%** | +3,2% |
| 1 | Seminovos recentes | 1.070 (44,3%) | R$ 97.990 | 2 anos | −0,9% | −0,9% |
| 3 | Zero-km e vitrine | 65 (2,7%) | R$ 175.990 | 0 anos | −9,6% | −10,9% |

![Segmentos no plano preço × km](imagens/figuras/modelagem/segmentos-preco-x-km.png)

*Tabela-fonte: `reports/tables/modelagem/perfil-dos-segmentos.csv`.*

**Leitura consolidada:** os 10 critérios de aceite dos 3 objetivos foram
atendidos. Dois ajustes foram feitos ao longo do projeto, ambos registrados
aqui em vez de escondidos:

1. **O critério de volume mínimo por segmento.** A primeira tentativa usava
   "≥ 5% da base" — um número redondo, sem exigência real do Canvas por trás —
   que reprovaria o segmento de zero-km/vitrine (2,7%), genuinamente
   interpretável. Foi substituído por um piso absoluto de 50 anúncios, volume
   mínimo para leitura estatística confiável.
2. **A estatística que ordena as oportunidades.** Era a média do desconto sobre
   a FIPE; passou a ser a mediana, com a média publicada ao lado. O motivo está
   na próxima seção.

### Critérios não atendidos

Nenhum. As duas limitações de dado (preço efetivo de venda; série temporal),
já registradas em [Entendimento dos dados](entendimento-dados.md#limitacoes) e
nas [pendências dos critérios de sucesso](criterios-sucesso.md#pendencias-de-dados),
não bloqueiam nenhum critério de aceite — apenas restringem até onde a
interpretação dos resultados pode ir.

## A revisão que mudou a conclusão

A leitura de oportunidade comercial era construída sobre a **média** do desconto
sobre a FIPE. `desconto_fipe_pct` é uma razão sem limite inferior, alimentada
por uma FIPE que em 6,4% dos anúncios vem de casamento por similaridade de
texto — a base bruta chegava a **−1.249%**, e um segmento tinha desvio-padrão de
181. A média não descrevia segmento nenhum: descrevia os extremos.

O que mudou:

| | Antes | Depois |
|:---|:---|:---|
| Ranking por média | 3 · 2 · 1 · 0 · 4 | 0 · 2 · 1 · 3 |
| Ranking por mediana | 0 · 4 · 3 · 2 · 1 | 0 · 2 · 1 · 3 |
| Segmentos em que média e mediana discordam no sinal | 2 de 5 | **0 de 4** |
| Segmentos com desconto positivo | 1 | **2** |

Antes da curadoria, trocar média por mediana **invertia o ranking inteiro** — o
que significa que a resposta à Pergunta 5 do Canvas dependia de uma escolha
estatística que não estava declarada em lugar nenhum. Depois das duas regras
novas de limpeza, os dois rankings coincidem. Essa coincidência é o resultado:
a leitura comercial deixou de depender de um punhado de anúncios mal casados
com a tabela.

O perfil continua publicando **as duas colunas**, porque a distância entre elas
mede o quanto cada segmento depende das pontas — no segmento 2 a média é 4,5× a
mediana, e isso é informação sobre o segmento, não ruído a esconder.

## Revisão do processo

- **O que funcionou** — testar a sensibilidade ao espaço de atributos antes de
  fixar a modelagem: a primeira tentativa (espaço misto, com one-hot das
  categóricas) falhava o critério de silhueta por um fator de 5×, e só ficou
  evidente porque o experimento comparou as duas leituras lado a lado, em vez
  de aceitar o primeiro resultado. Também funcionou registrar cada ajuste de
  limpeza com motivo e volume afetado (`registrar()` em `02-ajustes-dados`) —
  tornou o funil de 2.565 → 2.418 anúncios auditável linha a linha.
- **O que só apareceu na perfilagem** — um dos cinco segmentos da primeira
  modelagem era artefato de captura: 60 anúncios com idade mediana de 16,5 anos
  e quilometragem mediana de 200 km, ou seja, 14 km rodados por ano. Não era
  mercado, era hodômetro digitado em milhares. Nenhuma métrica de clusterização
  acusaria — o grupo é de fato coeso no espaço `ano`/`km` —, só a leitura do
  perfil linha a linha. Virou regra de limpeza, e o k caiu de 5 para 4.
- **O que atrasou** — descobrir, só depois de treinar e salvar o primeiro
  modelo, que a função de silhueta usada pelo `GridSearchCV` (definida dentro
  do notebook) impedia `joblib.load()` de funcionar em qualquer script fora do
  notebook — a aplicação Streamlit não conseguia carregar o modelo. Corrigido
  movendo a função para `src/model/avaliacao.py` e retreinando.
- **O que foi esquecido** — `desconto_fipe_pct` nunca passou pela etapa de
  detecção de discrepantes da EDA, embora fosse a única variável do projeto com
  cauda de quatro dígitos e a única a sustentar sozinha um objetivo de negócio.
  A etapa cobria `preco`, `km`, `ano` e `valor_fipe_final`, mas não a razão
  derivada delas. Incluí-la teria antecipado as duas correções acima.
- **O que já estava coberto** — a checagem de equivalência entre notebook e
  módulo (`preparacao.construir_base_curada()` reproduzido dentro do próprio
  notebook 02) segurou o risco mais provável: documentação e código divergirem.

## Próximas etapas

!!! info "Decisão"
    - [x] **Implantar** — seguir para [Implementação](implementacao.md)
    - [ ] **Iterar** — voltar a uma fase anterior; indique qual e por quê
    - [ ] **Encerrar** — registrar o aprendizado e não prosseguir

| Ação | Responsável | Prazo |
|:---|:---|:---|
| Publicar a documentação (MkDocs) e o app Streamlit | Equipe | entrega da disciplina |
| Se houver nova coleta futura, repetir a comparação de espaço de atributos antes de reusar a mesma configuração | Equipe | próxima iteração, se houver |
| Incluir `desconto_fipe_pct` na etapa de discrepantes da EDA (notebook 01) | Equipe | próxima iteração |

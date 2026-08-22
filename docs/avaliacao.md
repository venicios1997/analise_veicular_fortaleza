# Avaliação dos resultados

Enquanto a avaliação feita em [Modelagem dos dados](modelagem.md) é **técnica**, esta página
olha para o **projeto como um todo**: os resultados atendem aos objetivos de negócio, o
processo foi conduzido corretamente, e o que fazer em seguida.

## Confronto com os critérios de aceite

| Objetivo | Critério de aceite | Situação | Evidência |
|:---|:---|:---|:---|
| 1 | Entre 4 e 8 segmentos | atendido — 5 | `models/catalogo_de_segmentos.json` |
| 1 | Silhueta ≥ 0,40 | atendido — 0,542 | notebook `03-modelagem`, seção "Ajuste final" |
| 1 | Nenhum segmento com menos de 50 anúncios | atendido — mínimo 60 | `reports/tables/modelagem/criterios-de-sucesso.csv` |
| 1 | Espaço de atributos testado, não presumido | atendido | seção "Sensibilidade ao espaço de atributos" |
| 2 | Perfil de negócio para os 5 segmentos | atendido | `reports/tables/modelagem/perfil-dos-segmentos.csv` |
| 2 | ≥ 2 oportunidades comerciais identificadas | atendido — segmentos 3 e 2 (desconto +3,0% e −0,6% vs. FIPE) | `reports/tables/modelagem/oportunidades-comerciais.csv` |
| 2 | Validação externa contra variável fora da modelagem | atendido — `bairro` varia entre segmentos | seção "Validação externa" do notebook 03 |
| 3 | Aplicação classifica anúncio novo | atendido | `src/deployment/app.py`, aba "Classificar anúncio" |
| 3 | Aplicação mostra catálogo e mapa | atendido | abas "Catálogo de segmentos" e "Mapa preço x km" |
| 3 | Roda local sem retreinar | atendido | `uv run invoke app` carrega `models/modelo-segmentacao.joblib` |

**Leitura consolidada:** os 10 critérios de aceite dos 3 objetivos foram
atendidos. Nenhum ficou parcial ou não atendido — o único ajuste feito ao longo
do projeto foi ao próprio critério de volume mínimo por segmento: a primeira
tentativa usava "≥ 5% da base" (mais um número redondo herdado de um projeto de
referência do que uma exigência real do Canvas), que reprovaria dois segmentos
genuinamente interpretáveis (zero-km/elétricos, 3,4%; carros antigos de
baixíssima km, 2,4%). O critério foi substituído por um piso absoluto de 50
anúncios — volume mínimo para leitura estatística confiável — decisão registrada
em [Modelagem dos dados](modelagem.md), não escondida.

### Critérios não atendidos

Nenhum. As duas limitações de dado (preço efetivo de venda; série temporal),
já registradas em [Entendimento dos dados](entendimento-dados.md#limitacoes) e
nas [pendências dos critérios de sucesso](criterios-sucesso.md#pendencias-de-dados),
não bloqueiam nenhum critério de aceite — apenas restringem até onde a
interpretação dos resultados pode ir.

## Revisão do processo

- **O que funcionou** — testar a sensibilidade ao espaço de atributos antes de
  fixar a modelagem: a primeira tentativa (espaço misto, com one-hot das
  categóricas) falhava o critério de silhueta por um fator de 5×, e só ficou
  evidente porque o experimento comparou as duas leituras lado a lado, em vez
  de aceitar o primeiro resultado. Também funcionou registrar cada ajuste de
  limpeza com motivo e volume afetado (`registrar()` em `02-ajustes-dados`) —
  tornou o funil de 2.565 → 2.479 anúncios auditável linha a linha.
- **O que atrasou** — descobrir, só depois de treinar e salvar o primeiro
  modelo, que a função de silhueta usada pelo `GridSearchCV` (definida dentro
  do notebook) impedia `joblib.load()` de funcionar em qualquer script fora do
  notebook — a aplicação Streamlit não conseguia carregar o modelo. Corrigido
  movendo a função para `src/model/avaliacao.py` e retreinando.
- **O que foi esquecido** — nada identificado que exija correção adicional; a
  checagem de equivalência entre notebook e módulo (`preparacao.construir_base_curada()`
  reproduzido dentro do próprio notebook 02) já cobre o risco mais provável
  (documentação e código divergirem).

## Próximas etapas

!!! info "Decisão"
    - [x] **Implantar** — seguir para [Implementação](implementacao.md)
    - [ ] **Iterar** — voltar a uma fase anterior; indique qual e por quê
    - [ ] **Encerrar** — registrar o aprendizado e não prosseguir

| Ação | Responsável | Prazo |
|:---|:---|:---|
| Publicar a documentação (MkDocs) e o app Streamlit | Venicios | entrega da disciplina |
| Se houver nova coleta futura, repetir a comparação de espaço de atributos antes de reusar a mesma configuração | Venicios | próxima iteração, se houver |

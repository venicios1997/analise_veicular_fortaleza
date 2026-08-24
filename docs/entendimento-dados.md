# Entendimento dos dados

Esta página responde a três perguntas sobre o conjunto de dados: **o que existe**, **em que
qualidade** e **o que isso impede ou permite** dentro dos objetivos do projeto.

## Dados iniciais

Os dados analisados aqui vêm de `data/raw/anuncios_detalhados.csv` (ver
[Fonte dos dados](fonte-dados.md)). A apuração completa está no notebook
`00-dicionario-dados.ipynb` (dicionário de dados) e no `01-analise-exploratoria.ipynb`
(o roteiro de 8 etapas descrito abaixo).

## Descrição dos dados

### Grão

Cada linha é um **anúncio de veículo usado** (`link`, chave única). A tabela é
achatada — não há dimensão embutida a desnormalizar; cada anúncio já é a
unidade de análise final do projeto (ver Canvas do Problema, seção "Entidade de
análise").

### Grupos de colunas

| Dimensão | Exemplos de colunas |
|:---|:---|
| Identificação | `titulo`, `marca`, `modelo`, `versao`, `link` |
| Características técnicas | `ano`, `km`, `cambio`, `combustivel`, `carroceria`, `portas`, `cor`, `motor` |
| Características comerciais | `preco`, `vendedor_tipo`, `aceita_troca`, `unico_dono`, `bairro`, `municipio` |
| Referência de mercado | `valor_fipe_olx` (bruta), `valor_fipe_final` (mesclada com a API pública) |
| Metadado de coleta | `data_coleta` |

### Cobertura frente aos critérios de sucesso

| Requisito | Situação |
|:---|:---|
| 1.000 a 5.000 anúncios (meta do Canvas) | **atendida** — 2.565 coletados |
| Variáveis de identificação, técnicas e comerciais completas | **atendida** — as 23 colunas cobrem todas as dimensões do Canvas |
| Preço de venda efetivo (não só anunciado) | **inviável** — a OLX não publica esse dado |
| Série temporal de anúncios | **inviável** — coleta de um único dia (21/08/2026) |

## Qualidade dos dados

### Valores sentinela

A leitura padrão do `pandas` já trata corretamente os vazios deste CSV — não
há sentinela textual (`"NA"`, `"-"`) a decodificar manualmente. A única
sentinela numérica encontrada
foi descoberta na análise, não na leitura:

| Sentinela | Significado |
|:---|:---|
| `km = 999998` | Valor de preenchimento/erro de digitação (1 registro) — próximo de 10⁶ − 2, não uma quilometragem real |

Tratada em `02-ajustes-dados.ipynb`, bloco 4 (o registro é removido, não
corrigido — não há como inferir o valor real).

### Achados que mudam a análise

1. **62 anúncios com falha total de captura**: as 7 colunas do bloco
   `window.dataLayer` (marca, câmbio, combustível, carroceria, portas, tipo de
   vendedor, município) ficam vazias **juntas** quando o bloco falha ao
   carregar — falha do scraper, não ausência de informação do anúncio. Esses
   registros são removidos (`02-ajustes-dados.ipynb`, bloco 3), não imputados.
2. **Ausência real e legítima, não estrutural**: todo carro tem marca e
   câmbio — o que falta é real. `aceita_troca` (24,7%) e `unico_dono` (16,1%)
   dependem do vendedor informar; viram categoria explícita `NaoInformado` em
   vez de serem descartadas (um limiar único de 5% de ausência teria
   jogado fora essas duas variáveis, que o Canvas do Problema pede).
3. **`preco` e `valor_fipe_final` correlacionam em 0,98** (Spearman) — a FIPE é,
   por construção, quase um espelho do preço pedido. Por isso fica reservada
   da modelagem, e não descartada por redundância (ambas já são reservadas).
4. **Sem série temporal**: `data_coleta` tem um único valor distinto (a coleta
   foi feita num dia) — inviabiliza qualquer leitura de sazonalidade ou
   tendência, mas não afeta a segmentação por características do veículo.

## Dimensões-chave

`valor_fipe_final` não vem pronta na origem — é derivada na ingestão
(`src/data/ingestao.carregar_bruto()`), mesclando duas fontes.

| Valor | Descrição | Regra de derivação |
|:---|:---|:---|
| FIPE da OLX | Valor de referência que a própria OLX calcula e mostra no anúncio | `valor_fipe_olx` quando presente (90,7% dos anúncios) |
| FIPE via API pública | Casamento de marca/modelo/ano por similaridade de texto contra `parallelum.com.br/fipe` | Usada como *fallback* quando `valor_fipe_olx` é nula — eleva a cobertura para 97,1% |
| Sem FIPE | Nem a OLX nem o *fallback* encontraram valor | Permanece nula (2,9% dos anúncios); a coluna é reservada, então isso não afeta a modelagem |

## Limitações

- **Preço anunciado, não vendido** — afeta a leitura de "oportunidade
  comercial" (desconto vs. FIPE): mede intenção de venda, não transação
  fechada. Impacta o Objetivo 2 dos [critérios de sucesso](criterios-sucesso.md).
- **Sem série temporal** — os resultados retratam o mercado em 21/08/2026, não
  uma tendência. Não impede nenhum objetivo, mas limita a validade dos números
  no tempo.
- **Alta cardinalidade em `marca` (41 categorias) e `município` (27)** — cauda
  longa; tratada na modelagem agrupando categorias raras em `Outras` (ver
  [Modelagem dos dados](modelagem.md)).

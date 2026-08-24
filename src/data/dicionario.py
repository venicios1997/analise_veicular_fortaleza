"""Dicionário de dados: papel de cada coluna no projeto.

Este módulo é a **fonte única da verdade** sobre o papel de cada coluna da
base bruta de anúncios (`data/raw/anuncios_detalhados.csv`). As colunas já
chegam em `snake_case` português — não há camada de renomeação a partir de
um nome original em inglês.

Três decisões registradas aqui, e não no código de análise:

1. **`preco` é rótulo reservado.** Não entra em nenhuma etapa de
   modelagem — só na avaliação *a posteriori*. Usá-lo antes descaracterizaria
   o problema não supervisionado (o objetivo é segmentar por características
   do veículo, não redescobrir faixas de preço).
2. **`valor_fipe_olx` também fica de fora da modelagem.** É, por
   construção, função de `marca`/`modelo`/`ano` — incluí-lo redundaria com
   essas variáveis. Fica reservado para calcular, por segmento, o desconto
   médio em relação à FIPE — a métrica de oportunidade comercial que
   responde à Pergunta 5 do projeto.
3. **`bairro` fica de fora da modelagem.** Localização é candidata natural a
   determinante de preço; incluí-la faria o algoritmo redescobrir geografia
   por caminho indireto. Fica reservada para validação externa dos
   segmentos (`municipio`, com menos categorias e maior cobertura, entra na
   modelagem no lugar dela).
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Papel de cada coluna no projeto
# --------------------------------------------------------------------------- #

#: Rótulo reservado. Uso exclusivo na avaliação a posteriori.
ROTULO_RESERVADO = "preco"

#: Reservada para validação externa: não entra na modelagem (proxy de preço/geografia).
RESERVADA_VALIDACAO = "bairro"

#: Reservada para leitura de oportunidade comercial (desconto vs. FIPE), não
#: para segmentação — é derivada de marca/modelo/ano, portanto redundante
#: como atributo de agrupamento. É a FIPE já mesclada (OLX + API pública,
#: ver `src/data/ingestao.py`), não a coluna bruta `valor_fipe_olx`.
RESERVADA_FIPE = "valor_fipe_final"

#: Identificador único do anúncio.
IDENTIFICADORES = ["link"]

#: Texto livre / alta cardinalidade — não entram nos loops descritivos
#: tipados (título, versão e localização bruta não têm papel na modelagem;
#: `modelo` fica de fora por ter ~224 categorias, granularidade excessiva
#: para one-hot direto).
TEXTO_LIVRE = ["titulo", "localizacao", "versao", "modelo"]

#: Registrado pelo scraper (data em que o anúncio foi coletado); é metadado
#: de coleta, não característica do veículo.
METADADO_COLETA = "data_coleta"

# --------------------------------------------------------------------------- #
# Espaço de atributos da modelagem
# --------------------------------------------------------------------------- #

#: Numéricas contínuas e discretas. Descrevem idade e uso do veículo.
NUMERICAS = ["ano", "km"]

#: Nominais: sem ordem, entram por one-hot na preparação. `marca` tem
#: cardinalidade alta (42 categorias) — a etapa 03 decide se agrupa as
#: menos frequentes em "outras" antes do encoding.
NOMINAIS = [
    "marca",
    "cambio",
    "combustivel",
    "carroceria",
    "portas",
    "vendedor_tipo",
    "aceita_troca",
    "unico_dono",
    "municipio",
]

#: Esta base não tem colunas com escala ordinal declarada (do tipo
#: `Ex > Gd > TA > Fa > Po`); todas as nominais entram sem ordem.
ORDINAIS: list[str] = []

#: Binária derivada na 02-ajustes-dados (`km == 0`). Sinaliza veículo
#: novo/seminovo de vitrine — informação que `km` e `ano` sozinhos não
#: capturam (um `ano` recente com `km` maior que 0 é usado; `km == 0` é
#: categoricamente diferente).
BINARIAS = ["zero_km"]

#: As duas leituras do espaço de atributos comparadas no projeto.
ESPACO_NUMERICO = NUMERICAS
ESPACO_MISTO = NUMERICAS + NOMINAIS + BINARIAS

#: Limiar de assimetria a partir do qual a transformação (`log1p`) se
#: justifica. Convenção usual; ver notebook 01, 2ª etapa.
LIMIAR_ASSIMETRIA = 0.75

#: Variáveis contínuas cuja assimetria **na base curada** supera o limiar e
#: que, por isso, recebem `log1p` antes da padronização. Medido no notebook
#: `02-ajustes-dados`: `km` = 0,94 (cauda longa à direita — carros de alta
#: quilometragem). `ano` chega a −1,19, mas com sinal negativo: é assimetria à
#: **esquerda** (cauda de carros antigos), e `log1p` só corrige cauda à
#: direita — por isso `ano` fica de fora apesar de exceder o limiar em
#: módulo.
ASSIMETRICAS = ["km"]

# --------------------------------------------------------------------------- #
# Qualidade dos dados — específico da coleta por scraping
# --------------------------------------------------------------------------- #

#: As sete colunas que vêm do mesmo bloco `window.dataLayer` da página do
#: anúncio (ver `Software/coleta/scraper.py::_extrair_bloco_datalayer`).
#: Quando o bloco falha ao carregar, as sete ficam vazias **juntas** — é
#: falha de captura do scraper, não ausência de informação do vendedor.
NUCLEO_DATALAYER = [
    "marca",
    "cambio",
    "combustivel",
    "carroceria",
    "portas",
    "vendedor_tipo",
    "municipio",
]

#: Colunas em que a ausência é **real e legítima** (o vendedor não informou,
#: ou o campo ficou vazio no anúncio) e baixa o bastante para não justificar
#: descartar linha ou coluna. Cada uma recebe a categoria explícita
#: `NaoInformado` em vez de imputação estatística — não se inventa um valor
#: numérico, só se nomeia a ausência.
AUSENCIA_OPCIONAL = [
    "cambio",
    "combustivel",
    "carroceria",
    "portas",
    "aceita_troca",
    "unico_dono",
    "bairro",
    "cor",
    "motor",
    "tipo",
]

# --------------------------------------------------------------------------- #
# Descrição de negócio, para o dicionário publicado e para a aplicação
# --------------------------------------------------------------------------- #

DESCRICOES: dict[str, str] = {
    "preco": "Preço anunciado, em reais (rótulo reservado)",
    "ano": "Ano do veículo",
    "km": "Quilometragem informada no anúncio",
    "marca": "Marca do veículo",
    "modelo": "Modelo do veículo",
    "versao": "Versão/acabamento do veículo",
    "cambio": "Tipo de câmbio",
    "combustivel": "Tipo de combustível",
    "carroceria": "Carroceria do veículo",
    "portas": "Número de portas",
    "cor": "Cor do veículo",
    "motor": "Motorização declarada no anúncio",
    "vendedor_tipo": "Tipo de vendedor (particular ou profissional)",
    "aceita_troca": "Aceita troca por outro veículo",
    "unico_dono": "Veículo de único dono",
    "bairro": "Bairro do anunciante (reservado para validação externa)",
    "municipio": "Município do anunciante",
    "valor_fipe_olx": "Valor de referência FIPE (reservado para leitura de oportunidade)",
    "titulo": "Título do anúncio",
    "localizacao": "Localização declarada no card de listagem",
    "link": "URL do anúncio (identificador único)",
    "data_coleta": "Data da coleta do anúncio (metadado de scraping)",
    "zero_km": "Veículo com quilometragem zero (novo/seminovo de vitrine)",
    "idade_veiculo": "Idade do veículo em anos, calculada a partir de `config.ANO_REFERENCIA`",
    "km_por_ano": "Quilometragem média por ano de idade (intensidade de uso)",
    "desconto_fipe_pct": "Desconto do preço anunciado em relação à FIPE, em % (avaliação a posteriori)",
}

#: Rótulos curtos para gráficos.
ROTULOS_CURTOS: dict[str, str] = {
    "preco": "Preço",
    "ano": "Ano",
    "km": "Quilometragem",
    "marca": "Marca",
    "modelo": "Modelo",
    "cambio": "Câmbio",
    "combustivel": "Combustível",
    "carroceria": "Carroceria",
    "portas": "Portas",
    "cor": "Cor",
    "motor": "Motorização",
    "vendedor_tipo": "Tipo de vendedor",
    "aceita_troca": "Aceita troca",
    "unico_dono": "Único dono",
    "bairro": "Bairro",
    "municipio": "Município",
    "valor_fipe_olx": "Valor FIPE (OLX)",
}


def rotulo(coluna: str) -> str:
    """Devolve o rótulo curto de uma coluna, ou o próprio nome se não houver."""
    return ROTULOS_CURTOS.get(coluna, coluna.replace("_", " ").capitalize())

# Lacunas para Aplicação das Tabelas de Pontuação

## 1. Escopo

As lacunas abaixo são constatações sobre campos presentes ou ausentes nos quatro
datasets autorizados. Elas não completam, interpretam ou corrigem a norma.

## 2. Lacunas estruturais

### G-01 — ocorrência e quantidade

Os critérios fornecem unidade e valor, mas não contêm fatos, ocorrências ou
quantidades. A multiplicidade aplicável não pode ser obtida desses arquivos.

### G-02 — condições mantidas como texto

Condições existentes em `official_text` não possuem representação estruturada.
Entre as expressões observáveis estão duração mínima, fração acima de seis
meses, autorização, reconhecimento, registro, interesse institucional,
relevância, contribuição e comprovação. A auditoria não atribui significado
operacional a essas expressões.

### G-03 — escolha das variantes

Os quatro critérios do Anexo V estruturam valores para `titular` e `substituto`,
mas os datasets não fornecem o fato que seleciona uma dessas variantes.

### G-04 — acumulação

Não existe campo que declare se múltiplas ocorrências do mesmo critério, de
critérios distintos ou de períodos sobrepostos podem ser acumuladas.

### G-05 — exclusões

Não existe campo para exclusões, incompatibilidades ou consumo exclusivo de uma
mesma ocorrência por critérios diferentes.

### G-06 — limites e teto

Não foram encontrados limites mínimos, limites máximos ou teto de pontuação em
nível de critério, tabela, requisito ou conjunto.

### G-07 — arredondamento

Não existe regra estruturada de arredondamento. Os valores são strings com
separador decimal por vírgula.

### G-08 — dependências entre critérios

Não existe relação estruturada que condicione um critério a outro.

### G-09 — atos complementares

Os datasets não possuem campo que identifique ato complementar. Portanto, a
necessidade ou inexistência de tal ato não pode ser confirmada por estas
entradas.

### G-10 — codificação textual

Os textos carregados exibem sequências compatíveis com corrupção de codificação,
como `Ã` e `Â`. IDs e referências estruturadas continuam legíveis, mas a
fidelidade textual deve ser corrigida ou validada na fonte documental antes de
qualquer processamento automático de texto.

## 3. Referências cruzadas

As únicas referências cruzadas explícitas são seis relações `detailed_by`, cada
uma ligando um requisito à tabela do anexo correspondente. Não existem
referências cruzadas explícitas entre critérios.

## 4. Dependência humana

A classificação de todos os critérios como `ASSISTED` decorre da combinação:

- valor e unidade disponíveis;
- condição normativa preservada como texto;
- ausência de ocorrência, quantidade e decisão factual;
- ausência de regras de acumulação, exclusão, teto e arredondamento.

Nenhum critério foi classificado como `HUMAN_ONLY`, pois todos possuem valor
fixo ou variantes de valor e unidade. Nenhum foi classificado como
`FULLY_AUTOMATABLE`, pois nenhum possui toda a entrada factual e operacional
necessária nos datasets.

## 5. Impossibilidade atual

Com as quatro entradas isoladas, é impossível produzir automaticamente uma
pontuação oficial completa e demonstravelmente correta. É possível apenas
consultar a estrutura, apresentar valores e apoiar uma aplicação posterior.

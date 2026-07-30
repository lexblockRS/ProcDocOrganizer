# Auditoria das Tabelas Oficiais de Pontuação

## 1. Escopo e fontes

Esta auditoria utiliza exclusivamente:

- `decree_tables.json`;
- `decree_criteria.json`;
- `decree_requirements.json`;
- `decree_traceability.json`.

O código da aplicação, o motor legado e outras fontes não participaram da
análise. Este documento não calcula pontuação nem transforma texto normativo em
regra executável.

## 2. Estrutura encontrada

Os quatro arquivos declaram o schema
`decree-13048-documentary-model/1`, o documento
`BR-DEC-13048-2026` e a vigência em `2026-07-03`.

| Elemento | Quantidade | IDs únicos | Resultado |
|---|---:|---:|---|
| Tabelas | 6 | 6 | consistente |
| Requisitos | 6 | 6 | consistente |
| Critérios | 55 | 55 | consistente |
| Vínculos tabela–critério | 55 | 55 | consistente |
| Referências requisito–tabela | 6 | 6 | consistente |

Cada tabela corresponde a um anexo, a um inciso do art. 3º e a um requisito:

| Requisito | Tabela | Critérios |
|---|---|---:|
| `DEC13048-ART3-I` | `DEC13048-TABLE-ANEXO-I` | 10 |
| `DEC13048-ART3-II` | `DEC13048-TABLE-ANEXO-II` | 11 |
| `DEC13048-ART3-III` | `DEC13048-TABLE-ANEXO-III` | 3 |
| `DEC13048-ART3-IV` | `DEC13048-TABLE-ANEXO-IV` | 8 |
| `DEC13048-ART3-V` | `DEC13048-TABLE-ANEXO-V` | 4 |
| `DEC13048-ART3-VI` | `DEC13048-TABLE-ANEXO-VI` | 19 |

Não existem critérios órfãos, referências a critérios inexistentes ou tabelas
sem critérios.

## 3. Rastreabilidade

As seis tabelas identificam `article`, `inciso`, `annex`, `table`,
`legal_reference` e `hierarchy`. Os critérios repetem o anexo e a tabela e
acrescentam o item. Os seis requisitos apontam para as mesmas combinações de
inciso, anexo e tabela.

`decree_traceability.json` declara:

- 6 requisitos;
- 55 critérios;
- 6 tabelas;
- 6 referências `detailed_by`, uma de cada requisito para sua tabela.

As contagens declaradas coincidem com as coleções. A cadeia
requisito → tabela → critério pode ser reconstruída sem consultar outra fonte.

## 4. Elementos de pontuação modelados

### 4.1 Valores fixos

Há 51 critérios com um valor textual único em `points`. Os valores presentes
são `1`, `1,5`, `3`, `3,5`, `4,5`, `7,5`, `15`, `20`, `25` e `30`.

### 4.2 Valores variáveis

Quatro critérios do Anexo V possuem `points = null` e duas variantes explícitas:
`titular` e `substituto`. Cada variante possui seu próprio valor.

### 4.3 Unidades

Todos os 55 critérios possuem uma unidade textual. Foram encontradas 14
unidades distintas:

- por ano ou fração acima de seis meses: 11;
- por designação: 11;
- por produto: 8;
- por projeto: 8;
- por evento: 5;
- por prêmio: 3;
- por curso: 2;
- por capacitação, grupo de pesquisa, mês, mandato, patente, publicação e
  sistema: 1 cada.

## 5. Elementos não modelados

Os arquivos não apresentam campos estruturados para:

- faixas de pontuação;
- limites mínimos globais;
- limites máximos globais;
- teto de pontuação;
- regras de acumulação;
- regras de exclusão entre critérios;
- arredondamento;
- dependências entre critérios.

Alguns textos oficiais contêm condições, como duração mínima, fração temporal,
interesse institucional, reconhecimento formal, relevância ou comprovação. Nos
arquivos auditados essas condições permanecem dentro de `official_text`; não
existem operadores ou parâmetros estruturados que permitam executá-las.

## 6. Aplicabilidade automática

Os dados permitem localizar a tabela, a unidade e o valor aplicável depois que
um fato tiver sido qualificado e quantificado. Eles não permitem, isoladamente:

- decidir que o fato satisfaz o texto do critério;
- contar automaticamente as unidades realizadas;
- escolher uma variante sem receber o papel de titular ou substituto;
- aplicar condições textuais não estruturadas;
- determinar acumulação, exclusão, teto ou arredondamento.

Consequentemente:

- `FULLY_AUTOMATABLE`: 0 critérios;
- `ASSISTED`: 55 critérios;
- `HUMAN_ONLY`: 0 critérios.

`ASSISTED` significa que o valor e a unidade fornecem apoio estruturado, mas a
aplicação depende de fatos ou decisões não contidos nos quatro datasets. Não
significa que o critério foi atendido.

## 7. Conclusão

A correspondência estrutural entre requisitos, tabelas e critérios está
completa. As tabelas podem sustentar consulta e aplicação assistida dos valores,
mas os quatro arquivos não são suficientes para pontuação inteiramente
automática. Nenhum cálculo foi realizado nesta auditoria.

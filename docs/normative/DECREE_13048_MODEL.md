# Decreto nº 13.048/2026 — modelo normativo documental

## 1. Escopo e fonte

Este conjunto registra, sem interpretação, a estrutura textual do Decreto nº
13.048, de 3 de julho de 2026, que estabelece critérios e procedimentos para a
concessão do RSC-PCCTAE.

Fonte exclusiva: <https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d13048.htm>

O texto consultado informa publicação no DOU de 3 de julho de 2026, edição
extra, e vigência na data da publicação. O próprio portal adverte que a versão
HTML não substitui a publicação no DOU.

## 2. Princípios de modelagem

- O modelo é documental, não é um motor de avaliação.
- Os identificadores são estáveis e derivados da posição jurídica.
- O texto oficial é preservado nos registros de origem.
- Ausência de informação é representada por `null`.
- Pontos, percentuais, prazos e cardinalidades são dados literais, sem
  arredondamento ou inferência.
- A estrutura não cria `Requirement`, `Criterion`, `ScoringRule`,
  `EvaluationRule`, `Version`, DTO, Repository, Service ou qualquer classe.

## 3. Inventário

| Conjunto | Quantidade | Arquivo |
|---|---:|---|
| Artigos | 22 | `decree_articles.json` |
| Requisitos do art. 3º | 6 | `decree_requirements.json` |
| Critérios específicos dos anexos | 55 | `decree_criteria.json` |
| Tabelas/anexos | 6 | `decree_tables.json` |
| Categorias documentais expressas | 10 | `decree_documents.json` |
| Índices de rastreabilidade | 5 conjuntos | `decree_traceability.json` |

## 4. Estrutura jurídica

```text
Decreto nº 13.048/2026
├── corpo normativo
│   ├── arts. 1º a 22
│   ├── parágrafos, incisos e alíneas
│   └── vigência: art. 22
└── anexos
    ├── Anexo I   — requisito I  — 10 critérios
    ├── Anexo II  — requisito II — 11 critérios
    ├── Anexo III — requisito III — 3 critérios
    ├── Anexo IV  — requisito IV — 8 critérios
    ├── Anexo V   — requisito V  — 4 critérios com variantes titular/substituto
    └── Anexo VI  — requisito VI — 19 critérios
```

## 5. Estrutura da concessão registrada pela norma

O art. 3º enumera seis requisitos. O art. 4º e seu parágrafo único enumeram a
comprovação documental. O art. 5º contém seis níveis, pontuações mínimas,
quantidades mínimas de critérios e, nos níveis IV a VI, requisitos que devem
estar representados. O § 1º do art. 5º registra os percentuais do Incentivo à
Qualificação. Os §§ 2º a 4º tratam de acumulação, uso único e exclusão do
desempenho meramente ordinário.

Os Anexos I a VI associam a cada requisito uma tabela com item, critério
específico, unidade de medida e pontos. O Anexo V apresenta dois valores por
item, conforme atuação como titular ou substituto; essas variantes são
preservadas literalmente.

## 6. Procedimento

Os arts. 6º a 9º tratam da CRSC-PCCTAE. Os arts. 10 a 12 tratam de efeitos
financeiros, interstício e estágio probatório. O art. 13 especifica a instrução
do requerimento. Os arts. 14 e 15 registram verificações e fundamentação. Os
arts. 16 a 18 tratam de recurso, ato concessório e implantação. Os arts. 19 a
21 tratam de acompanhamento, controle e atos complementares.

## 7. Rastreabilidade

Cada registro extraído contém:

- `document_id`;
- posição jurídica (`article`, `paragraph`, `inciso`, `annex`, `table`,
  `item`);
- `official_text`;
- `legal_reference`;
- `hierarchy`;
- `effective_from`;
- `notes`.

`decree_traceability.json` indexa os arquivos e seus intervalos de
identificadores. A URL oficial é repetida nos metadados de cada arquivo para
que nenhum conjunto dependa deste documento Markdown para identificar a fonte.

## 8. Ambiguidades e lacunas preservadas

- O decreto admite, no art. 4º, parágrafo único, inciso VII, “outros documentos
  institucionais” a serem estabelecidos em ato ministerial, sem enumerá-los.
- O art. 14 usa a formulação “poderá ser indeferido” seguida de critérios
  objetivos; o conjunto não transforma essa redação em algoritmo.
- O art. 5º, § 3º, remete a sobreposição à avaliação fundamentada da comissão,
  sem fornecer regra automática de desempate.
- O art. 5º, § 4º, e o art. 15 empregam conceitos qualitativos que não são
  quantificados.
- O art. 19 vincula concessões a limite e disponibilidade orçamentária sem
  fornecer, neste decreto, fórmula de distribuição.
- Os atos complementares previstos nos arts. 4º, parágrafo único, VII, 13, I,
  19, § 1º, e 21 não integram esta extração.

Esses pontos permanecem textuais e não foram preenchidos por inferência.

# Inventário de Fontes Normativas e Operacionais do RSC

## 1. Objetivo

Este inventário registra os materiais efetivamente disponíveis no repositório
que mencionam a futura camada normativa do Reconhecimento de Saberes e
Competências dos Técnicos Administrativos em Educação. Ele separa fontes
normativas, instrumentos operacionais, materiais auxiliares e implementação de
software para impedir que código legado seja tratado como norma oficial.

## 2. Escopo

A auditoria abrangeu arquivos versionados de documentação, configuração,
domínio RSC, catálogos, validação, pontuação e testes. Foram procurados também
atos normativos, anexos, formulários, planilhas, manuais, pareceres e exemplos
de processo.

Não houve pesquisa externa. Não foram inferidos número, autoria, data,
vigência ou conteúdo de qualquer ato ausente.

## 3. Metodologia

1. enumeração dos arquivos versionados, independentemente do nome;
2. pesquisa textual por termos ligados a RSC, critérios, requisitos,
   pontuação, legislação e instrumentos operacionais;
3. leitura dos materiais com conteúdo normativo aparente;
4. classificação por natureza e autoridade;
5. cálculo SHA-256 dos arquivos catalogados;
6. registro separado das ausências e conflitos em `NORMATIVE_GAPS.md`.

Os checksums descrevem o estado local auditado e não conferem autenticidade
normativa.

## 4. Resultado por grupo

### A. Fontes normativas

Nenhuma fonte normativa primária está disponível no repositório. Não foram
localizados textos de legislação federal, atos regulamentares federais,
regulamentos institucionais da UNIPAMPA ou seus anexos.

### B. Instrumentos operacionais

Nenhum formulário oficial, planilha de pontuação, edital, orientação
institucional, manual operacional ou exemplo de processo foi localizado.

### C. Interpretação ou material auxiliar

Foram encontrados modelos conceituais, descrições de workflow, navegação,
modelo de domínio e decisões arquiteturais. Esses materiais orientam o
software, mas não possuem autoridade normativa.

### D. Implementação de software

Existe código que se denomina catálogo oficial, além de serviços e testes de
pontuação e validação. A origem primária não está ligada aos itens
implementados; portanto, todo esse conjunto é classificado como legado e
requer validação humana.

## 5. Inventário

| ID | Grupo | Título | Tipo | Emissor | Número/data/vigência | Caminho e rastreabilidade | Formato | Função | Autoridade | Análise |
|---|---|---|---|---|---|---|---|---|---|---|
| AUX-001 | C | Modelo Conceitual do ProcDoc RSC | material auxiliar | Projeto ProcDocOrganizer | não confirmado | `docs/domain-model.md`, §§ 2–6; linhas 52–53, 86 e 163–199 | Markdown | visão conceitual | não normativo | revisado |
| AUX-002 | C | Workflow de um Projeto RSC | material auxiliar | Projeto ProcDocOrganizer | não confirmado | `docs/workflow.md`, §§ 9–10; linhas 256–298 | Markdown | fluxo conceitual e memória de cálculo | não normativo | revisado |
| AUX-003 | C | Modelo de Navegação do ProcDoc RSC | material auxiliar | Projeto ProcDocOrganizer | não confirmado | `docs/navigation-model.md`, §§ 9–10; linhas 309–350 | Markdown | especificação de experiência | não normativo | revisado |
| AUX-004 | C | RSC Domain Model v1.0 | material auxiliar | Projeto ProcDocOrganizer | não confirmado | `docs/domain/RSC_DOMAIN_MODEL.md`, §§ 5.5, 10.3, 12 e 16.6; linhas 288–304, 646–660, 778–796 e 935–946 | Markdown | modelo interno e registro de pendências | não normativo | revisado |
| AUX-005 | C | ADR-029 — Auditabilidade dos objetos RSC | material auxiliar | Projeto ProcDocOrganizer | ADR-029; data não confirmada | `docs/architecture/adr/ADR-029-rsc-auditability.md`, §§ Contexto–Consequências, linhas 7–21 | Markdown | decisão arquitetural | não normativo | revisado |
| AUX-006 | C | ADR-030 — Versionamento normativo futuro | material auxiliar | Projeto ProcDocOrganizer | ADR-030; data não confirmada | `docs/architecture/adr/ADR-030-normative-versioning.md`, §§ Contexto–Consequências, linhas 7–21 | Markdown | decisão arquitetural | não normativo | revisado |
| SW-001 | D | Catálogo denominado `OfficialRscCatalog` | implementação legada | não identificado | não identificado | `applications/rsc/catalogs/official_criteria.py`: `_TITLES` linha 15, `_ROWS` linha 48, `_VARIANT_ROWS` linha 102 e `OfficialRscCatalog` linhas 155–195 | Python | catálogo executável de requisitos, critérios, unidades e pontos | não normativo | requer confronto com fontes primárias |
| SW-002 | D | `RscScoringService` | implementação legada | não identificado | não identificado | `applications/rsc/services/scoring_service.py`: `calculate_activity`, linha 21; `calculate_requirement`, linha 45; `calculate_process`, linha 63 | Python | cálculo executável | não normativo | requer validação humana |
| SW-003 | D | `RscValidationService` | implementação legada | não identificado | não identificado | `applications/rsc/services/validation_service.py`: `validate_activity`, linha 34; `validate_process`, linha 189 | Python | validação executável | não normativo | requer validação humana |
| TEST-001 | D | Testes da fundação de domínio RSC | teste legado | não identificado | não identificado | `applications/rsc/tests/test_domain_foundation.py`: `OfficialCatalogTests`, linhas 29–96; testes de pontuação e validação, linhas 257–417 | Python | expectativas executáveis | não normativo | requer validação humana |
| TEST-002 | D | Testes dos casos de uso de validação e pontuação | teste legado | não identificado | não identificado | `applications/rsc/tests/test_validation_scoring_use_cases.py`, classes e métodos de validação/pontuação; linhas 1–338 | Python | caracterização de orquestração | não normativo | requer validação humana |

Os campos estruturados equivalentes, incluindo checksums, estão em
`normative_sources.json`.

## 6. Hierarquia normativa preliminar

A hierarquia abaixo é apenas uma estrutura de organização a ser preenchida
quando as fontes forem fornecidas:

```text
Legislação federal aplicável                         [não disponível]
└── Ato regulamentar federal                        [não disponível]
    └── Anexos e tabelas oficiais                    [não disponíveis]
        └── Regulamento institucional da UNIPAMPA    [não disponível]
            ├── Editais/orientações institucionais  [não disponíveis]
            ├── Formulários oficiais                [não disponíveis]
            └── Planilha operacional de pontuação   [não disponível]

Materiais auxiliares internos                        [disponíveis]
Implementação e testes legados                       [disponíveis; sem autoridade]
```

Essa ordem não afirma a existência nem a precedência jurídica de documentos
específicos. A hierarquia final requer validação humana.

## 7. Relação entre os materiais

- `docs/domain-model.md`, `docs/workflow.md` e `docs/navigation-model.md`
  descrevem conceitos e fluxos pretendidos.
- `docs/domain/RSC_DOMAIN_MODEL.md` consolida o modelo interno e explicita que
  versão normativa, vigência e enquadramento ainda dependem de decisões.
- ADR-029 exige governança de auditoria antes da pontuação plenamente
  auditável.
- ADR-030 exige resultados reproduzíveis e vinculados a versão e vigência.
- `official_criteria.py` materializa 6 requisitos e 55 critérios, mas somente
  declara ter sido transcrito dos “Anexos I a VI”; os anexos não estão
  disponíveis para conferência.
- `scoring_service.py` e `validation_service.py` consomem o catálogo legado.
- os testes fixam comportamento e valores do software, não sua validade
  normativa.

## 8. Conflitos e ambiguidades

1. O nome `OfficialRscCatalog` e sua docstring sugerem oficialidade, mas não há
   referência identificável ao ato, versão, data, vigência, páginas ou anexos.
2. A documentação exige versionamento normativo futuro, enquanto o catálogo
   atual é um singleton sem metadados de versão ou vigência.
3. Valores e unidades estão codificados e testados, mas não existe matriz de
   rastreabilidade que associe cada linha a uma página/célula oficial.
4. O software possui regras de exclusão, arredondamento implícito, variantes e
   severidades de validação sem fonte primária disponível.
5. Não há instrumentos institucionais da UNIPAMPA para verificar adaptações
   locais, competência decisória ou fluxo operacional.

## 9. Limitações

- não foi possível validar autenticidade, completude ou vigência;
- não existem páginas ou células oficiais para citar;
- nomes de arquivos e classes não foram aceitos como prova normativa;
- checksums cobrem apenas materiais internos;
- o working tree já continha alterações anteriores, que não foram modificadas
  por esta auditoria.

## 10. Próximos passos

1. obter as fontes federais e institucionais em versão oficial;
2. obter todos os anexos e instrumentos operacionais correspondentes;
3. confirmar número, órgão emissor, publicação e intervalo de vigência;
4. criar matriz item a item entre fonte, página/tabela e catálogo executável;
5. submeter divergências a responsável humano competente;
6. somente depois modelar versões normativas e regras executáveis.

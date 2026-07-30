# Decisões Arquiteturais do Pipeline RSC

## ADR-RSC-001 — Snapshot factual como única entrada

Status: aceita.

Decisão: Engines normativos não acessam Aggregate Roots, Repositories ou
SQLite. Toda informação factual entra por `EvaluationContext`.

Consequência: o Builder é a única fronteira autorizada a consultar
Repositories.

## ADR-RSC-002 — Pipeline linear e append-only

Status: aceita.

Decisão: cada estágio cria um novo objeto imutável e preserva o estágio
anterior.

Consequência: há duplicação deliberada de dados, compensada por
explicabilidade e ausência de mutação.

## ADR-RSC-003 — Modelo Normativo somente leitura

Status: aceita.

Decisão: Engines consultam capacidades por Protocol e nunca alteram catálogos.

Consequência: adapters podem variar, mas precisam garantir IDs, origem e
valores imutáveis.

## ADR-RSC-004 — Matching exclusivamente explícito

Status: aceita.

Decisão: candidatos dependem de vínculos estruturados em metadata. Não há
similaridade textual, IA ou inferência.

Consequência: ausência de vínculo não significa ausência de enquadramento.

## ADR-RSC-005 — Qualificação documental não é força probatória

Status: aceita.

Decisão: “aceito” significa associação com categoria oficial, não autenticidade
nem suficiência.

Consequência: o Assessment não pode converter documentação compatível em
satisfação do critério.

## ADR-RSC-006 — Verificação separada de decisão

Status: aceita.

Decisão: condições `STRUCTURED` podem ser verificadas; `ASSISTED` produz
proposta não definitiva; `HUMAN_ONLY` permanece humana.

Consequência: estados descrevem operações e pendências, nunca aprovação.

## ADR-RSC-007 — Lacuna e ausência permanecem visíveis

Status: aceita.

Decisão: ausência de fato gera `INSUFFICIENT_INFORMATION`; ausência de
estrutura normativa gera `NORMATIVE_GAP`.

Consequência: `null` não é convertido em reprovação ou fato.

## ADR-RSC-008 — Assessment como consolidação, não recálculo

Status: aceita.

Decisão: o Assessment agrega resultados e preserva `source_evaluation`.

Consequência: mudanças nas regras de verificação pertencem ao Engine anterior.

## ADR-RSC-009 — Metadata como integração transitória

Status: aceita com dívida técnica.

Decisão atual: `criterion_candidate_links` e `constraint_facts` residem em
metadata congelado.

Risco: contratos textuais são frágeis e não descobertos estaticamente.

Direção futura: substituir dicionários por contratos factuais imutáveis, sem
acrescentar regra normativa.

## ADR-RSC-010 — Validação documental pertence à qualificação

Status: proposta para decisão futura.

Constatação: o Candidate Engine hoje filtra categoria documental, sobrepondo a
responsabilidade do Evidence Qualification Engine.

Direção recomendada: Candidate preserva vínculo; Qualification classifica.
Nenhuma mudança foi realizada nesta auditoria.

## ADR-RSC-011 — Imutabilidade profunda na fronteira normativa

Status: proposta para decisão futura.

Constatação: dataclass congelada não congela automaticamente
`expected_value` ou outros objetos fornecidos por adapters.

Direção recomendada: normalizar valores normativos para escalares, tuplas,
frozensets e mappings somente leitura.

## ADR-RSC-012 — Extensão de operadores por registry

Status: proposta para decisão futura.

Constatação: novos operadores exigem alteração de `_apply`.

Direção recomendada: registry fechado por whitelist, determinístico e sem
execução dinâmica arbitrária.

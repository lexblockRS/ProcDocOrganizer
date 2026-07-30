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

## ADR-RSC-013 — Computabilidade autodescritiva das medições

Status: aceita.

Invariante: toda `Measurement` possui uma política explícita de
computabilidade. A computabilidade não depende de uma regra única para
todos os tipos; cada tipo define as informações mínimas que devem estar
presentes. Na ausência de política explícita, o tipo é considerado
`NOT_COMPUTABLE`.

Políticas atualmente consolidadas:

- `QUANTITY`: exige `measurement.amount`;
- `COUNT`: exige `measurement.amount`;
- `HOURS`: exige `measurement.amount`;
- `DURATION`: exige intervalo temporal canônico completo, com data inicial
  e data final válidas; não exige `measurement.amount`.

Consequência: um intervalo constitui a informação factual de uma medição
`DURATION`, mas sua transformação em anos, meses, dias ou quantidade
normativa permanece posterior.

## ADR-RSC-014 — Compatibilidade separada da validação e do cálculo

Status: aceita.

Decisão: a compatibilidade entre o tipo factual de uma `Measurement` e a regra
normativa é avaliada em `ExecutionCompatibility`, depois da
`ExecutionValidation` e antes do `CriterionExecutionContract`.

Consequência: Validation responde somente por completude e consistência do
fato; o Kernel executa somente aritmética sobre contratos preparados. Regras
como `PER_YEAR`, `PER_MONTH`, `PER_EVENT` e `PER_PUBLICATION` reutilizam a
mesma infraestrutura de compatibilidade sem introduzir verificações
específicas nesses dois componentes.

## ADR-RSC-015 — Conhecimento normativo reside no catálogo

Status: aceita.

Decisão: descrição, família, unidade, Measurement requerida, política de
compatibilidade, motor, valor, limites, dependências, revisão humana e
explicabilidade dos critérios passam a ser representados por
`NormativeCriterionCatalog`.

O Kernel conhece apenas motores aritméticos e recebe operandos pelo contrato.
Ele não conhece códigos específicos do Decreto. As políticas de
compatibilidade também pertencem ao catálogo e são consumidas por
`ExecutionCompatibility`.

Consequência: os 55 critérios são parametrizados e validados como configuração
imutável. Os JSON anteriores permanecem como artefatos transitórios de
comparação e integração; não constituem decisão de persistência definitiva.

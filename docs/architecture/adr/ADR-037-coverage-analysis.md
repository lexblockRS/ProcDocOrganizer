# ADR-037 — Coverage Analysis

**Status:** ACCEPTED
**Data:** 2026-07-31
**Decisores:** Equipe de Arquitetura

**Relacionada a:**

- `PRODUCT_VISION`;
- ADR-034 — Presentation Workspace Navigation;
- ADR-035 — Resource Presentation Model;
- ADR-036 — Workspace Insights;
- RFC-004 — Coverage Analysis.

## Contexto

O ProcDocOrganizer já possui Workspace Navigation, Resource Model, Workspace
Insights, Evaluation Pipeline, Validation, Compatibility, Results e Evaluation
Reports. Entretanto, ainda não existe uma representação estruturada do grau de
organização e cobertura operacional de um Project.

As informações estão distribuídas entre Documents, Evidences, ExecutionFacts,
Bindings e resultados normativos. É desejável produzir uma análise consolidada
sem introduzir novas regras normativas.

## Decisão

Adotar Coverage como análise operacional, multidimensional, imutável e somente
leitura.

Coverage descreve presença, relacionamento, estruturação, utilização e projeção
de resultados normativos já existentes. Nunca produzirá interpretações
jurídicas, substituirá Evaluation ou alterará o domínio.

## Princípio derivado

### P-006 — Coverage Is Observational

Coverage observa o estado do Project. Nunca interpreta significado normativo,
cria enquadramentos, produz decisões ou substitui Validation, Compatibility ou
Evaluation.

## Modelo

```text
CoverageInput
      ↓
CoverageAnalyzer
      ↓
CoverageResult
      ↓
CoverageInsightProvider
      ↓
InsightCollection
      ↓
Dashboard / Coverage View / futuros consumidores
```

CoverageResult é a autoridade estrutural. Insights são projeções derivadas.

## CoverageInput

CoverageAnalyzer operará sobre entrada imutável contendo conceitualmente:

- project_id;
- project_revision;
- referências documentais;
- referências de Evidence;
- referências de ExecutionFact;
- referências de Binding;
- snapshot de Evaluation opcional.

CoverageAnalyzer não consulta Qt, Views, SQLite ou Stores concretos.

## CoverageResult

CoverageResult representa exclusivamente dados estruturados. Não representa
View, Insight, domínio ou Aggregate. Deverá conter:

- document_coverage;
- evidence_coverage;
- factual_coverage;
- normative_coverage;
- overall_coverage;
- findings;
- source_revisions.

CoverageResult permanece imutável.

## CoverageFinding

Cada observação individual será representada por:

- scope;
- subject (`ResourceIdentity`);
- state;
- observed;
- expected opcional;
- explanation;
- reason_codes;
- related_resources.

CoverageFinding nunca referencia entidades, apenas ResourceIdentity.

## Escopos

Cobertura será analisada independentemente para:

- Document Coverage;
- Evidence Coverage;
- Factual Coverage;
- Normative Coverage;
- Overall Coverage.

Cada escopo possui significado próprio. Overall Coverage nunca elimina as
dimensões individuais.

## Estados

Estados recomendados:

- `EMPTY`;
- `PARTIAL`;
- `COMPLETE`;
- `NOT_EVALUATED`;
- `INCONSISTENT`;
- `UNKNOWN`.

Estados adicionais para Findings individuais:

- `ABSENT`;
- `INSUFFICIENT`;
- `NOT_APPLICABLE`.

Os estados representam apenas condições estruturais observadas, nunca
significado jurídico.

## Cobertura normativa

Coverage não executa Evaluation; apenas projeta resultados existentes.

Sem Evaluation, `normative_coverage = NOT_EVALUATED`. Com Evaluation, Coverage
projeta RequirementScores e CriterionScores existentes. Coverage nunca antecipa
decisões normativas.

## ExecutionFact sem Binding

ExecutionFact poderá simultaneamente apresentar presença factual, pendência de
enquadramento e ausência de utilização normativa. Essas dimensões permanecem
independentes. Coverage não reduz situações multidimensionais a um único
estado.

## Overall Coverage

Overall Coverage consolida os escopos sem calcular médias ou produzir
percentuais autoritativos. Percentuais poderão ser derivados somente para a
interface. As medidas autoritativas permanecem `covered`, `total` e `ratio`.

## Explicabilidade

Toda conclusão possuirá `explanation` e `reason_codes`. As explicações serão
derivadas dos próprios dados estruturados e nunca acrescentarão interpretação
normativa.

## Relação com Resources

Coverage referencia exclusivamente ResourceIdentity, nunca Resources completos
ou entidades. Navigation permanece independente da análise.

## Relação com Insights

CoverageResult não produz Insights. CoverageInsightProviders traduzem Findings
em Insights quando apropriado; nem todo Finding deverá produzir um Insight.

Dashboard e futuras funcionalidades poderão consumir simultaneamente
CoverageResult e InsightCollection, preservando os respectivos contratos.

## Revisões

CoverageResult registrará:

- project_revision;
- evaluation_revision opcional;
- analysis_version;
- generated_at opcional.

Coverage sempre representa o estado atual das revisões informadas. Histórico
analítico permanece fora desta ADR.

## Não objetivos

Esta ADR não cria IA, OCR, recomendações automáticas, sugestões jurídicas,
histórico ou persistência de Coverage, nem novos estados normativos.

## Consequências

Benefícios:

- análise uniforme e reutilizável;
- explicabilidade;
- independência da apresentação;
- suporte a Dashboard e Coverage Analyzer;
- suporte futuro à interface Web;
- integração natural com Workspace Insights.

Custos:

- necessidade de CoverageInput;
- definição explícita dos estados;
- manutenção de Findings;
- coordenação dos Insight Providers.

## Compatibilidade

A decisão permanece compatível com Qt, Web, CLI e API futura. Nenhuma
dependência de toolkit é introduzida.

## Decisão Final

O ProcDocOrganizer adotará Coverage como análise operacional estruturada,
multidimensional e somente leitura.

CoverageResult será a autoridade estrutural para diagnósticos de cobertura.
Workspace Insights permanecerão projeções derivadas. Evaluation continuará
sendo a única autoridade normativa do sistema.

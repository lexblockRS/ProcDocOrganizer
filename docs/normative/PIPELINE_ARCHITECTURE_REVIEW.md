# Revisão Arquitetural do Pipeline Normativo

## 1. Escopo

Componentes auditados:

1. `EvaluationContext`;
2. `CriterionCandidateEngine`;
3. `EvidenceQualificationEngine`;
4. `ConstraintEvaluationEngine`;
5. `CriterionAssessmentEngine`.

A auditoria é exclusivamente documental. Nenhuma refatoração ou mudança
funcional foi realizada.

## 2. Avaliação geral

O pipeline apresenta arquitetura linear, explicável e predominantemente
coesa:

```text
fontes factuais
    ↓
EvaluationContext
    ↓
CriterionCandidateCollection
    ↓
QualifiedCriterionCandidateCollection
    ↓
ConstraintEvaluatedCandidateCollection
    ↓
CriterionAssessmentCollection
```

Não existem imports reversos. Cada estágio depende apenas do contrato factual,
do Modelo Normativo somente leitura e de tipos produzidos por estágios
anteriores. Nenhum Engine acessa infraestrutura persistente.

O desenho é adequado como fundação, mas ainda não deve ser considerado uma API
arquitetural congelada. Existem acoplamentos implícitos por metadata, uma
sobreposição de responsabilidade documental e lacunas de imutabilidade
profunda nas fronteiras com adaptadores normativos.

## 3. Pontos fortes

### 3.1 Fluxo unidirecional

As dependências seguem o sentido do processamento. Não foram encontradas
dependências circulares entre os cinco componentes.

### 3.2 Separação entre fato e norma

`EvaluationContext` encerra o acesso a Repositories e Aggregate Roots. Os
Engines posteriores recebem snapshots e portas normativas somente leitura.

### 3.3 Preservação dos resultados anteriores

Cada envelope mantém o estágio anterior:

- `QualifiedCriterionCandidate.source_candidate`;
- `ConstraintEvaluatedCandidate.qualified_candidate`;
- `CriterionAssessment.source_evaluation`.

Isso permite recuperar a informação original mesmo quando projeções agregadas
eliminam duplicidades.

### 3.4 Segurança semântica

Os estados distinguem candidatura, compatibilidade documental, verificação,
revisão humana, lacuna e estágio do Assessment. Não há estado chamado
“satisfeito”, “aprovado” ou “elegível”.

### 3.5 Determinismo

Não existem dependências de relógio, aleatoriedade, IA, similaridade ou
ordenação implícita. A ordem é derivada das coleções de entrada.

### 3.6 Imutabilidade estrutural

A auditoria AST identificou 27 dataclasses `frozen=True`; os objetos públicos
também usam `slots=True`. Coleções produzidas são tuplas e as coleções-raiz
rejeitam duplicidades.

## 4. Fragilidades encontradas

### F-01 — responsabilidade documental antecipada

Severidade: alta.

`CriterionCandidateEngine` consulta `find_accepted_document()` e descarta um
vínculo cuja categoria não exista. Entretanto, avaliar documento compatível ou
incompatível é responsabilidade declarada de `EvidenceQualificationEngine`.

Consequências:

- um documento incompatível pode ser eliminado antes da qualificação;
- a qualificação não consegue explicar esse descarte para candidatos formados
  exclusivamente por aquele vínculo;
- os dois Engines validam a mesma categoria normativa.

Recomendação futura: o Candidate Engine deve preservar o vínculo explícito e
deixar toda classificação documental para o Evidence Qualification Engine.

### F-02 — schemas implícitos em metadata

Severidade: alta.

`criterion_candidate_links` e `constraint_facts` são contratos reais, mas
existem apenas como chaves textuais e dicionários genéricos. Campo renomeado ou
ausente é descoberto apenas em execução.

Recomendação futura: criar contratos imutáveis próprios na camada factual, sem
introduzir regra normativa.

### F-03 — imutabilidade profunda não garantida na fronteira normativa

Severidade: média.

`EvaluationContext` congela metadata recursivamente. Porém,
`NormativeCondition.expected_value` copia `record.expected_value` sem congelar.
`FactUsed.value` também é tipado como `object`, embora os fatos provenientes do
contexto sejam normalmente congelados.

Um adapter normativo que devolva lista ou dicionário mutável pode introduzir
mutabilidade interna em uma dataclass congelada.

Recomendação futura: definir e validar um tipo recursivo de valor normativo
imutável na fronteira do adapter.

### F-04 — candidato comprime múltiplas origens factuais

Severidade: média.

A identidade de deduplicação do candidato é
critério/Activity/FunctionalExercise. `FactualTraceability` guarda apenas uma
cadeia documental. O Evidence Qualification Engine recupera as demais origens
relendo `criterion_candidate_links` no contexto.

Não há perda no pipeline completo enquanto o contexto permanece disponível,
mas o candidato isolado não é autossuficiente.

Recomendação futura: representar `factual_origins` como tupla no candidato ou
criar um ID estável de vínculo factual.

### F-05 — duplicação de índices e deduplicadores

Severidade: baixa.

Cada estágio reconstrói índices por ID e implementa sua própria preservação de
ordem/remoção de duplicidade. A repetição é pequena, mas pode divergir.

Recomendação futura: extrair utilitários internos mínimos somente após
estabilizar as identidades de cada estágio.

### F-06 — protocolos normativos fragmentados

Severidade: média.

`ReadOnlyNormativeModel` cobre critério, requisito e documento.
`ConstraintNormativeModel` cobre condições separadamente. Engines diferentes
aceitam protocolos diferentes, mas não existe uma composição nominal única.

Recomendação futura: definir capacidades pequenas e combináveis, por exemplo
`CriterionCatalog`, `DocumentCategoryCatalog` e `ConditionCatalog`.

### F-07 — validações desiguais na construção direta

Severidade: baixa.

As coleções-raiz validam tupla, tipo e duplicidade. Vários objetos-folha
congelados confiam no Engine para construir valores consistentes e não possuem
`__post_init__`.

Recomendação futura: decidir formalmente se construtores são públicos ou
internos. Se públicos, adicionar validações de contrato; se internos,
documentar factories como única entrada.

## 5. Duplicação de dados

A duplicação é majoritariamente deliberada e útil para explicabilidade:

- IDs aparecem no candidato e na rastreabilidade;
- origem normativa aparece no candidato, na condição e no Assessment;
- documentos aparecem na qualificação e na rastreabilidade do Assessment;
- o Assessment mantém projeções e o objeto-fonte completo.

Não se recomenda remover essa duplicação enquanto os objetos forem snapshots
imutáveis. A duplicação problemática é a repetição de regras de validação, não
a repetição de identificadores explicativos.

## 6. Perda de informação

Conclusão: não foi encontrada perda irrecuperável no pipeline completo.

Foram encontradas duas compressões:

1. múltiplos vínculos viram um candidato; os vínculos permanecem no contexto;
2. fatos e dispositivos agregados são deduplicados; as verificações e
   condições originais permanecem no resultado.

Essa conclusão depende de o `EvaluationContext` acompanhar o pipeline. Um
candidato serializado isoladamente não preserva necessariamente todas as
origens.

## 7. Nomenclatura

Nomes considerados adequados:

- `EvaluationContext`;
- `CriterionCandidate`;
- `QualifiedCriterionCandidate`;
- `ConstraintEvaluatedCandidate`;
- `CriterionAssessment`.

Pontos de atenção:

- `AcceptedDocument` pode ser entendido como aceitação probatória; o contrato
  atual significa apenas categoria documental compatível;
- `READY_FOR_SCORING` é seguro na documentação, mas pode ser confundido com
  aprovação por consumidores futuros;
- `human_review_required` combina revisão técnica, decisão humana e tratamento
  de lacuna, sendo deliberadamente conservador.

## 8. Recomendações priorizadas

1. Remover, em Sprint futura, a filtragem documental do Candidate Engine.
2. Tipar os dois schemas de metadata.
3. Congelar valores recebidos do adapter normativo.
4. Tornar o candidato autossuficiente para múltiplas origens.
5. Compor protocolos normativos por capacidade.
6. Formalizar política de construção direta dos objetos-folha.
7. Criar teste end-to-end com múltiplos documentos e múltiplas condições para
   o mesmo candidato.

Nenhuma dessas recomendações foi implementada nesta auditoria.

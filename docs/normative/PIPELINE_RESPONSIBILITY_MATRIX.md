# Matriz de Responsabilidades do Pipeline Normativo

## 1. Responsabilidade principal

| Componente | Deve fazer | Não deve fazer |
|---|---|---|
| EvaluationContext | snapshot factual e integridade das relações | conhecer norma |
| CriterionCandidateEngine | selecionar vínculos que merecem análise | qualificar documento ou condição |
| EvidenceQualificationEngine | qualificar presença e categoria documental | decidir critério |
| ConstraintEvaluationEngine | verificar condições estruturadas e organizar revisão | consolidar estágio global |
| CriterionAssessmentEngine | consolidar resultados anteriores | recalcular verificações |

## 2. Dependências

| Componente | Context | Modelo | Estágio anterior | Infraestrutura |
|---|:---:|:---:|:---:|:---:|
| EvaluationContextBuilder | constrói | não | Aggregate Roots | Repositories |
| CriterionCandidateEngine | lê | lê | não | não |
| EvidenceQualificationEngine | lê | lê | Candidate | não |
| ConstraintEvaluationEngine | lê | lê | Qualification | não |
| CriterionAssessmentEngine | lê | lê | Constraint | não |

Somente o Builder toca portas de persistência. Os Engines não conhecem
implementações concretas do Modelo Normativo.

## 3. Sobreposições

### Categoria documental

Conflito identificado:

- Candidate Engine valida categoria e pode descartar vínculo;
- Evidence Qualification Engine também valida e classifica categoria.

Responsável correto: Evidence Qualification Engine.

### Integridade documental

Sobreposição aceitável:

- EvaluationContext valida Evidence → Document;
- Evidence Qualification valida ID/identidade no vínculo;
- Assessment confirma que documento apresentado pertence ao contexto.

São verificações em fronteiras distintas e funcionam como defesa em
profundidade.

### Critério e requisito

Sobreposição aceitável:

- Candidate Engine confirma IDs ao criar o candidato;
- Assessment reconfirma IDs antes de consolidar.

A segunda validação protege contra coleção construída fora do Engine.

### Deduplicação

Responsabilidade repetida em todas as coleções. É uma invariante transversal,
mas ainda não possui política compartilhada.

## 4. Resultado da auditoria

| Critério | Resultado |
|---|---|
| Responsabilidades principais separadas | sim |
| Dependência circular | não |
| Engine acessando banco | não |
| Engine alterando contexto/modelo | não |
| Conflito de responsabilidade | sim, categoria no Candidate Engine |
| Reexecução indevida de condição no Assessment | não |
| Decisão final ou pontuação | não |

Portanto, não é possível confirmar literalmente “nenhuma responsabilidade
conflitante”. Existe uma sobreposição objetiva e documentada, sem alteração
comportamental nesta Sprint.

## 5. Direção recomendada

```text
Candidate Engine
    preserva todos os vínculos explícitos
             ↓
Evidence Qualification Engine
    classifica compatível/incompatível/faltante
             ↓
Constraint Evaluation Engine
    verifica condições
             ↓
Assessment Engine
    apenas consolida
```

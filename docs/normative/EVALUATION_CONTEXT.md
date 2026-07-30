# EvaluationContext

## 1. Objetivo

`EvaluationContext` é o contrato factual imutável destinado à futura entrada
do Motor Normativo. Ele representa um snapshot completo do projeto em um
instante de construção e impede que o consumidor alcance Repositories,
SQLite, Controllers, Workspaces ou Aggregate Roots.

O componente não contém norma, critério, pontuação, enquadramento ou decisão.

## 2. Fronteira arquitetural

```text
Project e Repositories factuais
              │
              ▼
  EvaluationContextBuilder
      leitura + validação
              │
              ▼
      EvaluationContext
   snapshot factual imutável
              │
              ▼
     futuro Motor Normativo
```

O Builder pertence ao lado factual da fronteira. Ele pode consultar as fontes
de leitura, mas não as inclui no resultado. Depois da construção, o contexto
não possui referência para qualquer Repository ou serviço.

## 3. Composição

O contexto contém tuplas ordenadas das seguintes projeções:

| Projeção | Origem factual | Identidade preservada |
|---|---|---|
| `EvaluationProject` | `Project` | nome, caminho e metadados persistentes |
| `EvaluationActivity` | `Activity` | `activity_id` |
| `EvaluationFunctionalExercise` | `FunctionalExercise` | UUID do exercício |
| `EvaluationFunctionalAssignmentEvidence` | `FunctionalAssignmentEvidence` | UUID da atribuição |
| `EvaluationEvidence` | `Evidence` | UUID da evidência |
| `EvaluationDocument` | `Document` | UUID e identidade documental `sha256` |

`metadata` recebe dados factuais adicionais fornecidos no momento da
construção. Mapas são convertidos em mapas somente leitura; listas e tuplas,
em tuplas; conjuntos, em conjuntos imutáveis; datas, enums e caminhos, em
representações escalares estáveis.

## 4. Cadeia de rastreabilidade

```text
EvaluationActivity.functionalExerciseIds
                    │
                    ▼
EvaluationFunctionalExercise.functionalAssignmentEvidenceIds
                    │
                    ▼
EvaluationFunctionalAssignmentEvidence.sourceEvidenceId
                    │
                    ▼
EvaluationEvidence.documentIdentity
                    │
                    ▼
EvaluationDocument.documentIdentity
```

As ligações diretas já existentes entre Activity e
FunctionalAssignmentEvidence também são preservadas. Nenhum relacionamento
inverso é criado e nenhum Aggregate Root é modificado.

## 5. Builder

`EvaluationContextBuilder` recebe cinco portas estruturais de leitura:

- Activity Repository;
- FunctionalExercise Repository;
- FunctionalAssignmentEvidence Repository;
- Evidence Repository;
- Document Repository.

Cada porta precisa oferecer `list_all()`. A ordem devolvida é capturada uma
única vez e mantida na tupla correspondente.

`build(project, metadata)` executa:

1. uma leitura de cada Repository;
2. verificação dos tipos factuais;
3. cópia para projeções imutáveis;
4. validação de identidades e referências;
5. congelamento profundo dos metadados;
6. criação do contexto somente após o sucesso integral.

Não há resultado parcial. Uma falha impede a entrega do contexto.

## 6. Invariantes

### Imutabilidade

- todas as projeções são dataclasses `frozen` e `slots`;
- coleções são tuplas;
- metadados são congelados recursivamente;
- mutações posteriores nos Aggregate Roots, Repositories ou mapas de entrada
  não afetam o snapshot;
- `to_dict()` produz uma nova árvore de valores e não expõe o estado interno.

### Identidade

- IDs devem ser textuais e não vazios;
- IDs são únicos dentro de cada tipo factual;
- identidades documentais são únicas;
- o valor original de cada identidade é preservado;
- hashes documentais são normalizados apenas internamente durante a
  comparação opaca.

### Relações

- toda referência de Activity deve localizar seu FunctionalExercise ou sua
  FunctionalAssignmentEvidence;
- toda referência de FunctionalExercise deve localizar sua
  FunctionalAssignmentEvidence;
- toda FunctionalAssignmentEvidence deve localizar sua Evidence;
- toda Evidence deve localizar exatamente um Document por identidade
  documental;
- referências repetidas são rejeitadas;
- relações ausentes não são ignoradas nem reconstruídas por inferência.

### Ordem

A ordem capturada de cada Repository é preservada. O contexto não classifica,
agrupa ou prioriza elementos.

## 7. Falhas estruturais

- `EvaluationContextError`: entrada factual estruturalmente inválida;
- `DuplicateEvaluationObjectError`: identidade ou referência duplicada;
- `InvalidEvaluationReferenceError`: referência para objeto inexistente;
- `IncompleteEvaluationTraceabilityError`: Evidence sem origem documental.

As falhas descrevem integridade factual, não resultado normativo.

## 8. Serialização

`to_dict()` oferece uma representação independente composta por dicionários,
listas e valores escalares. Ela pode ser serializada como JSON, mas não define
formato persistente, schema de projeto ou protocolo de transporte.

O contexto não implementa desserialização. Sua construção oficial continua
sendo responsabilidade do Builder, porque somente ele valida o snapshot
contra as fontes factuais.

## 9. Limitações

- o snapshot não garante consistência transacional simultânea entre cinco
  Repositories independentes; ele detecta inconsistências referenciais após
  as leituras;
- `metadata` contém somente valores fornecidos explicitamente ao Builder;
- disponibilidade física do arquivo não faz parte da identidade documental;
- o contexto não resolve páginas, interpreta trechos ou classifica documentos;
- não existe cache, atualização incremental ou mutação do snapshot;
- nenhum resultado de avaliação pode ser armazenado no contexto.

# ADR-003 — FunctionalAssignmentNormalizer

## Status

Proposed

## Contexto

O ProcDocRSC já possui:

- `FunctionalExercise`;
- `FunctionalAssignmentEvidence`;
- `CreateFunctionalAssignmentEvidenceCommand`;
- `FunctionalAssignmentEvidenceAssembler`.

O pipeline atual é:

```text
Document
    ↓
Evidence
    ↓
FunctionalAssignmentEvidence (RAW)
```

A próxima etapa do pipeline será:

```text
FunctionalAssignmentEvidence (RAW)
    ↓
FunctionalAssignmentNormalizer
```

Documentos administrativos podem descrever a mesma realidade utilizando
nomenclaturas diferentes. Exemplos:

- “Campus Alegrete”, “Campus de Alegrete” e “UNIPAMPA Campus Alegrete”;
- “PROGRAD” e “Pró-Reitoria de Graduação”;
- “Coordenação Acadêmica” e “Coordenador Acadêmico”.

Essas diferenças impedem comparações confiáveis. Antes de resolver identidade,
é necessário produzir uma representação consistente.

Este ADR deve ser interpretado conforme os princípios gerais da
[Visão do Domínio](../domain-vision.md).

## Definição

Normalização é o processo de transformar uma
`FunctionalAssignmentEvidence` em uma representação semanticamente
consistente, preservando integralmente seu significado administrativo.

A normalização nunca deve alterar o significado da evidência.

## Responsabilidade

O `FunctionalAssignmentNormalizer` é responsável apenas por:

- padronização de representações;
- uniformização de nomenclaturas;
- expansão de abreviações conhecidas;
- remoção de variações puramente sintáticas;
- preparação para comparação posterior.

O normalizador não:

- identifica exercícios;
- identifica pessoas;
- une evidências;
- cria `FunctionalExercise`;
- resolve continuidade;
- interpreta revogações;
- calcula pontuação;
- consulta banco;
- usa IA;
- corrige OCR;
- interpreta documentos;
- altera datas;
- altera `person_id`;
- altera `source_evidence_reference`.

Sempre que houver dúvida, o valor original deve ser preservado.

## Campos

| Campo | Decisão |
| --- | --- |
| `person_id` | Não deve ser normalizado. |
| `source_evidence_reference` | Não deve ser normalizado. |
| `exercise_type_code` | Depende de decisão futura; deve ser preservado até existir vocabulário canônico aprovado. |
| `exercise_type_label` | Pode receber normalização sintática; normalização semântica depende de vocabulário controlado futuro. |
| `role` | Pode receber normalização sintática; normalização semântica depende de vocabulário controlado futuro. |
| `organization` | Pode receber normalização sintática; normalização semântica depende de vocabulário institucional controlado futuro. |
| `unit` | Pode receber normalização sintática; normalização semântica depende de vocabulário institucional controlado futuro. |
| `administrative_reference` | Pode receber apenas normalização sintática que preserve integralmente a referência. |
| `start_date` | Não deve ser normalizado. |
| `end_date` | Não deve ser normalizado. |

## Níveis de normalização

### Normalização sintática

Remove variações de representação que não alteram o conteúdo, como:

- espaços;
- caixa;
- pontuação;
- abreviações triviais.

É determinística, local e de menor risco.

### Normalização semântica

Substitui representações diferentes por uma forma canônica conhecida, como:

```text
PROGRAD
    ↓
Pró-Reitoria de Graduação
```

ou:

```text
Campus Alegrete
    ↓
UNIPAMPA Campus Alegrete
```

Esse nível melhora comparações, mas apresenta risco maior de alterar o
significado administrativo quando o vocabulário ou o contexto forem
insuficientes.

Os dois níveis pertencem conceitualmente ao processo de normalização. Eles
podem ser separados internamente no futuro para permitir políticas,
vocabulários e evolução independentes, sem alterar a responsabilidade externa
do normalizador.

## Imutabilidade

Foram consideradas três alternativas:

### Alterar a entidade recebida

É simples, mas prejudica auditoria, comparação entre valor original e
normalizado e segurança em caso de falha.

### Retornar nova instância

Preserva a evidência recebida, torna a transformação explícita e facilita
auditoria, testes e rollback.

### Retornar objeto intermediário

Separa os dados normalizados da entidade, mas introduz um novo conceito e exige
uma etapa posterior para produzir a evidência normalizada.

A decisão é retornar uma nova instância de `FunctionalAssignmentEvidence`.
A instância de entrada permanece inalterada.

## Estado NORMALIZED

O normalizador coordena a transformação, mas não altera diretamente o estado.
A própria entidade é responsável por validar e realizar a transição permitida
de `RAW` para `NORMALIZED`.

Um Application Service poderá orquestrar o uso do normalizador no futuro, mas
não será o proprietário da regra de transição.

## Entrada e saída

A entrada conceitual é uma `FunctionalAssignmentEvidence` em estado `RAW`.

A saída conceitual é uma nova `FunctionalAssignmentEvidence`, equivalente à
entrada quanto à identidade, à fonte, à pessoa, às datas e ao significado
administrativo, com representações normalizadas e estado `NORMALIZED`.

Evidências que não estejam em estado `RAW` devem ser rejeitadas.

## Caso sem alterações

Mesmo que nenhum campo textual precise ser modificado, o normalizador retorna
uma nova instância equivalente em estado `NORMALIZED`.

Ele não retorna a mesma instância e não altera a instância original. Essa
decisão mantém comportamento uniforme, imutabilidade e rastreabilidade.

## Invariantes

A normalização deve preservar:

- identidade;
- `person_id`;
- `source_evidence_reference`;
- datas;
- significado administrativo;
- rastreabilidade documental.

Ela nunca poderá produzir uma evidência semanticamente diferente.

## Relação com IdentityResolver

O pipeline conceitual é:

```text
FunctionalAssignmentNormalizer
    ↓
IdentityResolver
```

O normalizador prepara representações comparáveis. O `IdentityResolver` decide
se evidências representam a mesma identidade funcional. Essas responsabilidades
não podem se misturar.

## Consequências

- a evidência original permanece disponível e inalterada;
- a transformação permanece determinística e auditável;
- representações podem ser comparadas com menor ruído;
- normalização não antecipa resolução de identidade ou continuidade;
- normalização semântica somente pode ocorrer quando houver correspondência
  conhecida e segura;
- valores ambíguos permanecem preservados.

## Decisões aprovadas

- Normalização prepara evidências para comparação posterior.
- Normalização preserva integralmente o significado administrativo.
- O normalizador aceita exclusivamente evidências em estado `RAW`.
- O normalizador sempre retorna uma nova instância.
- A própria entidade valida e realiza a transição `RAW` → `NORMALIZED`.
- A instância recebida nunca é alterada.
- Identidade, pessoa, fonte documental e datas nunca são modificadas.
- Normalização sintática e semântica pertencem ao mesmo processo conceitual.
- Os dois níveis poderão ser separados internamente no futuro.
- Normalização semântica exige correspondência conhecida e segura.
- Em caso de dúvida, o valor original é preservado.
- Uma evidência sem alterações textuais ainda produz nova instância
  `NORMALIZED`.
- O normalizador não resolve identidade, continuidade ou interpretação
  normativa.
- `IdentityResolver` atua somente depois da normalização.

## Questões para ADR futuro

- Como o `IdentityResolver` determinará equivalência entre evidências
  normalizadas?
- Como conflitos entre identidades candidatas serão representados?
- Como o `ContinuityResolver` distinguirá continuidade, interrupção e
  sobreposição?
- Quais informações normalizadas serão necessárias para sustentar decisões de
  continuidade?

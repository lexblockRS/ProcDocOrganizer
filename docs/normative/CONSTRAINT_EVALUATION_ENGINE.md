# Constraint Evaluation Engine

## 1. Responsabilidade

O `ConstraintEvaluationEngine` verifica condições normativas já estruturadas e
organiza condições qualitativas para revisão humana.

Ele pode produzir verificações objetivas e propostas preliminares. Nenhum
resultado significa que o critério foi definitivamente atendido, que existe
elegibilidade ou que uma decisão administrativa foi tomada.

## 2. Fronteira

```text
EvaluationContext somente leitura ───────────┐
Modelo Normativo somente leitura ────────────┤ configuração
                                             ▼
QualifiedCriterionCandidateCollection
                    │
                    ▼
        ConstraintEvaluationEngine
                    │
                    ▼
ConstraintEvaluatedCandidateCollection
```

O Engine não acessa Repositories, SQLite, Controllers, Workspaces ou Aggregate
Roots. Os fatos vêm exclusivamente de
`EvaluationContext.metadata["constraint_facts"]`.

## 3. Verificação não é decisão

Uma verificação responde se uma operação explícita produziu determinado
resultado sobre um fato igualmente explícito.

Uma decisão exigiria combinar requisitos, efeitos jurídicos, discricionariedade
e competência administrativa. Essa combinação não pertence a este
componente.

Assim:

- `VERIFIED` significa apenas que a condição estruturada foi confirmada pela
  operação declarada;
- `NOT_VERIFIED` significa apenas que aquela operação não confirmou a
  condição;
- nenhum dos estados é sinônimo de satisfação ou rejeição do critério.

## 4. Fonte das condições

O Modelo Normativo é consultado pela porta somente leitura:

```text
conditions_of_criterion(criterion_id)
```

Cada condição precisa informar:

- ID;
- critério relacionado;
- classificação;
- descrição;
- operação, quando estruturada;
- chave factual;
- valor esperado;
- dispositivo e hierarquia normativa;
- perguntas de validação.

Retorno `None` significa que as condições ainda não foram estruturadas e gera
`NORMATIVE_GAP`. Uma coleção vazia significa que o modelo declarou
explicitamente não haver condições vinculadas.

## 5. Classificações

### `STRUCTURED`

Permite verificação determinística por operação expressamente declarada.
Operações suportadas:

- `equals`;
- `not_equals`;
- `contains`;
- `is_true`;
- `is_false`.

O Engine não cria operações a partir do texto da norma. Operação desconhecida
gera `NORMATIVE_GAP`.

### `ASSISTED`

Permite organizar uma proposta preliminar quando os fatos fornecem
explicitamente:

- conclusão preliminar;
- fatos favoráveis;
- fatos contrários;
- informações ausentes.

A proposta sempre possui `definitive = false`, inclui perguntas de validação e
exige revisão humana.

### `HUMAN_ONLY`

Reserva integralmente a análise à pessoa competente. Mesmo que existam fatos,
o Engine não formula conclusão automática.

## 6. Estados

| Estado | Semântica |
|---|---|
| `VERIFIED` | operação estruturada retornou verdadeiro |
| `NOT_VERIFIED` | operação estruturada retornou falso |
| `NOT_APPLICABLE` | metadata marcou explicitamente a não aplicação |
| `REVIEW_RECOMMENDED` | proposta assistida disponível, sem decisão |
| `HUMAN_DECISION_REQUIRED` | condição reservada à decisão humana |
| `INSUFFICIENT_INFORMATION` | fato explícito necessário está ausente |
| `NORMATIVE_GAP` | condição ou operação não está estruturada |

A ausência de fato nunca é convertida automaticamente em
`NOT_VERIFIED`. Valores `null` também não são tratados como fatos.

## 7. Proposta assistida

`AssistedFramingProposal` contém:

- `preliminary_conclusion`;
- `favorable_facts`;
- `contrary_facts`;
- `missing_information`;
- `normative_reference`;
- `validation_questions`;
- `review_justification`;
- `definitive = false`.

O texto da conclusão preliminar deve estar registrado explicitamente no
contexto. Nesta Sprint o Engine não o redige por inferência.

## 8. Explicabilidade

Cada `ConditionVerification` preserva:

- condição analisada;
- classificação;
- estado;
- fatos utilizados e suas fontes;
- operação executada;
- explicação;
- pendências;
- alertas;
- necessidade de revisão humana;
- proposta assistida, quando existente.

Cada `ConstraintEvaluatedCandidate` agrega:

- candidato qualificado original;
- condições identificadas;
- verificações;
- fatos utilizados sem duplicidade;
- dispositivos normativos;
- pendências;
- alertas;
- propostas;
- sinalizador consolidado de revisão humana.

## 9. Regras de segurança

- nenhuma inferência silenciosa;
- nenhum `null` convertido em fato;
- ausência factual produz insuficiência, não reprovação;
- condição qualitativa não é transformada em operação estruturada;
- proposta assistida nunca é definitiva;
- lacunas permanecem visíveis;
- fatos duplicados para a mesma condição e candidato são rejeitados;
- ordem das condições e dos candidatos é preservada;
- as mesmas entradas produzem o mesmo resultado.

## 10. Futura integração com IA

Não existe integração com IA nesta Sprint.

Uma futura extensão poderá auxiliar a redação de propostas para condições
`ASSISTED`, desde que:

- não altere verificações `STRUCTURED`;
- cite integralmente fatos e dispositivos utilizados;
- mantenha toda incerteza explícita;
- produza apenas conteúdo não definitivo;
- exija validação humana;
- não crie fatos nem complete campos ausentes;
- possa ser desativada sem modificar o resultado determinístico.

Condições `HUMAN_ONLY` não podem ser convertidas em decisão automatizada por
essa futura integração.

## 11. Limitações

- depende de condições previamente estruturadas pelo Modelo Normativo;
- depende de fatos explicitamente registrados no contexto;
- não interpreta o texto original do decreto;
- não resolve conflitos, sobreposições ou conceitos jurídicos abertos;
- não combina condições em satisfação de critério;
- não calcula pontuação;
- não decide elegibilidade;
- não utiliza IA, LLM, similaridade textual, embeddings ou Machine Learning.

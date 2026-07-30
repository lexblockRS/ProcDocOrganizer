# Relatório de Prontidão para Pontuação Oficial

## 1. Resposta objetiva

O pipeline atual não fornece tudo que um futuro componente oficial de pontuação
precisaria.

**Classificação global: `NOT_READY`.**

Isso não representa falha do pipeline atual: seus contratos foram desenhados
para identificar candidatos, qualificar documentação, verificar condições e
consolidar Assessment, sem executar regras de pontuação.

## 2. Matriz de prontidão

| Requisito | Estado | Fundamentação |
|---|---|---|
| identidade de critério | `READY` | `criterion_id` chega ao Assessment |
| identidade de requisito | `READY` | `requirement_id` chega ao Assessment |
| cadeia Activity → Document | `READY` | FactualTraceability e source objects |
| documentos apresentados | `READY` | preservados em AssessmentTraceability |
| categorias documentais utilizadas | `READY` | preservadas em source_evaluation |
| origem normativa do critério | `READY` | NormativeOrigin preservada |
| condições e verificações | `READY_WITH_ASSISTANCE` | dependem de adaptador e metadata |
| fatos genéricos utilizados | `READY_WITH_ASSISTANCE` | aceitos via `constraint_facts`, sem produtor tipado |
| início e fim do período | `READY_WITH_ASSISTANCE` | presentes, mas opcionais/duplicados e sem alias |
| papel titular/substituto | `READY_WITH_ASSISTANCE` | `role` existe, mas vocabulário não é validado |
| quantidade por unidade | `NOT_READY` | nenhum contador factual é produzido |
| vínculo com `rule_id` | `NOT_READY` | Modelo Executável não é consumido |
| tabela e valor aplicável | `NOT_READY` | tabela não chega ao Assessment |
| aplicação de counting rule | `NOT_READY` | regra não é materializada nem aplicada |
| aplicação temporal | `NOT_READY` | não há normalização ou resultado temporal |
| seleção de variante | `NOT_READY` | role existe, mas regra não é ligada/selecionada |
| agregação | `NOT_READY` | não pertence aos Engines existentes |
| controle de sobreposição | `NOT_READY` | não há identidade de ocorrência consumida entre critérios |
| computability level | `NOT_READY` | não é preservado |
| rastreabilidade regra → fato | `NOT_READY` | falta `execution_rule_id` no fluxo |

## 3. Informações deliberadamente ausentes

São ausências coerentes com os contratos atuais:

- cálculo de pontos;
- soma;
- escolha de variante;
- resolução de sobreposição;
- ranking;
- elegibilidade;
- resultado final.

Essas ausências não devem ser “corrigidas” dentro dos Engines atuais.

## 4. Lacunas bloqueadoras

1. Não existe ligação entre candidato e regra executável.
2. Não existe produtor tipado das quantidades exigidas.
3. Datas e papel possuem fontes redundantes sem precedência formal.
4. Condições do Modelo Executável não alimentam automaticamente o adaptador de
   condições do Constraint Engine.
5. Não há identidade de ocorrência para impedir reutilização entre critérios.
6. Tabela, unidade normativa e variante não chegam ao Assessment.

## 5. Recomendações

Para uma Sprint futura, sem alterar responsabilidades dos Engines atuais:

1. definir um contrato somente leitura `ExecutionFactSet`;
2. criar um preparador factual antes da pontuação;
3. ligar `criterion_id` a `execution_rule_id`;
4. registrar aliases e fonte canônica para datas, papel e unidade;
5. introduzir identidade estável de ocorrência para auditoria de sobreposição;
6. transportar regra, fatos usados e suas fontes até o resultado futuro;
7. manter qualquer decisão humana explícita e rastreável;
8. não transformar metadata genérica em fonte implícita de verdade.

## 6. Conclusão

O pipeline está pronto para entregar Assessments rastreáveis e para preservar
fatos já fornecidos. Ele não está pronto para alimentar sozinho uma aplicação
oficial das tabelas. A preparação de fatos e a ligação ao Modelo Executável são
pré-requisitos ainda ausentes.

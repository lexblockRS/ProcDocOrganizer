# Evaluation Report

## Objetivo

O Evaluation Report apresenta o estado operacional completo de um `RSCProcess`
para candidatos e avaliadores. Ele explica resultados, rastreabilidade documental,
pendências e cobertura sem produzir decisão normativa ou documento oficial.

## Arquitetura

O fluxo de dados é unidirecional:

`RSCProcess → EvaluationReportViewModel → DTOs → EvaluationReportView`

O ViewModel somente lê o snapshot recebido. Não acessa persistência, não executa o
Kernel, não recalcula scores e não modifica o domínio. O tempo medido pelo serviço
de execução pode ser fornecido como contexto adicional de apresentação.

## ViewModel e DTOs

`EvaluationReportViewModel` cria DTOs `dataclass(frozen=True, slots=True)` para o
resumo, Requirements, Criteria, pendências, cobertura de Evidence e Documents,
usos documentais e estatísticas. A View recebe apenas `EvaluationSummary`; portanto,
não conhece aggregates nem objetos do pipeline normativo.

O indicador verde, amarelo ou vermelho é operacional: distingue ausência de
pendências, incompletude e pendências críticas. Ele não expressa deferimento,
aprovação ou qualquer conclusão normativa.

Em aderência ao P-001, fatos sem Binding aparecem como
**"ExecutionFact aguardando enquadramento."** e não são tratados como falha
fatal. O relatório permanece disponível com a pontuação parcial.

## Estrutura do relatório

1. Resumo Executivo: status, pontuação, contagens, tempo e indicador operacional.
2. Resultado da Avaliação: hierarquia Requirement/Criteria, estado e score.
3. Pendências: fatos sem score/binding, Evidence sem Document, incompatibilidades,
   falhas de Validation, Criteria não atendidos e itens consolidados restantes.
4. Mapa de Evidências: Document, Evidence, ExecutionFacts, bindings, Criteria,
   Requirements e pontuação sustentada.
5. Estatísticas: cobertura documental e totais do processo.

## Mapa de evidências

O mapa inverte a rastreabilidade existente no processo e agrupa cada uso pelo
Document. Um mesmo Document pode sustentar vários fatos e Criteria; sua pontuação
sustentada é a soma dos scores já calculados pelo pipeline. Documents sem fato e
Evidence sem Document recebem mensagens explícitas. Nenhuma pontuação nova é
calculada: o relatório apenas agrega visualmente os valores existentes.

A cobertura parte da coleção completa preservada em cada
`RSCProcessEvidence`; Documents sem uso e múltiplos Documents da mesma Evidence
permanecem visíveis.

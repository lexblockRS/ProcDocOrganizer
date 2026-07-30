# ExecutionFactBuilder

## 1. Responsabilidade

O Builder transforma Assessments em contratos factuais tipados. Ele é uma
fronteira de normalização, não um Engine normativo.

Entradas somente leitura:

- `CriterionAssessmentCollection`;
- `EvaluationContext`;
- `criterion_execution_rules.json`;
- `execution_rules_manifest.json`.

Não há acesso a repositories.

## 2. Construção

O Builder pode receber os dois documentos JSON já carregados ou usar
`from_files()`. Na inicialização ele:

1. indexa regras e manifesto por critério;
2. rejeita duplicidades;
3. exige cobertura idêntica;
4. confere regra, requisito e tabela em cada entrada.

Durante `build()` ele:

1. mantém a ordem dos Assessments;
2. localiza regra e entrada do manifesto;
3. valida referências no EvaluationContext;
4. normaliza datas, papel e unidade;
5. transporta fatos explicitamente registrados;
6. registra ausências;
7. cria uma ocorrência estrutural;
8. registra possíveis sobreposições;
9. entrega uma coleção imutável.

## 3. Quantidades

O Builder procura a chave requerida entre os `FactUsed` do Assessment. Quando o
valor é inteiro ou Decimal, ele é transportado para Measurement e Occurrence.
Quando não existe, `amount` e `quantity` ficam `None` e a chave entra em
`unresolved_items`.

Não há multiplicação pelo valor normativo, soma ou arredondamento.

## 4. Tempo

`start_date` e `end_date` são transportados como strings. Ausência de fim é
registrada quando `period_end` for requerido. O Builder não calcula anos, meses
ou a fração acima de seis meses.

## 5. Variantes

O Builder lê as opções da regra e verifica apenas se o fato de papel está
disponível. `selected_variant` é invariavelmente `None`; tentar construir um
ExecutionFact com seleção é rejeitado.

## 6. Sobreposição

A igualdade da origem estrutural entre fatos diferentes gera candidatos e o
estado `POSSIBLE`. Esse registro não escolhe critério, não elimina ocorrência e
não confirma conflito.

## 7. Explicabilidade

A explicação enumera:

- regra futura;
- fatos normalizados;
- fatos ausentes;
- quantidade de documentos;
- presença de variantes;
- ausência de pontuação, agregação e decisão.

Rastreabilidades normativa e factual permanecem objetos separados.

## 8. Falhas

São rejeitados:

- regra ausente;
- cobertura divergente entre regra e manifesto;
- referências inexistentes no contexto;
- IDs ou identidades documentais divergentes;
- fatos quantitativos não numéricos;
- identidades duplicadas;
- valores canônicos mutáveis.

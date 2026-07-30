# ExecutionContractResolver

## 1. Entradas

Somente leitura:

- `ExecutionFactCollection`;
- `ExecutionValidationCollection`;
- `criterion_execution_rules.json`;
- `execution_rules_manifest.json`;
- `decree_criteria.json`.

Não existe acesso a banco, repositories, Aggregate Roots ou pipeline.

## 2. Processo

Na inicialização, o Resolver:

1. indexa regras e manifesto por `criterion_id`;
2. rejeita IDs duplicados;
3. confere cobertura;
4. confere regra, requisito e tabela;
5. confere o perfil geral de documentos aceitos.
6. indexa os critérios oficiais e seus valores.

Durante `resolve()`:

1. indexa Validations por `execution_fact_id`;
2. exige correspondência exata com os Facts;
3. preserva a ordem dos Facts;
4. vincula Fact e Validation;
5. vincula regra e manifesto;
6. materializa descritores declarativos;
7. resolve o valor e sua origem;
8. separa computabilidade legal e de execução;
9. reúne pendências já registradas;
10. cria ID determinístico;
11. entrega coleção imutável.

## 3. O que é resolvido

- identidade da regra;
- critério e requisito;
- tipo e unidade de medição;
- counting rule;
- temporal rule;
- aggregation rule;
- overlap rule;
- variant rule;
- tabela aplicável;
- artigo e anexo;
- perfil documental;
- fatos requeridos.
- valor unitário oficial e sua unidade;
- origem do valor em decreto, tabela e critério.

Resolver significa localizar e reunir. Nenhuma dessas regras é aplicada.

## 4. Pendências

`unresolved_items` combina, sem eliminar informação:

- pendências do ExecutionFact;
- bloqueios e warnings da Validation;
- fatos, documentos e medições ausentes;
- variantes pendentes;
- inconsistências já registradas.

O Resolver não revalida nem tenta resolver os itens.

## 5. Explicabilidade

A explicação identifica:

- Fact e Validation usados;
- estado da Validation;
- regra e tabela;
- quantidade de fatos requeridos;
- quantidade de pendências;
- dependência textual;
- necessidade de revisão;
- bloqueio futuro;
- ausência de pontuação.

## 6. Falhas estruturais

São rejeitados:

- regra inexistente;
- Validation sem Fact ou Fact sem Validation;
- regra e manifesto divergentes;
- perfil documental divergente;
- requisito ou tabela incompatível;
- contratos duplicados.

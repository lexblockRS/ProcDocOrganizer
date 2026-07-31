# ExecutionFact Editor

## Papel do Aggregate

`ExecutionFact` é uma interpretação factual estruturada de uma `Evidence`.
Ele pertence a um `Project`, possui identidade própria e registra tipo,
descrição, quantidade opcional, unidade, período opcional, metadados,
timestamps e estado.

O Aggregate não representa um Document e não contém referências diretas a
Documents. Também não contém critério, Requirement, pontuação ou qualquer
resultado normativo.

As operações de edição produzem novas instâncias imutáveis e preservam
`aggregate_id` e data de criação. A identidade é independente do conteúdo do
snapshot.

## Relação com Evidence

Cada ExecutionFact referencia exatamente uma Evidence por `evidence_id` e o
Project proprietário por `project_id`. Uma Evidence pode possuir zero ou
vários ExecutionFacts. A remoção física de uma Evidence remove seus
ExecutionFacts persistidos por integridade referencial.

No Project Explorer, a lista de Execution Facts acompanha a Evidence
selecionada. Selecionar outra Evidence substitui a lista, sem criar estado
paralelo ou apresentar fatos pertencentes a outro vínculo.

## Relação futura com o Kernel

ExecutionFact registra somente informação factual fornecida pelo usuário.
Nesta Sprint ele não executa Validation, Compatibility ou Kernel. Uma camada
futura poderá traduzir estes dados para os contratos normativos existentes,
sem transformar este editor em executor de regras.

## Modelo físico

A tabela `platform_execution_facts` persiste:

- identidade do Aggregate;
- referências ao Project e à Evidence;
- tipo, descrição, quantidade e unidade;
- datas inicial e final opcionais;
- metadados;
- timestamps;
- estado.

Quantidades são armazenadas como texto decimal para evitar perda de precisão.
A associação com Evidence possui chave estrangeira. A implementação utiliza
um store SQLite específico, sem ORM, Repository genérico, cache ou Unit of
Work.

## Limites

Não há cálculo, pontuação, IA, OCR, parser documental ou inferência. O modelo
não altera Project, Workspace, Host, RSCProcess nem os componentes do pipeline
normativo.

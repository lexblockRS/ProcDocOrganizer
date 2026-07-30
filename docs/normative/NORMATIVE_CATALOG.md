# Catálogo Normativo Executável

## 1. Objetivo

O catálogo normativo transforma o conhecimento consolidado em
`MAPA_NORMATIVO_RSC.md` em definições tipadas, imutáveis e consultáveis. Seu
objetivo é impedir que descrição, unidade, Measurement, compatibilidade,
motor, valor, limites e dependências de um critério sejam codificados em
condicionais espalhadas pelo sistema.

O catálogo não avalia fatos, não executa pontuação e não decide concessão.

## 2. Modelo

`NormativeCriterionDefinition` representa um critério do Decreto nº
13.048/2026 e contém:

- código estável;
- identidade da regra executável e do requisito;
- descrição oficial;
- anexo e item;
- família computacional;
- unidade normativa;
- Measurement requerida;
- política de compatibilidade;
- motor aritmético;
- valor fixo ou variantes de valor;
- limites;
- dependências;
- necessidade de decisão humana;
- template mínimo de explicabilidade.

`NormativeCriterionCatalog` é uma coleção somente leitura. Ele rejeita códigos
e regras duplicadas e oferece consulta por código.

## 3. Tipos controlados

O modelo utiliza enums para impedir nomes livres:

- `MeasurementType`;
- `ArithmeticEngine`;
- `CompatibilityPolicyId`;
- `CriterionFamily`.

Valores normativos utilizam `Decimal`. Variantes como titular e substituto são
representadas por `NormativeValueVariant`.

## 4. Políticas de compatibilidade

`COMPATIBILITY_POLICIES` é a fonte única das combinações admitidas:

| Política | Measurements admitidas |
|---|---|
| TEMPORAL | DURATION |
| QUANTITATIVE | COUNT, QUANTITY, HOURS |
| EVENT | COUNT, QUANTITY, HOURS |
| PUBLICATION | COUNT, QUANTITY |

Cada motor declara sua política em
`ENGINE_COMPATIBILITY_POLICIES`. Uma definição cuja Measurement, política e
motor sejam incoerentes é rejeitada na construção.

`ExecutionCompatibilityEvaluator.from_catalog()` consome diretamente essas
definições. O adaptador de `criterion_execution_rules.json` permanece
temporariamente disponível para os componentes anteriores, mas reutiliza as
mesmas políticas e não mantém uma segunda tabela de compatibilidade.

## 5. Cobertura

O catálogo contém 55 critérios:

| Anexo | Critérios |
|---|---:|
| I | 10 |
| II | 11 |
| III | 3 |
| IV | 8 |
| V | 4 |
| VI | 19 |

Todos conservam dependências transversais de comprovação documental,
unicidade, não ordinariedade/relevância e revisão humana.

## 6. Relação com o mapa da RSC-008

O mapa é o relatório humano e a justificativa classificatória. O catálogo é a
projeção executável desse conhecimento:

```text
Decreto nº 13.048/2026
          ↓
MAPA_NORMATIVO_RSC.md
          ↓
NormativeCriterionCatalog
          ↓
Compatibility / Contract / Kernel
```

A suíte confere o catálogo contra `decree_criteria.json` e
`criterion_execution_rules.json` enquanto esses artefatos coexistirem. Essa
comparação é um gate de transição, não uma declaração de que JSON será a
persistência definitiva.

## 7. Relação com o Kernel

O `CriterionScoringKernel` não foi alterado. Ele já recebe pelo
`CriterionExecutionContract`:

- motor aritmético;
- Measurement;
- valor normativo resolvido;
- regra temporal;
- rastreabilidade.

Portanto, não precisa conhecer códigos dos 55 critérios nem importar o
catálogo. O catálogo prepara metadados; o Kernel conhece somente operações
aritméticas.

## 8. Explicabilidade

Cada definição contém os elementos necessários para uma explicação futura:

- critério e origem;
- unidade;
- quantidade;
- valor ou variante;
- fórmula;
- limites;
- dependências;
- revisão humana.

Esta Sprint apenas modela os dados. Não existe gerador automático de texto.

## 9. Extensibilidade

Um novo critério deve ser incluído como configuração e validado contra:

1. Measurement conhecida;
2. política existente;
3. motor declarado;
4. coerência entre motor e política;
5. valor fixo ou variantes, nunca ambos;
6. código e regra únicos.

Um novo motor ou Measurement exige primeiro a ampliação explícita dos enums e
das políticas. Não há fallback heurístico.

## 10. Estado de transição e persistência futura

O catálogo Python é propositalmente temporário para validar o modelo. Ele:

- não utiliza banco ou SQLite;
- não define formato definitivo de persistência;
- não carrega JSON em tempo de execução;
- não modifica Aggregate Roots ou Pipeline;
- não substitui o Decreto como fonte jurídica.

Antes de persistência futura, recomenda-se:

- versionar formalmente o schema do catálogo;
- separar identidade estável de textos localizados;
- definir assinatura e validação de origem normativa;
- criar migração explícita dos consumidores JSON;
- preservar `Decimal`, enums, variantes e rastreabilidade;
- impedir ativação de catálogo parcial ou inconsistente.

## 11. Benefícios arquiteturais

- elimina tabelas de compatibilidade duplicadas no código;
- concentra metadados dos 55 critérios;
- torna inconsistências detectáveis na inicialização;
- permite testar cobertura integral;
- mantém o Kernel independente do Decreto;
- prepara versionamento e persistência futuros sem antecipá-los.

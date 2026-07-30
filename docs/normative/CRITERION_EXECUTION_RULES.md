# Regras de Execução dos Critérios

## 1. Tipos de medição

| Tipo | Significado declarativo |
|---|---|
| `COUNT` | quantidade discreta da unidade indicada |
| `DURATION` | duração expressa em ano, mês ou fração |

## 2. Counting rules

As unidades do decreto foram mapeadas literalmente:

| Unidade textual | Counting rule | Fato quantitativo |
|---|---|---|
| por ano ou fração acima de seis meses | `PER_YEAR` | `period_start`, `period_end` |
| por mês | `PER_MONTH` | `period_start`, `period_end` |
| por evento | `PER_EVENT` | `event_count` |
| por publicação | `PER_PUBLICATION` | `publication_count` |
| por designação | `CUSTOM_TEXT` | `designation_count` |
| por projeto | `CUSTOM_TEXT` | `project_count` |
| por produto | `CUSTOM_TEXT` | `product_count` |
| por prêmio | `CUSTOM_TEXT` | `award_count` |
| por curso | `CUSTOM_TEXT` | `course_count` |
| demais unidades nominais | `CUSTOM_TEXT` | `<unidade>_count` |

`CUSTOM_TEXT` preserva a unidade oficial porque o vocabulário fechado do
contrato não contém um tipo específico. Isso não reduz a unidade a
`PER_ACTIVITY` nem cria equivalências.

## 3. Regras temporais

- unidades anuais: `FRACTION_ABOVE_SIX_MONTHS`;
- unidade mensal: `PER_MONTH`;
- demais unidades: `NONE`.

O modelo não mede períodos, não converte dias, não arredonda e não decide se uma
fração superou seis meses.

## 4. Variantes

Os quatro critérios do Anexo V usam `ROLE_BASED`, com as variantes literais
`titular` e `substituto`. Todos os demais usam `NONE`. A presença de `role` é
obrigatória para futura escolha, mas nenhuma variante é selecionada agora.

## 5. Condições

Cada regra possui uma condição `OFFICIAL_CRITERION_TEXT`, referenciada ao campo
`official_text` do critério. Isso conserva integralmente expressões como
“formalmente”, “relevante”, “interesse institucional” e “comprovada”, sem
convertê-las em predicados inventados.

## 6. Agregação e sobreposição

Todas as regras referenciam:

- soma declarada pelo art. 5º, §2º;
- sobreposição proibida pelo art. 5º, §3º;
- resolução humana da sobreposição pela comissão, também no §3º.

## 7. Documentos

Cada regra aponta para os dez tipos de `decree_documents.json` por meio do perfil
documental geral. O decreto estruturado não oferece uma lista específica para
cada critério.

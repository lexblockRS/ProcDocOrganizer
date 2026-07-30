# Modelo de Computabilidade Dupla

## 1. Motivação

A capacidade de reconhecer juridicamente um critério e a capacidade de executar
uma operação aritmética são dimensões distintas. O contrato passa a registrá-las
separadamente.

## 2. LegalComputability

- `FULLY_EXECUTABLE`;
- `PARTIALLY_EXECUTABLE`;
- `TEXT_DEPENDENT`;
- `HUMAN_ONLY`.

O valor é copiado da regra executável e descreve dependência jurídica ou textual.
O Resolver não o reclassifica.

## 3. ExecutionComputability

- `EXECUTABLE`: Validation não bloqueada, valor singular e quantidade
  disponíveis;
- `NOT_EXECUTABLE`: revisão humana, valor não singular ou quantidade ausente;
- `BLOCKED`: Validation em estado `BLOCKED`.

Essa classificação não executa a regra. Ela apenas informa se os operandos estão
materializados.

## 4. Combinações

Combinações legítimas incluem:

| Legal | Execução | Significado |
|---|---|---|
| `TEXT_DEPENDENT` | `EXECUTABLE` | texto já refletido no contrato validado; operandos disponíveis |
| `TEXT_DEPENDENT` | `NOT_EXECUTABLE` | falta valor singular, quantidade ou revisão |
| qualquer | `BLOCKED` | Validation bloqueou o contrato |
| `FULLY_EXECUTABLE` | `EXECUTABLE` | regra e operandos estruturados |

`EXECUTABLE` não significa satisfeito, aprovado ou pontuado.

## 5. Precedência

1. Validation `BLOCKED` → execução `BLOCKED`;
2. revisão humana → `NOT_EXECUTABLE`;
3. valor unitário `None` → `NOT_EXECUTABLE`;
4. quantidade ausente → `NOT_EXECUTABLE`;
5. caso contrário → `EXECUTABLE`.

## 6. Limite

O modelo não considera quais operações um Engine específico suporta. Essa
restrição pertence ao consumidor futuro do contrato.

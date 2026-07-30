# Classificação de Computabilidade

## 1. Classes

- `FULLY_EXECUTABLE`: todos os fatos, condições e operações necessários estão
  estruturados.
- `PARTIALLY_EXECUTABLE`: parte da operação está estruturada, mas existem
  entradas ou decisões externas.
- `TEXT_DEPENDENT`: a condição que determina aplicação permanece em texto
  normativo, embora unidade e valor possam estar estruturados.
- `HUMAN_ONLY`: não há estrutura operacional suficiente.

## 2. Resultado

| Classe | Critérios |
|---|---:|
| `FULLY_EXECUTABLE` | 0 |
| `PARTIALLY_EXECUTABLE` | 0 |
| `TEXT_DEPENDENT` | 55 |
| `HUMAN_ONLY` | 0 |

## 3. Justificativa

Todos os critérios possuem unidade e valor, ou variantes explícitas de valor.
Entretanto, a correspondência entre fato e critério depende do respectivo
`official_text`. Os datasets não transformam esse texto em condições
estruturadas nem fornecem fatos ou quantidades.

`TEXT_DEPENDENT` é, portanto, a classificação uniforme e conservadora. Ela não
afirma que todos os critérios exigirão necessariamente decisão humana em toda
implementação futura; afirma apenas que, no modelo disponível, sua condição de
aplicação ainda é textual.

## 4. Lacunas compartilhadas

- fatos factuais ausentes;
- quantidade não fornecida;
- condição do critério não estruturada;
- documentos aceitos definidos apenas em escopo geral;
- resolução de sobreposição reservada à avaliação fundamentada;
- ato complementar do art. 4º, parágrafo único, VII não disponível;
- texto oficial com sinais de problema de codificação.

## 5. Limite da classificação

A classificação avalia a estrutura documental, não a complexidade jurídica nem
o mérito do critério. Nenhuma regra foi executada e nenhuma pontuação foi
produzida.

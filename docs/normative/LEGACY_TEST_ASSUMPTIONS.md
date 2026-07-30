# Pressupostos dos Testes do Motor Normativo Legado

## 1. Advertência

Os testes abaixo caracterizam o software. Eles não comprovam que uma regra é
oficial. Não foi encontrada fixture normativa externa: os dados são construídos
diretamente nos testes, por comandos, factories locais, `SimpleNamespace`,
spies e mocks.

## 2. Catálogo e constantes

| Teste | Expectativa fixa | Fixture/mecanismo | Regra relacionada | Origem |
|---|---|---|---|---|
| `test_domain_foundation.py:34` | 6 requisitos, 55 critérios, distribuição `[10,11,3,8,4,19]` | instancia `OfficialRscCatalog` | LR-A-001/002 | código; documento oficial ausente |
| `test_domain_foundation.py:52` | IDs inicial/final e valores 1.5, 4.5, 7.5, 3.5; unidade MONTH | consultas diretas | LR-A-002 | código |
| `test_domain_foundation.py:78` | variantes do requisito 5: `(9,4.5)`, `(7.5,3)`, `(4.5,1.5)`, `(3,1)` | tupla literal | LR-A-004 | código |
| `test_domain_foundation.py:92` | catálogo read-only e IDs desconhecidos rejeitados | tentativa de mutação | LR-C-001 | técnica |

## 3. Pontuação

| Teste | Cenário e valor esperado | Hipótese |
|---|---|---|
| `test_domain_foundation.py:257` | mandato 2 unidades + prêmio + variante substituto totalizam `27.5`; excluída aplica `0` | multiplicação e soma sem teto; LR-A-006/007/008 |
| `test_domain_foundation.py:296` | amostras retornam `4.5`, `7.5`, `3`, `1.5`, `1`, `20`, `30`, `9`, `4.5` | valores do catálogo tratados como estáveis |
| `test_domain_foundation.py:330` | duas Activities do mesmo critério somam `15` | acumulação simples, sem limite demonstrado |
| `test_application_facade_summary.py:42` | fluxo completo totaliza `9.0` e conclusão `100` | Facade preserva cálculo e resumo |
| `test_application_facade_summary.py:86` | processo vazio retorna score e percentual `0` | neutro técnico |
| `test_application_facade_summary.py:104` | parcial retorna percentual `50.0` e score `10.5` | percentual operacional independente do fundamento normativo |
| `test_validation_scoring_use_cases.py:183-231` | incluída pontua, excluída não aplica pontos | orquestração delega ao serviço |

## 4. Validação

| Teste | Expectativa | Hipótese |
|---|---|---|
| `test_domain_foundation.py:344` | Activity draft sem Evidence gera warning; complete gera error | LR-A-012 |
| `test_domain_foundation.py:365` | requerente/instituição ausentes, critério inválido e Evidence ausente geram errors | LR-A-010/014 |
| `test_domain_foundation.py:385` | processo vazio é válido; variante ausente/proibida gera códigos específicos | LR-A-011 e decisão técnica de validade |
| `test_validation_scoring_use_cases.py:79-146` | casos de uso retornam contagens e não ocultam issues | orquestração |
| `test_validation_scoring_use_cases.py:318` | módulo de pipeline não contém fórmula, catálogo ou enum de severidade | separação arquitetural LR-B-005 |

## 5. Domínio e relacionamentos

| Teste | Pressuposto |
|---|---|
| `test_domain_foundation.py:125` | quantidade zero, data final anterior e Evidence duplicada são inválidas |
| `test_domain_foundation.py:143` | Evidence exige documentos |
| `test_domain_foundation.py:156` | um documento pode sustentar diferentes Evidence; status e justificativa são preservados |
| `test_activity_evidence_workflow_use_cases.py:103` | critério desconhecido e quantidade inválida são rejeitados |
| `test_activity_evidence_workflow_use_cases.py:115` | variantes requeridas/proibidas seguem o catálogo |
| `test_activity_evidence_workflow_use_cases.py:190` | documentos ausentes, duplicados ou não relacionados são rejeitados |

## 6. Mocks, spies e fixtures

- `test_validation_scoring_use_cases.py` usa stores, validators e scorers
  spies para verificar número e ordem de delegações.
- `test_application_facade_summary.py` usa `EvidenceLookup`, sessão real em
  memória e patches/spies de casos de uso.
- `test_domain_foundation.py` constrói todos os dados no próprio arquivo; não
  carrega anexos, planilhas ou atos.
- `test_activity_evidence_workflow_use_cases.py` usa comandos e sessão em
  memória; os documentos são entidades de teste, não arquivos oficiais.
- Não foram localizadas fixtures `.pdf`, `.xlsx`, `.ods`, `.docx` ou `.csv`
  com conteúdo normativo.

## 7. Regras presentes apenas em testes

Nenhuma regra de cálculo ou validação foi encontrada exclusivamente em teste:
as expectativas numéricas espelham constantes ou algoritmos de produção.

Há, contudo, uma hipótese arquitetural verificada apenas por inspeção AST em
`test_validation_scoring_use_cases.py:318`: o módulo de casos de uso não deve
conter fórmula, catálogo ou enum de severidade. Ela é uma restrição técnica,
não normativa.

## 8. Pontos que exigem conferência humana

Todos os valores numéricos, contagens, variantes, unidades, estados com efeito
na pontuação, acumulação sem teto e severidades com significado operacional.
Nenhum deles possui, nos testes, citação de ato, página, tabela ou célula.

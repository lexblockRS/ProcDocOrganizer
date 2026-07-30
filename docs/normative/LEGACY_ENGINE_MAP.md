# Mapa Técnico do Motor Normativo Legado

## 1. Escopo e advertência

Este documento descreve o comportamento executável encontrado no repositório.
Ele não confirma que qualquer catálogo, valor, fórmula ou validação seja
oficial. As fontes primárias estão ausentes, conforme
`NORMATIVE_SOURCE_INVENTORY.md` e `NORMATIVE_GAPS.md`.

## 2. Visão executável

```text
RscApplicationFacade
    → RscUseCaseRegistry
        → ValidateProcessUseCase
            → RscValidationService
                → OfficialRscCatalog
        → CalculateScoreUseCase
            → RscScoringService
                → OfficialRscCatalog
        → GenerateSummaryUseCase
            → validação + pontuação

OfficialRscCatalog
    → RscRequirement
    → RscCriterion
        → CriterionScoreVariant
        → MeasurementUnit

RscProcess
    → 0..* RscActivity
        → criterion_id + quantity + score_variant_id
        → 0..* evidence_ids
    → 0..* document_ids

RscScoringService
    → ActivityScore
    → RequirementScore
    → RscScoreResult

RscValidationService
    → ValidationIssue
    → RscValidationResult
```

Não há Controller ou Workspace normativo dedicado. A UI atual não executa
fórmulas; o motor é alcançado pela Facade/casos de uso e por integrações
legadas de sessão.

## 3. Componentes

### 3.1 Catálogo e constantes

| Componente | Responsabilidade | Entradas | Saídas | Dependências/objetos | Constantes | Recebe chamadas de | Chama |
|---|---|---|---|---|---|---|---|
| `OfficialRscCatalog` — `applications/rsc/catalogs/official_criteria.py:156` | indexar requisitos e critérios imutáveis | IDs de requisito/critério | `RscRequirement`, `RscCriterion`, tuplas | `MappingProxyType`, modelos de domínio | `_TITLES`, `_ROWS`, `_VARIANT_ROWS`, 6/55 | serviços e composição | construtores dos modelos |
| `_variant` — linha 110 | construir variante titular/substituto | critério, papel, pontos em texto | `CriterionScoreVariant` | `Decimal` | qualificadores `role` | construção do catálogo | `CriterionScoreVariant` |
| `RSC_REQUIREMENT_IDS` e factories — `domain/identifiers.py:7` | códigos internos e validação básica | números/valores | IDs, UUIDs, textos e Decimal | `UUID`, `Decimal`, UTC | padrões de IDs, faixa 1..6, quantidade > 0 | todo o domínio | biblioteca padrão |
| `MeasurementUnit` — `domain/enums.py:37` | conjunto de unidades aceitas | não aplicável | valores enum | `Enum` | 15 flags de unidade | catálogo e critérios | nenhuma |

### 3.2 Modelos

| Componente | Responsabilidade | Entradas | Saídas/invariantes | Dependências | Chamado por |
|---|---|---|---|---|---|
| `RscRequirement` — `domain/requirement.py:9` | representar requisito | ID, número, textos, ordem | objeto imutável; número 1..6 e ordem igual ao número | factories de IDs | catálogo |
| `RscCriterion` — `domain/criterion.py:31` | representar item e modo de pontuação | requisito, item, unidade, pontos/variantes | exatamente um modo de pontuação; IDs de variantes únicos | `MeasurementUnit`, `Decimal` | catálogo, scoring, validation |
| `CriterionScoreVariant` — `criterion.py:11` | pontos condicionados por qualificador | ID, rótulo, pontos, qualifiers | pontos positivos; qualifiers imutáveis | `MappingProxyType` | catálogo e scoring |
| `RscActivity` — `domain/activity.py:13` | atividade já ligada a critério | criterion_id, título, quantidade, datas, status, variante e Evidence | quantidade positiva, datas coerentes, Evidence sem duplicidade | enums e identifiers | activity service, scoring, validation |
| `RscEvidence` — `domain/evidence.py:16` | alegação normativa ligada à Activity/documentos | activity_id, documentos, descrição, status | ao menos um documento, sem duplicidade | `EvidenceStatus`, timestamps | evidence service, validation |
| `RscDocument` — `domain/document.py:15` | referência documental normativa legada | nomes/caminhos/status/metadata | textos e timestamps normalizados | `DocumentStatus` | document service, validation |
| `RscProcess` — `domain/process.py:31` | conter Activities e referências documentais | requerente, instituição, metadata | coleções por identidade e lifecycle | `RscProcessStatus` | process service, use cases |
| `ValidationIssue/Result` — `domain/validation.py:14` | resultado estruturado | código, severidade, entidade/campo | contagens e `is_valid` sem ERROR | `ValidationSeverity` | validation service/use case |
| `ActivityScore`, `RequirementScore`, `RscScoreResult` — `domain/score.py:9` | resultados imutáveis | valores calculados | memória de cálculo em três níveis | `Decimal`, timestamp | scoring service/use cases |

### 3.3 Serviços

| Componente | Responsabilidade | Consome | Produz | Dependências | Chamadas realizadas |
|---|---|---|---|---|---|
| `RscScoringService.calculate_activity` — `services/scoring_service.py:21` | escolher pontos e calcular Activity | `RscActivity` | `ActivityScore` | catálogo, Decimal | `get_criterion`, `get_variant` |
| `calculate_requirement` — linha 45 | filtrar e somar por requisito | `RscProcess`, requirement_id | `RequirementScore` | catálogo | `calculate_activity` |
| `calculate_process` — linha 65 | calcular todos os requisitos | `RscProcess` | `RscScoreResult` | catálogo, UTC | `calculate_requirement` |
| `RscValidationService.validate_activity` — `validation_service.py:34` | validar critério, variante, quantidade, datas e Evidence | Activity e evidências fornecidas | `RscValidationResult` | catálogo, severidades | `get_criterion/get_variant`, `_issue` |
| `validate_evidence` — linha 132 | validar documentos e Activity correspondente | Evidence e Activity opcional | resultado | modelos | `_issue` |
| `validate_document` — linha 165 | validar nome e status | Document | resultado | `DocumentStatus` | `_issue` |
| `validate_process` — linha 189 | agregar validações e integridade de referências | Process, Evidence, Documents | resultado agregado | demais validadores | `validate_activity/evidence/document` |
| `RscActivityService` — `services/activity_service.py:10` | criar e consultar Activities por catálogo | atributos de Activity | `RscActivity` | catálogo | `get_criterion/get_variant` |
| `RscEvidenceService` — `services/evidence_service.py:9` | criar/vincular Evidence normativa | Activity/documentos | Activity/Evidence atualizadas | modelos | métodos imutáveis |
| `RscProcessService` — `services/process_service.py:6` | store em memória de processos | Process/IDs | Process/coleções | dicionário | domínio |

### 3.4 Casos de uso, Facade e composição

| Componente | Entrada | Saída | Dependências | Chamadas |
|---|---|---|---|---|
| `ValidateProcessUseCase.execute` — `use_cases/validation_scoring_use_cases.py:47` | `ValidateProcessCommand` | `ValidationUseCaseResult` | process/document/evidence services, validator | resolve Process e delega validação |
| `CalculateScoreUseCase.execute` — linha 100 | `CalculateScoreCommand` | `ScoreUseCaseResult` | process service, scoring | delega `calculate_process` |
| `GenerateSummaryUseCase.execute` — `summary_use_case.py:35` | comando de resumo | `SummaryUseCaseResult` | registry, validação, scoring | executa dois casos de uso e calcula percentual |
| `RscApplicationFacade` — `facade.py:30` | Commands públicos | Results públicos | `RscProjectSession.use_cases` | `_execute` |
| `RscUseCaseRegistry` — `use_cases/registry.py:11` | instâncias/tipos | caso de uso | mapping interno | register/get/dispose |
| `create_rsc_project_session` — `composition.py:126` | lookup/repositories | `RscProjectSession` | singleton do catálogo, serviços, casos de uso | instancia e injeta dependências |
| `RscProjectSession` — `project_session.py:34` | componentes compostos | API da sessão | serviços, catálogo, registry | dispose |

### 3.5 DTOs e resultados

- `ActivityDTO`, `ProjectDTO`, `FunctionalAssignmentEvidenceDTO` e
  `FunctionalExerciseDTO` são transportes; não executam regra de pontuação.
- `ValidationUseCaseResult` expõe issues, validade e contagens.
- `ScoreUseCaseResult` expõe score e total.
- `SummaryUseCaseResult` agrega validação, pontuação, contagens e percentual.
- Localização: `applications/rsc/dto/` e
  `applications/rsc/use_cases/results.py:9-126`.

### 3.6 Persistência, adapters e repositories

- O motor normativo original usa `RscProcessService` como store em memória.
- A persistência `.pdop` usa
  `applications/rsc/infrastructure/project_repository.py` e
  `serializers.py`; serializa processos, documentos, Activities e Evidence.
- Os repositories SQLite em `applications/rsc/repositories/` pertencem ao
  pipeline funcional mais recente (`Activity`, `FunctionalExercise` e
  `FunctionalAssignmentEvidence`) e não executam catálogo, validação ou
  pontuação normativa.
- Não há adapter externo de legislação, registry de versões normativas ou
  repository de normas.

### 3.7 Controllers e Workspaces

- `core/project_controller.py` coordena lifecycle e Workspaces funcionais.
- `presentation/activities`, `functional_assignments` e
  `functional_exercises` tratam reconstrução factual, não pontuação normativa.
- `ui/views/` apenas apresenta estado e emite intenções.
- Não há `NormativeController`, `ScoringController`, Normative Workspace ou
  Scoring Workspace implementados.
- Logo, não foram encontradas regras de interface que alterem cálculo. A regra
  LR-D-001 registra essa ausência de algoritmo na apresentação.

### 3.8 Configuração

Não há arquivo de configuração para requisitos, pesos, limites, vigência ou
seleção de versão normativa. O catálogo é código Python importado como
singleton. `requirements.txt` configura dependências técnicas, não regras RSC.

## 4. Classificação das regras

| Classe | Significado neste inventário | Quantidade |
|---|---|---:|
| A | aparentemente normativa, mas sem confirmação oficial | 14 |
| B | técnica ou de produto | 5 |
| C | infraestrutura/persistência | 4 |
| D | interface | 1 |
| E | origem desconhecida não classificável como norma | 1 |
| **Total** |  | **25** |

Todas as regras A também possuem origem normativa desconhecida.

## 5. Constantes

`LEGACY_CONSTANTS.json` registra 24 grupos de constantes. `_ROWS` contém os 55
registros individuais do catálogo; para evitar duplicar o próprio código no
inventário, eles são tratados como um conjunto catalogado em LC-003/LC-011 e
rastreáveis a `official_criteria.py:48-100`. Antes de qualquer implementação
futura, cada linha precisa ser desmembrada e ligada a página/tabela oficial.

## 6. Chamadas principais

### Validação

```text
Facade.validate_process(command)
→ registry.get(ValidateProcessUseCase)
→ use_case.execute(command)
→ process_service.get_process
→ document/evidence services
→ validation_service.validate_process
→ validate_activity + validate_evidence + validate_document
→ ValidationUseCaseResult
```

### Pontuação

```text
Facade.calculate_score(command)
→ registry.get(CalculateScoreUseCase)
→ use_case.execute(command)
→ process_service.get_process
→ scoring_service.calculate_process
→ calculate_requirement (para cada requisito)
→ calculate_activity (para cada Activity aplicável)
→ ScoreUseCaseResult
```

### Resumo

```text
Facade.generate_summary(command)
→ GenerateSummaryUseCase
→ ValidateProcessUseCase
→ CalculateScoreUseCase
→ percentual operacional de conclusão
→ SummaryUseCaseResult
```

## 7. Riscos técnicos

1. “Official” é apenas nome de classe, sem prova de oficialidade.
2. catálogo, versão e vigência não são dados; são estado global em código.
3. não existe proveniência por critério.
4. Activity factual e `RscActivity` normativa coexistem.
5. os testes tornam o comportamento estável, mas não demonstram validade.
6. resultados possuem timestamp, porém não identificam regulamento.
7. não há limites/tetos explícitos; a ausência pode ser regra ou lacuna.

## 8. Navegação

- regras: `LEGACY_RULES.json`;
- constantes: `LEGACY_CONSTANTS.json`;
- pressupostos executáveis: `LEGACY_TEST_ASSUMPTIONS.md`;
- fontes disponíveis: `NORMATIVE_SOURCE_INVENTORY.md`;
- lacunas: `NORMATIVE_GAPS.md`.

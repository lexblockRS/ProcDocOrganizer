# API pública RSC — Sprint 1.5.1

## Superfície estável

A futura camada de apresentação deve importar exclusivamente de:

- `applications.rsc`
- `applications.rsc.api`

Essa superfície contém:

- `RscApplication`, `RscProjectSession` e `RscApplicationFacade`;
- comandos aceitos pela fachada;
- resultados retornados pela fachada;
- DTOs de diagnóstico documental;
- entidades e enums necessários para leitura dos resultados;
- exceções da coordenação de casos de uso.

`applications.rsc.api.PUBLIC_API_VERSION` identifica a revisão documental
da superfície, não o schema `.pdop`.

## Detalhes internos

Não são contratos estáveis para a apresentação:

- `applications.rsc.services`
- `applications.rsc.repositories`
- `applications.rsc.infrastructure`
- classes concretas de `applications.rsc.use_cases`
- `applications.rsc.composition`
- serializers e registries

Esses módulos podem ser usados pela composição e pelos testes internos.

## Compatibilidade legada

Os módulos abaixo pertencem ao fluxo anterior e permanecem disponíveis
porque ainda são usados internamente:

- `applications.rsc.models`
- `applications.rsc.commands`
- DTOs `ActivityDTO`, `ProjectDTO`, `FunctionalExerciseDTO` e
  `FunctionalAssignmentEvidenceDTO`;
- portas e repositories associados ao fluxo funcional anterior.

Eles não devem ser usados por código novo da apresentação. Não houve
remoção, renomeação ou alteração comportamental nesta consolidação.

Em particular:

- `applications.rsc.api.CreateActivityCommand` é o comando do fluxo
  canônico baseado em `domain` e `use_cases`;
- `applications.rsc.commands.CreateActivityCommand` é preservado somente
  para compatibilidade do fluxo anterior;
- `applications.rsc.infrastructure.ProjectRepository` não é parte da API
  pública, evitando conflito com a porta legada de mesmo nome.

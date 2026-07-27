# ADR-007 — Camada de Apresentação e Projeções

## Status

Accepted

## Contexto

A evolução da `HomeView` para um Dashboard exige combinar informações do
projeto, documentos, evidências e, opcionalmente, da aplicação RSC. Entregar
sessões ou entidades diretamente à view faria a interface conhecer detalhes de
composição, persistência e regras que não lhe pertencem.

O número ADR-006 já está ocupado pela decisão sobre resolução de identidade.
Esta decisão usa o próximo número disponível sem substituir aquele documento.

## Decisão

- A fronteira `presentation/dashboard` reúne controller, service e projections
  específicos da apresentação, sem criar dependência do pacote `services`
  sobre `ui`.
- `DashboardController` coordena os estados sem projeto, carregando, pronto e
  erro, além do ciclo da sessão ativa.
- `DashboardService` consulta exclusivamente serviços públicos presentes na
  `ProjectSession` e agrega seus resultados.
- Projections imutáveis representam todos os dados entregues ao Dashboard.
- A `HomeView` é passiva: apresenta projections prontas e não recebe sessões,
  services, repositories ou entidades para agregar.
- A UI não acessa SQLite nem repositories diretamente.
- DTOs de aplicação atravessam fronteiras de casos de uso; projections são
  modelos específicos da apresentação e não substituem esses DTOs.
- A parte RSC é opcional e alcançada somente pelo serviço de Dashboard através
  dos serviços públicos já compostos na `RscProjectSession`.

## Consequências

O `ProjectController` permanece responsável pelo ciclo de vida e pela navegação
global, mas delega o resumo do projeto. O Dashboard pode evoluir visualmente sem
transferir regras para widgets ou acoplar a apresentação à persistência.

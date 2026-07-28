# Arquitetura da Camada de Apresentação — Release 1.6

**Versão:** 1.0
**Status:** referência arquitetônica oficial da Release 1.6
**Escopo:** contratos de apresentação atualmente implementados

## Índice

1. [Visão geral](#visao-geral)
2. [Princípios arquitetônicos](#principios)
3. [Visão estrutural](#visao-estrutural)
4. [Camada de estado](#camada-estado)
5. [Camada de coordenação](#camada-coordenacao)
6. [DTOs e tipos de contrato](#dtos)
7. [Fluxos principais](#fluxos)
8. [Matriz de dependências](#dependencias)
9. [Regras oficiais](#regras)
10. [Decisões arquitetônicas](#decisoes)
11. [Qualidade e testabilidade](#qualidade)
12. [Próximos passos previstos](#roadmap)
13. [Glossário](#glossario)

<a id="visao-geral"></a>
## 1. Visão geral

A camada de apresentação fornece contratos independentes de toolkit para
representar estado de interface, coordenar fluxos lógicos e distribuir eventos
transitórios. Seu objetivo é estabelecer uma fronteira estável antes da
integração visual.

A arquitetura separa três naturezas de componente:

- **Stores** possuem estado de apresentação e publicam snapshots imutáveis.
- **Controllers e executores** coordenam APIs públicas sem duplicar estado.
- **DTOs** transportam valores validados sem comportamento visual.

Essa divisão evita que navegação, execução operacional ou notificações sejam
confundidas com estado persistente. Também permite testar todos os contratos
sem Qt, infraestrutura ou entidades do domínio RSC.

Os benefícios observáveis são:

- mudanças de estado explícitas e rastreáveis por revisão;
- invariantes concentradas nos respectivos proprietários;
- consumidores desacoplados por snapshots e callbacks;
- coordenação testável por chamadas síncronas;
- fronteira pronta para adaptadores visuais futuros;
- ausência de dependências circulares entre os contratos.

Este documento descreve apenas o que existe. MainWindow, widgets e adaptadores
Qt não fazem parte desta arquitetura contratual e aparecem somente como ponto
de integração previsto.

<a id="principios"></a>
## 2. Princípios arquitetônicos

### 2.1 Estado tem proprietário

Cada Store é a fonte autoritativa do estado que representa. Nenhum controller
edita snapshots ou replica valores para se tornar uma segunda fonte de
verdade.

`PresentationContextStore` é um caso deliberadamente derivado: os três stores
observados continuam autoritativos, enquanto ele possui somente seu
`PresentationSnapshot` consolidado.

### 2.2 Coordenação não é estado

`NavigationController`, `OperationExecutor` e `NotificationCenter` não
possuem snapshot ou revisão. Referências a dependências, callbacks inscritos e
objetos transitórios de uma chamada não constituem estado autoritativo da
aplicação.

### 2.3 DTOs e snapshots são imutáveis

Os DTOs centrais são `dataclass(frozen=True, slots=True)`. Um Store cria uma
nova instância de snapshot para cada mudança efetiva. Consumidores nunca
recebem acesso mutável ao estado interno.

### 2.4 Revisão mede mudanças efetivas

Cada snapshot de Store possui `revision`, iniciada em zero e incrementada uma
vez por alteração efetiva daquele Store. Operações redundantes preservam a
instância atual, não incrementam a revisão e não notificam observers.

As revisões são locais. A revisão do `PresentationSnapshot`, por exemplo, mede
recomposições do contexto, não substitui as revisões dos snapshots internos.

### 2.5 Observação é síncrona e isolada

Stores expõem `subscribe(callback)` e devolvem uma função de cancelamento
idempotente. Os callbacks recebem apenas o snapshot correspondente. A falha de
um observer é registrada e não impede os demais.

`NotificationCenter` reutiliza a mesma disciplina de callbacks, mas entrega
eventos transitórios em vez de snapshots.

### 2.6 Núcleo independente

Os contratos não dependem de:

- Qt ou afinidade com a thread visual;
- MainWindow ou widgets;
- infraestrutura e persistência;
- entidades ou regras do domínio RSC;
- `ApplicationFacade`.

<a id="visao-estrutural"></a>
## 3. Visão estrutural

### 3.1 Diagrama geral

```text
                         CAMADA DE COORDENAÇÃO

  NavigationController       OperationExecutor       NotificationCenter
           │                         │                        │
           │ comandos públicos      │ ciclo operacional      │ eventos
           ▼                         ▼                        ▼

                            CAMADA DE ESTADO

  SelectionStore      PerspectiveStore      ApplicationStateStore
         ▲                 ▲       ▲                  │
         │                 │       │ consulta         │ observação
         │                 │       └──── WorkspaceStore
         │                 │
         └────────── NavigationController ────────────┘

  ApplicationStateStore ─┐
  SelectionStore ────────┼──> PresentationContextStore
  PerspectiveStore ──────┘               │
                                         ▼
                              PresentationSnapshot

  Stores ──> snapshots imutáveis ──> observers
```

As setas representam dependências ou chamadas permitidas, não propriedade
compartilhada. `WorkspaceStore` apenas consulta o catálogo de perspectivas.
`PresentationContextStore` apenas observa os stores de origem.

### 3.2 Organização lógica

```text
presentation/
├── application_state.py       estado operacional global
├── selection.py               seleção global
├── perspectives.py            catálogo e ativação de perspectivas
├── presentation_context.py    projeção consolidada derivada
├── workspace.py               montagem lógica central
├── navigation.py              coordenação da navegação
├── operations.py              coordenação do ciclo operacional
└── notifications.py           distribuição de eventos transitórios
```

<a id="camada-estado"></a>
## 4. Camada de estado

### 4.1 ApplicationStateStore

**Objetivo.** Ser o único proprietário do estado operacional global da
apresentação.

**Snapshot.** `ApplicationStateSnapshot` registra estado atual, estado
anterior quando aplicável, operação ativa, identidade do projeto, indicadores
de projeto/modificação, erro e revisão.

**Responsabilidades.**

- realizar transições diretas válidas;
- iniciar, concluir, cancelar e falhar operações;
- preservar o contexto do projeto durante ciclos operacionais;
- rejeitar transições incompatíveis sem alterar o snapshot;
- publicar mudanças efetivas.

**Invariantes principais.**

- `NO_PROJECT` não possui projeto nem modificação;
- `PROJECT_OPEN` possui projeto sem modificação;
- `PROJECT_MODIFIED` possui projeto modificado;
- `BUSY` exige estado anterior e identificador de operação;
- `ERROR` exige descrição;
- `CLOSING` é terminal;
- somente `BUSY` possui operação ativa.

**Dependências permitidas.** Somente biblioteca padrão. Não conhece os demais
stores.

### 4.2 SelectionStore

**Objetivo.** Ser o único proprietário da seleção global de apresentação.

**Snapshot.** `SelectionSnapshot` contém um `SelectionContext` e sua revisão.

**Responsabilidades.**

- selecionar um contexto validado;
- limpar para a seleção canônica `NONE`;
- copiar e congelar metadata recursivamente;
- ignorar seleção ou limpeza redundante;
- publicar mudanças efetivas.

**Invariantes principais.**

- `SelectionKind.NONE` não possui identificador, nome ou metadata;
- seleções reais exigem identificador textual;
- metadata aceita somente escalares e coleções imutáveis suportadas;
- nenhuma entidade, widget, sessão ou facade é armazenada.

**Dependências permitidas.** Somente biblioteca padrão.

### 4.3 PerspectiveStore

**Objetivo.** Possuir o catálogo declarativo e a identidade da perspectiva
ativa.

**Snapshot.** `PerspectiveSnapshot` contém `active`, a tupla `available` e a
revisão.

**Responsabilidades.**

- registrar, consultar, listar e verificar perspectivas;
- ordenar definições deterministicamente;
- ativar e desativar perspectivas registradas;
- recusar IDs ou títulos conflitantes;
- armazenar factories sem executá-las.

**Invariantes principais.**

- IDs e títulos são únicos;
- somente perspectiva registrada pode estar ativa;
- existe no máximo uma perspectiva ativa;
- a coleção disponível é imutável;
- ativação e desativação redundantes são no-op.

**Dependências permitidas.** Somente biblioteca padrão.

### 4.4 PresentationContextStore

**Objetivo.** Expor uma visão consolidada do estado global sem substituir os
proprietários individuais.

**Snapshot.** `PresentationSnapshot` referencia
`ApplicationStateSnapshot`, `SelectionSnapshot`, `PerspectiveSnapshot` e
possui revisão própria.

**Responsabilidades.**

- capturar os snapshots iniciais;
- observar os três stores de origem;
- substituir somente a referência interna que mudou;
- publicar uma nova consolidação por mudança efetiva.

**Invariantes principais.**

- snapshots internos nunca são modificados;
- stores de origem permanecem autoritativos;
- o Context Store não emite comandos aos stores observados;
- uma atualização redundante não recompõe o contexto.

**Dependências permitidas.** `ApplicationStateStore`, `SelectionStore` e
`PerspectiveStore`, exclusivamente para leitura inicial e observação.

### 4.5 WorkspaceStore

**Objetivo.** Possuir o estado lógico do espaço central onde uma perspectiva
será apresentada.

**Snapshot.** `WorkspaceSnapshot` contém `WorkspaceState`,
`active_perspective` e revisão.

**Responsabilidades.**

- montar logicamente uma perspectiva registrada;
- substituir a montagem lógica;
- limpar o Workspace;
- consultar a existência do ID no catálogo;
- publicar mudanças efetivas.

**Invariantes principais.**

- `EMPTY` implica `active_perspective=None`;
- `READY` exige exatamente um `PerspectiveId`;
- nenhuma factory é executada;
- nenhum widget é criado;
- montar não ativa o `PerspectiveStore`.

**Dependências permitidas.** `PerspectiveStore`, somente para consulta pública
ao catálogo.

### 4.6 Contrato comum dos Stores

| Característica | Regra |
|---|---|
| Propriedade | Cada Store possui apenas seu snapshot |
| Imutabilidade | Snapshots são frozen e slotted |
| Mudança | Cria nova instância |
| Redundância | Preserva instância e revisão |
| Observação | `subscribe()` retorna unsubscribe idempotente |
| Falha de observer | Registrada e isolada |
| Coordenação | Store não comanda outro Store |
| UI concreta | Proibida |

<a id="camada-coordenacao"></a>
## 5. Camada de coordenação

### 5.1 NavigationController

**Responsabilidade.** Coordenar, em ordem, ativação de perspectiva, montagem
do Workspace e limpeza opcional da seleção.

```text
PerspectiveId
      │
      ▼
PerspectiveStore.activate()
      │
      ▼
WorkspaceStore.mount()
      │
      ▼
SelectionStore.clear()  [quando configurado]
```

**Dependências.** `PerspectiveStore`, `WorkspaceStore` e `SelectionStore`.

**Ausência de estado.** Não possui snapshot, revisão, observers ou histórico.
Mantém somente referências às dependências e a política de limpeza.

**Responsabilidades proibidas.** Não cria views, executa factories, abre
projetos, acessa domínio, implementa voltar/avançar ou mantém breadcrumbs.

**Semântica de falha.** A navegação não é transacional. A primeira exceção
interrompe chamadas posteriores e é propagada sem compensação. Stores já
alterados preservam suas próprias invariantes, mas podem permanecer
parcialmente atualizados.

### 5.2 OperationExecutor

**Responsabilidade.** Executar uma unidade de trabalho síncrona e coordenar
seu ciclo no `ApplicationStateStore`.

**Dependência.** Somente `ApplicationStateStore`.

**Ausência de estado.** Não possui snapshot, revisão, observers, operação
ativa própria, fila, histórico ou cache.

**Fluxos.**

- sucesso: `begin_operation()` → trabalho → `complete_operation()`;
- cancelamento: `begin_operation()` → `OperationCancelled` →
  `cancel_operation()` → propagação;
- falha: `begin_operation()` → exceção → `fail_operation()` → propagação;
- falha de início: a unidade de trabalho não é executada.

O token é verificado antes e depois do trabalho. O resultado de sucesso é
retornado sem envelope ou transformação. Falhas secundárias ao registrar
cancelamento ou erro são registradas e não mascaram a exceção original.

**Responsabilidades proibidas.** Não cria threads, não oferece API assíncrona,
não navega, não notifica visualmente, não persiste resultados, não implementa
retry e não executa rollback de negócio.

### 5.3 NotificationCenter

**Responsabilidade.** Distribuir `Notification` diretamente aos callbacks
inscritos, preservando a ordem de inscrição.

**Dependências.** Somente biblioteca padrão.

**Ausência de estado autoritativo.** Não possui snapshot, revisão, fila,
histórico ou retenção de eventos. A lista de callbacks ativos é infraestrutura
transitória de distribuição, não estado da aplicação.

**Falhas.** Uma exceção de observer é registrada e não impede os seguintes.

**Responsabilidades proibidas.** Não cria widgets, diálogos ou mensagens
visuais, não escreve em status bar, não altera stores e não persiste
notificações.

<a id="dtos"></a>
## 6. DTOs e tipos de contrato

### 6.1 Estado operacional

| Tipo | Conteúdo | Observação |
|---|---|---|
| `ApplicationState` | seis estados operacionais | enum textual |
| `ApplicationStateSnapshot` | estado, operação, projeto, erro, revisão | snapshot autoritativo |

### 6.2 Seleção

| Tipo | Conteúdo | Observação |
|---|---|---|
| `SelectionKind` | tipo estável da seleção | enum textual |
| `SelectionIdentity` | kind e identificador | `none()` é canônico |
| `SelectionContext` | identidade, nome e metadata | metadata profundamente congelada |
| `SelectionSnapshot` | contexto e revisão | snapshot autoritativo |

### 6.3 Perspectivas

| Tipo | Conteúdo | Observação |
|---|---|---|
| `PerspectiveId` | identidade textual dinâmica | hashable e serializável |
| `PerspectiveDefinition` | ID, título, ordem, ícone, requisito e factory | serialização omite factory |
| `PerspectiveSnapshot` | ativa, disponíveis, revisão | catálogo imutável |

Uma perspectiva é um ponto de vista declarativo, não uma View ou widget.

### 6.4 Contexto e Workspace

| Tipo | Conteúdo | Observação |
|---|---|---|
| `PresentationSnapshot` | três snapshots internos e revisão | projeção derivada |
| `WorkspaceState` | `EMPTY` ou `READY` | sem estado de carregamento |
| `WorkspaceSnapshot` | estado, perspectiva montada, revisão | montagem somente lógica |

### 6.5 Operações

| Tipo | Conteúdo | Observação |
|---|---|---|
| `OperationId` | identidade textual | hashable e serializável |
| `CancellationToken` | sinal cooperativo | mutável, idempotente e seguro para sinalização |
| `OperationContext` | ID e referência estável ao token | DTO frozen e slotted |
| `OperationWork[T]` | protocolo `work(context) -> T` | resultado genérico |
| `OperationCancelled` | cancelamento reconhecido | exceção da apresentação |

O token é intencionalmente mutável; a imutabilidade do contexto estabiliza a
referência, não o sinal interno.

### 6.6 Notificações

| Tipo | Conteúdo | Observação |
|---|---|---|
| `NotificationLevel` | info, success, warning, error | enum textual fechado |
| `Notification` | nível, título, mensagem, timeout | DTO hashable e serializável |

O timeout opcional é medido em segundos e não possui semântica ligada a Qt.

<a id="fluxos"></a>
## 7. Fluxos principais

### 7.1 Mudança de snapshot

```text
comando público
      │
      ▼
validação das invariantes
      │
      ├── redundante ──> snapshot atual
      │
      ▼
novo snapshot + revision
      │
      ▼
Store substitui referência
      │
      ▼
observers recebem snapshot
```

### 7.2 Troca de perspectiva

```text
chamador
   │
   ▼
NavigationController.navigate_to(id)
   │
   ├──> PerspectiveStore.activate(id)
   ├──> WorkspaceStore.mount(id)
   └──> SelectionStore.clear() [política habilitada]
```

O fluxo é síncrono, sequencial e não transacional. Não existe rollback manual.

### 7.3 Consolidação do contexto

```text
mudança em um Store de origem
            │
            ▼
PresentationContextStore recebe snapshot
            │
            ▼
PresentationSnapshot(revision + 1)
            │
            ▼
observers do contexto
```

### 7.4 Execução de operação

```text
execute(id, work, token?)
          │
          ▼
ApplicationStateStore.begin_operation()
          │
          ▼
token.throw_if_cancellation_requested()
          │
          ▼
work(OperationContext) ──┬── sucesso ──> nova verificação ──> complete
                         ├── cancelamento ────────────────> cancel
                         └── falha ──────────────────────> fail
```

Os três caminhos de finalização são mutuamente exclusivos.

### 7.5 Cancelamento cooperativo

```text
chamador ou trabalho
        │
        ▼
token.request_cancellation()
        │
        ▼
throw_if_cancellation_requested()
        │
        ▼
OperationCancelled
        │
        ▼
ApplicationStateStore.cancel_operation()
```

Não há interrupção forçada de thread ou processo.

### 7.6 Publicação de notificação

```text
publish(Notification)
        │
        ├──> observer 1
        ├──> observer 2  [mesmo se observer 1 falhar]
        └──> observer N

fim da chamada ──> Notification não é retida
```

<a id="dependencias"></a>
## 8. Matriz de dependências

### 8.1 Dependências permitidas

| Componente | Pode conhecer |
|---|---|
| `ApplicationStateStore` | biblioteca padrão |
| `SelectionStore` | biblioteca padrão |
| `PerspectiveStore` | biblioteca padrão |
| `PresentationContextStore` | os três stores acima |
| `WorkspaceStore` | `PerspectiveStore` para consulta |
| `NavigationController` | `PerspectiveStore`, `WorkspaceStore`, `SelectionStore` |
| `OperationExecutor` | `ApplicationStateStore` |
| `NotificationCenter` | biblioteca padrão |

### 8.2 Operações permitidas entre componentes

| Origem | Destino | Operação |
|---|---|---|
| `PresentationContextStore` | stores de origem | snapshot inicial e `subscribe()` |
| `WorkspaceStore` | `PerspectiveStore` | `contains()` |
| `NavigationController` | `PerspectiveStore` | `activate()` |
| `NavigationController` | `WorkspaceStore` | `mount()` |
| `NavigationController` | `SelectionStore` | `clear()` |
| `OperationExecutor` | `ApplicationStateStore` | ciclo operacional público |
| consumidores | `NotificationCenter` | `subscribe()` e `publish()` |

### 8.3 Dependências proibidas

Todos os componentes contratuais proíbem dependência de Qt, MainWindow,
widgets, domínio RSC, infraestrutura, persistência e `ApplicationFacade`.

Adicionalmente:

- Stores não conhecem controllers;
- stores autoritativos não conhecem o `PresentationContextStore`;
- `OperationExecutor` não conhece outros stores;
- `NotificationCenter` não altera store algum;
- `NavigationController` não conhece estado da aplicação ou contexto
  consolidado;
- DTOs não conhecem controllers nem componentes visuais.

<a id="regras"></a>
## 9. Regras oficiais

1. Um Store é proprietário somente do estado definido por seu contrato.
2. Um Store nunca coordena comandos em outro Store.
3. Consulta ou observação read-only não transfere propriedade.
4. Controllers usam exclusivamente APIs públicas.
5. Controllers não possuem snapshots ou revisões.
6. Snapshots são imutáveis e substituídos, nunca editados.
7. Mudanças redundantes não incrementam revisão nem notificam.
8. Observers recebem um único DTO e suas falhas são isoladas.
9. Factories de perspectiva não são executadas pelos contratos atuais.
10. Workspace representa montagem lógica, não composição de widgets.
11. Navegação é sequencial e não transacional.
12. Operações são síncronas e canceláveis cooperativamente.
13. Notificações são transitórias e não possuem replay.
14. MainWindow não será proprietária dos estados definidos pelos Stores.
15. Integrações futuras devem adaptar esses contratos sem introduzir Qt no
    núcleo.

<a id="decisoes"></a>
## 10. Decisões arquitetônicas

### 10.1 Stores separados

Estado operacional, seleção, perspectivas e Workspace mudam por razões
diferentes. Stores separados mantêm invariantes locais e evitam um objeto
global monolítico.

### 10.2 PresentationContextStore como projeção

O nome “Store” refere-se à propriedade do snapshot consolidado, não à
propriedade dos estados internos. A projeção reduz dependências futuras sem
apagar a autoridade dos stores de origem.

### 10.3 Perspectiva diferente de View

Perspectiva é uma definição declarativa de ponto de vista. View é um elemento
visual concreto. A separação impede dependência prematura de toolkit.

### 10.4 Workspace lógico

O Workspace registra somente qual perspectiva está montada. Ele não executa
factory nem cria widget. Essa decisão mantém o contrato verificável antes da
composição visual.

### 10.5 NavigationController sem snapshot

A navegação é ação coordenada, não uma nova fonte de estado. O resultado pode
ser observado nos stores proprietários.

### 10.6 Navegação sem rollback manual

O fluxo atual é curto e composto por stores independentes. Compensação
prematura produziria revisões e notificações artificiais. A não atomicidade é
explícita; transações de interface só serão avaliadas quando houver integração
concreta que as justifique.

### 10.7 OperationExecutor síncrono

O núcleo síncrono define primeiro a semântica de sucesso, cancelamento e falha.
Um adaptador de background poderá executar o mesmo contrato posteriormente,
sem introduzir Qt ou APIs assíncronas fictícias no núcleo.

### 10.8 CancellationToken cooperativo

O token sinaliza intenção e nunca força interrupção. A unidade de trabalho
mantém controle sobre pontos seguros de cancelamento.

### 10.9 Resultado sem envelope

`execute()` devolve diretamente o valor genérico produzido pelo trabalho.
Sucesso, cancelamento e falha já possuem caminhos distintos; um
`OperationResult` seria redundante nesta versão.

### 10.10 NotificationCenter não é Store

Uma notificação é evento, não estado. O centro distribui a mesma instância e a
descarta ao fim da publicação. Snapshot, revisão e histórico contradiriam essa
semântica transitória.

<a id="qualidade"></a>
## 11. Qualidade e testabilidade

A arquitetura favorece testes unitários sem ambiente visual:

- DTOs podem ser construídos e comparados estruturalmente;
- invariantes inválidas são testadas diretamente;
- revisões e identidade de snapshots tornam no-ops verificáveis;
- observers podem ser substituídos por callbacks simples;
- controllers podem ter a ordem de chamadas observada;
- resultados e exceções do executor são preservados;
- inspeção AST verifica dependências proibidas.

O logging registra transições relevantes, observers defeituosos, falhas de
trabalho e falhas secundárias de atualização. Conteúdo documental e dados
sensíveis não fazem parte dessas mensagens contratuais.

<a id="roadmap"></a>
## 12. Próximos passos previstos

Os passos seguintes são pontos de integração, não alterações desta
arquitetura:

- composição dos contratos pela MainWindow;
- adaptadores Qt para renderização e lifecycle;
- ligação entre perspectiva lógica e widget concreto;
- consumidores visuais de notificações;
- backend de execução em background reutilizando o executor síncrono;
- integração coordenada com a API pública da aplicação.

Detalhes de implementação permanecem deliberadamente fora deste documento.

<a id="glossario"></a>
## 13. Glossário

| Termo | Definição |
|---|---|
| Store | proprietário de um snapshot de estado de apresentação |
| Snapshot | representação imutável do estado de um Store em uma revisão |
| Observer | callback síncrono que recebe snapshot ou evento |
| Controller | coordenador sem estado autoritativo |
| Perspectiva | ponto de vista declarativo sobre um processo |
| Workspace | espaço central lógico de montagem |
| Operação | unidade de trabalho coordenada com o estado operacional |
| Notificação | evento transitório distribuído sem retenção |

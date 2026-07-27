# Core 1.0 Validation

## 1. Resumo executivo

Auditoria executada sobre o branch `feature/rsc-application`, HEAD
`25d89af15a40bc7019133788656e60ad4b78a54a`, após o PF-05B. O núcleo formado
pelos contratos, catálogo, contextos, runtime e factory suporta mais de uma
Application e delega a criação da sessão sem conhecer uma aplicação concreta.

O diretório físico `core`, porém, ainda reúne três papéis: núcleo neutro,
Platform Host e composition root. Por isso, o diretório como um todo não é
neutro: `application.py` registra RSC legitimamente no bootstrap,
`project_controller.py` contém integração visual RSC, e `project_session.py`
mantém a bridge tipada para `RscProjectSession`. Presentation e MainWindow
também contêm funcionalidades RSC explícitas.

Decisão: **B. CORE 1.0 APROVADO COM PENDÊNCIAS NÃO BLOQUEANTES**. A base
contratual e de composição pode ser congelada como Core 1.0. A neutralização
do Host, a montagem de contribuições modulares e a conexão completa do
lifecycle devem ser tratadas antes de considerar o Host extensível concluído.

## 2. Escopo

Foram revisados `contracts`, `core`, o composition root, registry, descriptor,
contrato modular, lifecycle, capabilities, contextos, runtime, sessões,
factory, RSC, contribuições, navegação, Presentation, UI, testes e documentos
arquiteturais. Não foram alteradas funcionalidades, persistência, schemas, UI,
Presentation ou regras RSC.

O worktree já estava sujo: 133 entradas no `git status --porcelain`, sendo 56
arquivos rastreados modificados e 77 não rastreados. A auditoria preservou
essas alterações.

## 3. Metodologia

- leitura integral dos contratos e componentes de composição;
- pesquisa estática de imports, IDs e tipos RSC com `rg`;
- análise AST de imports internos;
- inspeção dos fluxos de abertura e fechamento de projeto;
- simulação testável de uma segunda aplicação;
- execução dos testes arquiteturais e da suíte integral;
- `compileall` e `git diff --check`.

Foram analisados 183 arquivos Python produtivos. A análise AST encontrou 173
ocorrências de imports internos distribuídas em 33 arestas entre pacotes.

## 4. Mapa real de dependências

| Camada | Importa atualmente | Pode ser importada por | Avaliação |
| --- | --- | --- | --- |
| Contracts | `models.Project` no contrato legado | todas as camadas | Quase neutra; a dependência de `Application` para o modelo legado é bridge |
| Platform Core neutro | contracts, models, services e database | Host e Applications | Registry, runtime, contextos e factory são neutros |
| Platform Host | PySide6, UI, controllers, Presentation, services e sessão | composition root | Ainda conhece fluxos RSC |
| Composition Root | Host, registry e `RscApplication` | `app.py` | Dependência RSC legítima |
| Applications/RSC | contracts, SessionContext, database e domínio RSC | composition root e Presentation RSC | Direção principal correta; infraestrutura SQLite fica dentro da composição RSC |
| Document Engine | models, database, contracts e serviços de busca | Core, Host e Presentation | Reutilizável, embora ainda organizado sob `services` |
| Knowledge Engine | models, contracts e persistência de Evidence | Core, Host e RSC | Reutilizável como serviço compartilhado |
| Presentation | UI, models e diretamente `applications.rsc` | Host e UI | Não neutra; controllers funcionais são RSC |
| UI | PySide6, Presentation, services, models e contracts | Host | MainWindow contém views/actions RSC |
| Infrastructure | database, SQLite, filesystem, OCR | engines e RSC | Dependências concretas nas bordas esperadas |

Arestas internas observadas:

```text
Composition Root -> Host/Core -> Contracts
Composition Root -> RSC -> Contracts
Host -> UI + Presentation + Controllers + Services
Factory -> Registry + ProjectSession + Document/Knowledge services
RSC -> SessionContext + Contracts + RSC Infrastructure
Presentation RSC -> RSC + UI
Services -> Models + Database + Contracts
```

Não foi encontrado ciclo de import que impeça carregamento. Existe, contudo,
acoplamento bidirecional conceitual entre `core` e `applications`: RSC importa
`SessionContext`, enquanto a bridge `ProjectSession` importa
`RscProjectSession`. É uma bridge transitória conhecida, não uma propriedade
do núcleo definitivo.

## 5. Neutralidade por camada

### Contracts

Não há referências a RSC, UI ou Presentation. `Application`, legado, ainda
depende de `models.Project`; `ApplicationModule`, descriptor, lifecycle e
capabilities são neutros.

### Core

O núcleo interno é neutro, mas o pacote físico não é integralmente neutro:

| Ocorrência | Classificação | Motivo |
| --- | --- | --- |
| `core/application.py` importa `RscApplication` | D — legítima fora do núcleo | É o composition root produtivo |
| `core/project_session.py` importa `RscProjectSession` | B — bridge transitória | Mantém `rsc_session is application_session` |
| `core/project_controller.py` consulta `rsc_session` e monta controllers RSC | A — acoplamento do Host | Host ainda possui navegação e lifecycle visual RSC |
| `core/project_session_factory.py` passa `rsc_session=None` | B — bridge transitória | Mantém a assinatura histórica, sem reconhecer RSC |

Não existem `RSC_APPLICATION_ID`, `_create_rsc_session`, repositories RSC ou
regras RSC na factory.

### Host, Presentation e Dashboard

- **Core neutro:** sim para o núcleo contratual; não para todo o diretório
  físico devido às bridges e ao Host nele alojado.
- **Host neutro:** não. `ProjectController` e `MainWindow` conhecem views,
  actions e disponibilidade RSC.
- **Presentation neutra:** não como conjunto. Activities, Functional
  Assignments e Functional Exercises importam ou consomem elementos RSC.
- **Dashboard neutro:** parcialmente. Controller e HomeView são passivos e
  neutros, mas `DashboardService` e suas projections possuem resumo RSC.

Esses acoplamentos não contaminam a factory nem o registry, mas impedem afirmar
que o Platform Host já aceita toda contribuição de uma nova aplicação sem
alteração.

## 6. ProjectSessionFactory

A factory:

1. resolve a aplicação e sua visão modular;
2. compõe repositories e serviços compartilhados;
3. cria `ProjectSession`, que materializa os contextos;
4. chama `ApplicationModule.create_session(SessionContext)`;
5. publica o resultado pela bridge de `ProjectSession`.

Não importa Applications, RSC, UI ou Presentation. Não conhece IDs concretos,
repositories RSC, métodos legados específicos ou regras de domínio. A falha de
`create_session` é propagada e nenhuma sessão parcial é devolvida.

Pendência: não há protocolo de descarte para os recursos compartilhados em
falhas ou fechamento. Os recursos atuais não expõem handles persistentes de
fechamento, reduzindo o risco imediato.

## 7. ApplicationRegistry

O registry suporta:

- múltiplas Applications legadas;
- múltiplos `ApplicationModule`;
- objeto híbrido que satisfaça ambos os contratos;
- aliases e proteção do alias histórico `ProcDocOrganizer`;
- descriptors oficiais e transitórios;
- rejeição de IDs desconhecidos;
- validação de plataforma e schema;
- ordenação determinística por ID canônico;
- resolução sem criar sessões.

Os testes existentes cobrem colisões, aliases, compatibilidade, híbridos e
determinismo. O teste desta auditoria registrou simultaneamente RSC, Asset
Audit modular e uma aplicação legada.

Limitação no Host: `ProjectController` usa `registry.applications` para o
diálogo de novo projeto. Módulos puros não aparecem nessa coleção legada,
embora o registry e a factory os suportem.

## 8. PlatformSession

`PlatformSession` agrega corretamente:

- `ProjectContext`: snapshot imutável do projeto e metadados;
- `SessionContext`: engines, capacidades e serviços compartilhados;
- `ApplicationRuntime`: descriptor, módulo, estado e sessão concreta.

Os objetos de contexto são congelados e os mappings são somente leitura.
`ApplicationRuntime` é deliberadamente mutável para publicação da sessão e
evolução de lifecycle. As identidades dos serviços compartilhados coincidem
com as dependências históricas de `ProjectSession`.

Campos definitivos: os três agregados de `PlatformSession`, descriptor, módulo,
project context e session context. Campos ainda subutilizados: navigation,
capability provider e lifecycle state. Campos transitórios/duplicados:
dependências de `ProjectSession`, `application`, `rsc_session` e o acesso
paralelo à sessão modular.

Há risco de divergência porque `ProjectSession` e `PlatformSession` expõem
representações paralelas. A construção sincroniza os objetos, e
`bind_application_session` preserva a identidade RSC, mas não existe mecanismo
geral de verificação após mutações externas do runtime.

## 9. RSC modular

`RscApplication` possui descriptor oficial, implementa `prepare`,
`create_session`, `contributions`, `transition` e `dispose`, e continua
compatível com `Application`. `create_session` consome somente o
`SessionContext`, cria o mesmo `RscProjectSession` concreto e é chamado uma
única vez pela factory.

`application_session` e `rsc_session` apontam para a mesma instância. As
contribuições permanecem vazias. `prepare`, `transition` e `dispose` são hooks
formais sem efeito produtivo. `create_project_session` permanece como API
legada dentro da própria aplicação.

## 10. Bridges e fallbacks

| Bridge/fallback | Consumidor e razão | Risco de remoção | Destino |
| --- | --- | --- | --- |
| `ProjectSession` | Controllers e Presentation históricos | alto | remover somente após migração integral para `PlatformSession` |
| `rsc_session` | Host, Dashboard e presenters RSC | alto | fase de neutralização do Host/Presentation |
| Import de `RscProjectSession` no Core | sincroniza alias por tipo | médio | substituir quando consumidores usarem contrato de sessão |
| `Application` legado | projetos e aplicações históricas | alto | manter durante ciclo de compatibilidade 1.x |
| `registry.applications` | diálogo de novo projeto | alto | substituir por catálogo baseado em descriptors |
| Descriptor transitório | Applications legadas | médio | remover após fim do contrato legado |
| `ProcDocOrganizer` histórico | projetos sem metadata moderna | alto | manter enquanto esses projetos forem suportados |
| `create_project_session` | chamadas/testes RSC legados | médio | deprecar depois da estabilização modular |
| Campos duplicados de sessão | consumidores ainda não migrados | alto | convergir após Host modular |

Todas podem permanecer no Core 1.0 desde que documentadas como compatibilidade,
não como API desejada para novas aplicações.

## 11. Lifecycle e descarte

O lifecycle está **modelado, mas não conectado**. Os estados e transições
válidas são verificáveis, porém o fluxo produtivo:

- inicia o runtime em `REGISTERED`;
- não chama `prepare`;
- chama `create_session`;
- não move o estado para `SESSION_CREATED`;
- não chama `transition`;
- não chama `dispose` ao fechar projeto;
- apenas solta referências e limpa controllers/contribuições.

Não há ordem formal de descarte, idempotência produtiva ou fechamento da
`application_session`. Hoje o RSC não mantém recurso próprio aberto e seus
repositories abrem conexões por operação, de modo que o risco imediato de
recurso órfão é baixo. Isso não bloqueia a baseline Core 1.0, mas bloqueia
considerar o lifecycle completo e deve anteceder módulos que mantenham recursos
de longa duração.

## 12. Teste Asset Audit

`tests/test_core_1_0_architecture.py` define somente doubles de teste:

- `AssetAuditModule`, com descriptor e sessão próprios;
- contribuição fictícia;
- `LegacyAuditApplication`;
- registro conjunto com `RscApplication`.

A mesma `ProjectSessionFactory` resolveu Asset Audit, passou o
`SessionContext`, criou e publicou sua sessão e manteve `rsc_session=None`.
Nenhum arquivo produtivo, UI ou persistência real foi criado para Asset Audit.

A simulação prova a extensibilidade do registry e da factory. Não prova
integração completa no desktop, pois seleção, montagem de views e contribuições
de módulos puros ainda dependem da evolução do Host.

## 13. ADRs e documentação

| Decisão | Estado observado |
| --- | --- |
| ADR-003 Normalizer | implementada no RSC, embora o documento ainda diga Proposed |
| ADR-004 Taxonomia funcional | parcialmente implementada; resolução/taxonomia futura |
| ADR-005 Discovery de identidade | ainda não implementada integralmente |
| ADR-006 Identity Resolution | ainda não implementada |
| ADR-007 Presentation/Projections | implementada para Dashboard; neutralidade multiapp parcial |
| ADR-008 Activity | implementada |
| ADR-009 persistência de Activity | implementada |
| ADR-010–016, 019–022, 024–025, 027 Search/Evidence | implementadas no motor atual |
| ADR-028 fontes históricas | implementada |
| ADR-029 auditabilidade RSC | decisão vigente; implementação futura deliberada |
| ADR-030 versionamento normativo | ainda não implementada |
| ADR-031 associações/exclusão | parcialmente implementada |
| ADR-032 estado inicial de Activity | implementada |

`architecture-audit-v1.0.md` é histórico e descreve uma estrutura anterior ao
PF-02–PF-05B; não deve ser tratado como retrato atual. Não existe ADR específico
no diretório formalizando ApplicationModule, PlatformSession ou a bridge
multiaplicação, embora os contratos e testes expressem essas decisões.

## 14. Riscos

1. O Host usa APIs legadas do registry e não instala contribuições com a sessão
   modular.
2. Fechamento não chama `dispose`.
3. Runtime e alias legado podem divergir por mutação externa.
4. A bridge tipada cria dependência reversa `core -> applications.rsc`.
5. MainWindow e ProjectController precisam ser alterados para cada família de
   views RSC.
6. Capabilities e navigation estão contratadas, mas ainda não alimentam o
   fluxo produtivo modular.

## 15. Pendências

### Bloqueantes para Core 1.0

Nenhuma para aprovar a baseline contratual e de composição, considerando as
bridges como compatibilidade explicitamente exigida.

### Não bloqueantes para Core 1.0

- conectar lifecycle, transições e descarte;
- tornar o Host orientado a descriptors e módulos;
- instalar contribuições usando a sessão modular;
- retirar conhecimento RSC de MainWindow, ProjectController e Dashboard;
- migrar Presentation para fronteiras de Application;
- eliminar gradualmente `ProjectSession` e `rsc_session`;
- formalizar ADR da plataforma e da política de compatibilidade.

Esses itens são bloqueantes para declarar o **Platform Host** plenamente
extensível, não para congelar o núcleo Core 1.0.

## 16. Decisão final

**B. CORE 1.0 APROVADO COM PENDÊNCIAS NÃO BLOQUEANTES**

O registry, os contratos, os contextos, o runtime e a factory estão aptos a
receber uma segunda aplicação sem mudança estrutural. A simulação Asset Audit
comprova essa afirmação.

O PF-06 pode ser iniciado com segurança, desde que seu escopo ataque as
pendências do Host e do lifecycle e preserve as bridges até a migração de todos
os consumidores. Não se deve interpretar esta aprovação como neutralidade já
concluída da UI, Presentation ou do Platform Host.

## Evidências de validação

Comandos principais:

```text
python -m unittest tests.test_core_1_0_architecture ...
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q .
git diff --check
rg -n "applications.rsc|RscApplication|RscProjectSession|..."
rg -n "\.prepare\(|\.transition\(|\.dispose\(|create_session\("
```

Os resultados finais são registrados no relatório de execução entregue junto
com esta validação:

- testes arquiteturais focados: 78 aprovados;
- suíte integral: 932 aprovados em 18,129 s;
- `compileall`: aprovado;
- `git diff --check`: aprovado;
- referências RSC proibidas na factory: zero;
- chamadas produtivas a `create_session`: uma, na factory;
- chamadas produtivas a `dispose`: zero.

A saída controlada sobre um JSON corrompido durante a suíte pertence a um teste
de tolerância a erro do Document Service e não representa falha.

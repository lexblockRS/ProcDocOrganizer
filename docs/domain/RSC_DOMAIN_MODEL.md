# ProcDocOrganizer — Modelo de Domínio RSC

**Versão:** 1.0
**Release de consolidação:** 1.6
**Status:** referência oficial para os Workspaces da Fase II
**Natureza:** consolidação conceitual; não define schema, API ou interface

## 1. Objetivo

Este documento consolida o modelo de domínio já estabelecido para o
ProcDocOrganizer no contexto de Reconhecimento de Saberes e Competências
(RSC). Ele reúne o vocabulário, as entidades, os agregados, os objetos-valor,
as relações, as regras e os limites que devem orientar os Workspaces da Fase
II.

O documento não cria funcionalidades nem resolve questões ainda abertas. Uma
ideia só é tratada como consolidada quando possui apoio na documentação
existente, em decisão arquitetural aceita ou no modelo de domínio atual.
Menções exploratórias e ADRs propostos são identificados como tal.

Há três níveis de maturidade usados nesta consolidação:

- **consolidado:** decisão conceitual aceita ou comportamento estável;
- **implementado:** existe representação executável no repositório;
- **pendente:** conceito necessário, mas com identidade, ciclo ou regra ainda
  não definidos.

## 2. Fontes e precedência

Foram considerados:

- o modelo conceitual e o workflow RSC existentes;
- a visão de domínio e o blueprint de reconstrução funcional;
- ADRs de normalização, taxonomia, identidade, Activity, auditabilidade,
  versionamento normativo, associações e exclusão;
- decisões do motor documental, pesquisa e Evidence;
- o projeto funcional do Document Workspace;
- o domínio normativo em `applications/rsc/domain`;
- o pipeline funcional em `applications/rsc/models`;
- os modelos compartilhados de Project, Document e Evidence.

Em caso de tensão, esta consolidação aplica a seguinte precedência:

1. decisões aceitas mais recentes;
2. invariantes do domínio implementado e protegido por testes;
3. documentação conceitual oficial;
4. ADR proposto, identificado como proposta;
5. roadmap ou hipótese, mantidos como pendência.

Essa regra evita que uma intenção antiga substitua silenciosamente uma decisão
posterior. Ela também não declara o código como definição completa do negócio:
o código confirma invariantes implementadas, enquanto questões conceituais
podem continuar abertas.

## 3. Visão geral do domínio

O ProcDocOrganizer apoia a reconstrução, comprovação e organização da
trajetória profissional de uma pessoa para posterior interpretação segundo
uma normativa de RSC.

O trabalho não começa pelo cálculo de pontos. Ele começa por uma atividade
lembrada e por fontes documentais dispersas. A cadeia conceitual é:

```text
Pessoa de interesse
    ↓ orienta
Descoberta de documentos e evidências
    ↓
Evidence documental rastreável
    ↓
FunctionalAssignmentEvidence (AR)
    ↓ identificação e vínculo explícitos
FunctionalExercise
    ↓ relacionado à lembrança
Activity comprovada
    ↓ interpretação normativa versionada
RSC Criterion / Item Normativo
    ↓
Enquadramento e pontuação auditável
    ↓
Timeline e Reports/Dossiê derivados
```

As fronteiras fundamentais são:

- documentos são fontes, não atividades;
- Evidence é uma afirmação rastreável, não um fato automaticamente confirmado;
- Activity acompanha a hipótese lembrada até a comprovação;
- FunctionalExercise é o fato funcional reconstruído em contexto e período;
- critérios RSC interpretam fatos e não definem sua existência;
- pontuação é resultado posterior, reproduzível e revisável;
- Timeline e Reports apresentam dados derivados e não são fontes de verdade.

## 4. Contextos conceituais

### 4.1 Gestão do projeto

Mantém o projeto físico, seu ciclo de abertura, aplicação associada, sessão e
persistência. Esse contexto torna o trabalho interrompível e retomável.

### 4.2 Acervo documental

Mantém arquivos originais, registros documentais, disponibilidade,
processamento e pesquisa. Ele preserva a fonte sem interpretar por conta
própria a trajetória funcional.

### 4.3 Conhecimento documental

Mantém Evidence ligada a uma identidade documental, página, trecho, notas,
categoria e datas. Faz a ponte rastreável entre fonte e interpretação.

### 4.4 Reconstrução funcional

Transforma evidências documentais em afirmações estruturadas, resolve
identidade e natureza funcional, consolida exercícios e relaciona esses fatos
às atividades lembradas.

### 4.5 Interpretação normativa RSC

Aplica requisitos e critérios de uma versão normativa a fatos já
reconstruídos, produz validações, enquadramentos e pontuação.

### 4.6 Projeções

Timeline, dashboards e Reports/Dossiê organizam informações dos contextos
anteriores. Não possuem fatos próprios nem reescrevem as fontes.

## 5. Entidades e conceitos solicitados

### 5.1 Project

**Situação:** consolidado e implementado, com representações ainda duplicadas.

Projeto RSC é o contexto agregador de uma preparação documental para uma
avaliação determinada. Reúne pessoa requerente, instituição/contexto,
documentos, atividades, versão normativa, resultados e produtos de
conferência. Não é apenas uma pasta nem o processo administrativo formal.

O repositório contém:

- `models.Project`, que representa o projeto físico, formato, caminho,
  aplicação, banco e timestamps;
- `RscProcess`, declarado como raiz agregada do processo normativo;
- `applications.rsc.models.Project`, representação interna mínima e
  explicitamente denominada Aggregate Root.

Essas representações não devem ser tratadas como três conceitos de negócio.
A relação exata entre projeto físico, processo RSC e modelo mínimo permanece
pendente de consolidação da API interna.

Regras já decididas:

- o projeto delimita o acervo e a sessão;
- uma abertura cria novas instâncias de sessão;
- o trabalho pode ser interrompido e retomado;
- a versão normativa aplicável deve ser identificável;
- o estado geral não substitui estados das atividades;
- o projeto pode evoluir de novo/rascunho até revisão, submissão e
  arquivamento, mas os vocabulários existentes ainda precisam ser alinhados.

### 5.2 Document

**Situação:** consolidado e implementado.

Documento é o registro identificável de uma fonte original pertencente ao
projeto. Ele preserva arquivo, identidade de conteúdo, metadados, situação e
rastreabilidade. Não é uma atividade nem uma interpretação conclusiva.

O modelo compartilhado contém ID, SHA-256, nome original, caminho relativo,
nome armazenado, tipo, MIME, tamanho, páginas, datas e estados de acervo e
processamento. O domínio RSC também possui `RscDocument`, uma referência
documental neutra e imutável.

Decisões consolidadas:

- arquivo original e interpretações são separados;
- SHA-256 identifica conteúdo e suporta deduplicação, mas não substitui
  necessariamente o ID do registro;
- caminho absoluto não é identidade persistente;
- disponibilidade do arquivo, status do acervo e processamento são dimensões
  diferentes;
- processamento e índice são derivados;
- um documento pode originar várias evidências;
- remoção não destrói silenciosamente referências históricas;
- documentos indisponíveis continuam identificáveis para auditoria.

Metadados editoriais ampliados, categorias, tags e substituição de arquivo
permanecem decisões do épico documental.

### 5.3 Activity

**Situação:** consolidada e implementada no pipeline funcional.

Activity é a entidade que acompanha uma atividade profissional desde a
lembrança inicial até sua comprovação. Ela preserva a descrição fornecida pela
pessoa, o grau de investigação e referências tipadas aos elementos factuais
que a sustentam.

Seu ciclo aceito é:

```text
REMEMBERED
    → UNDER_INVESTIGATION
    → PARTIALLY_PROVEN
    → PROVEN
```

Regras:

- toda Activity nasce `REMEMBERED`;
- criação não significa investigação, comprovação ou enquadramento;
- transições não saltam etapas;
- comprovação parcial exige ao menos uma
  `FunctionalAssignmentEvidence`;
- comprovação exige ao menos uma evidência funcional e um
  `FunctionalExercise`;
- referências não se repetem;
- Activity não possui nem controla o ciclo de Evidence ou
  FunctionalExercise;
- classificação e enquadramento RSC ficam fora desse ciclo factual.

Existe também `RscActivity`, voltada à avaliação normativa, com critério,
quantidade, datas, evidências e status próprio. A correspondência entre
Activity comprovada e RscActivity normativa ainda não foi formalizada. Não se
deve fundi-las implicitamente.

### 5.4 Evidence

**Situação:** consolidada e implementada como Aggregate Root do contexto de
conhecimento documental, com níveis de Evidence intencionalmente distintos.

`Evidence` é uma afirmação documental rastreável. Possui identidade, referência
opaca ao documento, página opcional, título, trecho, notas, categoria, datas e
auditoria. Pode estar incompleta ou ser insuficiente isoladamente.

`FunctionalAssignmentEvidence` é uma interpretação funcional estruturada de
uma Evidence. Registra pessoa indicada, fonte, tipo de exercício, denominação,
papel, organização, unidade, referência administrativa, datas e estado do
pipeline:

```text
RAW → IDENTIFIED → LINKED
```

`NORMALIZED` permanece reconhecido apenas para reidratação compatível de
registros legados e pode avançar para `IDENTIFIED`; não integra o fluxo atual
de criação nem exige uma etapa automática.

`RscEvidence`, no domínio normativo, relaciona atividade e um ou mais
documentos e possui estado proposto, aceito, rejeitado ou em revisão. A ponte
exata entre Evidence compartilhada, FunctionalAssignmentEvidence e
RscEvidence ainda exige consolidação.

Regras:

- toda Evidence aponta para identidade documental opaca;
- página, trecho e texto original sustentam rastreabilidade;
- Evidence não modifica Document;
- Documents e Search produzem `EvidenceSourceCandidate`, não persistem
  Evidence diretamente;
- normalização preserva identidade, pessoa, fonte, datas e significado;
- uma evidência histórica não é apagada automaticamente quando a fonte fica
  indisponível;
- associações são explícitas e não transferem propriedade.

`Evidence` controla exclusivamente seu próprio ciclo de criação, edição e
remoção autorizada. Sua identidade é o UUID da Evidence; a identidade
documental é uma referência externa opaca e não transfere a propriedade do
`Document`. Alterações passam por casos de uso ou serviços de aplicação que
invocam o comportamento da entidade e persistem o resultado por
`EvidenceRepository`. Nem `Document`, `Activity`,
`FunctionalAssignmentEvidence`, `FunctionalExercise` nem `RscEvidence` podem
modificar uma Evidence diretamente.

A fronteira transacional do agregado termina na própria Evidence. Uma
transação pode validar a existência ou a disponibilidade de sua referência
documental, mas não modifica `Document`, `Activity`,
`FunctionalAssignmentEvidence`, `FunctionalExercise` ou `RscEvidence`.
Associações com outros agregados são coordenadas por casos de uso próprios e
não ampliam essa fronteira. A política de autorização e retenção para remoção
quando existirem referências permanece uma decisão separada.

### 5.5 RSC Criterion

**Situação:** consolidado e implementado como `RscCriterion`; conceitualmente
equivale ao Item Normativo.

RSC Criterion é um item de uma versão normativa aplicável. Contém identidade,
requisito, número, descrição, unidade de medida, ordem e regra de pontos comum
ou variantes explícitas.

Regras implementadas:

- o item e sua ordem são positivos e correspondentes;
- cada critério pertence a um dos requisitos oficiais;
- usa pontos comuns ou variantes, nunca ambos;
- quantidades e pontos usam `Decimal` positivo;
- IDs de variantes não se repetem;
- critérios podem ser ativos ou inativos;
- pontuação não comprova uma atividade;
- cálculo deve preservar quantidade, regra, limites, resultado e avisos.

Todo resultado normativo futuro deve identificar regulamento, versão,
vigência, critérios, parâmetros e momento do cálculo. Recalcular é operação
explícita e não substitui silenciosamente resultado histórico.

### 5.6 Category

**Situação:** conceito consolidado como classificação; entidade não
consolidada.

Category aparece:

- como atributo opcional de Evidence;
- como agrupamento de critério/item normativo;
- como organização proposta do acervo documental;
- como dimensão de filtros e limites de pontuação.

Não existe decisão que lhe atribua identidade, ciclo de vida ou propriedade
suficientes para tratá-la como entidade. No estado atual, Category deve ser
considerada valor classificatório ou referência a vocabulário controlado.

Permanecem abertos: escopo global/projeto/instituição, unicidade,
hierarquia, versionamento, cardinalidade e diferença entre categoria
documental, funcional e normativa.

### 5.7 Institution

**Situação:** conceito consolidado como contexto; entidade não consolidada.

Instituição contextualiza a pessoa, os documentos, a terminologia
administrativa, as unidades e a normativa. `RscProcess` mantém instituição
textual, e `FunctionalContext` preserva organização, unidade e referência.

A taxonomia funcional deve ser independente de instituição. Nomes
institucionais são preservados para rastreabilidade, mas não definem a
ontologia da atividade. Títulos iguais podem ter significados diferentes, e
títulos diferentes podem representar atividades funcionalmente equivalentes.

Não foram decididos identidade institucional canônica, hierarquia,
vigência, fusões, aliases ou repository. Portanto, Institution não é declarada
Aggregate Root nesta versão.

### 5.8 Person

**Situação:** sujeito central consolidado; entidade canônica ainda pendente.

Pessoa é o sujeito cuja trajetória se pretende reconstruir. Ela aparece como
requerente no processo e por `person_id` no pipeline funcional. A documentação
define `Identity Profile` como conjunto de pistas que orienta descoberta e
`Identity Resolution` como decisão auditável sobre equivalência entre
evidências.

O perfil não é a Pessoa e uma ocorrência nominal não confirma identidade.
Nome igual não prova identidade; ausência de identificador não é conflito;
homônimos e divergências devem permanecer explícitos. Decisões humanas e
critérios de identidade precisam de versão, autoria, justificativa e
proveniência.

Ainda não existe entidade Person canônica, política de criação, identificador
principal ou agregado de identidade. Criar essa entidade exige ADR próprio.

### 5.9 Report

**Situação:** produto/projeção consolidado; entidade não consolidada.

Reports e Dossiê são representações derivadas para conferência. Organizam
atividades, períodos, fontes, enquadramentos, pontuações e memórias de cálculo.
Não armazenam fatos próprios e não substituem o memorial profissional, que
permanece externo ao sistema.

Um relatório pode futuramente precisar de snapshot versionado para
reprodutibilidade, mas essa necessidade não foi decidida. Até lá, Report não
deve ser modelado como entidade ou Aggregate Root. O Reports Workspace consome
queries e DTOs públicos e não lê outros widgets.

## 6. Entidades consolidadas

### 6.1 FunctionalAssignmentEvidence

Afirmação estruturada sobre possível exercício funcional, derivada de
Evidence. É imutável, possui identidade UUID e avança explicitamente por
identificação e vínculo. É Aggregate Root: possui ciclo de vida, invariantes,
Repository e fronteira transacional próprios. A Evidence de origem é uma
referência obrigatória a outro agregado, não uma parte possuída.

### 6.2 FunctionalExercise

Fato profissional reconstruído de que uma pessoa exerceu uma atividade
funcional, em papel, contexto e período determinados. Seu estado é temporal:
ativo exige período aberto; encerrado exige data final.

Ele não representa o grau de comprovação da Activity nem o enquadramento RSC.
Pode ser sustentado por várias evidências funcionais e pode participar de mais
de uma Activity.

### 6.3 RscRequirement

Requisito oficial ao qual critérios pertencem. O domínio implementado usa seis
requisitos numerados e IDs canônicos correspondentes.

### 6.4 CriterionScoreVariant

Variante explícita de pontuação dentro de um critério, com identidade, rótulo,
pontos por unidade e qualificadores simples.

### 6.5 Enquadramento Normativo

Relação argumentada entre atividade suficientemente comprovada e Item
Normativo. Deve registrar justificativa, fontes, condições e ressalvas.
Embora consolidado conceitualmente, não existe ainda uma entidade canônica
implementada com esse nome.

### 6.6 Pontuação

Resultado calculado do enquadramento. `ActivityScore`, `RequirementScore` e
`RscScoreResult` são resultados imutáveis, não entidades com ciclo autônomo.

### 6.7 Evento Documental

Informação relevante identificada em um documento, como designação,
continuidade, substituição ou encerramento. É conceito do modelo original. No
pipeline atual, parte desse papel é exercida por Evidence e
FunctionalAssignmentEvidence.

A relação exata entre Evento Documental e essas estruturas permanece
pendente. “Evento Documental” não é sinônimo de evento de domínio e não deve
ser denominado “Ato Administrativo”.

## 7. Aggregate Roots

### 7.1 Agregados confirmados

#### Projeto/Processo RSC

`RscProcess` é explicitamente a raiz agregada normativa. Controla atividades
RSC incorporadas e referências documentais, rejeita duplicidades e atualiza
sua marca temporal. O projeto físico controla o ciclo da sessão e a
persistência do contêiner.

O limite definitivo entre essas duas responsabilidades permanece pendente,
mas consumidores não devem alterar coleções internas sem passar pelos casos de
uso ou métodos da raiz correspondente.

#### Activity

Activity possui identidade, invariantes, transições e relações próprias e é
persistida por repository dedicado. Controla somente sua descrição, estado e
associações. Não controla Evidence nem FunctionalExercise.

#### Evidence

`Evidence` é a raiz do agregado de conhecimento documental. Possui identidade
UUID, invariantes editoriais e temporais, referência documental opaca e ciclo
de vida independente. `EvidenceRepository` é sua porta de persistência e cada
operação de criação, consulta, atualização ou remoção autorizada atua sobre
uma Evidence por vez.

O agregado preserva como invariantes: identidade válida e estável; identidade
documental obrigatória; página positiva quando informada; título obrigatório
e limitado; textos opcionais normalizados; intervalo de datas válido;
timestamps válidos e não regressivos; e referência histórica preservada
quando a fonte fica indisponível. Disponibilidade física da fonte é verificada
pela aplicação através de uma porta e não altera o `Document`.

#### FunctionalAssignmentEvidence

`FunctionalAssignmentEvidence` é a raiz do agregado de interpretação
funcional. Sua identidade UUID representa uma interpretação funcional
individual e não apenas a chave de uma associação: a entidade contém dados
próprios, pode existir antes de qualquer `Activity` ou `FunctionalExercise` e
percorre, por ação explícita, o pipeline `RAW → IDENTIFIED → LINKED`.

Sua criação é coordenada pelo caso de uso de criação, que exige uma referência
válida à `Evidence` de origem. Atualizações, transições e remoção são
coordenadas pelo serviço de gerenciamento e persistidas por
`FunctionalAssignmentEvidenceRepository`. O Workspace atua somente como
cliente desses serviços.

A fronteira transacional termina na própria
`FunctionalAssignmentEvidence`. Nenhuma operação desse agregado modifica
`Evidence`, `Activity` ou `FunctionalExercise`; esses conceitos são
referenciados por identidade e mantêm ciclos de vida independentes. A
exclusão remove somente a interpretação funcional e não produz remoção em
cascata.

### 7.2 Agregados operacionais não formalizados

Document possui identidade e ciclo independente, repository e operações
próprias. Na prática funciona como unidade de consistência do contexto
documental. A documentação, porém, ainda não o declarou formalmente Aggregate
Root. Esta consolidação não antecipa essa decisão.

### 7.3 Não são Aggregate Roots

- Category, no estado atual;
- Institution, no estado atual;
- Person, até definição canônica;
- FunctionalPeriod, FunctionalRole e FunctionalContext;
- RSC Criterion isolado de seu catálogo normativo versionado;
- resultados de pontuação e validação;
- Timeline;
- Report/Dossiê.

## 8. Value Objects

### 8.1 Identificadores

- UUID normalizado de processo, documento, atividade e evidência;
- `FunctionalAssignmentEvidenceId`;
- `FunctionalExerciseId`;
- `SourceEvidenceReference`;
- IDs canônicos de requisito e critério;
- identidade documental opaca;
- identidade de conteúdo SHA-256.

Identidade documental opaca evita acoplar Evidence ao algoritmo atual de hash.
UUIDs e referências históricas não são reescritos quando um destino fica
indisponível.

### 8.2 Valores temporais

- `FunctionalPeriod`, intervalo inclusivo aberto ou fechado;
- data do documento;
- página documental;
- datas alegadas, extraídas e comprovadas;
- timestamps com timezone no domínio normativo;
- vigência e versão normativa, ainda sem Value Object implementado.

Datas alegadas, documentais, inferidas e comprovadas não são intercambiáveis.
Período aberto não autoriza inventar encerramento.

### 8.3 Valores funcionais

- `FunctionalExerciseType`;
- `FunctionalRole`;
- `FunctionalContext`;
- unidade de medição;
- status tipados;
- quantidade e pontos em `Decimal`;
- categoria enquanto valor classificatório;
- metadados simples e imutáveis.

### 8.4 Resultados imutáveis

- `ActivityScore`;
- `RequirementScore`;
- `RscScoreResult`;
- `ValidationIssue`;
- `RscValidationResult`.

São produtos determinísticos de serviços de domínio e não fontes autoritativas
independentes.

## 9. Relacionamentos

### 9.1 Visão estrutural

```text
Project / RscProcess
    ├── identifica Pessoa requerente
    ├── contextualiza Instituição
    ├── referencia 0..* Document
    ├── contém/referencia 0..* Activity
    └── usa 1 versão normativa

Document
    └── origina 0..* Evidence

Evidence
    └── origina 0..* FunctionalAssignmentEvidence

FunctionalAssignmentEvidence (AR)
    ├── refere 1 Pessoa indicada
    ├── preserva 1 Evidence de origem
    └── sustenta 0..* FunctionalExercise

FunctionalExercise
    ├── pertence a 1 Pessoa
    ├── possui 1 tipo, papel, contexto e período
    └── relaciona 0..* FunctionalAssignmentEvidence

Activity
    ├── relaciona 0..* FunctionalAssignmentEvidence
    └── relaciona 0..* FunctionalExercise

Activity comprovada
    └── recebe 0..* Enquadramento Normativo

Enquadramento Normativo
    ├── aponta para 1 RSC Criterion
    ├── preserva justificativa e fontes
    └── produz Pontuação

Timeline e Reports
    └── projetam o conjunto sem possuir os fatos
```

### 9.2 Cardinalidades e propriedade

- um projeto possui ou referencia muitos documentos e atividades;
- um documento pode originar muitas Evidence;
- uma Evidence possui uma fonte documental;
- uma FunctionalAssignmentEvidence preserva uma Evidence de origem;
- Activity pode existir sem relações enquanto lembrada;
- Activity relaciona muitas evidências e exercícios;
- uma evidência ou exercício pode participar de várias atividades;
- um exercício pode ter muitas evidências de atribuição;
- associações não transferem propriedade;
- exclusão do proprietário remove apenas suas associações;
- destinos relacionados não são removidos em cascata;
- referências históricas textuais podem permanecer órfãs deliberadamente.

## 10. Regras de negócio consolidadas

### 10.1 Rastreabilidade e integridade

1. Fontes originais não são modificadas por interpretação.
2. Toda afirmação relevante deve retornar a documento e, quando possível,
   página e trecho.
3. Ausência posterior da fonte não apaga a relação histórica.
4. Dados derivados não substituem metadados confirmados silenciosamente.
5. Exclusões amplas exigem política explícita de autorização, impacto,
   retenção e comunicação.

### 10.2 Reconstrução factual

1. Atividade lembrada é hipótese, não fato comprovado.
2. Evidence é afirmação, não confirmação automática.
3. Normalização não altera significado, pessoa, fonte ou datas.
4. Identidade, natureza funcional e continuidade são decisões separadas.
5. Nome igual não comprova identidade.
6. Semelhança textual não comprova equivalência funcional.
7. Mudanças institucionais não reescrevem fatos históricos.
8. Um novo documento não inicia necessariamente novo período.
9. Alteração de outras pessoas não encerra automaticamente o exercício da
   pessoa de interesse.
10. Incertezas, conflitos, lacunas e sobreposições permanecem visíveis.

### 10.3 Activity e FunctionalExercise

1. Activity nasce lembrada.
2. Transições de Activity são sequenciais.
3. Comprovação parcial exige evidência funcional.
4. Comprovação exige evidência e exercício.
5. FunctionalExercise ativo exige período aberto.
6. FunctionalExercise encerrado exige período fechado.
7. Data final não antecede data inicial.
8. Relações tipadas não contêm duplicidade.

### 10.4 Interpretação normativa

1. Norma interpreta fatos já reconstruídos.
2. Critério não define a existência da atividade.
3. Enquadramento é argumentado e revisável.
4. Quantidade e pontos devem preservar precisão decimal.
5. Pontuação ocorre depois de comprovação e enquadramento.
6. Resultado deve possuir memória de cálculo.
7. Limites de item/categoria e acumulação devem ser explícitos.
8. Pontuação calculada não é decisão final da banca.
9. Resultado normativo identifica versão, vigência, parâmetros e instante.
10. Recálculo não substitui silenciosamente histórico anterior.

### 10.5 Automação e revisão humana

1. IA e heurísticas são assistivas.
2. Sugestão não é evidência nem decisão.
3. Resultado relevante deve ser explicável e reproduzível.
4. Confirmação humana registra responsável, momento, justificativa,
   critérios e proveniência.
5. Revisão produz nova decisão rastreável e preserva histórico.

## 11. Eventos de domínio

### 11.1 Distinção necessária

Nenhum catálogo técnico de eventos foi implementado. Os nomes abaixo
consolidam fatos conceituais já descritos; não prescrevem classes, barramento
ou persistência.

`Evento Documental` é informação extraída de uma fonte. Um evento de domínio é
o registro de que uma mudança de negócio já ocorreu. Os dois conceitos não são
sinônimos.

### 11.2 Fatos documentais

| Evento conceitual | Significado consolidado |
|---|---|
| `DocumentImported` | Arquivo e registro foram incorporados ao acervo. |
| `DocumentUpdated` | Metadados documentais persistidos foram alterados. |
| `DocumentRemoved` | Remoção coordenada autorizada foi concluída. |
| `DocumentBecameUnavailable` | O registro existe, mas a fonte não pode ser resolvida. |
| `DocumentProcessingChanged` | O estado ou resultado derivado de processamento mudou. |

`DocumentImported` e remoção coordenada possuem comportamento implementado.
Atualização editorial e indisponibilidade como eventos publicáveis ainda
dependem de contrato.

### 11.3 Fatos de Evidence

| Evento conceitual | Responsável | Significado consolidado |
|---|---|---|
| `EvidenceCreated` | Evidence | Uma afirmação rastreável foi registrada. |
| `EvidenceUpdated` | Evidence | Uma nova versão editorial foi persistida. |
| `EvidenceLinked` | Associação coordenada pela aplicação | Uma associação explícita foi estabelecida sem transferir propriedade. |
| `EvidenceNormalized` | FunctionalAssignmentEvidence | A interpretação avançou de RAW para NORMALIZED sem mudar significado. |
| `EvidenceIdentityResolved` | FunctionalAssignmentEvidence | Uma decisão auditável de identidade foi produzida. |

Associação e transições existem no domínio; o mecanismo de publicação desses
fatos não foi definido.

### 11.4 Fatos de Activity

| Evento conceitual | Significado consolidado |
|---|---|
| `ActivityRemembered` | Uma hipótese profissional foi criada em REMEMBERED. |
| `ActivityInvestigationStarted` | A busca e análise documental começaram. |
| `ActivityPartiallyProven` | Há sustento documental ainda não consolidado por completo. |
| `ActivityProven` | Evidências sustentam ao menos um exercício reconstruído. |
| `FunctionalExerciseEnded` | Um exercício antes ativo recebeu encerramento válido. |

O exemplo `ActivityValidated` não possui significado único consolidado:
“validada” pode significar comprovação factual, validação normativa ou revisão
humana. O vocabulário deve usar o fato específico.

### 11.5 Fatos normativos

| Evento conceitual | Situação |
|---|---|
| `NormativeClassificationProposed` | Compatível com enquadramento proposto, mas ainda sem entidade canônica. |
| `NormativeClassificationConfirmed` | Exige governança de autoria e versão ainda pendente. |
| `ScoreCalculated` | Resultado determinístico foi produzido para versão e parâmetros identificados. |
| `ScoreRecalculated` | Novo resultado foi produzido sem apagar o anterior. |

`CriterionSatisfied` não está consolidado como evento. Satisfação de critério
pode ser conclusão de validação ou parte do enquadramento e precisa de
definição antes de entrar no vocabulário oficial.

## 12. Timeline e Reports

### 12.1 Timeline

CareerTimeline/Linha do Tempo é projeção reconstruível dos
FunctionalExercises de uma pessoa. Deve evidenciar períodos, continuidade,
interrupções, lacunas, sobreposições e incertezas. Documentos e evidências
aparecem como sustento.

Não é:

- lista de documentos por data;
- proprietária de períodos ou atividades;
- mecanismo de correção de identidade;
- fonte normativa.

### 12.2 Reports e Dossiê

Reports organiza visões de conferência e o Dossiê reúne atividades, períodos,
documentos, enquadramentos e pontuações. Deve preservar memória de cálculo e
rastreabilidade até as fontes.

Não é:

- repositório de fatos próprios;
- substituto do memorial profissional;
- mecanismo de alteração de atividades ou pontuações;
- dependente de widgets de outros Workspaces.

## 13. Limites entre camadas

### 13.1 Domínio

Pertencem ao domínio:

- entidades, Value Objects e invariantes;
- transições válidas de Activity, Evidence funcional e exercícios;
- regras de identidade, continuidade, classificação e enquadramento quando
  formalizadas;
- critérios, requisitos, unidades e precisão;
- cálculo e validação determinísticos;
- relações e políticas conceituais de rastreabilidade;
- fatos/eventos conceituais concluídos.

O domínio não conhece Qt, MainWindow, SQLite, ZIP, caminhos de diálogo,
notificações ou detalhes de serializer.

### 13.2 Aplicação

Pertencem à aplicação:

- casos de uso, comandos, queries e DTOs;
- coordenação de repositories e serviços de domínio;
- autorização de fluxos e sequência operacional;
- transações e compensações no nível do caso de uso;
- conversão entre fronteiras públicas e domínio;
- decisão de publicar notificações após sucesso;
- seleção explícita da versão normativa aplicável.

A aplicação não implementa regra visual nem persiste diretamente por detalhes
de banco.

### 13.3 Infraestrutura

Pertencem à infraestrutura:

- arquivos, SQLite, FTS, ZIP `.pdop` e diretórios;
- repositories concretos;
- serializers e migrations;
- parser PDF, OCR, indexação e hash;
- relógio, UUID e integrações externas quando injetados;
- disponibilidade física e atomicidade técnica.

A infraestrutura não decide se uma atividade está comprovada, qual identidade
é correta ou qual critério deve ser usado.

### 13.4 Interface

Pertencem à interface:

- Views, layout, formulários e acessibilidade;
- Stores e snapshots de apresentação;
- seleção, perspectiva e workspace ativos;
- encaminhamento de comandos;
- apresentação de progresso, erros, incertezas e notificações;
- projeções visuais de Timeline e Reports.

A interface não altera entidades diretamente, não acessa repositories e não
transforma seleção visual em decisão de domínio.

## 14. Persistência, identidade e auditabilidade

### 14.1 Persistência não define o domínio

Tabelas associativas, chaves estrangeiras e JSONs implementam relações, mas
não substituem suas regras. Reidratação deve passar pelos construtores
públicos e revalidar invariantes.

### 14.2 Referências fortes e históricas

Associações internas fortes protegem destinos relacionados. Na fronteira
documental, referências textuais históricas podem sobreviver à ausência do
destino. A interface mostra identidade, tipo e indisponibilidade e desabilita
navegação não resolvível.

### 14.3 Governança

Antes de pontuação plenamente auditável, é necessário consolidar:

- `created_at` e `updated_at`;
- autoria e autoridade;
- justificativa e origem da decisão;
- histórico de versões;
- regulamento e versão;
- efeito de revisão e recálculo.

Essa governança foi deliberadamente adiada; a ausência atual não autoriza
resultados normativos sem proveniência.

## 15. Compatibilidade e conceitos sobrepostos

### 15.1 Project versus RscProcess

Projeto físico, Project mínimo e RscProcess não devem divergir em identidade
ou ciclo sem bridge explícita. A escolha de uma raiz pública definitiva
permanece pendente.

### 15.2 Activity versus RscActivity

Activity factual e RscActivity normativa possuem responsabilidades
diferentes. A primeira acompanha lembrança e comprovação; a segunda registra
quantidade e critério para avaliação. A conversão deve ser caso de uso
explícito e preservar proveniência.

### 15.3 Evidence em três níveis

- Evidence compartilhada: afirmação documental;
- FunctionalAssignmentEvidence: interpretação funcional estruturada;
- RscEvidence: relação normativa entre atividade e documentos.

Esses níveis não podem ser fundidos apenas por semelhança nominal.

### 15.4 Evento Documental versus FunctionalAssignmentEvidence

O modelo original usa Evento Documental como unidade interpretada. O pipeline
novo usa Evidence e FunctionalAssignmentEvidence. É necessário decidir se
Evento Documental será termo de negócio, abstração superior ou conceito
substituído.

## 16. Decisões ainda não consolidadas

### 16.1 Projeto e agregados

1. Qual representação é a API canônica de Project RSC?
2. RscProcess e projeto físico compartilham identidade?
3. Qual catálogo normativo pertence ao agregado e como é versionado?
4. Document será formalmente Aggregate Root?
5. Quais transições de estado do projeto são oficiais?

### 16.2 Pessoa e instituição

6. Qual é a entidade Person canônica e seu identificador?
7. Como Identity Profile se relaciona à Person confirmada?
8. Quais estados de resolução de identidade serão implementados?
9. Quem pode confirmar identidade e revisar uma decisão?
10. Institution terá identidade, hierarquia, aliases e vigência?
11. Como múltiplos vínculos institucionais são representados?

### 16.3 Activity e reconstrução

12. Como Activity comprovada se converte em RscActivity normativa?
13. Functional Activity Taxonomy terá quais itens, versões e governança?
14. Como funciona o `FunctionalActivityResolver`?
15. Como continuidade, interrupção e sobreposição são resolvidas?
16. Um exercício pode ter períodos descontínuos ou deve haver vários
    FunctionalExercises?
17. Qual é o papel definitivo de Evento Documental?
18. Como revisão de identidade repercute em exercícios já reconstruídos?

### 16.4 Document e Evidence

19. Documento sem arquivo é permitido?
20. ID de registro ou SHA-256 é a identidade pública entre contextos?
21. O mesmo conteúdo pode originar vários registros?
22. Como substituir ou revincular arquivo sem perder histórico?
23. Qual política de remoção vale com Evidence relacionada?
24. Como Evidence compartilhada se relaciona formalmente a RscEvidence?
25. Quais metadados e categorias pertencem ao Documento?

### 16.5 Category

26. Existem categorias distintas para documento, atividade e norma?
27. Category é Value Object, item de catálogo ou entidade versionada?
28. Qual é seu escopo, cardinalidade, hierarquia e normalização?
29. Limites de pontuação por categoria pertencem a qual estrutura normativa?

### 16.6 Normativa e pontuação

30. Qual entidade representa Regulamento/NormativeVersion?
31. Como vigência, carreira e instituição selecionam regras?
32. Qual entidade representa Enquadramento Normativo?
33. Como limites, acúmulo e dupla contagem são formalizados?
34. Qual política de revisão, autoria e histórico torna resultados auditáveis?
35. Quando um critério é “satisfeito” e esse resultado é evento ou validação?

### 16.7 Timeline e Reports

36. Quais eventos e incertezas entram na Timeline?
37. Como a Timeline trata períodos alegados e não comprovados?
38. Report é sempre projeção ao vivo ou pode ser snapshot versionado?
39. Qual é a estrutura oficial do Dossiê?
40. Quais formatos e garantias de reprodutibilidade são exigidos?

## 17. Decisões explicitamente não tomadas

Esta versão não:

- cria entidade Category, Institution, Person ou Report;
- escolhe um único modelo Project;
- une Activity e RscActivity;
- une os três níveis de Evidence;
- define algoritmo de identidade, atividade ou continuidade;
- define catálogo de taxonomia funcional;
- define entidade de regulamento ou enquadramento;
- declara `CriterionSatisfied` como evento;
- transforma Timeline em agregado;
- transforma Reports em persistência;
- modifica regra, API, serializer, schema ou interface.

## 18. Referência para os Workspaces da Fase II

### Document Workspace

Manipula acervo, metadados e navegação documental. Não comprova Activity nem
persiste Evidence diretamente.

### Evidence Workspace

Manipula afirmações rastreáveis e candidatos documentais. Não resolve
automaticamente identidade, atividade, continuidade ou enquadramento.

### Activity Workspace

Acompanha lembrança, investigação e comprovação. Não possui o ciclo das
evidências/exercícios relacionados nem aplica pontuação.

### Timeline Workspace

Projeta FunctionalExercises e períodos. Não cria fatos para preencher lacunas.

### RSC/Criteria Workspace

Interpreta atividades comprovadas usando normativa versionada. Não reescreve a
trajetória factual.

### Reports Workspace

Consulta projeções públicas para conferência e dossiê. Não lê widgets, não
altera fontes e não escreve o memorial.

## 19. Glossário consolidado

- **Activity:** hipótese profissional que evolui até comprovação.
- **Category:** classificação cujo modelo definitivo está pendente.
- **Document:** registro e fonte original rastreável.
- **Enquadramento Normativo:** relação argumentada entre fato e critério.
- **Evidence:** afirmação documental rastreável.
- **Evento Documental:** informação relevante identificada em uma fonte.
- **Functional Activity:** categoria canônica da natureza de uma atuação.
- **FunctionalAssignmentEvidence:** interpretação funcional estruturada.
- **FunctionalExercise:** exercício concreto por pessoa, contexto e período.
- **Institution:** contexto histórico e administrativo, ainda sem entidade.
- **Item Normativo/RSC Criterion:** regra da normativa aplicável.
- **Person:** sujeito da trajetória, ainda sem entidade canônica.
- **Project RSC:** contexto agregador da preparação para avaliação.
- **Report/Dossiê:** produto derivado de conferência.
- **Timeline:** projeção cronológica da trajetória reconstruída.

# Document Workspace — Projeto funcional

**Produto:** ProcDocOrganizer
**Release:** 1.6
**Épico:** Document Workspace
**Contrato:** Functional Design
**Status:** referência funcional para implementações posteriores
**Natureza:** especificação conceitual; não define API nem autoriza mudança arquitetônica

## 1. Finalidade deste documento

Este documento define o comportamento funcional esperado do Document
Workspace. Ele é a referência para decompor, implementar e validar as etapas
posteriores do épico, sem substituir os contratos arquitetônicos da camada de
apresentação nem antecipar decisões de domínio ainda abertas.

O desenho parte da arquitetura e da capacidade já existentes. Atualmente, o
ProcDocOrganizer possui catálogo documental por projeto, importação com
detecção de duplicidade por SHA-256, remoção coordenada, processamento de PDF,
pesquisa textual, leitura de metadados e páginas processadas, visualização de
documentos e criação de candidatos de evidência. O desenho funcional amplia a
experiência de organização e edição sem declarar que todas essas capacidades
já estão implementadas.

Os termos normativos são:

- **deve**: requisito necessário para a implementação funcional;
- **pode**: comportamento permitido ou opcional;
- **futuro**: intenção que depende de contrato posterior;
- **baseline atual**: comportamento observado no repositório durante esta
  auditoria.

## 2. Objetivo do Workspace

O Document Workspace é o espaço central para incorporar, localizar,
organizar, compreender e relacionar os documentos pertencentes ao projeto
aberto.

Ele deve permitir que o usuário:

1. forme um acervo documental confiável dentro do projeto;
2. reconheça rapidamente o conteúdo e a situação de cada documento;
3. organize o acervo por metadados, categorias e tags;
4. encontre documentos por propriedades ou conteúdo;
5. visualize o arquivo e, quando disponível, seu texto processado;
6. mantenha metadados descritivos sem alterar o arquivo original;
7. use um documento ou uma página como origem de uma evidência;
8. navegue para contextos relacionados sem perder a identidade documental.

O sucesso funcional não é medido apenas pela quantidade de arquivos
importados. O Workspace deve reduzir o esforço para responder: “qual é este
documento?”, “onde ele está?”, “qual é seu estado?”, “com que evidências ele
se relaciona?” e “como posso reutilizá-lo em outra perspectiva?”.

## 3. Responsabilidades

### 3.1 Responsabilidades funcionais

O Document Workspace deve:

- representar o catálogo documental do projeto ativo;
- oferecer entrada para criação de um registro e importação de arquivo;
- apresentar estados vazio, carregando, pronto e erro de forma inequívoca;
- permitir seleção única de documento e, quando aplicável, de página;
- apresentar propriedades, disponibilidade e situação de processamento;
- permitir edição controlada dos metadados autorizados;
- oferecer pesquisa e filtros combináveis;
- permitir abertura e pré-visualização do conteúdo disponível;
- iniciar a associação entre documento e evidência;
- informar o resultado de operações por meio do mecanismo global de
  notificações;
- preservar seleção e contexto quando uma atualização do catálogo não
  remover o item selecionado;
- solicitar confirmação antes de operações destrutivas;
- manter acessibilidade básica, navegação por teclado e mensagens úteis.

### 3.2 Responsabilidades arquitetônicas preservadas

O Workspace é uma perspectiva visual, não uma nova fonte autoritativa de
estado. A integração prevista mantém:

- `ProjectState` e `ApplicationStateStore` como fontes do contexto do projeto;
- `PerspectiveStore` como catálogo e proprietário da perspectiva ativa;
- `NavigationController` como caminho exclusivo para troca de perspectiva;
- `WorkspaceStore` como estado lógico do espaço central;
- `WorkspaceHost` como hospedeiro da View ativa;
- `SelectionStore` como proprietário da seleção global;
- `ProjectController` e controllers específicos como coordenadores;
- serviços e repositories como fronteira das operações e da persistência;
- `NotificationCenter` como canal de mensagens transitórias.

O fluxo arquitetônico de entrada permanece:

```text
Comando do usuário
        ↓
MainWindow encaminha ação
        ↓
Controller coordena o caso
        ↓
Serviço/repository executa ou consulta
        ↓
Stores publicam estado de apresentação
        ↓
Workspace reflete snapshots e resultados
        ↓
NotificationCenter comunica o resultado
```

## 4. Limites do Workspace

### 4.1 Está dentro do escopo

- catálogo e organização de documentos do projeto;
- metadados descritivos do documento;
- vínculo lógico com categorias e tags;
- pesquisa e filtros documentais;
- visualização ou encaminhamento para visualização;
- situação do arquivo e do processamento;
- navegação para evidências relacionadas;
- criação de evidência a partir do documento, página ou trecho selecionado;
- ações em lote explicitamente contratadas em etapas futuras.

### 4.2 Está fora do escopo

- editar o conteúdo binário do arquivo;
- funcionar como editor de PDF, DOCX ou imagem;
- definir critérios de pontuação ou validação RSC;
- interpretar automaticamente o mérito de um documento;
- produzir relatórios finais;
- possuir a linha do tempo do projeto;
- substituir o Evidence, Timeline ou Reports Workspace;
- executar OCR, parsing ou indexação dentro da View;
- acessar diretamente banco de dados ou sistema de arquivos;
- possuir o estado global do projeto, navegação ou seleção;
- apagar silenciosamente evidências relacionadas;
- sincronização em nuvem, colaboração multiusuário ou controle de versão;
- incorporar IA sem contrato funcional e técnico próprio.

### 4.3 Fronteira entre metadado e arquivo

O registro documental e o arquivo físico são conceitos relacionados, mas
distintos. Alterar nome de exibição, categoria, data, observações ou tags não
deve modificar bytes, hash ou nome físico armazenado. Substituir o arquivo é
uma operação diferente de editar metadados e exige contrato próprio, pois pode
invalidar processamento, pesquisa e vínculos.

## 5. Auditoria da baseline e pontos de integração

### 5.1 Projeto e sessão

Um `Project` identifica nome, caminho, aplicação, versão de formato e banco
local. A `ProjectSession` agrega repositories e serviços vinculados àquele
projeto. Ao abrir ou criar um projeto, o ciclo de vida instala a sessão,
carrega o catálogo documental e ativa a perspectiva inicial. Ao fechar, os
serviços são desligados e o workspace é limpo.

Consequência funcional: nenhuma operação documental deve ficar disponível sem
projeto aberto, e nenhum item de um projeto anterior pode permanecer visível
depois da troca de sessão.

### 5.2 Perspectiva, navegação e workspace

A perspectiva `documents` já é registrada no `PerspectiveStore` com
`requires_project=True`. Menu e seletor de toolbar derivam desse catálogo. A
navegação deve continuar por `NavigationController`, que ativa a perspectiva,
monta o `WorkspaceStore` e limpa a seleção global conforme o contrato atual.
O `WorkspaceHost` apresenta a View criada pela definição da perspectiva.

Consequência funcional: Evidence, Timeline, Reports ou Search não devem abrir
a View documental diretamente. Devem emitir uma solicitação neutra contendo a
identidade do documento e, opcionalmente, a página.

### 5.3 Seleção

O `SelectionStore` já reconhece `SelectionKind.DOCUMENT`. A evolução deve
publicar uma `SelectionContext` documental imutável, contendo apenas identidade
e metadados simples necessários à apresentação. Entidades, widgets, sessions
e repositories não devem ser armazenados no Store.

### 5.4 Controller e serviços documentais

O `DocumentsController` atual carrega o catálogo, conserva a seleção quando
possível, resolve navegação por `DocumentNavigationRequest`, seleciona
documentos e páginas, solicita remoção e cria `EvidenceSourceCandidate`.
O `DocumentService` atual é somente leitura e compõe catálogo, detalhes e
páginas a partir do registro documental e do resultado de processamento.

Importação e remoção pertencem ao `DocumentImportService`. Persistência do
catálogo pertence ao `DocumentRepository`. Processamento, OCR e indexação têm
serviços próprios. A futura edição de metadados deve respeitar a mesma
separação, em vez de ser incorporada à View.

### 5.5 MainWindow

A MainWindow inicia ações e hospeda componentes, mas não deve manipular
arquivos, repositories, snapshots ou regras documentais. Habilitação deve ser
derivada do estado da aplicação e da perspectiva. Mensagens novas devem usar
`NotificationCenter`.

## 6. Objeto conceitual Documento

Documento é a unidade identificável do acervo de um projeto. Ele representa
um registro persistente e sua relação com um arquivo, não apenas um caminho no
sistema operacional.

### 6.1 Atributos conceituais

| Atributo | Significado e justificativa |
|---|---|
| Identificador | Identidade estável do registro, independente de nome e caminho. Permite referências internas seguras e futuras alterações de metadados. |
| Identidade de conteúdo | Impressão digital, atualmente SHA-256, usada para integridade, deduplicação e correlação com processamento e pesquisa. Não substitui o identificador do registro. |
| Nome de exibição | Nome compreensível apresentado ao usuário. Pode inicialmente refletir o arquivo original, mas deve poder evoluir sem renomear o arquivo físico. |
| Nome original | Preserva a denominação do arquivo na origem para auditoria e reconhecimento. |
| Tipo documental | Natureza administrativa ou semântica, como portaria, resolução, ofício ou certificado. Orienta filtros, apresentação e integrações. |
| Categoria | Agrupamento organizacional definido para o acervo. Diferencia a natureza documental de uma estrutura de organização configurável. |
| Data do documento | Data atribuída ao conteúdo ou ato representado. É necessária para ordenação cronológica e Timeline; não se confunde com importação. |
| Arquivo físico | Referência controlada ao arquivo armazenado no projeto, incluindo caminho relativo, nome armazenado, extensão, MIME e tamanho. Permite verificar disponibilidade sem expor caminhos absolutos como identidade. |
| Observações | Texto editorial do usuário para contexto que não pertence ao conteúdo original. |
| Tags | Vocabulário flexível e possivelmente múltiplo para recuperação transversal. Complementa, mas não substitui, a categoria. |
| Evidências relacionadas | Relações consultáveis com evidências que usam ou citam o documento. Permitem rastreabilidade e navegação; não implicam propriedade das evidências. |
| Status do acervo | Situação do registro, por exemplo ativo, indisponível ou futuramente arquivado. Deve ser separado da situação de processamento. |
| Status de processamento | Estado técnico do parsing/OCR/indexação: não processado, pendente, processando, processado, falho, cancelado ou dependente de OCR. Explica quais operações de conteúdo estão disponíveis. |
| Disponibilidade | Indica se o arquivo referenciado está acessível, ausente ou em condição desconhecida. Evita confundir registro existente com arquivo disponível. |
| Quantidade de páginas | Resumo para navegação e conferência, obtido do processamento quando disponível. |
| Data de importação | Registra quando o item ingressou no projeto e apoia auditoria operacional. |
| Data de criação do registro | Permite distinguir criação lógica de outros marcos quando os fluxos evoluírem. |
| Data de atualização | Identifica a última alteração de metadados do registro. |
| Resultado de processamento | Referência lógica a texto, páginas e diagnósticos derivados. É reconstruível e não deve ser tratado como conteúdo editorial do documento. |

### 6.2 Invariantes conceituais

- o identificador do registro não muda quando metadados são editados;
- a identidade de conteúdo só muda se o arquivo for substituído;
- caminhos absolutos não são identidade persistente;
- categoria e tipo documental são conceitos diferentes;
- tags não possuem ordem semântica;
- data do documento, data de importação e data de atualização são distintas;
- status do acervo, disponibilidade e processamento são dimensões distintas;
- relações com evidências sobrevivem à indisponibilidade da fonte quando a
  política de preservação assim determinar;
- remoção deve explicitar impacto sobre arquivo, processamento, índice e
  relações;
- dados derivados não devem sobrescrever silenciosamente metadados editoriais.

### 6.3 Vocabulários a definir

O tipo documental já possui uma enumeração inicial. Categoria, tags e status
editorial ainda exigem decisão. A implementação não deve cristalizar listas
sem definir:

- se categorias são globais, por aplicação ou por projeto;
- se a categoria é única ou múltipla;
- se categorias admitem hierarquia;
- se tags preservam caixa e acentuação ou usam chave normalizada;
- quais estados editoriais são necessários além de “importado”;
- como sugestões extraídas do processamento interagem com valores confirmados
  pelo usuário.

## 7. Experiência do usuário

### 7.1 Entrada e estado inicial

Sem projeto, a perspectiva permanece indisponível. Com projeto aberto, o
usuário pode acessá-la pelo menu `Exibir → Perspectivas`, pelo seletor da
toolbar ou por navegação contextual de outro workspace.

Ao entrar:

- durante a consulta, vê um estado de carregamento;
- sem documentos, vê orientação e a ação primária “Importar documento”;
- com documentos, vê catálogo, filtros e detalhes;
- em falha, vê mensagem recuperável e opção de tentar novamente;
- se a navegação trouxer uma identidade, o documento e a página solicitados
  são selecionados depois da carga.

### 7.2 Criação

“Criar documento” significa criar um registro documental antes ou sem anexar
arquivo, caso essa política seja aprovada. O fluxo conceitual deve:

1. solicitar os metadados mínimos;
2. validar nome, tipo, categoria e data;
3. permitir anexar um arquivo ou registrar uma pendência;
4. mostrar resumo antes da confirmação;
5. persistir pelo caso de uso apropriado;
6. selecionar o item criado e notificar o resultado.

Como a baseline exige arquivo na importação, documentos sem arquivo são uma
decisão em aberto e não devem ser implementados implicitamente.

### 7.3 Importação

O usuário seleciona um ou vários arquivos. O sistema:

1. valida origem e disponibilidade;
2. calcula identidade de conteúdo;
3. detecta duplicidades;
4. copia cada arquivo para armazenamento controlado;
5. cria o registro documental;
6. informa importados, duplicados e falhas;
7. atualiza o catálogo;
8. oferece processamento quando suportado.

Uma importação em lote deve apresentar resultado por item e evitar que uma
falha esconda os sucessos. Duplicidade não deve criar novo registro por
acidente; políticas de reutilização ou cópia lógica exigem decisão explícita.

### 7.4 Organização

O usuário organiza documentos por tipo, categoria, data e tags. Alterações
devem ser editoriais, reversíveis antes de salvar e separadas do arquivo
físico. A interface deve indicar:

- campos obrigatórios;
- valores controlados e livres;
- alterações ainda não salvas;
- conflitos ou validações;
- origem automática ou manual de um valor, se essa distinção existir.

### 7.5 Pesquisa e filtros

Pesquisa nominal e filtros de metadados pertencem ao Document Workspace.
Pesquisa integral no texto pode reutilizar a infraestrutura de Search e
encaminhar o resultado de volta ao documento/página.

Filtros previstos:

- texto no nome, observações ou tags;
- tipo documental;
- categoria;
- intervalo da data do documento;
- data de importação;
- tag;
- status do acervo;
- disponibilidade do arquivo;
- status de processamento;
- existência de evidências relacionadas.

Filtros ativos devem permanecer visíveis, possuir ação “Limpar” e produzir
contagem de resultados. A combinação padrão deve ser explicitada; recomenda-se
“E” entre filtros diferentes e “OU” entre múltiplos valores do mesmo filtro.

### 7.6 Edição

Ao editar, a tela deve distinguir visualização e modo de edição. Salvar só
ocorre após validação. Cancelar restaura os dados persistidos. Trocar seleção,
perspectiva ou projeto com alterações pendentes exige a política global de
saída segura.

Campos técnicos como SHA-256, caminho armazenado, tamanho e datas de auditoria
são somente leitura. Nome de exibição, tipo, categoria, data, observações e
tags são candidatos a edição.

### 7.7 Visualização

Quando o arquivo estiver disponível e houver visualizador compatível, a
pré-visualização deve abrir no painel destinado a conteúdo. Para PDF,
navegação por página, zoom e pesquisa interna podem reutilizar a View
existente. Formatos não suportados devem permitir abertura externa segura ou
exibir metadados, conforme contrato futuro.

Se o arquivo estiver ausente, o registro permanece consultável e a interface
explica a indisponibilidade. Texto processado pode continuar acessível se sua
política de retenção permitir.

### 7.8 Associação com evidências

O usuário pode:

- criar evidência a partir do documento inteiro;
- criar evidência a partir da página atual;
- criar evidência a partir de trecho selecionado, quando suportado;
- consultar evidências já relacionadas;
- navegar para uma evidência;
- retornar da evidência ao documento e página de origem.

O Document Workspace produz um candidato neutro. O Evidence Workspace é
responsável por validar, editar e persistir a evidência. O documento não deve
criar ou alterar diretamente entidades de evidência.

## 8. Layout conceitual

### 8.1 Visão estrutural

```text
Projeto aberto
    ↓
Perspectiva: Documentos
    ├── Barra de contexto
    │   ├── Importar
    │   ├── Criar registro
    │   ├── Processar
    │   ├── Remover
    │   └── Atualizar
    │
    ├── Painel de organização e filtros
    │   ├── Pesquisa rápida
    │   ├── Categorias
    │   ├── Tipos documentais
    │   ├── Tags
    │   ├── Datas
    │   └── Status
    │
    ├── Lista de documentos
    │   ├── ordenação
    │   ├── indicadores de disponibilidade/processamento
    │   └── seleção
    │
    ├── Painel de propriedades
    │   ├── metadados editoriais
    │   ├── metadados técnicos
    │   ├── páginas
    │   └── evidências relacionadas
    │
    └── Painel de pré-visualização
        ├── arquivo compatível
        ├── texto processado
        ├── navegação por página
        └── seleção de origem para evidência
```

### 8.2 Composição responsiva

Em largura ampla, recomenda-se organização, catálogo e conteúdo em colunas
redimensionáveis. Em largura reduzida, propriedades e pré-visualização podem
ser alternadas por abas ou painéis recolhíveis. Essa adaptação é visual e não
deve criar estados autoritativos paralelos.

### 8.3 Estados da tela

| Estado | Conteúdo esperado | Ações |
|---|---|---|
| Sem projeto | orientação para abrir/criar projeto | navegação de projeto |
| Carregando | progresso não bloqueante | cancelar, se suportado |
| Vazio | explicação e ação primária | importar/criar |
| Pronto sem seleção | catálogo e instrução de seleção | ações globais |
| Pronto com seleção | detalhes e conteúdo | editar, remover, evidência |
| Filtrado sem resultado | filtros ativos e orientação | limpar filtros |
| Erro recuperável | mensagem e contexto preservado | tentar novamente |
| Arquivo ausente | registro e diagnóstico | localizar/reparar futuramente |
| Processamento pendente | metadados e indicador | processar/cancelar conforme estado |

## 9. Objetos manipulados

O Workspace consome ou produz representações conceituais, não necessariamente
classes com estes nomes:

- **Resumo de documento:** item leve para catálogo;
- **Detalhes de documento:** metadados editoriais, técnicos e disponibilidade;
- **Página documental:** número, texto e origem de processamento;
- **Consulta documental:** texto, filtros, ordenação e paginação;
- **Rascunho de metadados:** valores em edição antes de persistir;
- **Resultado de importação:** sucessos, duplicidades e falhas por arquivo;
- **Relação documento–evidência:** identidade de ambos e localização da fonte;
- **Solicitação de navegação documental:** identidade e página opcional;
- **Candidato de evidência:** documento, página e trecho;
- **Resumo de processamento:** estado, diagnóstico e instante;
- **Contexto de seleção:** identidade documental e dados simples de exibição.

## 10. Casos de uso

### UC-DOC-01 — Importar documento

**Pré-condição:** projeto aberto.
**Fluxo principal:** selecionar arquivos, validar, deduplicar, copiar,
registrar, atualizar catálogo e notificar.
**Alternativas:** cancelamento sem efeito; duplicado reportado sem novo
registro; formato não processável preservado; falha parcial reportada por item.
**Pós-condição:** cada sucesso possui registro e referência física coerentes.

### UC-DOC-02 — Criar registro documental

**Pré-condição:** projeto aberto e política de registro sem arquivo definida.
**Fluxo principal:** preencher metadados, validar, confirmar, persistir e
selecionar.
**Alternativas:** anexar arquivo durante criação; cancelar; corrigir campos.
**Pós-condição:** registro consistente, com disponibilidade explicitada.

### UC-DOC-03 — Remover documento

**Pré-condição:** documento selecionado.
**Fluxo principal:** apresentar impacto e relações, solicitar confirmação,
remover coordenadamente artefatos autorizados, atualizar catálogo e limpar
seleção.
**Alternativas:** cancelar; arquivo já ausente; falha com restauração;
restrição por relações.
**Pós-condição:** nenhum estado intermediário inconsistente fica exposto.

### UC-DOC-04 — Editar metadados

**Pré-condição:** documento selecionado.
**Fluxo principal:** entrar em edição, alterar campos permitidos, validar,
salvar, atualizar detalhes e notificar.
**Alternativas:** cancelar; erro de validação; conflito de atualização; saída
com alterações pendentes.
**Pós-condição:** identidade e arquivo permanecem preservados.

### UC-DOC-05 — Pesquisar documentos

**Pré-condição:** projeto aberto.
**Fluxo principal:** informar consulta, executar, apresentar resultados,
selecionar e abrir item.
**Alternativas:** consulta vazia; índice indisponível; nenhum resultado;
resultado aponta para documento indisponível.
**Pós-condição:** consulta não altera o acervo.

### UC-DOC-06 — Filtrar e ordenar catálogo

**Pré-condição:** catálogo carregado.
**Fluxo principal:** escolher critérios, combinar, atualizar resultados e
contagem, alterar ordenação.
**Alternativas:** combinação sem resultado; limpar um ou todos os filtros.
**Pós-condição:** filtros afetam apenas a projeção da lista.

### UC-DOC-07 — Abrir documento

**Pré-condição:** documento selecionado.
**Fluxo principal:** resolver disponibilidade, escolher visualização
compatível, abrir conteúdo e página solicitada.
**Alternativas:** formato não suportado; arquivo ausente; falha de leitura;
abrir externamente.
**Pós-condição:** seleção documental permanece coerente.

### UC-DOC-08 — Localizar documentos relacionados

**Pré-condição:** documento selecionado e critério de relação definido.
**Fluxo principal:** consultar relações por categoria, tags, data, conteúdo ou
evidências; apresentar resultados e navegar.
**Alternativas:** nenhuma relação; relação aponta para item indisponível.
**Pós-condição:** nenhum vínculo é criado automaticamente.

### UC-DOC-09 — Vincular evidência

**Pré-condição:** documento selecionado; página/trecho opcionais.
**Fluxo principal:** produzir candidato, navegar ao Evidence Workspace,
completar dados, validar e salvar evidência.
**Alternativas:** usuário cancela; fonte indisponível; página inválida;
alterações pendentes no Evidence Workspace impedem navegação.
**Pós-condição:** evidência referencia identidade e localização da fonte.

### UC-DOC-10 — Consultar evidências relacionadas

**Pré-condição:** documento selecionado.
**Fluxo principal:** listar relações, selecionar evidência e navegar pelo
contrato neutro.
**Alternativas:** evidência removida ou inacessível.
**Pós-condição:** documento não modifica a evidência.

## 11. Operações suportadas

### 11.1 Operações da primeira capacidade funcional

- carregar e atualizar catálogo;
- importar um ou vários arquivos;
- selecionar documento e página;
- consultar detalhes e texto processado;
- abrir documento;
- remover com confirmação;
- iniciar criação de evidência;
- receber navegação contextual;
- pesquisar conteúdo pela integração existente.

### 11.2 Operações planejadas

- criar registro sem arquivo, se aprovado;
- editar metadados;
- gerir categorias e tags;
- aplicar filtros compostos e ordenação;
- listar evidências relacionadas;
- processar/reprocessar por item e em lote;
- reparar referência de arquivo indisponível;
- executar ações em lote;
- exportar seleção para Reports.

### 11.3 Regras de habilitação

As ações devem derivar de projeto aberto, seleção, disponibilidade, estado de
processamento, permissões do formato e operação global em andamento. A View
não deve manter cópia autoritativa dessas condições.

## 12. Eventos relevantes

Os eventos abaixo são conceituais. Este documento não decide barramento,
classes, persistência nem publicação técnica. Eventos de acervo registram
fatos; eventos de interação podem permanecer apenas na apresentação.

| Evento | Natureza | Quando ocorre | Consumidores potenciais |
|---|---|---|---|
| `DocumentoImportado` | acervo | arquivo e registro foram incorporados com sucesso | catálogo, Timeline, processamento |
| `DocumentoCriado` | acervo | registro sem importação foi criado, se suportado | catálogo, Timeline |
| `DocumentoRemovido` | acervo | remoção coordenada foi concluída | catálogo, Search, Timeline, Evidence |
| `DocumentoAlterado` | acervo | metadados persistidos mudaram | catálogo, Timeline, Reports |
| `ArquivoDocumentoIndisponivel` | diagnóstico | referência física não pôde ser resolvida | Document, Evidence, Reports |
| `ProcessamentoDocumentalAlterado` | técnico | status ou resultado de processamento mudou | catálogo, Search, visualização |
| `DocumentoSelecionado` | apresentação | seleção global passou a identificar documento | propriedades, comandos contextuais |
| `PaginaDocumentoSelecionada` | apresentação | página ativa mudou | pré-visualização, candidato de evidência |
| `CategoriaAlterada` | acervo | categoria persistida mudou | filtros, Timeline, Reports |
| `TagsAlteradas` | acervo | conjunto de tags persistido mudou | filtros, Reports |
| `FiltroAlterado` | apresentação | projeção do catálogo recebeu novos critérios | lista e contagem |
| `EvidenciaVinculadaAoDocumento` | relação | evidência foi persistida com a fonte documental | Document, Evidence, Reports |
| `NavegacaoDocumentalSolicitada` | coordenação | outro workspace solicita documento/página | NavigationController e DocumentsController |

Eventos de remoção e alteração só representam sucesso concluído. Tentativas,
cancelamentos e falhas são resultados operacionais e notificações, não fatos
de domínio consumados.

## 13. Integrações com outros Workspaces

### 13.1 Evidence Workspace

O Document Workspace fornece identidade, nome, página e trecho como candidato
de fonte. O Evidence Workspace:

- possui o rascunho e a validação da evidência;
- decide salvar ou cancelar;
- consulta disponibilidade da fonte;
- pode solicitar retorno ao documento e página.

Documentos removidos não devem apagar evidências silenciosamente. A baseline
preserva trecho e dados históricos e marca a fonte como indisponível.

### 13.2 Timeline Workspace

A Timeline poderá consumir datas do documento, importação, alterações e
eventos documentais. Deve navegar para o documento por uma solicitação neutra.
Ela não deve editar metadados documentais nem usar a data de importação como
substituta automática da data do documento.

Decisões necessárias: quais eventos aparecem, como documentos sem data são
tratados e se alterações editoriais geram entradas históricas.

### 13.3 Reports Workspace

Reports poderá consultar documentos por filtros, categorias, tags, status e
relações com evidências. Resultados devem usar DTOs ou queries públicas e não
ler widgets ou o estado interno do Document Workspace.

Decisões necessárias: escopo dos relatórios, campos exportáveis, critérios de
ordenação, rastreabilidade e tratamento de arquivos indisponíveis.

### 13.4 Search e visualização

Search retorna identidade documental e página opcional. A navegação é
convertida em `DocumentNavigationRequest`. A visualização é uma capacidade
consumida pelo Workspace; não deve tornar-se proprietária do catálogo ou da
seleção.

## 14. Fluxos transversais e falhas

### 14.1 Troca e fechamento de projeto

Ao fechar ou trocar o projeto:

- operações pendentes devem seguir a política global de saída;
- catálogo, detalhes, páginas, filtros contextuais e seleção são limpos;
- nenhuma instância da sessão anterior pode ser reutilizada;
- a perspectiva deixa de estar disponível sem projeto;
- notificações não devem expor caminhos ou detalhes sensíveis.

### 14.2 Concorrência e operações demoradas

Importação em lote, processamento, OCR e indexação podem ser demorados. A
evolução deve usar `OperationExecutor` ou mecanismo compatível, preservar
responsividade e publicar progresso/cancelamento quando contratados. O
Workspace não deve inventar um segundo estado operacional.

### 14.3 Consistência e recuperação

- falha ao copiar não cria registro;
- falha ao persistir restaura ou remove a cópia parcial;
- remoção coordenada restaura artefatos quando a etapa transacional falha;
- atualização de metadados não altera arquivo;
- falha ao atualizar a projeção não deve corromper a fonte canônica;
- recarregar deve reconstruir a tela a partir dos serviços, não de cache
  autoritativo da View.

## 15. Requisitos de qualidade

- **Acessibilidade:** nomes acessíveis, ordem de tabulação, ações por teclado,
  estados não comunicados apenas por cor.
- **Desempenho:** catálogo grande não deve exigir carregar conteúdo integral
  de todos os documentos; paginação ou virtualização deve ser avaliada.
- **Determinismo:** ordenação deve possuir desempate estável por identidade.
- **Privacidade:** caminhos absolutos e conteúdo não devem aparecer em logs ou
  notificações sem necessidade.
- **Auditabilidade:** mudanças persistentes devem registrar datas e, se houver
  requisito futuro, autoria.
- **Testabilidade:** controllers testáveis sem Qt; Views testáveis com doubles
  de serviços; integrações exercitadas com Stores reais.
- **Compatibilidade:** documentos existentes devem continuar legíveis durante
  evolução de metadados e persistência.
- **Internacionalização futura:** textos visuais não devem ser usados como
  identificadores persistentes.

## 16. Roadmap de implementação por contratos

Cada contrato deve ser pequeno, preservar comportamento anterior e incluir
testes específicos, regressão completa, `compileall`, whitespace e AST.

### Contrato 2 — Read Model e estados do catálogo

- consolidar DTOs de resumo, detalhes, página e disponibilidade;
- formalizar estados vazio, carregando, pronto e erro;
- definir paginação/limite para acervos grandes;
- preservar navegação por identidade e página.

### Contrato 3 — Seleção documental

- integrar `SelectionKind.DOCUMENT`;
- definir metadata mínima da seleção;
- sincronizar catálogo, propriedades e comandos;
- limpar seleção em navegação e fechamento.

### Contrato 4 — Layout operacional

- implementar painel de filtros, catálogo, propriedades e pré-visualização;
- manter placeholders para ações ainda não contratadas;
- validar acessibilidade, redimensionamento e teclado;
- não introduzir lógica de persistência na View.

### Contrato 5 — Importação aprimorada

- resultado detalhado por arquivo;
- progresso e cancelamento;
- política explícita de duplicidade;
- notificações pelo `NotificationCenter`;
- atualização incremental do catálogo.

### Contrato 6 — Edição de metadados

- decidir atributos persistidos e validações;
- criar comando/DTO e serviço de aplicação;
- suportar salvar, cancelar e saída segura;
- preservar identidade de registro e conteúdo.

### Contrato 7 — Categorias e tags

- definir vocabulário, normalização e escopo;
- persistência e migração;
- edição e apresentação;
- testes de compatibilidade.

### Contrato 8 — Pesquisa, filtros e ordenação

- contrato de consulta documental;
- filtros compostos e contagem;
- integração com pesquisa textual;
- tratamento de índice indisponível.

### Contrato 9 — Visualização documental

- integração limpa com visualizador PDF;
- seleção de página e trecho;
- formatos não suportados;
- arquivo ausente e abertura externa segura.

### Contrato 10 — Relações com evidências

- listar relações;
- criar candidato por documento/página/trecho;
- navegação bidirecional;
- política de remoção e fonte indisponível.

### Contrato 11 — Integração Timeline e Reports

- queries públicas e DTOs;
- navegação contextual;
- eventos e datas exibidos;
- exportação sem dependência entre Views.

### Contrato 12 — Operações em lote e robustez

- processamento, categorização ou tags em lote;
- seleção múltipla, se aprovada;
- progresso, cancelamento e falhas parciais;
- testes de volume e recuperação.

## 17. Critérios funcionais de aceite do épico

O Document Workspace será considerado funcionalmente consolidado quando:

- todas as operações autorizadas estiverem acessíveis por um projeto aberto;
- o catálogo representar fielmente a persistência;
- seleção, filtros e visualização permanecerem sincronizados;
- importação e remoção forem consistentes diante de falhas;
- metadados puderem ser editados sem alterar o arquivo;
- navegação entre Document, Evidence, Timeline e Reports usar contratos
  neutros;
- estados vazios, erros e indisponibilidade forem compreensíveis;
- o Workspace não possuir estado global nem acessar infraestrutura;
- a experiência for acessível e adequada a acervos realistas;
- testes funcionais, arquitetônicos e de regressão estiverem aprovados.

## 18. Decisões preservadas

Este projeto funcional preserva:

1. Stores como proprietários exclusivos de estado de apresentação;
2. NavigationController como coordenador de perspectivas;
3. WorkspaceStore e WorkspaceHost como montagem lógica e visual;
4. MainWindow sem regras de negócio ou acesso à infraestrutura;
5. controllers como coordenadores, sem persistência direta na View;
6. identidade documental estável e SHA-256 como identidade de conteúdo;
7. separação entre arquivo, catálogo, processamento e índice;
8. JSON processado como fonte canônica do conteúdo derivado atual;
9. pesquisa SQLite/FTS como projeção reconstruível;
10. preservação histórica de evidências quando a fonte é removida;
11. `DocumentNavigationRequest` como contrato neutro de documento/página;
12. NotificationCenter para mensagens transitórias da nova integração.

## 19. Questões em aberto antes da implementação

As seguintes decisões precisam de contrato explícito:

1. documentos sem arquivo serão permitidos?
2. categoria é única, múltipla ou hierárquica?
3. categorias pertencem ao projeto, à aplicação ou a um catálogo global?
4. como tags são normalizadas e deduplicadas?
5. quais metadados são obrigatórios por tipo documental?
6. data parcial, desconhecida ou intervalo serão aceitos?
7. qual identidade é usada externamente: ID do registro ou SHA-256?
8. um mesmo conteúdo pode originar múltiplos registros lógicos?
9. haverá substituição/revinculação de arquivo? Com qual impacto?
10. remover é exclusão definitiva, arquivamento ou envio à lixeira?
11. qual política vale quando existem evidências relacionadas?
12. metadados extraídos automaticamente são sugestão ou valor autoritativo?
13. quais filtros precisam persistir entre sessões?
14. seleção múltipla e operações em lote fazem parte da Release 1.6?
15. quais formatos terão pré-visualização interna?
16. qual limite exige paginação ou virtualização do catálogo?
17. quais eventos devem ser históricos e quais são apenas de apresentação?
18. Reports poderá acessar arquivo/conteúdo ou somente metadados e relações?

## 20. Glossário

- **Acervo:** conjunto de registros documentais pertencentes ao projeto.
- **Arquivo físico:** bytes armazenados e referenciados pelo registro.
- **Categoria:** classificação organizacional controlada.
- **Documento:** registro identificável do acervo e sua referência de arquivo.
- **Identidade de conteúdo:** hash usado para integridade e deduplicação.
- **Metadado editorial:** informação confirmada ou escrita pelo usuário.
- **Metadado técnico:** informação derivada do arquivo ou processamento.
- **Página:** unidade navegável de um resultado documental processado.
- **Perspectiva:** definição declarativa de um espaço funcional da interface.
- **Tag:** marcador flexível para recuperação transversal.
- **Workspace:** conteúdo central correspondente à perspectiva ativa.

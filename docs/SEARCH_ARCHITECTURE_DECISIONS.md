# Decisões arquiteturais do Search

Este registro mínimo reúne decisões homologadas no Épico Search. O módulo não
possui ainda um diretório ou processo próprio para ADRs.

Estas decisões devem ser interpretadas conforme os princípios gerais descritos
na [Visão do Domínio](architecture/domain-vision.md).

## ADR-010 — Search produz SearchHit

Search retorna ocorrências (`SearchHit`), nunca `Document` ou arquivos físicos.

## ADR-011 — SearchService depende de SearchIndex

`SearchService` depende somente da porta de consulta `SearchIndex`. SQLite,
FTS5 e SQL pertencem ao adaptador concreto.

## ADR-012 — Fonte canônica e projeção

`ProcessingRepository` é a fonte canônica do texto processado. `SearchIndex` é
uma projeção reconstruível e não substitui os resultados de processamento.

## ADR-013 — Navegação documental

A navegação originada em Search usa o contrato compartilhado e imutável
`DocumentNavigationRequest`. O ponto de composição entrega a solicitação ao
`DocumentsController`, que resolve a identidade e a página por seus contratos
públicos. Search nunca acessa `PdfView` diretamente.

## ADR-014 — Consulta e manutenção separadas

`SearchIndex` é uma porta somente leitura. Escrita, remoção, reconstrução e
reconciliação pertencem à porta separada `SearchIndexMaintainer`. O
`SearchService`, o `SearchController` e o Workspace não dependem dessa porta.
O adaptador de consulta continua abrindo SQLite em modo somente leitura.

## ADR-015 — Paginação V1

A V1 usa `offset` e busca `limit + 1` registros. `has_more` é conhecido sem
exigir `total_hits`, que pode permanecer `None`.

## ADR-016 — Score de Relevância da Pesquisa

Score representa relevância relativa somente dentro da mesma consulta. Maior
valor público significa maior relevância, sem comparabilidade obrigatória entre
consultas ou mecanismos.

O score representa exclusivamente relevância de pesquisa. Não representa:

- pontuação normativa;
- mérito;
- classificação funcional;
- pontuação RSC;
- duração de exercício.

## DT-004 — Remover contratos legados de Search

Remover `SearchFilters`, os dois modelos `SearchResult`,
`LegacyIndexedSearchService` e as facades relacionadas somente após:

- migração do Search Workspace;
- migração completa de Evidence;
- implementação da navegação;
- estabilização dos contratos públicos.

Na IS-8.6.2, o Workspace já usa `SearchHit`, mas a compatibilidade legada ainda
é preservada para consumidores externos e testes históricos.

## ADR-019 — SearchIndex é uma projeção reconstruível

### Contexto

O índice de pesquisa é derivado dos resultados processados canônicos.

### Decisão

`ProcessingRepository` permanece a fonte canônica. Um adaptador de fronteira
produz `SearchIndexDocument`, e o índice pode ser removido e reconstruído sem
perda de informação canônica.

### Consequências

- nenhuma informação exclusiva deve existir apenas no índice;
- inconsistências podem ser corrigidas por `reconcile`;
- corrupção pode ser corrigida por `rebuild`;
- manutenção não pertence ao `SearchService`;
- `SearchIndex` permanece somente leitura.

## ADR-020 — Rebuild transacional no banco compartilhado

O índice FTS5 compartilha o SQLite do projeto com estruturas que não pertencem
à projeção de pesquisa. Por isso, o rebuild não substitui o arquivo do banco.
Ele materializa e valida a fonte antes da escrita e substitui apenas as tabelas
da projeção em uma única transação. Qualquer falha executa rollback e preserva
o índice anterior. Upsert e remoção também usam transações curtas e conexões
independentes.

## DT-008 — Eliminar o fluxo legado de indexação

`DocumentIndexer` foi preservado como facade de compatibilidade e já delega o
upsert textual e a remoção ao `SearchIndexMaintainer`. O tratamento histórico
dos estados não processados e dos relatórios mutáveis deverá ser removido
depois da estabilização da nova porta e da migração dos consumidores legados.

As dívidas já homologadas permanecem fora do escopo desta sprint:

- DT-005 — eliminar a pressuposição externa de SHA-256;
- DT-006 — revisar campos vazios do preview;
- DT-007 — revisar orquestrações inter-workspace.

## ADR-021 — EvidenceRepository é uma porta

### Contexto

O repository de Evidence acumulava o contrato usado pelos casos de uso e os
detalhes concretos de SQLite, SQL, conexões e transações.

### Decisão

`EvidenceRepository` passa a ser uma porta de persistência estrutural.
`SQLiteEvidenceRepository` implementa essa porta como adaptador de
infraestrutura. `EvidenceService` depende somente da porta e o composition root
seleciona o adaptador concreto.

### Consequências

- casos de uso não importam SQLite ou o adaptador concreto;
- schema, migrations, transações e comportamento permanecem inalterados;
- o import histórico `services.evidence_repository.EvidenceRepository`
  permanece temporariamente como alias do adaptador para compatibilidade.

## ADR-022 — Evidence referencia documentos por identidade opaca

### Contexto

Os contratos públicos de Evidence expunham `document_sha256`, embora o
algoritmo usado pela infraestrutura não faça parte da semântica da evidência.

### Decisão

Entidade, requests, draft, candidato, portas e casos de uso usam
`document_identity`, tratado como texto opaco não vazio. O adaptador SQLite
continua mapeando essa identidade para a coluna V2 `document_sha256`, e o
resolver temporário continua interpretando-a como SHA-256 internamente.

### Consequências

- schema, migrations e registros existentes permanecem compatíveis;
- aliases `document_sha256` são mantidos temporariamente nos contratos;
- identidades opacas são aceitas pelo domínio, embora a infraestrutura atual
  ainda exija SHA-256 para persistência e resolução;
- DT-005 permanece aberta enquanto os aliases legados forem públicos.

## DT-009 — Desacoplar disponibilidade de Evidence da projeção Search

A disponibilidade documental ainda é consultada na tabela derivada
`documents`. Sua substituição por uma fonte canônica pertence a sprint futura.

## DT-010 — Remover campos legados de EvidenceSourceCandidate

Campos físicos e específicos do resultado legado devem ser removidos somente
após a migração de todos os consumidores.

## ADR-027 — Documents é a autoridade documental

### Contexto

Evidence precisa verificar se a fonte de uma evidência está disponível, mas o
repository de Evidence consultava diretamente a tabela `documents`, que hoje
pertence à projeção reconstruível de Search.

### Decisão

Toda resolução de disponibilidade passa pela porta `DocumentSourceResolver`.
Enquanto Documents Core não oferecer API própria, o adaptador temporário
`SearchDocumentSourceResolver` preserva a estratégia atual de consulta.
`EvidenceService` depende da porta e `SQLiteEvidenceRepository` cuida somente
da persistência de evidências.

### Consequências

- EvidenceRepository não consulta documentos;
- a dependência temporária da projeção fica isolada em um adaptador;
- schema, contratos de Evidence e comportamento permanecem inalterados;
- DT-009 permanece aberta até o adaptador ser substituído por uma integração
  baseada em Documents Core.

## ADR-024 — Entradas externas convergem para EvidenceSourceCandidate

### Decisão

Search e Documents entregam fontes externas a Evidence exclusivamente por
`EvidenceSourceCandidate`. Search mantém a adaptação
`EvidenceSourceCandidate.from_search_hit()`. Documents constrói o candidato
somente com `document_identity`, `document_name`, `page_number` e o trecho
disponível, sem importar Search, EvidenceService, visualizador ou caminho físico.
O `ProjectController` encaminha ambos por callbacks explícitos.

### Consequências

- Evidence recebe uma única forma de entrada, independentemente da origem;
- Documents não cria nem persiste Evidence;
- os campos legados do candidato permanecem inalterados conforme DT-010;
- schema, migrations, repository e resolução documental não são afetados.

## ADR-025 — Evidence utiliza DocumentNavigationRequest

### Decisão

Evidence solicita abertura da fonte exclusivamente por
`DocumentNavigationRequest`. O `EvidenceController` cria o contrato e o entrega
a um callback. O `ProjectController`, como composition root, encaminha a
solicitação para `DocumentsController.navigate()` e exibe o Documents Workspace
somente após navegação bem-sucedida.

### Consequências

- Evidence não conhece DocumentsController, Workspace, PdfView, filesystem ou
  SQLite;
- Documents continua sendo a autoridade da navegação documental;
- o mesmo fluxo de destino é compartilhado por Search e Evidence;
- não são introduzidos contratos nem lógica documental no composition root.

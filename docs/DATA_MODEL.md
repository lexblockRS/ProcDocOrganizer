# Modelo de Dados

## Objetivo

Este documento descreve as entidades utilizadas pelo ProcDocOrganizer e os relacionamentos entre elas.

O objetivo é manter uma estrutura simples, flexível e independente de um processo administrativo específico.

---

# Entidades

## Projeto

Representa um trabalho realizado pelo usuário.

Um projeto possui:

- documentos;
- evidências;
- configurações.

---

## Documento

Representa um arquivo utilizado como fonte de informação.

Exemplos:

- Portaria
- Certificado
- Boletim
- Processo
- Declaração

Cada documento possui:

- nome;
- caminho;
- hash;
- número de páginas;
- tipo de documento;
- status de processamento;
- data de processamento;
- data do documento;
- observações.

Um documento poderá gerar nenhuma, uma ou várias evidências.

O texto extraído não é armazenado diretamente no documento. Os resultados
de processamento são persistidos separadamente por hash do arquivo e mantêm
o texto de cada página, o status e eventuais erros.

A pesquisa textual consulta exclusivamente esses resultados persistidos e
retorna o documento, a página e um trecho de cada ocorrência encontrada.

Resultados processados também podem conter metadados estruturados derivados
deterministicamente do texto extraído: título, tipo documental, número, data,
órgão emissor e identificadores SEI. O JSON registra a versão do extrator de
metadados para permitir a evolução futura das heurísticas.

Os campos de metadados são `title`, `document_type`, `document_number`,
`document_date`, `issuing_organization`, `sei_process_number` e `sei_code`.
Campos sem identificação permanecem `null`; `document_type` utiliza `unknown`
quando nenhuma regra de tipo documental for reconhecida.
Para documentos institucionais, o título e a data priorizam a linha do ato
documental; o órgão emissor prioriza unidades específicas sobre universidade,
instituto ou ministério.

Os estados de processamento suportados são: `not_processed`, `pending`,
`processing`, `processed`, `ocr_required`, `failed` e `cancelled`.

O estado `ocr_required` indica que o PDF foi lido corretamente, mas não possui
texto nativo pesquisável. Ele não representa falha de processamento.

Resultados novos não produzem mais `ocr_required`: cada página sem texto
nativo suficiente é enviada ao OCR. O estado continua aceito ao ler e
reconstruir projetos antigos. O campo aditivo `text_source` informa `native`,
`ocr` ou `mixed`; `ocr_used` informa se ao menos uma página exigiu OCR.

---

## Evidência

Representa um fato comprovado por um documento.

Exemplos:

- Participação em comissão;
- Exercício de chefia;
- Curso de capacitação;
- Fiscalização de contrato;
- Publicação;
- Projeto de extensão.

Cada evidência possui:

- título;
- descrição;
- categoria;
- data inicial;
- data final (opcional);
- observações;
- documento de origem.

Uma evidência poderá ser classificada em um critério do RSC.

---

## Critério RSC

Representa um item previsto na regulamentação.

Cada critério possui:

- código;
- descrição;
- requisito;
- pontuação.

Esses dados serão importados da tabela de critérios do RSC.

---

# Relacionamentos

Projeto

↓

Documentos

↓

Evidências

↓

Critério RSC

---

# Visualizações

As informações cadastradas poderão ser apresentadas através de:

- Linha do Tempo;
- Pontuação;
- Relatórios.

Essas visualizações não armazenam dados próprios.

São geradas automaticamente pelo sistema.

---

# Índice textual SQLite (Sprint 7.1)

Cada pasta de projeto `.pdop` possui um `database.db` SQLite. O arquivo
`project.json` continua indicando seu nome no campo `database`; os JSONs em
`processing/<sha256>.json` permanecem como resultados canônicos do
processamento e não tiveram seu formato alterado.

O schema usa `PRAGMA user_version = 1` e também registra o estado lógico
`schema_version = 1` e `index_version = 1` na tabela `index_state`.

## Tabela `documents`

Uma linha por conteúdo identificado por SHA-256. Armazena nome e caminho
opcionais, estado e quantidade de páginas do processamento, metadados
determinísticos, instante de indexação e datas técnicas de criação e
atualização. `sha256` é único. Metadados ausentes permanecem `NULL` e
`document_type` não possui `CHECK` fechado.

## Tabela `document_pages`

Uma linha por página, com `UNIQUE(document_id, page_number)` e chave
estrangeira `ON DELETE CASCADE` para `documents`. A numeração começa em 1.
O texto integral é preservado, inclusive quando vazio.
Antes da gravação, apenas caracteres nulos (`U+0000`) são removidos para
manter compatibilidade com SQLite/FTS; nenhum outro caractere é normalizado.
Para resultados `processed`, `page_count` deve ser igual à quantidade de itens
em `pages`. Estados `ocr_required` e `failed` podem manter a contagem original
sem armazenar páginas no índice.

## Tabela virtual `document_pages_fts`

Contém somente páginas cujo texto não é vazio após `strip()`. Usa FTS5 com:

```sql
tokenize = 'unicode61 remove_diacritics 2'
```

`document_id` e `page_number` são campos `UNINDEXED`. O FTS não respeita
chaves estrangeiras; suas linhas são removidas explicitamente antes da
remoção relacional.

## Estados e reindexação

- `processed`: substitui integralmente as páginas e o FTS e define
  `indexed_at`;
- `ocr_required`: registra o documento, remove texto anterior e mantém
  `indexed_at` como `NULL`;
- `failed`: registra o estado quando o SHA-256 é válido e remove o índice
  textual anterior;
- outros estados são rejeitados antes de qualquer alteração no banco.

Cada documento é atualizado em uma transação única. A reconstrução
incremental processa os JSONs em ordem de nome e preserva outros registros. A
reconstrução completa é uma operação separada e explícita que limpa as
linhas do índice antes de recompô-lo; ela não apaga o arquivo do banco nem o
schema.

FTS5 é dependência obrigatória. A inicialização falha com erro explícito
quando o SQLite do ambiente não oferece o módulo. Não há fallback, OCR,
embeddings ou busca semântica.

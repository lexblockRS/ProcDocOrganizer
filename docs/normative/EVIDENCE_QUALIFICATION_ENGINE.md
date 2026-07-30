# Evidence Qualification Engine

## 1. Responsabilidade

O `EvidenceQualificationEngine` responde somente:

> Há documentação apresentada e associada explicitamente a uma categoria
> documental oficial para que a análise possa continuar?

Ele não responde se o critério foi atendido, se o requerente é elegível ou
quantos pontos devem ser considerados.

## 2. Fronteira

```text
EvaluationContext somente leitura ────┐
Modelo Normativo somente leitura ─────┤ configuração
                                      ▼
CriterionCandidateCollection ─► EvidenceQualificationEngine
                                      │
                                      ▼
                      QualifiedCriterionCandidateCollection
```

`qualify()` recebe somente a coleção produzida pelo componente anterior. O
contexto factual e o modelo são fornecidos ao construtor e permanecem
imutáveis.

O Engine não acessa Repositories, SQLite, Controllers, Workspaces ou Aggregate
Roots.

## 3. Conceitos documentais

### Documento apresentado

Um `PresentedDocument` corresponde a um Document efetivamente presente no
`EvaluationContext`, localizado simultaneamente por ID e identidade
documental.

### Documento aceito

Um `AcceptedDocument` é a associação entre:

- um `PresentedDocument`; e
- uma `OfficialDocumentCategory` localizada no Modelo Normativo.

“Aceito” significa apenas compatibilidade com a categoria documental
explicitamente indicada. Não significa autenticidade, suficiência ou
atendimento do critério.

### Documento faltante

Um `MissingDocument` preserva ID e identidade de uma referência documental que
não pôde ser localizada no contexto.

### Categoria satisfeita

Uma categoria é documentalmente satisfeita quando:

1. foi indicada explicitamente no vínculo;
2. existe no Modelo Normativo;
3. o documento vinculado está presente no contexto.

### Categoria pendente

Uma categoria é pendente somente quando existe no Modelo Normativo, foi
indicada explicitamente e seu documento está ausente. Uma categoria
desconhecida não é promovida a pendência oficial.

O Decreto não estabelece que todas as categorias do art. 4º sejam
simultaneamente obrigatórias. Por isso, o Engine não calcula “faltantes” pela
subtração de todas as categorias oficiais.

## 4. Algoritmo determinístico

Para cada `CriterionCandidate`, na ordem recebida:

1. localiza em `criterion_candidate_links` todos os vínculos com a mesma
   combinação critério/Activity/FunctionalExercise;
2. se não houver vínculo adicional, utiliza a rastreabilidade factual já
   preservada no candidato;
3. localiza cada Document por ID e identidade;
4. consulta a categoria documental pelo ID normativo explícito;
5. registra documento apresentado, aceito ou faltante;
6. registra categorias satisfeitas e pendentes;
7. elimina repetições preservando a primeira ocorrência;
8. produz justificativa baseada apenas nas contagens verificadas.

Não há leitura de texto, nome de arquivo, descrição de Activity, conteúdo de
Evidence ou trecho documental.

## 5. Saída

`QualifiedCriterionCandidate` contém:

- o `CriterionCandidate` original;
- `presented_documents`;
- `accepted_documents`;
- `missing_documents`;
- `satisfied_categories`;
- `pending_categories`;
- `documentary_justification`;
- `normative_traceability`.

`has_compatible_documentation` informa exclusivamente se existe ao menos uma
associação Document/categoria oficial. Não representa decisão normativa.

`QualifiedCriterionCandidateCollection` é uma tupla ordenada e sem
duplicidades.

## 6. Justificativa documental

A justificativa registra:

- quantidade de documentos apresentados;
- associações com categorias oficiais;
- documentos ausentes;
- categorias satisfeitas;
- categorias pendentes;
- declaração explícita de que o resultado é apenas documental.

Ela não contém conclusão sobre critério, requisito ou elegibilidade.

## 7. Invariantes

- `EvaluationContext` permanece inalterado;
- o Modelo Normativo é somente leitura;
- a coleção e os candidatos de origem são preservados;
- a origem normativa do candidato é preservada;
- ID e identidade devem apontar para o mesmo Document;
- documentos e categorias não se repetem na saída;
- a ordem dos candidatos e a primeira ocorrência documental são preservadas;
- somente categorias oficiais podem ser satisfeitas ou pendentes;
- as mesmas entradas produzem o mesmo resultado.

## 8. Limitações

- a associação Document/categoria precisa existir explicitamente no metadata;
- o Engine não classifica documentos por nome, tipo local ou conteúdo;
- categoria desconhecida produz documento incompatível, não categoria
  pendente;
- ausência de documentação compatível não prova descumprimento;
- documentação compatível não prova satisfação do critério;
- autenticidade, validade temporal e força probatória não são avaliadas;
- não há pontuação, elegibilidade, decisão, ranking ou interpretação
  qualitativa;
- não é utilizada IA, similaridade textual, embedding ou aprendizado de
  máquina.

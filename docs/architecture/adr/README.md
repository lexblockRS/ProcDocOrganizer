# Índice de ADRs

Este diretório é o índice oficial das decisões arquiteturais do projeto. Todos
os ADRs devem ser interpretados conforme os princípios gerais da
[Visão do Domínio](../domain-vision.md).

## Decisões

| ADR | Título | Descrição | Situação | Localização |
| --- | --- | --- | --- | --- |
| ADR-007 | Camada de Apresentação e Projeções | Separa coordenação, agregação e apresentação do Dashboard. | Accepted | [ADR-007](ADR-007-presentation-layer-and-projections.md) |
| ADR-001 | Não localizado | Nenhuma decisão formal foi encontrada nos arquivos, branches ou histórico Git disponíveis. | Ausente; número reservado | — |
| ADR-002 | Não localizado | Nenhuma decisão formal foi encontrada nos arquivos, branches ou histórico Git disponíveis. | Ausente; número reservado | — |
| ADR-003 | FunctionalAssignmentNormalizer | Define o significado, os limites e o ciclo da normalização de evidências de atribuição funcional. | Proposed | [ADR-003](ADR-003-functional-assignment-normalizer.md) |
| ADR-010 | Search produz SearchHit | Define a ocorrência de pesquisa como resultado público de Search. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-011 | SearchService depende de SearchIndex | Separa o serviço de pesquisa do adaptador concreto do índice. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-012 | Fonte canônica e projeção | Distingue resultados processados canônicos do índice reconstruível. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-013 | Navegação documental | Define o contrato compartilhado de navegação até a fonte documental. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-014 | Consulta e manutenção separadas | Separa leitura e manutenção do índice de pesquisa. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-015 | Paginação V1 | Registra a estratégia inicial de paginação da pesquisa. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-016 | Score de Relevância da Pesquisa | Define o score exclusivamente como relevância relativa de pesquisa. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-019 | SearchIndex é uma projeção reconstruível | Estabelece que o índice pode ser reconstruído a partir da fonte canônica. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-020 | Rebuild transacional no banco compartilhado | Preserva outras estruturas e o índice anterior durante reconstruções. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-021 | EvidenceRepository é uma porta | Separa o contrato de persistência de Evidence do adaptador concreto. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-022 | Evidence referencia documentos por identidade opaca | Remove o algoritmo de identidade da semântica pública de Evidence. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-024 | Entradas externas convergem para EvidenceSourceCandidate | Unifica as entradas documentais recebidas por Evidence. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-025 | Evidence utiliza DocumentNavigationRequest | Define o contrato usado para solicitar abertura da fonte documental. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-027 | Documents é a autoridade documental | Atribui a Documents a resolução de disponibilidade das fontes. | Ativo | [Decisões de Search](../../SEARCH_ARCHITECTURE_DECISIONS.md) |
| ADR-028 | Referências históricas e fontes removidas | Preserva relações indisponíveis e exige apresentação explícita. | Aceito | [ADR-028](ADR-028-historical-source-references.md) |
| ADR-029 | Auditabilidade dos objetos RSC | Adia metadados parciais e exige desenho de governança antes da pontuação. | Aceito | [ADR-029](ADR-029-rsc-auditability.md) |
| ADR-030 | Versionamento normativo futuro | Exige resultados normativos identificáveis e reproduzíveis. | Aceito | [ADR-030](ADR-030-normative-versioning.md) |
| ADR-031 | Associações e política de exclusão | Define propriedade, cascade, restrição e exclusões explícitas. | Aceito | [ADR-031](ADR-031-associations-and-deletion-policy.md) |
| ADR-032 | Estado inicial de Activity | Formaliza que Activity nasce lembrada, não comprovada. | Aceito | [ADR-032](ADR-032-activity-initial-state.md) |
| ADR-033 | Avaliação Progressiva | Preserva avaliações parciais e fatos ainda sem Binding. | Aceito | [ADR-033](ADR-033-progressive-evaluation.md) |

## Lacunas de numeração

- ADR-001 e ADR-002 não foram formalizados nos arquivos, branches ou histórico
  Git disponíveis. Seus números permanecem reservados para eventual localização
  histórica.
- ADR-017, ADR-018, ADR-023 e ADR-026 permanecem não localizados.
- Lacunas não autorizam renumeração nem reutilização automática.
- Os registros `DT-*` presentes no documento consolidado de Search representam
  débitos ou decisões transitórias e não integram a numeração de ADRs.

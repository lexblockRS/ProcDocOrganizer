# Evidence Manager

## Objetivo

O Evidence Manager introduz `Evidence` como Aggregate Root utilizado
diretamente pelo usuário dentro de um `Project`. Uma Evidence representa
uma unidade de comprovação organizada; ela não representa um arquivo e não
executa regras normativas.

## Aggregate Evidence

Cada Evidence possui identidade UUID própria (`aggregate_id`), referência
ao Project proprietário, título, descrição, datas de criação e atualização,
estado, metadados escalares e uma coleção ordenada de Documents. Suas
revisões preservam a identidade e são imutáveis: editar ou alterar a coleção
produz uma nova instância.

O estado inicial é `ACTIVE`. Uma Evidence arquivada permanece como registro
histórico e não pode ser alterada ou reativada.

## Document

`Document` é um objeto descritivo e neutro em relação ao RSC. Ele contém
identificador, nome, caminho relativo ao Workspace, tipo, hash SHA-256
opcional e tamanho opcional. O caminho é apenas uma referência: o objeto não
abre, copia ou interpreta arquivos.

O vínculo é mantido pela Evidence e não modifica o Project nem o Workspace.
Não há OCR, visualização de PDF, drag-and-drop ou extração automática.

## Project Explorer

O Project Explorer apresenta uma área **Evidências** com lista e operações
Adicionar, Editar e Remover. A lista é carregada para o Project corrente e
permanece vazia quando nenhum Project está aberto. Nesta versão, a interface
edita somente os dados básicos da Evidence; Documents são exercitados pelo
contrato de domínio e pela persistência.

## Modelo físico

A persistência SQLite utiliza três estruturas específicas:

- `platform_evidences`: identidade, Project proprietário, conteúdo,
  timestamps, estado e metadados;
- `platform_documents`: referências descritivas dos Documents;
- `platform_evidence_documents`: associação ordenada entre Evidence e
  Document.

O store realiza reidratação integral e preserva identidade, timestamps,
metadados e ordem dos Documents. Documents sem qualquer vínculo são removidos
como detalhe físico do store. Não foi criado Repository genérico, ORM, cache
ou Unit of Work.

## Limites

Evidence não contém pontuação, `ExecutionFact`, validação, compatibilidade ou
qualquer conhecimento do Kernel. O modelo não altera `Project`, Workspace,
Host ou os Aggregates RSC existentes. Também não incorpora conteúdo binário:
o arquivo continua localizado no Workspace por caminho relativo.

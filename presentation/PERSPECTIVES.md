# Contrato de Perspectivas

Uma perspectiva é um ponto de vista sobre o mesmo Processo RSC. Ela descreve
como esse ponto de vista poderá ser identificado, ordenado e criado no futuro;
não é uma janela, tela, entidade, documento ou widget.

Uma **View** é um componente visual concreto e pode depender do toolkit
gráfico. Uma **Perspectiva** é apenas uma definição declarativa da camada de
apresentação. Nesta etapa não existe ligação entre as duas.

## Elementos

- `PerspectiveId` é a identidade textual, dinâmica, imutável e serializável.
- `PerspectiveDefinition` reúne ID, título, ordem, ícone textual,
  `requires_project` e uma factory. `to_dict()` omite a factory, pois código
  executável não faz parte dos metadados serializáveis.
- `PerspectiveSnapshot` contém a perspectiva ativa, a tupla ordenada de
  definições disponíveis e a revisão.
- `PerspectiveStore` é o único proprietário do catálogo e da ativação. Ele
  registra, consulta, lista, verifica existência, ativa, desativa e publica
  snapshots.

## Ciclo de vida

Uma perspectiva é primeiro registrada. Pode então ficar ativa e, ao ativar
outra, torna-se conceitualmente substituída. Não há remoção, cache, criação de
widget ou execução de factory neste contrato.

## Invariantes

- IDs e títulos (sem distinção entre maiúsculas e minúsculas) são únicos.
- Definições, IDs, snapshots e a coleção disponível são imutáveis.
- No máximo uma perspectiva registrada pode estar ativa.
- Registro e mudança efetiva de ativação incrementam `revision`.
- Ativação ou desativação redundante preserva snapshot e revisão.
- Observers recebem somente o novo snapshot; falhas são isoladas.
- A ordenação é determinística por `order`, título e ID.
- O contrato não depende de Qt, domínio, navegação, estado ou seleção.

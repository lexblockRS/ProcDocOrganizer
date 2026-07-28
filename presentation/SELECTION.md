# Contrato de Seleção Global

A seleção global é somente uma referência estável de apresentação. Ela
não armazena entidades, widgets, sessões, repositories ou fachadas.

## Valores

`SelectionKind` possui os valores estáveis `none`, `process`, `document`,
`activity`, `evidence` e `requirement`.

`SelectionIdentity` combina o kind com um identificador público do tipo
`str`. Identificadores reais são normalizados com `strip()`. A identidade
oficial sem seleção é `SelectionIdentity.none()`, cujo identifier é
sempre `None`.

`SelectionContext` acrescenta um nome de exibição e metadata auxiliar.
`SelectionContext.none()` é a representação canônica da seleção vazia.

`SelectionSnapshot` contém o contexto atual e a revision. A revision
começa em zero e aumenta uma vez somente quando a seleção muda de forma
efetiva.

## Metadata

Metadata aceita escalares (`str`, `int`, `float`, `bool`, `None`),
tuplas, frozensets e mappings compostos recursivamente pelos mesmos
tipos. Mappings são copiados defensivamente e expostos como
`MappingProxyType`. Listas, sets, callbacks e objetos arbitrários são
recusados.

## Store e observação

```python
store = SelectionStore()
unsubscribe = store.subscribe(render_selection)
store.select(
    SelectionContext(
        SelectionIdentity(SelectionKind.DOCUMENT, "document-1"),
        "Portaria.pdf",
        {"category": "Portaria"},
    )
)
store.clear()
unsubscribe()
```

Seleções redundantes e `clear()` redundante preservam o mesmo snapshot,
não incrementam revision e não notificam observers. Falhas de um
observer são registradas e não impedem os seguintes.

O Store é independente de Qt, ApplicationStateStore, domínio RSC,
ApplicationFacade e infraestrutura. Navegação, histórico, seleção
múltipla e integração com widgets pertencem a etapas futuras.

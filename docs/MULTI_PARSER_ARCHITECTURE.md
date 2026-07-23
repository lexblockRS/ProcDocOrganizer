# Arquitetura multi-parser

`ProcessingResult` é o contrato canônico entre parsing, persistência,
indexação, pesquisa e evidências. Os campos de página permanecem inalterados:
formatos paginados usam páginas reais e um futuro formato não paginado poderá
usar uma unidade lógica. Não há mudança no JSON nem no schema do banco.

O fluxo é `DocumentProcessor -> ParserRegistry -> DocumentParser ->
ProcessingResult -> ProcessingRepository`. O registro consulta os parsers em
ordem de registro; isso permite que futuros parsers especializados e genéricos
reconheçam a mesma extensão sem um mapa rígido. O registro padrão contém apenas
`PDFParser` e é criado por factory, sem estado global mutável.

## Identidades distintas

- Formato físico descreve o contêiner, como PDF, XML ou DOCX.
- Tipo documental descreve o domínio, como portaria, currículo ou ata.
- `parser_id` identifica a implementação, como `pdf` ou um futuro
  `lattes_xml`.

## Detecção de PDF

`PDFParser` aceita a extensão `.pdf` sem diferenciar maiúsculas e minúsculas.
Para preservar a compatibilidade, uma assinatura inválida não é rejeitada
nesta etapa: o carregador PDF continua sendo a validação definitiva. A assinatura
`%PDF-` também permite reconhecer um PDF sem extensão. Origem inexistente ou
diretório é rejeitada pelo registro antes de consultar parsers. Extensão vazia
sem assinatura e XML continuam não suportados.

## Conteúdo estruturado futuro

Para o primeiro Lattes XML, recomenda-se inicialmente um campo opcional e
versionado `structured_data` no `ProcessingResult`, desde que uma versão futura
faça análise de compatibilidade e limites de tamanho. Um artefato separado passa
a ser preferível quando o conteúdo for grande, tiver ciclo de vida ou permissões
próprios, ou demandar schemas e indexação independentes. Em ambos os casos, o
JSON bruto não deve ser confiado diretamente ao indexador.

Parsers XML futuros devem desativar entidades externas e acesso à rede, impedir
XXE e expansão de entidades, não executar XSLT arbitrário, limitar tamanho e
profundidade e validar a estrutura com uma biblioteca segura. Nenhuma biblioteca
ou lógica XML faz parte deste sprint.

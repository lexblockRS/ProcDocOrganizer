# Motor documental

## Fluxo operacional

O fluxo ativo é único e associado à `ProjectSession`:

1. `DocumentImportService` calcula o SHA-256, evita duplicidade, copia o
   arquivo para `documents/` e cria o registro de catálogo no SQLite.
2. `DocumentProcessor` resolve o parser. O registro padrão contém somente
   `PDFParser`.
3. `PDFParser` extrai texto nativo por página com QtPdf. Páginas sem texto
   suficiente são renderizadas e enviadas ao Tesseract.
4. `ProcessingRepository` grava o `ProcessingResult` canônico em
   `processing/<sha256>.json`.
5. O `DocumentIndexer` injetado no processor atualiza a projeção SQLite,
   as páginas e o índice FTS.
6. `SearchService` consulta exclusivamente a projeção FTS.
7. Evidências guardam o SHA-256, a página e uma cópia do trecho selecionado.

O JSON é a fonte canônica do conteúdo processado. O catálogo SQLite registra
identidade, arquivo, estado resumido e metadados de acervo. As tabelas de
páginas e FTS são projeções reconstruíveis a partir dos JSONs.

## Formatos

Qualquer arquivo pode ser preservado no acervo. O processamento textual
automático suporta somente PDF. PDFs podem conter texto nativo, páginas
digitalizadas ou ambos. Não há parser para imagens isoladas, DOCX ou TXT.

## OCR

O OCR usa o executável externo Tesseract e o idioma `por`. A localização é
resolvida nesta ordem:

1. caminho passado ao `TesseractOCREngine`;
2. variável de ambiente `PROCDOC_TESSERACT_PATH`;
3. executável `tesseract` disponível no `PATH`.

Antes do reconhecimento, o motor verifica o executável e consulta
`--list-langs`. A indisponibilidade do Tesseract ou do idioma é registrada no
resultado sem interromper páginas que já possuam texto nativo suficiente.

## Falhas e repetição

Resultados `processed` com o mesmo SHA-256 são reutilizados e têm sua projeção
de pesquisa confirmada. Resultados falhos não são cache válido e podem ser
tentados novamente. Se a indexação falhar, o resultado é marcado como
`failed`, o diagnóstico é persistido e é feita uma tentativa compensatória de
remoção do índice textual.

## Remoção

A remoção retira, de forma coordenada, arquivo físico, JSON, catálogo, páginas,
FTS e estado de manutenção da pesquisa. Arquivos são primeiro movidos para
nomes temporários; uma falha no SQLite restaura os arquivos.

Evidências não são apagadas. Elas preservam o trecho e os dados históricos,
mas a fonte passa a ser reportada como indisponível.

# Lacunas das Fontes Normativas do RSC

## Critério

Uma lacuna é marcada como bloqueadora quando impede confirmar conteúdo,
autoridade, vigência ou rastreabilidade necessários à modelagem normativa.
“Não bloqueadora” significa apenas que outras atividades documentais podem
prosseguir; não autoriza implementar a regra ausente.

| ID | Descrição | Impacto potencial | Evidência da lacuna | Ação recomendada | Bloqueia |
|---|---|---|---|---|---|
| GAP-001 | Legislação federal aplicável não disponível | Não é possível estabelecer base legal, escopo pessoal ou conceitos oficiais | busca em todos os arquivos versionados não encontrou ato primário; inventário, grupo A | fornecer cópia oficial e metadados de publicação | sim |
| GAP-002 | Ato regulamentar federal e respectivos anexos não disponíveis | Impede confirmar requisitos, critérios, unidades, pontos e condições | `official_criteria.py:1,15,48,102` menciona “Anexos I a VI”, mas nenhum anexo está no repositório | fornecer ato completo e todos os anexos, preferencialmente com paginação estável | sim |
| GAP-003 | Regulamento institucional da UNIPAMPA não disponível | Impede identificar adaptações locais, autoridades, procedimentos e vigência institucional | nenhum PDF, regulamento ou ato institucional foi localizado | fornecer regulamento vigente e versões históricas aplicáveis | sim |
| GAP-004 | Editais ou orientações institucionais não disponíveis | Fluxos, prazos, documentos exigidos e competência decisória não podem ser validados | nenhum edital ou orientação foi localizado | fornecer editais e orientações por edição/processo | sim para fluxo institucional |
| GAP-005 | Formulários oficiais não disponíveis | Campos obrigatórios e declarações operacionais permanecem desconhecidos | nenhum formulário versionado foi localizado | fornecer modelos oficiais, indicando versão e vigência | não para inventário; sim para operação |
| GAP-006 | Planilha oficial de pontuação não disponível | Não é possível confrontar fórmulas, unidades, limites ou arredondamentos | nenhuma planilha foi localizada; valores existem apenas em código e testes | fornecer planilha original e ato associado | sim |
| GAP-007 | Proveniência do catálogo executável não demonstrada | Os 6 requisitos, 55 critérios e valores não podem ser tratados como oficiais | `official_criteria.py:15-168`; `test_domain_foundation.py:34-95` | construir matriz de rastreabilidade item a item após receber as fontes | sim |
| GAP-008 | Versão e vigência normativa não confirmadas | Resultados não podem ser reproduzidos para uma data de referência | ADR-030, linhas 7–21; `RSC_DOMAIN_MODEL.md:528,778-796` | identificar versões, início/fim de vigência e regras de transição | sim |
| GAP-009 | Regras presentes somente no código | Fórmulas e validações podem refletir interpretação antiga ou incompleta | `scoring_service.py:21-73`; `validation_service.py:34-242` | revisar cada comportamento contra fonte primária e registrar decisão humana | sim |
| GAP-010 | Regras presentes somente em testes | Contagens e resultados esperados podem cristalizar comportamento sem autoridade | `test_domain_foundation.py:34-95,257-417`; `test_validation_scoring_use_cases.py:1-338` | tratar testes como caracterização, nunca como norma; vincular futuros testes a fontes | sim |
| GAP-011 | Não há exemplos oficiais de processos decididos | Casos limítrofes e interpretação institucional não podem ser confrontados | nenhum exemplo de processo foi localizado | fornecer processos anonimizados e decisões, com autorização adequada | não para catálogo; relevante para validação |
| GAP-012 | Datas de publicação e vigência ausentes em todos os materiais catalogados | Não é possível selecionar normativa aplicável temporalmente | todos os registros em `normative_sources.json` possuem datas normativas `null` | validação humana e obtenção dos metadados oficiais | sim |

## Divergências ainda não verificáveis

Não foi possível comparar formulários, planilhas e regulamentos porque nenhum
desses instrumentos está disponível. Portanto, não se afirma que exista ou
não exista divergência entre eles.

## Conceitos sujeitos a validação humana

- definição oficial e alcance do RSC aplicável;
- requisitos e critérios vigentes;
- unidades de medida e tratamento de frações;
- valores, variantes, limites e eventuais tetos;
- documentos comprobatórios exigidos;
- condições de exclusão ou acumulação;
- arredondamentos e precisão;
- autoridade competente e efeitos da decisão;
- vigência, transição entre versões e tratamento histórico;
- adaptações e procedimentos específicos da UNIPAMPA.

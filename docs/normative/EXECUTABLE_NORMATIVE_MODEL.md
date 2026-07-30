# Modelo Normativo Executável

## 1. Objetivo

O Modelo Normativo Executável representa, de forma declarativa, as partes
computáveis dos critérios do Decreto nº 13.048/2026. Ele não calcula pontuação,
não decide enquadramento e não substitui o texto oficial.

As únicas fontes utilizadas são os seis datasets documentais do decreto. Código,
pipeline e software legado não são fontes deste modelo.

## 2. Arquitetura

```text
Decreto estruturado
├── artigos
├── requisitos
├── critérios
├── tabelas
├── documentos aceitos
└── rastreabilidade
        ↓
criterion_execution_rules.json
        ↓
execution_rules_manifest.json
        ↓
futuro consumidor, fora deste contrato
```

Cada regra conserva o identificador do critério e aponta para requisito, artigo,
anexo, tabela e documentos aceitos. Valores e textos permanecem nas fontes; o
modelo registra referências, tipos e fatos necessários, sem duplicar autoridade
normativa.

## 3. Princípios

- somente leitura;
- uma regra por critério;
- IDs estáveis e únicos;
- nenhuma condição criada por inferência;
- texto não suficientemente estruturável permanece `CUSTOM_TEXT`;
- ausência normativa permanece `UNSPECIFIED`;
- seleção de variante nunca é realizada pelo modelo;
- nenhuma contagem, conversão temporal ou soma é executada;
- toda regra aponta para sua origem jurídica.

## 4. Fronteira entre modelo e motor

O modelo declara:

- qual unidade é contada;
- qual regra temporal está expressa;
- quais variantes existem;
- quais fatos seriam necessários;
- quais regras gerais de agregação e sobreposição incidem;
- onde está o texto que exige apreciação;
- qual é o grau de computabilidade.

Um futuro motor seria responsável por receber fatos validados e aplicar regras.
Ele não existe nesta Sprint. O modelo também não verifica documentos, interpreta
expressões qualitativas ou decide se uma atividade corresponde a um critério.

## 5. Regra documental geral

O art. 4º declara dez tipos documentais válidos para comprovação dos critérios
dos Anexos I a VI. Os datasets não relacionam tipos específicos a critérios
individuais. Por isso cada regra referencia o perfil geral
`DEC13048-DOCUMENT-PROFILE-ART4`, sem inventar especializações.

## 6. Regras transversais

O art. 5º, §2º declara caráter cumulativo da pontuação. O §3º declara que a mesma
atividade só pode ser considerada uma vez e veda utilização simultânea em mais
de um critério. O modelo registra:

- `aggregation_rule = SUM`;
- `overlap_rule = FORBIDDEN`.

Esses valores descrevem o texto, mas não efetuam soma nem resolvem sobreposição.
O próprio §3º reserva o enquadramento sobreposto à avaliação fundamentada da
comissão.

## 7. Limitações

- condições qualitativas continuam dependentes do texto;
- os datasets não fornecem fatos ou quantidades;
- não há seleção automática de titular ou substituto;
- não há modelo de conversão de períodos;
- os textos apresentam sinais de corrupção de codificação;
- o ato referido no art. 4º, parágrafo único, VII não está enumerado;
- não existe cálculo, score, ranking, elegibilidade ou resultado.

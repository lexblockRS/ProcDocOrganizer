# Blueprint do Pipeline de Reconstrução Funcional

## 1. Objetivo

O pipeline de reconstrução funcional transforma evidências documentais em uma
representação canônica, rastreável e auditável da trajetória funcional de uma
pessoa.

Seu objetivo é reconstruir fatos: quem exerceu determinada atividade, em qual
contexto, durante qual período e com fundamento em quais fontes. O pipeline não
interpreta normas, não atribui pontuação, não reconhece direitos e não decide
efeitos administrativos ou jurídicos. Essas interpretações pertencem aos
consumidores da trajetória já reconstruída.

## 2. Pipeline completo

```text
Documento
    ↓
Evidence
    ↓
FunctionalAssignmentEvidence
    ↓
FunctionalAssignmentNormalizer
    ↓
IdentityResolver
    ↓
FunctionalActivityResolver
    ↓
ContinuityResolver
    ↓
FunctionalExercise
    ↓
CareerTimeline
```

- **Documento:** fonte original que registra um ato, uma declaração ou um
  acontecimento administrativo.
- **Evidence:** afirmação extraída da fonte, mantendo referência precisa ao
  documento que a sustenta.
- **FunctionalAssignmentEvidence:** recorte factual que reúne os elementos de
  uma possível atribuição funcional, ainda conforme a linguagem documental.
- **FunctionalAssignmentNormalizer:** reduz variações sintáticas e, quando
  houver correspondência segura, semânticas, sem mudar o significado da
  evidência.
- **IdentityResolver:** determina a identidade funcional à qual cada evidência
  se refere, sem decidir a atividade, as datas ou a continuidade.
- **FunctionalActivityResolver:** relaciona a atribuição documentada a uma
  atividade da taxonomia funcional, quando houver sustentação suficiente.
- **ContinuityResolver:** avalia como evidências de mesma identidade e atividade
  se relacionam no tempo, distinguindo continuidade, interrupção, sobreposição
  e ausência de informação.
- **FunctionalExercise:** fato profissional reconstruído, com pessoa, atividade,
  contexto, período, fundamentos e incertezas preservados.
- **CareerTimeline:** visão cronológica dos exercícios funcionais reconstruídos,
  sem interpretação normativa.

Cada etapa acrescenta uma decisão conceitual delimitada e preserva as
informações recebidas. Etapas posteriores não reescrevem decisões que pertencem
às anteriores; quando detectam conflito ou insuficiência, tornam essa condição
visível.

## 3. Componentes

### 3.1 Documento

#### Objetivo

Preservar a fonte documental original da qual podem ser extraídas afirmações
sobre acontecimentos administrativos.

#### Entradas

Documento obtido de uma origem identificável, acompanhado dos metadados
disponíveis sobre procedência, tipo, emissão e integridade.

#### Saídas

Fonte disponível para consulta e para produção de evidências rastreáveis.

#### Responsabilidades

Manter conteúdo, contexto documental, procedência e referências que permitam
localizar os trechos relevantes.

#### O que pode fazer

Ser armazenado, indexado, submetido a OCR e relacionado a evidências, sem perda
do original.

#### O que nunca deve fazer

Representar por si só um exercício funcional, ser alterado pela reconstrução ou
receber interpretação normativa dentro do pipeline.

#### Invariantes preservados

Integridade da fonte, procedência, conteúdo original e possibilidade de
verificação humana.

#### Dependências

Origem documental e mecanismos externos de aquisição, preservação ou leitura.

#### Consumidores

Produção de `Evidence`, auditoria e consulta humana.

### 3.2 Evidence

#### Objetivo

Representar uma afirmação documental delimitada e vinculada à fonte que a
sustenta.

#### Entradas

Documento e localização verificável do conteúdo relevante.

#### Saídas

Afirmação rastreável, acompanhada de seu contexto, origem e eventuais limites
de qualidade ou confiança.

#### Responsabilidades

Responder ao que o documento afirma, sem converter automaticamente essa
afirmação em fato profissional consolidado.

#### O que pode fazer

Registrar texto, metadados, localização na fonte, método de extração,
ambiguidades e necessidade de revisão.

#### O que nunca deve fazer

Modificar o documento, preencher lacunas como fatos, resolver identidade,
classificar atividade, consolidar períodos ou aplicar norma.

#### Invariantes preservados

Rastreabilidade até a fonte, fidelidade à afirmação documental e visibilidade
da incerteza.

#### Dependências

Documento e processo rastreável de extração ou registro.

#### Consumidores

Produção de `FunctionalAssignmentEvidence`, revisão humana e auditoria.

### 3.3 FunctionalAssignmentEvidence

#### Objetivo

Representar os elementos documentados de uma possível atribuição funcional,
antes de sua reconstrução como exercício.

#### Entradas

Uma ou mais afirmações documentais pertinentes, com referências às fontes.

#### Saídas

Evidência de atribuição funcional em estado bruto, com pessoa indicada,
denominações administrativas, organização, unidade, referências e datas
expressamente disponíveis.

#### Responsabilidades

Reunir de modo estruturado somente as informações sustentadas pelas evidências
de origem e manter seus valores documentais.

#### O que pode fazer

Registrar dados completos, parciais, divergentes ou ausentes e explicitar a
condição de cada informação.

#### O que nunca deve fazer

Inferir identidade funcional, atividade canônica, continuidade, datas não
documentadas ou efeitos normativos.

#### Invariantes preservados

Vínculo com todas as evidências de origem, fidelidade aos valores extraídos,
imutabilidade da evidência documental e visibilidade de lacunas.

#### Dependências

`Evidence` e critérios de seleção factual da atribuição funcional.

#### Consumidores

`FunctionalAssignmentNormalizer`, auditoria e revisão humana.

### 3.4 FunctionalAssignmentNormalizer

#### Objetivo

Produzir uma representação comparável da evidência de atribuição funcional,
preservando integralmente seu significado administrativo.

#### Entradas

`FunctionalAssignmentEvidence` em estado bruto e vocabulários de normalização
aprovados.

#### Saídas

Nova representação normalizada, equivalente à entrada quanto a identidade,
pessoa indicada, fonte, datas e significado administrativo.

#### Responsabilidades

Padronizar representações, uniformizar nomenclaturas, expandir abreviações
conhecidas, remover variações puramente sintáticas e preparar comparações
posteriores.

#### O que pode fazer

Aplicar normalização sintática e correspondências semânticas conhecidas,
seguras, versionadas e explicáveis.

#### O que nunca deve fazer

Alterar a entrada, corrigir OCR, interpretar documentos, modificar pessoa,
fonte ou datas, resolver identidade, atividade ou continuidade, unir
evidências, criar exercício ou aplicar norma.

#### Invariantes preservados

Identidade documental, pessoa indicada, referências de origem, datas,
significado administrativo, imutabilidade da entrada e rastreabilidade das
transformações.

#### Dependências

`FunctionalAssignmentEvidence` bruta, regras determinísticas e vocabulários
controlados de normalização.

#### Consumidores

`IdentityResolver`, auditoria e revisão de normalização.

### 3.5 IdentityResolver

#### Objetivo

Determinar, de forma rastreável, quais evidências normalizadas se referem à
mesma identidade funcional.

#### Entradas

Evidências de atribuição normalizadas, identificadores disponíveis, contexto
institucional e critérios de identidade aprovados.

#### Saídas

Associação entre evidências e uma identidade funcional resolvida, ou resultado
explícito de conflito, ambiguidade ou insuficiência.

#### Responsabilidades

Comparar atributos pertinentes à identidade, registrar critérios aplicados,
manter evidências concorrentes visíveis e impedir fusões sem sustentação.

#### O que pode fazer

Confirmar equivalência, distinguir identidades, manter candidatos em aberto e
indicar necessidade de revisão conforme critérios determinísticos.

#### O que nunca deve fazer

Alterar valores normalizados, escolher atividade funcional, modificar datas,
resolver continuidade, criar exercício, suprir dado ausente ou aplicar norma.

#### Invariantes preservados

Conteúdo das evidências, atividade ainda não resolvida, datas, referências de
origem, explicabilidade da associação e visibilidade da incerteza.

#### Dependências

Evidências normalizadas, critérios institucionais de identidade e decisões a
serem formalizadas pelo ADR-005.

#### Consumidores

`FunctionalActivityResolver`, auditoria e revisão de identidade.

### 3.6 FunctionalActivityResolver

#### Objetivo

Relacionar a atribuição documentada à atividade funcional canônica que melhor
representa sua natureza, quando as evidências forem suficientes.

#### Entradas

Evidências normalizadas com identidade resolvida, contexto administrativo,
responsabilidades documentadas, taxonomia funcional e critérios de
correspondência.

#### Saídas

Atividade funcional canônica associada às evidências, ou resultado explícito
de ambiguidade, conflito ou ausência de classificação segura.

#### Responsabilidades

Avaliar significado e responsabilidades sustentadas, aplicar critérios
taxonômicos, registrar a justificativa e preservar a nomenclatura
institucional original.

#### O que pode fazer

Relacionar denominações distintas à mesma atividade, distinguir denominações
iguais quando o conteúdo diferir e manter classificações candidatas sem forçar
uma decisão.

#### O que nunca deve fazer

Alterar identidade, datas, fontes ou conteúdo das evidências, resolver
continuidade, atribuir pontuação, escolher categoria normativa ou confundir
semelhança lexical com equivalência funcional.

#### Invariantes preservados

Identidade resolvida, período documentado, contexto institucional,
rastreabilidade, independência normativa e visibilidade da incerteza
taxonômica.

#### Dependências

Resultado do `IdentityResolver`, Taxonomia de Atividades Funcionais, critérios
de correspondência e decisões a serem formalizadas pelo ADR-006.

#### Consumidores

`ContinuityResolver`, auditoria e revisão taxonômica.

### 3.7 ContinuityResolver

#### Objetivo

Determinar a relação temporal entre evidências compatíveis de uma mesma
identidade e atividade, delimitando exercícios sem inventar períodos.

#### Entradas

Evidências com identidade e atividade resolvidas, datas documentadas,
referências administrativas e critérios temporais aprovados.

#### Saídas

Segmentos temporais sustentados e relações explícitas de continuidade,
interrupção, sobreposição, sucessão, revogação documentada ou incerteza.

#### Responsabilidades

Ordenar ocorrências, avaliar limites temporais, evitar dupla contagem factual,
registrar as razões de consolidação ou separação e preservar conflitos.

#### O que pode fazer

Consolidar evidências complementares em um mesmo período quando os critérios
forem satisfeitos e manter períodos separados ou indeterminados quando não
forem.

#### O que nunca deve fazer

Alterar identidade ou atividade, modificar datas documentadas, presumir
continuidade pelo silêncio documental, apagar sobreposições, redefinir fontes
ou aplicar efeitos normativos.

#### Invariantes preservados

Identidade, atividade, datas documentadas, referências de origem, distinção
entre data conhecida e limite inferido, e explicabilidade temporal.

#### Dependências

Resultados de identidade e atividade, evidências temporais, regras
determinísticas e decisões a serem formalizadas pelo ADR-007.

#### Consumidores

Produção de `FunctionalExercise`, auditoria e revisão temporal.

### 3.8 FunctionalExercise

#### Objetivo

Representar o fato profissional reconstruído de que uma pessoa exerceu uma
atividade funcional em contexto e período determinados.

#### Entradas

Identidade resolvida, atividade canônica, resultado de continuidade, contexto
institucional e conjunto completo de evidências sustentadoras.

#### Saídas

Fato funcional consolidado, rastreável e independente de qualquer avaliação
normativa.

#### Responsabilidades

Preservar pessoa, atividade, contexto, limites temporais, fundamentos,
incertezas e cadeia de decisões que sustentam o fato.

#### O que pode fazer

Expressar períodos abertos, limites desconhecidos, sobreposições legítimas e
grau de resolução factual conforme as evidências.

#### O que nunca deve fazer

Substituir evidências, ocultar conflitos, alterar documentos, incorporar
pontuação, mérito, enquadramento ou efeito de uma norma.

#### Invariantes preservados

Proveniência completa, separação entre fato e norma, identidade e atividade
resolvidas, fidelidade temporal e auditabilidade.

#### Dependências

Resultados dos três resolvedores e evidências documentais preservadas.

#### Consumidores

`CareerTimeline`, revisão humana, auditoria e modelos consumidores.

### 3.9 CareerTimeline

#### Objetivo

Organizar cronologicamente a trajetória funcional reconstruída de uma pessoa
como projeção derivada e reconstruível dos exercícios funcionais.

#### Entradas

Conjunto de `FunctionalExercise` atribuídos à mesma pessoa.

#### Saídas

Visão ordenada e consolidada dos exercícios, incluindo simultaneidades,
intervalos, lacunas e incertezas. Essa visão é uma projeção e não constitui a
fonte primária de verdade da trajetória.

#### Responsabilidades

Oferecer uma representação factual reutilizável, preservar cada exercício e
expor relações cronológicas sem atribuir significado normativo. A projeção deve
poder ser reconstruída deterministicamente a partir dos `FunctionalExercise`,
que constituem a representação canônica da trajetória funcional reconstruída.
Alterações nas evidências podem produzir novos exercícios e, a partir deles,
uma nova projeção temporal rastreável.

#### O que pode fazer

Ordenar, agrupar para apresentação, destacar sobreposições e lacunas e
disponibilizar recortes factuais a consumidores.

#### O que nunca deve fazer

Reescrever exercícios, preencher lacunas, eliminar simultaneidades, selecionar
fatos por conveniência normativa, pontuar ou reconhecer direitos. Consumidores
normativos não podem escrever na `CareerTimeline` nem utilizá-la para modificar
os `FunctionalExercise` dos quais ela deriva.

#### Invariantes preservados

Integridade dos exercícios, rastreabilidade até os documentos, independência
normativa, coexistência de fatos simultâneos e visibilidade da incerteza.

#### Dependências

`FunctionalExercise` reconstruídos e critérios neutros de ordenação.

#### Consumidores

RSC, progressão, promoção, aposentadoria, auditoria, gestão de pessoas e outros
modelos institucionais.

## 4. Contratos conceituais

Os contratos abaixo descrevem informação e responsabilidade. Não prescrevem
estruturas de software, mecanismo de armazenamento ou forma de chamada.

### Documento para Evidence

Entra uma fonte preservada e localizável. Sai uma afirmação delimitada que
indica o conteúdo observado, sua posição na fonte, o método de obtenção e as
incertezas conhecidas. A saída não afirma que o conteúdo já constitui fato
funcional.

### Evidence para FunctionalAssignmentEvidence

Entram afirmações pertinentes a uma atribuição funcional. Sai um recorte
estruturado contendo apenas pessoa indicada, denominação, papel, organização,
unidade, referências e datas sustentadas, com cada valor ligado às evidências
que o originaram.

### FunctionalAssignmentEvidence para FunctionalAssignmentNormalizer

Entra uma evidência de atribuição em estado bruto. Sai uma nova representação
normalizada, com registro das transformações aplicadas. Pessoa indicada, fonte,
datas e significado administrativo permanecem equivalentes.

### FunctionalAssignmentNormalizer para IdentityResolver

Entram representações comparáveis e suas versões originais rastreáveis. Sai a
associação justificada a uma identidade funcional, ou a indicação explícita de
que a identidade permanece ambígua, conflitante ou não resolvida.

### IdentityResolver para FunctionalActivityResolver

Entram evidências vinculadas a uma identidade, sem modificação de suas
atividades ou períodos. Sai uma associação justificada a uma atividade
canônica da taxonomia, ou uma classificação não resolvida com suas alternativas
e razões.

### FunctionalActivityResolver para ContinuityResolver

Entram evidências que compartilham identidade e atividade resolvidas, mantendo
datas e referências documentais. Saem relações temporais e segmentos
sustentados, com distinção explícita entre limites documentados, derivados por
regra e desconhecidos.

### ContinuityResolver para FunctionalExercise

Entram agrupamentos temporais justificados e todas as evidências relacionadas.
Sai um fato profissional que identifica pessoa, atividade, contexto, período,
fontes, decisões e incertezas. Nenhuma informação normativa integra essa saída.

### FunctionalExercise para CareerTimeline

Entram fatos profissionais preservados individualmente. Sai uma organização
cronológica que mantém exercícios simultâneos, lacunas e conflitos visíveis e
permite recuperar a cadeia completa até cada documento.

### CareerTimeline para consumidores

Entra uma trajetória factual independente de finalidade. Saem visões ou
seleções solicitadas pelo consumidor, sem que esse consumo altere a trajetória.
Pontuação, enquadramento e efeito jurídico são resultados externos ao pipeline.

## 5. Invariantes globais

- A rastreabilidade nunca pode ser perdida: todo fato deve alcançar as
  evidências e os documentos que o sustentam.
- Evidências e documentos nunca são modificados pela reconstrução.
- Cada transformação produz um resultado novo ou uma decisão registrada, sem
  apagar sua entrada.
- Fatos reconstruídos são independentes de normas, regulamentos, pontuações e
  finalidades consumidoras.
- Identidade não altera atividade.
- Atividade não altera identidade nem datas.
- Continuidade não altera identidade, atividade ou datas documentadas.
- Normalização não cria equivalência de identidade, atividade ou período.
- Nenhuma etapa preenche ausência, ambiguidade ou conflito como se fosse fato.
- Incerteza, divergência, insuficiência e hipótese permanecem distinguíveis de
  informação confirmada.
- Toda decisão cognitiva informa os critérios, os insumos e a versão das
  referências utilizadas.
- O mesmo conjunto de entradas, critérios e versões produz o mesmo resultado.
- Denominações e contextos institucionais originais permanecem disponíveis
  mesmo após a adoção de representações canônicas.
- Limites temporais documentados nunca são substituídos por limites inferidos;
  a natureza de cada limite permanece explícita.
- Evidências conflitantes não são descartadas por conveniência de
  consolidação.
- Sobreposição não implica automaticamente duplicidade, e lacuna documental
  não implica automaticamente interrupção ou continuidade.
- Um resultado não resolvido é válido e preferível a uma decisão sem
  sustentação suficiente.
- A evolução de vocabulários, taxonomias ou critérios não reescreve
  silenciosamente resultados históricos; qualquer reconstrução posterior deve
  ser identificável e reproduzível.
- Consumidores podem interpretar a trajetória, mas nunca alterar a fonte
  factual compartilhada.
- `FunctionalExercise` constitui a representação canônica da trajetória
  funcional reconstruída; `CareerTimeline` é uma projeção derivada,
  deterministicamente reconstruível e nunca modifica sua fonte canônica.
- Falha ou incerteza em uma etapa não autoriza etapa posterior a assumir a
  responsabilidade daquela decisão.

## 6. Componentes cognitivos

Componentes cognitivos são os que transformam a representação do conhecimento
ou decidem relações entre informações. No pipeline, são o
`FunctionalAssignmentNormalizer`, o `IdentityResolver`, o
`FunctionalActivityResolver` e o `ContinuityResolver`.

### Normalizer

Reduz ruído de representação para tornar evidências comparáveis. Seu trabalho
cognitivo é limitado à equivalência sintática e às correspondências semânticas
previamente conhecidas e seguras. Não decide o que as evidências representam
em termos de pessoa, atividade ou período.

### IdentityResolver

Decide se referências documentais correspondem à mesma identidade funcional.
Considera somente atributos pertinentes à identidade e produz confirmação,
distinção ou resultado não resolvido. A decisão de identidade permanece
separada do conteúdo funcional e temporal.

### FunctionalActivityResolver

Decide qual conceito da taxonomia descreve a natureza da atribuição
documentada. Considera responsabilidades e contexto sustentados, não apenas
semelhança entre títulos. Quando não há base suficiente, preserva candidatas ou
mantém a atividade não resolvida.

### ContinuityResolver

Decide como ocorrências compatíveis se relacionam no tempo e se sustentam um ou
mais exercícios. Distingue datas expressas, limites derivados, intervalos,
sobreposições e ausência documental sem transformar silêncio em certeza.

Esses componentes permanecem determinísticos porque operam com regras
explícitas, critérios controlados, entradas delimitadas e referências
versionadas. Permanecem auditáveis porque cada resultado conserva os insumos,
as regras aplicadas, as justificativas, as alternativas rejeitadas quando
relevantes e a cadeia até a fonte. A possibilidade de produzir um resultado
não resolvido impede que heurísticas opacas sejam usadas para fabricar certeza.

## 7. Papel da IA

A inteligência artificial pode atuar de modo assistivo antes ou ao redor das
decisões determinísticas. Usos admissíveis incluem:

- OCR e melhoria da legibilidade para apoiar a extração;
- extração textual e indicação de trechos potencialmente relevantes;
- reconhecimento de pessoas, organizações, unidades, datas e nomenclaturas;
- sugestão de expansão de siglas e possíveis correspondências terminológicas;
- sugestão de atividades candidatas da taxonomia;
- detecção de possíveis conflitos, lacunas ou documentos relacionados;
- priorização de itens para revisão humana.

Toda saída de IA deve ser tratada como proposta ou dado extraído sujeito a
verificação, ligada à fonte que a motivou e acompanhada de sua condição de
incerteza. IA não cria evidência por autoridade própria.

A IA nunca substitui:

- as regras aprovadas de normalização;
- a decisão determinística de identidade;
- a correspondência auditável com a taxonomia funcional;
- as regras de continuidade, interrupção, sobreposição ou revogação;
- a formação final do fato reconstruído;
- a distinção entre conteúdo documentado e inferência;
- a revisão exigida para casos ambíguos;
- qualquer interpretação normativa externa.

Uma sugestão de IA somente pode influenciar o resultado após ser confirmada por
critério determinístico ou revisão humana registrada. Modelo, probabilidade ou
similaridade não constituem justificativa factual suficiente.

## 8. Exemplo ponta a ponta

Considere a fictícia **Portaria nº 42/2021, de 15 de março de 2021**, emitida
pelo Instituto Federal do Pampa. O texto declara: “Designar Maria de Souza,
matrícula 12345, para exercer a Coordenação Acadêmica do Campus de Alegrete, a
contar de 1º de abril de 2021”. Uma segunda portaria fictícia, nº 18/2022,
dispensa Maria da mesma função a contar de 1º de fevereiro de 2022.

O **Documento** preserva cada portaria, seus metadados e seu conteúdo original.
O OCR pode auxiliar a leitura, mas a imagem ou arquivo de origem continua sendo
a referência verificável.

Uma **Evidence** registra a afirmação de designação, indicando a página e o
trecho da Portaria nº 42/2021. Outra registra a afirmação de dispensa e sua
localização na Portaria nº 18/2022. Cada uma expressa somente o que sua fonte
afirma.

A **FunctionalAssignmentEvidence** da designação reúne, conforme documentado:
Maria de Souza, matrícula 12345, “Coordenação Acadêmica”, “Campus de Alegrete”,
referência à Portaria nº 42/2021 e início em 1º de abril de 2021. A evidência da
dispensa reúne a mesma identificação funcional, a mesma denominação e o limite
de 1º de fevereiro de 2022. Nenhuma delas ainda é um exercício consolidado.

O **FunctionalAssignmentNormalizer** padroniza as formas conhecidas. Por
exemplo, representa consistentemente “Campus de Alegrete” como “IF Pampa —
Campus Alegrete” somente se essa correspondência constar de vocabulário
aprovado. Preserva os textos originais, a matrícula, as referências e as datas.

O **IdentityResolver** verifica, pelos critérios aprovados, que as duas
evidências se referem à mesma Maria de Souza, apoiado especialmente pela
matrícula 12345 e pelo contexto institucional. Essa decisão não diz qual
atividade Maria exerceu.

O **FunctionalActivityResolver** considera a denominação “Coordenação
Acadêmica” e as responsabilidades sustentadas pelas fontes auxiliares
admissíveis. Havendo correspondência determinística na taxonomia, relaciona as
evidências à atividade canônica “coordenação acadêmica”. A denominação original
continua preservada. Se o título não fosse suficiente para demonstrar a
natureza da atividade, a classificação permaneceria não resolvida.

O **ContinuityResolver** relaciona a designação e a dispensa como limites do
mesmo período, pois compartilham identidade e atividade e as referências
administrativas satisfazem os critérios de continuidade. O início permanece 1º
de abril de 2021. A dispensa “a contar de 1º de fevereiro de 2022” estabelece o
limite conforme a convenção temporal que será definida pelo ADR-007; o pipeline
registra a redação documental e não escolhe silenciosamente se o último dia de
exercício foi 31 de janeiro ou 1º de fevereiro.

O **FunctionalExercise** resultante afirma que Maria de Souza exerceu a
atividade canônica de coordenação acadêmica no IF Pampa — Campus Alegrete,
desde 1º de abril de 2021 até o limite determinado pela portaria de dispensa.
Ele referencia ambas as evidências, os dois documentos, as normalizações e as
decisões de identidade, atividade e continuidade. Não contém pontos de RSC nem
conclusão sobre progressão.

Por fim, a **CareerTimeline** posiciona esse exercício entre os demais fatos
funcionais de Maria. Se houver outro exercício simultâneo, ambos permanecem
visíveis. Um consumidor de RSC ou aposentadoria poderá interpretar o período,
mas não poderá reescrever o fato compartilhado.

## 9. Pontos de extensão

O pipeline expõe uma trajetória factual comum. Novos consumidores reutilizam
`FunctionalExercise` e `CareerTimeline`, aplicando suas próprias regras depois
da reconstrução:

- **RSC:** seleciona e avalia exercícios conforme critérios e períodos do
  regulamento aplicável.
- **Progressão:** relaciona fatos funcionais aos requisitos da carreira, sem
  alterar os fatos.
- **Promoção:** aplica critérios próprios sobre atividades e períodos já
  reconstruídos.
- **Aposentadoria:** interpreta períodos e naturezas de exercício para a
  finalidade previdenciária correspondente.
- **Auditoria:** percorre a cadeia entre conclusão, exercício, decisões,
  evidências e documentos.
- **Gestão de pessoas:** apresenta trajetórias e identifica lacunas que exigem
  documentação adicional.
- **Outras instituições:** fornecem seus vocabulários institucionais e
  correspondências aprovadas, reutilizando a mesma taxonomia e preservando seus
  contextos originais.

Também são extensíveis os recursos auxiliares de extração, os vocabulários de
normalização, os critérios institucionais de identidade e a taxonomia. Essas
extensões devem ser versionadas e não podem ampliar a responsabilidade de uma
etapa nem introduzir dependência de um consumidor normativo no núcleo factual.

Novas apresentações, consultas e exportações podem consumir a
`CareerTimeline`. Novos mecanismos de revisão podem consumir resultados não
resolvidos. Em ambos os casos, a extensão ocorre nas bordas do pipeline, sem
alterar documentos, evidências ou fatos consolidados.

## 10. Próximas decisões arquiteturais

Este blueprint define fronteiras, fluxo e invariantes, mas não fixa os critérios
detalhados dos três resolvedores. Ele prepara as seguintes decisões:

- **ADR-005 — Identity Resolution:** critérios de equivalência, conflito,
  ambiguidade, identificadores e revisão de identidade;
- **ADR-006 — Functional Activity Resolution:** critérios de correspondência
  taxonômica, granularidade, candidatas e tratamento de classificação
  insuficiente;
- **ADR-007 — Continuity Resolution:** regras de limites temporais,
  continuidade, interrupção, sobreposição, revogação e consolidação.

Esses ADRs deverão respeitar a ordem do pipeline, a separação estrita de
responsabilidades e todos os invariantes globais aqui registrados. Decisões de
implementação, persistência e contratos de software permanecem fora do escopo
deste blueprint.

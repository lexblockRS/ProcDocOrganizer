# ADR-006 — Identity Resolution

## 1. Título e status

**Título:** ADR-006 — Identity Resolution

**Status:** Proposed

**Data:** 2026-07-25

Esta decisão define a resolução de identidade entre evidências documentais no
pipeline de reconstrução funcional. Deve ser interpretada conforme a
[Visão do Domínio](../domain-vision.md), o
[ADR-005](ADR-005-identity-profile-and-evidence-discovery.md) e o
[Blueprint do Pipeline de Reconstrução Funcional](../functional-reconstruction-pipeline.md).

## 2. Contexto

`Evidence Discovery` localiza evidências candidatas potencialmente relacionadas
a um `Identity Profile`. A confiança atribuída durante essa descoberta informa
quão plausível é a relação entre uma ocorrência encontrada e o perfil
pesquisado. Ela não confirma que todas as evidências encontradas se referem à
mesma pessoa.

O acervo pode conter:

- homônimos;
- nomes abreviados ou incompletos;
- alterações de nome ao longo do tempo;
- grafias divergentes;
- SIAPE presente em apenas alguns documentos;
- CPF parcial ou mascarado;
- matrículas institucionais distintas;
- identificadores conflitantes;
- documentos sem identificadores únicos;
- uma pessoa com múltiplos vínculos institucionais;
- várias pessoas mencionadas no mesmo documento.

Por isso, o `IdentityResolver` precisa distinguir evidências que representam a
mesma pessoa, pessoas diferentes, identidades possivelmente equivalentes,
identidades contraditórias e identidades ainda não resolvidas.

A resolução não pode ser reduzida a uma comparação binária nem à repetição da
confiança da descoberta. Ela precisa preservar sinais favoráveis, sinais
contrários, contradições, lacunas, proveniência e decisões humanas, sem
transformar incerteza em certeza.

## 3. Decisão arquitetural

`Identity Resolution` é um componente independente do pipeline. Sua
responsabilidade exclusiva é avaliar a equivalência de identidade entre
evidências candidatas já descobertas e expressar uma decisão conceitual
auditável.

O `IdentityResolver`:

- recebe evidências candidatas já descobertas e, no pipeline principal,
  representações preparadas para comparação;
- avalia agrupamentos e distinções de identidade;
- preserva os atributos e fundamentos examinados;
- produz um dos estados conceituais definidos neste ADR;
- admite que a identidade permaneça ambígua ou não resolvida.

O componente não localiza documentos, não executa `Evidence Discovery`, não
classifica atividades, não altera datas, não resolve continuidade temporal,
não aplica regras de RSC e não modifica documentos nem evidências.

Uma decisão de identidade relaciona evidências; ela não substitui as fontes,
não corrige seu conteúdo e não afirma qual atividade foi exercida.

## 4. Entradas conceituais

O `IdentityResolver` pode considerar, entre outros elementos:

- nome;
- nomes alternativos ou anteriormente utilizados;
- SIAPE;
- CPF integral, parcial ou mascarado;
- matrícula institucional;
- instituição;
- unidade organizacional;
- cargo;
- período;
- contexto documental;
- proveniência dos identificadores;
- confirmações humanas anteriores;
- critérios institucionais versionados.

Cargo, unidade, instituição e período são elementos contextuais. Podem apoiar
ou enfraquecer uma associação, mas não devem ser convertidos em fatos
funcionais pela resolução de identidade.

Nenhum atributo isolado é universalmente suficiente, salvo quando um critério
institucional explícito, aplicável e versionado determinar sua suficiência no
contexto examinado. Mesmo identificadores normalmente fortes podem conter erro
material, reutilização indevida ou conflito documental, que devem permanecer
visíveis.

Este ADR não define algoritmo, ordem operacional, pesos numéricos ou limiares.
Define quais informações podem fundamentar a decisão e quais limites ela deve
respeitar.

## 5. Resultados possíveis

A resolução deve produzir um estado conceitual que não reduza todos os casos a
verdadeiro ou falso:

### Confirmed Same Identity

Os critérios aplicáveis sustentam que as evidências se referem à mesma pessoa,
sem contradição relevante não resolvida. A confirmação registra quais
elementos e critérios fundamentam a equivalência.

### Confirmed Different Identity

Os critérios aplicáveis sustentam que as evidências se referem a pessoas
distintas. O resultado preserva os elementos que demonstram a distinção e não
descarta semelhanças existentes.

### Probable Same Identity

Os sinais disponíveis favorecem a equivalência, mas são insuficientes para
confirmá-la segundo os critérios vigentes. As evidências podem permanecer como
candidatas relacionadas, sem receber o mesmo efeito de uma identidade
confirmada.

### Contradictory Identity

Existem atributos relevantes incompatíveis ou decisões conflitantes que
impedem uma conclusão coerente sem esclarecimento adicional. A contradição é
parte do resultado e não deve ser corrigida ou descartada silenciosamente.

### Ambiguous Identity

Mais de uma associação permanece plausível e os critérios disponíveis não
distinguem com segurança entre as alternativas. Esse estado é especialmente
relevante para homônimos e documentos com identificação insuficiente.

### Unresolved Identity

As informações disponíveis não permitem confirmar equivalência, diferença,
probabilidade suficiente, contradição determinante ou alternativas claramente
delimitadas. A insuficiência permanece explícita até que novos elementos ou
uma revisão autorizada permitam nova resolução.

Esses estados descrevem a decisão de identidade no momento da resolução. Uma
decisão posterior não apaga a anterior; produz novo resultado rastreável.

## 6. Evidências positivas, negativas e contraditórias

**Evidência positiva de identidade** é um atributo ou relação que, segundo os
critérios aplicáveis, indica possível equivalência. O mesmo SIAPE em documentos
diferentes pode ser um sinal positivo forte, sujeito à proveniência e à
ausência de conflito relevante.

**Evidência negativa de identidade** é um atributo ou relação que indica
possível distinção. Nomes iguais em instituições diferentes ou SIAPEs
diferentes para nomes semelhantes podem constituir sinais negativos, conforme
o contexto e os critérios institucionais.

**Contradição de identidade** ocorre quando atributos relevantes entram em
conflito de forma material. Exemplos incluem o mesmo nome associado a CPFs
incompatíveis ou identificadores que não podem coexistir segundo o critério
aplicável.

O mesmo CPF acompanhado de grafias diferentes do nome pode sustentar
equivalência e, simultaneamente, exigir que a divergência nominal seja
explicada. Uma matrícula histórica substituída por outra pode aparentar
distinção, mas a relação documentada de substituição pode explicar a mudança.

Ausência de identificador não equivale a conflito. Um documento sem SIAPE não
contradiz outro que o contenha. Silêncio documental não prova equivalência nem
diferença e não pode ser tratado como confirmação de um atributo.

Sinais positivos não anulam automaticamente sinais negativos, e sinais
negativos não apagam coincidências relevantes. A decisão deve conservar o
conjunto considerado e explicar como os critérios versionados conduziram ao
estado produzido.

## 7. Homônimos

Nome igual não é prova suficiente de identidade.

O sistema deve preservar homônimos como candidatos distintos enquanto não
existirem critérios suficientes para agrupamento. Semelhança nominal, inclusive
quando exata, não autoriza a união automática de evidências.

O `IdentityResolver` não deve unir evidências apenas por nome, proximidade
ortográfica ou ocorrência no mesmo documento. Instituição, unidade, período e
cargo podem oferecer contexto, mas também não substituem os critérios
necessários à resolução.

Quando duas ou mais pessoas homônimas continuarem plausíveis, o resultado deve
ser `Ambiguous Identity`, `Unresolved Identity` ou outro estado aplicável sem
fusão indevida dos conjuntos candidatos.

## 8. Identificadores divergentes

Identificadores divergentes devem ser avaliados em seu contexto e nunca
corrigidos silenciosamente:

- **Mesmo nome com SIAPEs diferentes:** pode representar pessoas distintas,
  múltiplos vínculos, mudança documentada ou erro material; a divergência
  permanece registrada até que critérios e evidências permitam distingui-la.
- **Mesmo SIAPE com nomes divergentes:** pode refletir variação gráfica,
  alteração de nome, erro documental ou conflito; o identificador comum não
  apaga a divergência nominal.
- **CPF divergente:** constitui conflito relevante quando os valores são
  comparáveis e incompatíveis; CPFs parciais ou mascarados exigem tratamento
  compatível com sua incompletude.
- **Matrícula divergente:** pode indicar pessoas distintas, vínculos diferentes
  ou substituição histórica; a mera diferença não determina universalmente uma
  dessas hipóteses.
- **Identificador historicamente substituído:** exige sustentação da relação
  entre o identificador anterior e o posterior, preservando ambos e seus
  períodos de uso.
- **Erro material em documento:** deve permanecer como conteúdo da fonte. Uma
  retificação oficial ou confirmação autorizada pode fundamentar nova decisão,
  mas não altera retroativamente o documento original.

Contradições devem manter ligação com as evidências e atributos que as
originaram. A resolução pode explicar ou superar uma aparente divergência
segundo critérios explícitos, mas nunca apagar seu histórico.

## 9. Confirmação humana

Usuários autorizados podem confirmar ou rejeitar associações ambíguas,
prováveis, contraditórias ou não resolvidas quando a política aplicável permitir.
A intervenção humana produz uma decisão auditável; não modifica documentos nem
evidências originais.

Toda confirmação ou rejeição humana deve registrar:

- decisão;
- responsável;
- data;
- evidências consideradas;
- justificativa, quando aplicável;
- versão dos critérios;
- proveniência.

A autoridade e o alcance da decisão também devem permanecer verificáveis. Uma
confirmação não autoriza inferir atividades, datas ou continuidade e não
transforma atributos ausentes em conteúdo documental.

Decisões humanas podem ser revistas. A revisão produz nova decisão ligada à
anterior, registra sua razão e preserva integralmente o histórico, inclusive
quando substitui o resultado vigente.

## 10. Proveniência e versionamento

Toda decisão de identidade deve registrar:

- evidências utilizadas;
- atributos comparados;
- proveniência dos atributos;
- critérios aplicados;
- versão dos critérios;
- resultado;
- grau ou estado de confiança;
- decisões humanas relacionadas;
- momento da resolução.

Quando relevante, também devem permanecer visíveis as alternativas avaliadas,
os conflitos encontrados e as limitações das fontes.

Novos critérios, novas evidências ou correções oficialmente reconhecidas não
devem reescrever silenciosamente decisões históricas. Uma nova resolução deve
produzir nova versão ou novo resultado rastreável, relacionado aos anteriores e
capaz de explicar por que o estado vigente mudou.

A reprodução histórica depende da preservação conjunta das entradas, dos
critérios versionados e das decisões humanas então vigentes.

## 11. Relação com Identity Profile

O `Identity Profile` orienta a descoberta de evidências. O `IdentityResolver`
avalia evidências concretas já encontradas e decide relações de identidade entre
elas.

Atributos descobertos podem enriquecer o perfil, desde que cada incorporação
registre sua proveniência, confiança e modo de confirmação. Um valor extraído
de uma associação ambígua não deve tornar-se automaticamente um identificador
confirmado no perfil.

O enriquecimento do perfil não confirma fatos funcionais, e o perfil não
substitui decisões de identidade. Mesmo um atributo confirmado no perfil deve
ser relacionado às evidências concretas conforme os critérios vigentes.

## 12. Relação com Evidence Discovery

`Evidence Discovery` responde:

> Esta evidência pode estar relacionada ao perfil pesquisado?

`Identity Resolution` responde:

> Esta evidência se refere à mesma pessoa das demais evidências?

Confiança da descoberta e confiança da identidade são independentes. A primeira
qualifica a seleção candidata em relação ao perfil; a segunda qualifica a
decisão de equivalência entre evidências.

Uma evidência descoberta com alta confiança pode continuar ambígua na resolução
de identidade. Por exemplo, ela pode corresponder com segurança a um nome
pesquisado, mas o acervo pode conter homônimos sem identificadores suficientes
para distinguir a qual deles a ocorrência se refere.

Da mesma forma, evidências inicialmente encontradas com confiança menor podem
ser confirmadas como pertencentes à mesma identidade quando elementos
posteriores e critérios auditáveis sustentarem essa conclusão.

## 13. Relação com o pipeline

O fluxo conceitual é:

```text
Identity Profile
    ↓
Evidence Discovery
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

O `IdentityResolver` atua depois da normalização porque precisa de
representações comparáveis, sem assumir a responsabilidade de normalizá-las.
Seu resultado determina agrupamentos, distinções ou estados não conclusivos de
identidade.

Ele não modifica conteúdo documental, atividade ou temporalidade. O
`FunctionalActivityResolver` recebe o resultado de identidade sem poder
reescrevê-lo implicitamente; o `ContinuityResolver` também não pode unir
identidades para facilitar uma consolidação temporal.

## 14. Invariantes

- Evidências são imutáveis.
- Documentos são imutáveis.
- Toda decisão preserva rastreabilidade até os documentos e evidências
  considerados.
- Nome igual não implica mesma identidade.
- Ausência de identificador não implica conflito.
- Silêncio documental não prova equivalência nem diferença.
- Conflito não pode ser apagado por conveniência.
- Decisões ambíguas podem permanecer não resolvidas.
- `IdentityResolver` não localiza documentos.
- `IdentityResolver` não altera datas.
- `IdentityResolver` não classifica atividades.
- `IdentityResolver` não resolve continuidade.
- `IdentityResolver` não aplica interpretação normativa.
- Identificadores divergentes não são corrigidos silenciosamente.
- Decisões humanas são auditáveis e revisáveis sem perda do histórico.
- Critérios são explícitos e versionados.
- Resultados históricos não são reescritos silenciosamente.
- Atributos enriquecidos no `Identity Profile` registram proveniência.
- Confiança de descoberta não determina confiança de identidade.
- Falhas posteriores do pipeline não podem alterar decisões de identidade.
- Mudanças posteriores exigem nova resolução rastreável.

## 15. Determinismo e auditabilidade

Para o mesmo conjunto de evidências, atributos, critérios versionados e
decisões humanas vigentes, o `IdentityResolver` deve produzir o mesmo resultado.

Determinismo não significa ausência de ambiguidade nem obrigação de escolher
uma identidade. Um resultado determinístico pode ser `Ambiguous Identity` ou
`Unresolved Identity`. Preservar a insuficiência de modo reproduzível é mais
auditável do que fabricar uma conclusão.

A auditabilidade exige que um revisor consiga identificar quais entradas foram
comparadas, quais sinais foram considerados positivos, negativos ou
contraditórios, quais critérios produziram o estado, quais intervenções humanas
participaram e qual versão estava vigente.

## 16. Papel da IA

A inteligência artificial pode auxiliar:

- no reconhecimento de nomes;
- na identificação de grafias variantes;
- na extração de identificadores;
- na sugestão de possíveis correspondências;
- na identificação de possíveis erros de OCR.

Essas saídas são assistivas e devem manter ligação com suas fontes. A IA não
pode:

- confirmar identidade por conta própria;
- apagar contradições;
- substituir critérios determinísticos;
- inventar identificadores;
- modificar documentos ou evidências;
- transformar sugestão em decisão definitiva sem critério auditável.

Uma sugestão de IA pode originar revisão ou comparação adicional. Não constitui
por si só evidência de identidade nem justificativa suficiente para agrupar
pessoas.

## 17. Consequências

### Consequências positivas

- redução de falsos agrupamentos;
- preservação de homônimos e múltiplas identidades candidatas;
- auditabilidade das associações;
- suporte a pessoas com múltiplos vínculos;
- tratamento explícito de contradições;
- evolução segura dos critérios;
- possibilidade de revisão sem perda histórica;
- separação entre descoberta, identidade, atividade e continuidade.

### Custos arquiteturais

- maior complexidade conceitual que uma comparação binária;
- necessidade de revisão humana em determinados casos;
- persistência legítima de estados ambíguos ou não resolvidos;
- necessidade de versionamento dos critérios e resultados;
- necessidade de proveniência detalhada;
- possibilidade de novas resoluções quando entradas ou critérios mudarem;
- exigência de consumidores preparados para não tratar probabilidade como
  confirmação.

Esses custos são consequência da preservação da incerteza e da prevenção de
fusões factuais indevidas.

## 18. Alternativas rejeitadas

### Agrupar apenas pelo nome

Rejeitada porque nomes iguais podem identificar pessoas diferentes e nomes
distintos podem pertencer à mesma pessoa. A alternativa produziria falsos
agrupamentos e apagaria homônimos.

### Exigir identificador único em todos os documentos

Rejeitada porque muitos documentos legítimos contêm somente nome, matrícula,
identificador parcial ou contexto. A exigência excluiria evidências relevantes
e não resolveria erros materiais em identificadores.

### Resolver ambiguidades automaticamente

Rejeitada porque transforma insuficiência em certeza sem sustentação. Casos
ambíguos devem permanecer visíveis ou receber confirmação humana auditável.

### Usar somente similaridade textual

Rejeitada porque proximidade entre nomes não demonstra identidade e pode
ignorar identificadores ou contradições contextuais mais relevantes.

### Delegar a decisão integralmente à IA

Rejeitada porque resultados probabilísticos ou opacos não oferecem, por si,
reprodutibilidade e justificativa factual suficientes. IA permanece assistiva.

### Permitir que etapas posteriores corrijam identidade implicitamente

Rejeitada porque misturaria responsabilidades e faria atividade ou continuidade
reescrever a identidade para alcançar um resultado conveniente. Qualquer
revisão deve voltar à resolução de identidade e gerar decisão rastreável.

## 19. Fora do escopo

Este ADR não define:

- algoritmo de matching;
- pesos;
- limiares;
- banco de dados;
- formato de persistência;
- interface gráfica;
- algoritmo ou mecanismo de OCR;
- implementação;
- classes;
- interfaces;
- entidades de domínio implementadas;
- taxonomia de atividades;
- continuidade temporal;
- regras de RSC;
- política institucional específica.

## 20. Relação com outros documentos

### Domain Vision

A [Visão do Domínio](../domain-vision.md) exige reconstrução determinística,
rastreável e independente de normas. Este ADR aplica esses princípios à decisão
sobre quais evidências representam a mesma pessoa.

### ADR-003 — FunctionalAssignmentNormalizer

O [ADR-003](ADR-003-functional-assignment-normalizer.md) prepara representações
comparáveis sem resolver identidade. O `IdentityResolver` consome esse resultado
sem alterar os valores originais ou normalizados.

### ADR-004 — Functional Activity Taxonomy

O [ADR-004](ADR-004-functional-activity-taxonomy.md) define a linguagem canônica
das atividades. A taxonomia não resolve identidade e o `IdentityResolver` não
classifica atividades.

### ADR-005 — Identity Profile & Evidence Discovery

O [ADR-005](ADR-005-identity-profile-and-evidence-discovery.md) define quem
orienta a pesquisa e como evidências candidatas são encontradas. Este ADR recebe
essas candidatas em etapa posterior e avalia suas relações de identidade.

### Blueprint do Pipeline de Reconstrução Funcional

O [Blueprint](../functional-reconstruction-pipeline.md) delimita o
`IdentityResolver` entre normalização e resolução de atividade. Este ADR detalha
essa responsabilidade sem alterar o fluxo e preserva `FunctionalExercise` como
representação canônica da trajetória, da qual `CareerTimeline` é projeção
reconstruível.

Este ADR prepara explicitamente:

- **ADR-007 — Functional Activity Resolution:** decisão taxonômica posterior à
  identidade;
- **ADR-008 — Continuity Resolution:** decisão temporal posterior à identidade
  e à atividade.

## 21. Questões em aberto

Permanecem para decisões posteriores:

- representação concreta de identidades candidatas;
- granularidade das decisões, incluindo pares, grupos ou outras unidades
  conceituais;
- política e autoridade de revisão humana;
- critérios institucionais específicos;
- tratamento de identificadores corrigidos oficialmente;
- persistência e consulta das versões;
- impacto da remoção, invalidação ou indisponibilidade posterior de evidências;
- interface para comparação de candidatos;
- critérios para enriquecimento automático do `Identity Profile`;
- efeito operacional de cada estado sobre o encaminhamento às etapas
  posteriores;
- governança de critérios e histórico de revisões.

Para o ADR-007 — Functional Activity Resolution, permanecem especialmente:

- quais estados de identidade admitem classificação de atividade sem promover
  probabilidade ou ambiguidade a identidade confirmada;
- como classificações candidatas permanecem separadas quando a identidade
  ainda não está confirmada;
- como o contexto usado como sinal de identidade pode auxiliar a compreensão
  da atividade sem transferir ao resolvedor de atividade a decisão de
  identidade;
- como uma revisão posterior de identidade repercute em classificações de
  atividade já produzidas, sem reescrita silenciosa.

Essas questões não autorizam antecipar estruturas de implementação. Suas
respostas deverão preservar os estados conceituais, invariantes e fronteiras de
responsabilidade definidos neste ADR.

## Decisões aprovadas

- `Identity Resolution` é independente de `Evidence Discovery`, normalização,
  atividade e continuidade.
- Confiança de descoberta e confiança de identidade são independentes.
- A resolução admite seis estados conceituais e não se reduz a verdadeiro ou
  falso.
- Nome igual não prova identidade.
- Ausência de identificador não representa conflito.
- Identificadores divergentes e erros materiais permanecem rastreáveis.
- Confirmações humanas produzem decisões auditáveis e revisáveis.
- Entradas, critérios, decisões e resultados são versionados ou historicamente
  identificáveis.
- O mesmo conjunto de entradas e decisões vigentes produz o mesmo resultado,
  inclusive quando esse resultado é não resolvido.
- IA pode sugerir correspondências, mas não confirmar identidade.
- Etapas posteriores não corrigem identidade implicitamente.
- ADR-007 e ADR-008 detalharão atividade e continuidade, respectivamente.

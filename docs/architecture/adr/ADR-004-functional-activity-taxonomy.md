# ADR-004 — Taxonomia de Atividades Funcionais

## Status

Proposed

## Contexto

O ProcDocOrganizer reconstrói trajetórias funcionais a partir de evidências
documentais. Documentos registram acontecimentos administrativos por meio das
terminologias adotadas em seu tempo e em sua instituição de origem.

Instituições diferentes podem usar nomes distintos para atividades
funcionalmente equivalentes. Uma mesma instituição também pode alterar sua
estrutura ou seu vocabulário ao longo do tempo. Além disso, regulamentos como
RSC, progressão e aposentadoria podem selecionar, agrupar ou valorar os fatos
de maneiras diferentes.

A trajetória funcional não pode depender de uma dessas terminologias nem ser
reescrita sempre que uma instituição ou uma norma mudar. É necessária uma
linguagem funcional comum que represente os fatos reconstruídos de modo
estável, independente e reutilizável.

Este ADR deve ser interpretado conforme os princípios gerais da
[Visão do Domínio](../domain-vision.md).

## 1. Problema

Documentos administrativos não utilizam um vocabulário funcional universal.
Eles podem:

- empregar terminologias distintas para atividades equivalentes;
- reproduzir nomenclaturas próprias da estrutura de cada instituição;
- usar o mesmo termo para responsabilidades materialmente diferentes;
- refletir estruturas administrativas que posteriormente foram renomeadas,
  reorganizadas ou extintas.

Modelos normativos também mudam ao longo do tempo. Seus agrupamentos e
critérios respondem a finalidades específicas e não constituem uma descrição
neutra da trajetória profissional.

Sem uma taxonomia funcional independente, a representação dos fatos ficaria
acoplada à redação dos documentos, à organização de uma instituição ou à
versão de uma norma. Isso impediria comparações confiáveis e faria uma mudança
externa reclassificar indevidamente fatos históricos já reconstruídos.

## 2. Decisão

A Taxonomia de Atividades Funcionais será a representação canônica das
atividades desempenhadas por uma pessoa.

Ela:

- independe da instituição;
- independe do regulamento;
- independe do RSC;
- representa fatos reconstruídos;
- fornece uma linguagem comum para relacionar descrições administrativas a
  conceitos funcionais estáveis;
- preserva a separação entre reconstrução factual e interpretação normativa.

A taxonomia descreve a natureza funcional de uma atividade. Ela não atribui
valor, mérito, pontuação ou efeito jurídico ao fato.

A denominação institucional permanece preservada como contexto documental e
administrativo. Sua tradução para uma atividade canônica somente é válida
quando estiver sustentada pelo conteúdo das evidências e por critérios
determinísticos e auditáveis.

## 3. Conceitos

### Documento

É a fonte documental que registra um ato, uma declaração ou um acontecimento
administrativo. Sua redação expressa o contexto e o vocabulário da instituição
que o produziu.

O documento não é, por si só, uma atividade ou um exercício funcional.

### Evidência

É uma afirmação rastreável extraída ou registrada a partir de um documento.
Ela responde ao que a fonte afirma e preserva sua ligação com essa fonte.

Uma evidência pode ser incompleta, ambígua ou insuficiente para estabelecer
isoladamente um fato profissional.

### Atividade Funcional

É o conceito canônico que descreve a natureza de uma atuação profissional,
independentemente da nomenclatura administrativa utilizada para registrá-la.

A atividade funcional pertence à linguagem da taxonomia. Ela não representa,
isoladamente, que uma pessoa concreta a exerceu em determinado local ou
período.

### Exercício Funcional

É o fato profissional reconstruído de que uma pessoa desempenhou uma atividade
funcional em um contexto e período determinados, sustentado por evidências
rastreáveis.

O exercício funcional é uma ocorrência histórica concreta. A atividade
funcional é a categoria canônica usada para descrever a natureza dessa
ocorrência.

### Interpretação Normativa

É a leitura que um regulamento realiza sobre exercícios funcionais já
reconstruídos. Ela pode selecionar, agrupar, qualificar ou atribuir efeitos aos
fatos conforme uma finalidade administrativa específica.

A interpretação normativa não redefine a atividade nem reescreve o exercício
funcional que consome.

Esses cinco conceitos representam responsabilidades sucessivas e distintas.
Não são sinônimos e não podem ser substituídos uns pelos outros.

## 4. Princípios

### Atividades representam fatos

A taxonomia descreve a natureza funcional de atuações profissionais
reconstruídas, sem incorporar o resultado de sua avaliação por uma norma.

### Normas interpretam fatos

Regulamentos consomem a trajetória funcional. Seus critérios não definem a
existência ou o significado básico das atividades.

### Documentos descrevem fatos

Documentos são fontes. Sua redação oferece evidências, mas não constitui
automaticamente a representação canônica da atividade.

### A mesma atividade pode possuir diferentes nomes administrativos

Variações de nomenclatura podem apontar para uma mesma atividade funcional
quando suas responsabilidades forem materialmente equivalentes.

### Diferentes documentos podem representar a mesma atividade

Evidências provenientes de fontes distintas podem sustentar a reconstrução de
uma mesma natureza de atividade ou de um mesmo exercício funcional.

### Mudanças institucionais não alteram a atividade reconstruída

Renomeações e reorganizações preservam seu valor como contexto histórico, mas
não mudam retroativamente a natureza funcional de um fato já estabelecido.

### Equivalência exige sustentação

Semelhança de nomes não demonstra equivalência, e diferença de nomes não
demonstra diferença funcional. A classificação deve considerar o significado
e as responsabilidades sustentadas pelas evidências.

### Incerteza deve ser preservada

Quando as evidências não sustentarem uma classificação segura, o sistema não
deve forçar uma atividade canônica por aproximação ou conveniência normativa.

## 5. Papel das instituições

Instituições fornecem o contexto em que documentos são produzidos e atividades
são desempenhadas. Seus nomes de cargos, funções, unidades e estruturas
administrativas devem permanecer rastreáveis.

Essas nomenclaturas, contudo, não definem a ontologia do domínio. Duas
instituições podem nomear de maneira diferente atividades funcionalmente
equivalentes. Por exemplo:

- a Instituição A utiliza “Coordenador Acadêmico”;
- a Instituição B utiliza “Chefe de Ensino”.

Quando as evidências demonstrarem responsabilidades equivalentes, ambas as
denominações podem ser relacionadas à mesma atividade funcional canônica.
Essa equivalência decorre das atribuições efetivamente demonstradas, e não da
mera proximidade entre os títulos.

Da mesma forma, títulos iguais não devem ser considerados equivalentes quando
o contexto e as responsabilidades documentadas forem diferentes.

## 6. Papel da IA

Recursos de inteligência artificial poderão auxiliar:

- reconhecimento textual;
- expansão de siglas;
- sugestões de classificação.

Esses recursos têm caráter assistivo. Suas respostas não constituem, por si
sós, evidência nem decisão taxonômica.

A decisão final sobre a atividade funcional deve permanecer determinística,
explicável, reproduzível e auditável. Toda classificação deve preservar a
rastreabilidade até as evidências que a sustentam, e sugestões incertas não
podem preencher lacunas como se fossem fatos estabelecidos.

## 7. Consequências

### Reutilização por diferentes normas

RSC, progressão, aposentadoria e outros modelos podem interpretar a mesma
trajetória sem exigir taxonomias factuais incompatíveis.

### Reutilização por diferentes instituições

Novas instituições podem relacionar suas nomenclaturas à linguagem funcional
comum sem criar um domínio paralelo.

### Estabilidade histórica

Mudanças de estrutura, vocabulário ou norma não reescrevem atividades e
exercícios funcionais já reconstruídos.

### Baixo acoplamento

A reconstrução dos fatos permanece separada das fontes específicas e dos
consumidores normativos.

### Comparabilidade

Atividades funcionalmente equivalentes podem ser comparadas mesmo quando os
documentos utilizam denominações administrativas diferentes.

### Auditabilidade

A classificação canônica não elimina a nomenclatura original nem a ligação
com as evidências que justificam sua adoção.

### Necessidade de governança futura

A estabilidade da linguagem comum exigirá decisões posteriores sobre
granularidade, evolução, equivalências, ambiguidades e histórico da taxonomia.

## 8. Fora do escopo

Este ADR não define:

- tabela do RSC;
- pontuação;
- critérios de mérito;
- algoritmo de continuidade;
- algoritmo de identidade;
- implementação;
- catálogo inicial de atividades;
- mecanismo de armazenamento;
- fluxo de aprovação ou revisão de classificações;
- regras de interpretação de qualquer consumidor normativo.

## 9. Relação com os demais ADRs

### Visão do Domínio

A Visão do Domínio estabelece que o núcleo reconstrói fatos profissionais e
que módulos consumidores realizam a interpretação normativa. Este ADR
formaliza a linguagem comum necessária para representar a natureza desses
fatos sem dependência de instituições ou normas.

### ADR-003 — FunctionalAssignmentNormalizer

O ADR-003 prepara evidências de atribuição funcional para comparação,
preservando seu significado administrativo. O ADR-004 define a linguagem
canônica à qual essas descrições poderão ser relacionadas em uma etapa
posterior.

Normalização e classificação taxonômica permanecem responsabilidades
distintas. O normalizador reduz variações de representação; a taxonomia
expressa a natureza funcional reconstruída. Nenhuma das duas resolve, por si
só, identidade ou continuidade.

### Próximas decisões do pipeline

Este ADR prepara as decisões futuras sobre:

- correspondência entre evidências normalizadas e atividades funcionais;
- resolução de identidade entre evidências;
- reconstrução de exercícios funcionais;
- resolução de continuidade e sobreposição;
- consumo da trajetória por modelos normativos.

Essas decisões deverão preservar a ordem conceitual entre fonte documental,
evidência, atividade funcional, exercício funcional e interpretação
normativa.

## Decisões aprovadas

- A Taxonomia de Atividades Funcionais é a linguagem canônica das atividades
  desempenhadas.
- Atividade funcional e exercício funcional são conceitos distintos.
- A taxonomia representa a natureza funcional dos fatos, não sua avaliação
  normativa.
- A taxonomia independe de instituição, regulamento e RSC.
- Nomenclaturas institucionais permanecem preservadas como contexto.
- Equivalência funcional depende das responsabilidades sustentadas pelas
  evidências, e não apenas dos títulos administrativos.
- Mudanças institucionais ou normativas não reescrevem fatos reconstruídos.
- Classificações devem ser determinísticas, auditáveis e rastreáveis.
- IA pode sugerir classificações, mas não constitui a decisão final.
- Incertezas não devem ser ocultadas por classificações forçadas.

## Questões para ADR futuro

- Qual será a granularidade inicial das atividades funcionais?
- Como atividades serão incluídas, revisadas, descontinuadas ou substituídas
  sem perder estabilidade histórica?
- Como serão representadas relações hierárquicas ou de especialização entre
  atividades?
- Como serão registradas equivalências institucionais e suas justificativas?
- Como classificações ambíguas ou concorrentes permanecerão visíveis?
- Quais critérios determinarão a correspondência entre uma evidência
  normalizada e uma atividade funcional?
- Como a taxonomia participará da resolução de identidade e continuidade sem
  assumir essas responsabilidades?

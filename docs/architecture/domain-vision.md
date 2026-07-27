# Visão de Domínio do ProcDocOrganizer

## 1. Missão

> O ProcDocOrganizer reconstrói de forma determinística a trajetória funcional
> de agentes públicos a partir de evidências documentais.

Documentos são fontes que registram acontecimentos, declarações e atos
administrativos. Eles não são, por si mesmos, a trajetória funcional de uma
pessoa. O sistema utiliza essas fontes para reconstruir fatos profissionais de
forma rastreável, coerente e auditável.

Essa reconstrução busca responder o que a pessoa efetivamente realizou, em qual
contexto e durante qual período. Somente depois de estabelecidos esses fatos,
normas administrativas podem interpretá-los para uma finalidade específica.

Assim, o domínio distingue três elementos:

- documentos fornecem evidências;
- fatos profissionais são reconstruídos a partir dessas evidências;
- normas administrativas interpretam posteriormente os fatos reconstruídos.

## 2. Princípio fundamental

> O núcleo do sistema reconstrói fatos profissionais.
>
> A interpretação normativa constitui responsabilidade de módulos
> consumidores.

Um fato profissional não depende do RSC nem de qualquer outro regulamento para
existir. O exercício de uma função, a participação em uma comissão ou a
realização de uma atividade permanecem fatos da trajetória mesmo quando não
produzem pontuação em determinado modelo normativo.

Da mesma forma, uma mudança de norma pode alterar a maneira como um fato é
avaliado, mas não deve reescrever o fato histórico. A reconstrução funcional
deve, portanto, permanecer separada das regras que concedem valor, efeito ou
classificação normativa aos fatos.

## 3. Camadas conceituais

### 3.1 Evidências documentais

Esta camada responde:

> O que o documento afirma?

Ela reúne as fontes documentais e as afirmações que podem ser extraídas delas.
Entre essas fontes estão:

- portarias;
- boletins;
- certificados;
- declarações;
- atas.

Uma evidência documental sustenta uma afirmação, mas pode ser incompleta,
ambígua ou complementar a outras evidências. Sua existência não confirma
automaticamente toda a extensão de um fato profissional. A origem documental
de cada afirmação deve permanecer rastreável durante todo o processo.

### 3.2 Trajetória funcional

Esta camada responde:

> O que a pessoa efetivamente realizou?

Ela representa fatos profissionais reconstruídos a partir do conjunto de
evidências disponíveis. Exemplos incluem:

- exercício de chefia;
- exercício de coordenação;
- participação em comissão;
- fiscalização;
- docência;
- capacitação.

A trajetória funcional organiza esses fatos de maneira independente da
redação particular de cada documento e da norma que futuramente os avaliará.
Ela é uma representação profissional consolidada, e não uma coleção de
documentos nem um resultado normativo.

### 3.3 Modelos normativos

Esta camada responde:

> Como determinado regulamento interpreta esses fatos?

Modelos normativos consomem a trajetória funcional já reconstruída e aplicam
critérios próprios para uma finalidade administrativa. Entre os possíveis
modelos estão:

- Reconhecimento de Saberes e Competências;
- progressão;
- avaliação;
- aposentadoria;
- auditoria.

Cada modelo pode selecionar fatos diferentes, atribuir-lhes efeitos distintos
ou ignorá-los. Essas diferenças pertencem ao modelo normativo e não devem
contaminar a representação dos fatos profissionais.

## 4. Papel das instituições

As instituições fornecem o contexto no qual documentos são produzidos e
atividades profissionais são exercidas. Nomes de órgãos, unidades, campi,
comissões e estruturas administrativas ajudam a compreender a origem e o
alcance de uma evidência.

As instituições, entretanto, não definem o significado universal dos fatos
profissionais. Estruturas administrativas diferentes podem representar
atividades funcionalmente equivalentes, assim como denominações semelhantes
podem esconder responsabilidades distintas.

As diferenças institucionais devem ser preservadas como contexto e traduzidas,
quando houver sustentação suficiente, para uma representação funcional comum.
Essa tradução não pode apagar a origem documental nem alterar o significado
administrativo do fato.

## 5. Papel da Taxonomia Funcional

A Taxonomia Funcional constitui a linguagem comum entre:

- documentos;
- instituições;
- modelos normativos.

Ela descreve atividades profissionais de maneira independente da instituição
que as nomeou e da norma que as consumirá. Sua finalidade é permitir que
expressões documentais e administrativas diferentes sejam relacionadas a
conceitos funcionais consistentes.

A taxonomia não atribui pontuação nem decide efeitos jurídicos. Ela organiza o
vocabulário utilizado para representar fatos profissionais, preservando os
contextos institucionais e as evidências que sustentam cada interpretação.

## 6. Papel dos modelos normativos

O RSC é o primeiro consumidor implementado da trajetória funcional. Ele não
constitui o núcleo do sistema.

O núcleo deve permanecer reutilizável por outros modelos e finalidades, como:

- progressão funcional;
- aposentadoria;
- auditoria;
- gestão de pessoas;
- outros processos administrativos.

Cada consumidor interpreta os fatos segundo suas próprias normas, versões,
critérios e períodos de validade. Nenhum consumidor deve redefinir a trajetória
funcional exclusivamente para atender às suas regras.

## 7. Princípios arquiteturais

### Reconstrução precede interpretação

O sistema deve primeiro determinar quais fatos são sustentados pelas
evidências. Somente depois deve aplicar uma leitura normativa.

### Fatos precedem normas

Fatos profissionais possuem identidade e validade conceitual independentes das
normas que os avaliam.

### Instituições fornecem contexto

Nomes e estruturas institucionais qualificam as evidências e os fatos, mas não
substituem uma representação funcional comum.

### Atividades funcionais são independentes das instituições

Atividades equivalentes podem existir em organizações distintas e sob
denominações administrativas diferentes.

### Componentes cognitivos devem permanecer determinísticos

Transformações, normalizações, resoluções e consolidações que alterem a
representação do conhecimento devem produzir resultados explicáveis,
reproduzíveis e auditáveis.

### IA pode auxiliar, mas não substituir regras auditáveis

Recursos de inteligência artificial podem sugerir extrações, associações ou
interpretações. Suas sugestões não substituem critérios determinísticos, não
eliminam a revisão humana e não podem se tornar a única justificativa para um
fato reconstruído.

### Rastreabilidade acompanha todo o domínio

Todo fato reconstruído deve poder ser relacionado às evidências que o
sustentam. Normalizações e interpretações não devem romper essa relação.

### Incerteza deve permanecer visível

Ausências, divergências e ambiguidades não devem ser preenchidas por suposição.
O domínio deve preservar o que é conhecido, o que é apenas alegado e o que
ainda depende de resolução.

## 8. Consequências arquiteturais

### Mudanças normativas não alteram fatos

Uma nova norma pode modificar critérios, enquadramentos ou resultados, mas a
trajetória funcional reconstruída permanece a mesma enquanto as evidências e
os fatos não mudarem.

### Novos consumidores reutilizam o mesmo núcleo

Cada novo modelo normativo pode consumir a trajetória existente, sem exigir
uma reconstrução específica e incompatível dos fatos.

### Novas instituições não exigem alteração do domínio

Variações de nomenclatura e estrutura administrativa devem ser representadas
como contexto e traduzidas pela linguagem funcional comum. A entrada de uma
nova instituição não deve exigir a criação de um domínio profissional
paralelo.

### A trajetória funcional é o principal ativo do sistema

Documentos podem ser reorganizados e normas podem mudar. A trajetória
funcional reconstruída, sustentada por evidências e preservada de forma
rastreável, constitui o ativo central e reutilizável do ProcDocOrganizer.

### Separação entre reconstrução e consumo

A evolução de um consumidor normativo não deve introduzir dependências no
núcleo factual. Da mesma forma, o aperfeiçoamento da reconstrução deve
beneficiar todos os consumidores sem privilegiar um regulamento específico.

### Auditabilidade como condição de confiança

Resultados normativos confiáveis dependem de fatos reconstruídos por processos
explicáveis. A cadeia entre fonte documental, interpretação funcional, fato
consolidado e consumo normativo deve permanecer verificável.

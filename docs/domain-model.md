# Modelo Conceitual do ProcDoc RSC

## 1. Finalidade do documento

Este documento define o vocabulário, as entidades, as relações, os princípios
e os limites do domínio do ProcDoc RSC. Ele estabelece uma compreensão comum
sobre o problema que o sistema pretende apoiar, sem antecipar decisões sobre
classes, banco de dados, interfaces, persistência ou qualquer outra tecnologia.

O modelo deverá orientar futuras decisões de implementação. Quando surgirem
dúvidas sobre estruturas, funcionalidades ou regras, a solução deverá ser
avaliada primeiro à luz dos conceitos aqui apresentados. Questões ainda não
resolvidas são identificadas explicitamente e não devem ser tratadas como
decisões definitivas.

## 2. Missão do ProcDoc RSC

O ProcDoc RSC é uma plataforma para reconstruir, documentar e organizar a
trajetória funcional do servidor público, transformando documentos
administrativos dispersos em atividades profissionalmente comprovadas,
temporalmente consolidadas e prontas para avaliação conforme a normativa de
RSC.

Sua finalidade central não é apenas organizar arquivos nem calcular pontos. O
sistema deve apoiar a compreensão daquilo que o servidor realizou, da
documentação que sustenta essa trajetória, dos períodos efetivamente
comprovados e do enquadramento normativo aplicável.

## 3. Problema de domínio

O trabalho normalmente começa pela memória do servidor sobre atividades
realizadas no passado. Essa lembrança fornece uma hipótese inicial: qual
atividade ocorreu, em que contexto e durante qual período aproximado.

Em seguida, o servidor procura documentos capazes de sustentar essa hipótese.
Os arquivos encontrados frequentemente estão desordenados, foram produzidos
para outras finalidades e contêm informações sobre várias pessoas e
atividades. Um documento pode iniciar uma composição, outro pode alterá-la
parcialmente e um terceiro pode registrar seu encerramento. Documentos também
podem se sobrepor no tempo ou omitir informações que permanecem válidas.

O fluxo real envolve:

1. lembrar as atividades realizadas;
2. cadastrar uma descrição e um período inicialmente estimados;
3. procurar e reunir documentos comprobatórios;
4. interpretar documentos parcial ou temporalmente sobrepostos;
5. identificar informações de início, continuidade, alteração e encerramento;
6. distinguir alterações que afetam o servidor daquelas que atingem apenas
   outras pessoas;
7. consolidar períodos de exercício;
8. relacionar a atividade comprovada à normativa aplicável;
9. calcular a pontuação com memória de cálculo;
10. organizar atividades e documentos para conferência da banca;
11. utilizar externamente as informações consolidadas como apoio à elaboração
    do memorial profissional.

Um documento não é uma atividade. Tampouco representa, isoladamente, uma prova
já interpretada. A comprovação resulta da leitura rastreável de informações e
da combinação coerente de documentos sucessivos.

## 4. Princípios do domínio

- **Atividades organizam a trajetória; documentos fornecem sustentação.** A
  Atividade Profissional é a entidade central do domínio.
- **Documentos devem permanecer íntegros e rastreáveis.** A interpretação não
  substitui nem modifica a fonte original.
- **Toda informação interpretada deve apontar para sua origem.** Sempre que
  aplicável, a referência deve permitir localizar documento, página e trecho.
- **Um documento pode originar vários Eventos Documentais.** Informações
  distintas do mesmo documento podem sustentar atividades diferentes.
- **Uma atividade pode ser sustentada por vários Eventos Documentais.** Sua
  compreensão pode depender da combinação de fontes sucessivas.
- **Documentos sucessivos podem formar um único período contínuo.** A mudança
  da composição de um grupo não necessariamente encerra a atividade de todos
  os seus integrantes.
- **A ausência de alteração referente ao servidor não implica interrupção.**
  Continuidade e encerramento devem ser avaliados no contexto documental.
- **Período lembrado e período comprovado podem ser diferentes.** A memória
  orienta a busca, mas não substitui a comprovação.
- **Informação alegada, interpretada, confirmada e validada são situações
  distintas.** O usuário deve saber qual é o grau de consolidação de cada
  conclusão.
- **Incertezas não devem ser ocultadas.** Datas, relações ou períodos
  incompletos devem permanecer identificados para revisão.
- **A pontuação deve possuir memória de cálculo.** Quantidade, regra, limites,
  resultado e justificativa precisam ser compreensíveis.
- **Resultados automatizados não substituem revisão humana.** Extrações,
  inferências, enquadramentos e cálculos relevantes devem poder ser
  conferidos.
- **O memorial profissional é externo ao sistema.** O ProcDoc RSC organiza
  informações que podem apoiar sua elaboração, mas não o escreve.

## 5. Glossário oficial

### Projeto RSC

- **Definição:** contexto agregador no qual um servidor organiza sua trajetória
  funcional para uma avaliação de RSC.
- **Finalidade:** reunir atividades, documentos, normativa, enquadramentos,
  pontuações e produtos de conferência relacionados a uma avaliação.
- **Exemplo:** trabalho de preparação documental de um servidor para um
  processo específico de Reconhecimento de Saberes e Competências.
- **Não representa:** apenas uma pasta de arquivos ou o processo administrativo
  formal da instituição.
- **Relações:** contém Atividades Profissionais e Documentos, utiliza uma
  normativa e dá origem à Linha do Tempo e ao Dossiê.

### Atividade Profissional

- **Definição:** aquilo que o servidor realizou em sua trajetória funcional e
  que pode ser compreendido, comprovado e eventualmente enquadrado na
  normativa.
- **Finalidade:** organizar a trajetória a partir do trabalho realizado, e não
  a partir da ordem dos documentos encontrados.
- **Exemplos:** fiscalização de contrato, participação em comissão, exercício
  de função, realização de curso ou atuação em projeto institucional.
- **Não representa:** um documento, uma simples ocorrência textual ou um item
  normativo.
- **Relações:** é sustentada por Eventos Documentais, possui Períodos de
  Exercício, recebe Enquadramento Normativo e pode produzir Pontuação.

### Documento

- **Definição:** arquivo original utilizado como fonte de comprovação.
- **Finalidade:** preservar a fonte documental que permite verificar as
  interpretações e conclusões do projeto.
- **Exemplos:** portaria, boletim de serviço, certificado, declaração, diploma,
  ata, ofício, termo ou relatório.
- **Não representa:** a própria atividade nem uma interpretação definitiva de
  seu conteúdo.
- **Relações:** pertence ao Projeto RSC, origina Eventos Documentais e sustenta
  conclusões apresentadas no Dossiê.

### Evento Documental

- **Definição:** informação relevante identificada em um documento e utilizada
  para reconstruir a trajetória funcional do servidor.
- **Finalidade:** registrar, de modo rastreável, a unidade de informação
  interpretada que contribui para compreender uma atividade.
- **Exemplos:** designação, permanência, substituição, dispensa, encerramento,
  recondução, conclusão de curso, participação registrada, alteração de
  composição ou definição de vigência.
- **Não representa:** o documento completo, uma atividade inteira ou um “Ato
  Administrativo”. Este último termo não integra o vocabulário do domínio.
- **Relações:** origina-se em um Documento, sustenta uma ou mais Atividades
  Profissionais e ajuda a formar Períodos de Exercício.

### Período de Exercício

- **Definição:** intervalo temporal consolidado durante o qual uma Atividade
  Profissional foi exercida.
- **Finalidade:** expressar o resultado da interpretação temporal de eventos e
  documentos, incluindo incertezas e limites de comprovação.
- **Exemplo:** período contínuo entre a designação de um servidor como fiscal e
  sua posterior retirada da composição.
- **Não representa:** necessariamente a vigência integral de um documento nem
  o período apenas lembrado pelo servidor.
- **Relações:** pertence a uma Atividade Profissional, é formado com auxílio de
  Eventos Documentais e pode fornecer quantidade para o enquadramento e a
  pontuação.

### Item Normativo

- **Definição:** critério previsto na versão da normativa aplicável ao Projeto
  RSC.
- **Finalidade:** expressar o critério contra o qual uma atividade comprovada
  pode ser avaliada.
- **Exemplo:** item que atribui valor por período de exercício de determinada
  função, sujeito a requisitos e limites.
- **Não representa:** a Atividade Profissional nem sua seleção automática para
  pontuação.
- **Relações:** pertence a uma normativa e é associado à atividade por meio de
  um Enquadramento Normativo.

### Enquadramento Normativo

- **Definição:** relação argumentada entre uma Atividade Profissional
  suficientemente comprovada e um Item Normativo.
- **Finalidade:** registrar por que a atividade atende ao critério, quais
  evidências sustentam a associação e quais ressalvas permanecem.
- **Exemplo:** associação de um período comprovado de fiscalização ao item
  aplicável, acompanhada da justificativa documental.
- **Não representa:** uma simples escolha de categoria ou uma decisão
  automática e definitiva.
- **Relações:** conecta Atividade Profissional e Item Normativo e fornece a base
  para a Pontuação.

### Pontuação

- **Definição:** resultado calculado a partir de um Enquadramento Normativo e
  das quantidades comprovadas.
- **Finalidade:** apresentar um resultado reproduzível, justificável e
  revisável conforme a normativa.
- **Exemplo:** quantidade de meses multiplicada pelo valor aplicável, com
  incidência posterior do limite previsto.
- **Não representa:** uma estimativa sem regra, a comprovação da atividade ou a
  decisão final da banca.
- **Relações:** deriva do Enquadramento Normativo, utiliza Períodos de Exercício
  e integra o Dossiê.

### Dossiê

- **Definição:** conjunto organizado de atividades, conclusões e fontes para
  apresentação e conferência pela banca.
- **Finalidade:** permitir que a banca compreenda o que está sendo apresentado,
  como foi comprovado, enquadrado e calculado.
- **Exemplo:** organização de uma atividade com período alegado, período
  comprovado, item normativo, memória de cálculo e documentos correspondentes.
- **Não representa:** mera cópia de uma pasta de documentos nem o memorial
  profissional.
- **Relações:** reúne Atividades Profissionais, Documentos, Enquadramentos
  Normativos e Pontuações do Projeto RSC.

### Linha do Tempo

- **Definição:** representação cronológica das atividades consolidadas do
  servidor.
- **Finalidade:** oferecer uma visão temporal coerente da trajetória funcional,
  incluindo continuidades, interrupções, sobreposições e incertezas.
- **Exemplo:** exibição dos períodos de fiscalização, participação em comissões
  e formação ao longo dos anos.
- **Não representa:** apenas uma lista de documentos ordenada por data.
- **Relações:** é formada por Atividades Profissionais e seus Períodos de
  Exercício; Documentos e Eventos aparecem como sustentação.

### Estado da Atividade

- **Definição:** situação conceitual da Atividade Profissional no fluxo de
  lembrança, comprovação, enquadramento e revisão.
- **Finalidade:** indicar o grau de elaboração da atividade e orientar o
  trabalho ainda necessário.
- **Exemplo:** atividade aguardando documentos ou com período já consolidado.
- **Não representa:** uma enumeração técnica definitiva nem uma garantia
  automática de validade.
- **Relações:** acompanha a evolução da Atividade Profissional e depende do
  avanço na análise de Documentos, Eventos, Períodos e Enquadramentos.

## 6. Entidades conceituais

### 6.1 Projeto RSC

O Projeto RSC agrega o trabalho realizado pelo servidor para uma avaliação
determinada. Ele estabelece o contexto em que documentos são relevantes,
atividades são reconstruídas e uma versão da normativa é utilizada. Um mesmo
arquivo institucional pode conter informações sobre várias pessoas, mas o
projeto seleciona e interpreta somente o que é pertinente à trajetória em
análise.

### 6.2 Atividade Profissional

A Atividade Profissional é a entidade central: aquilo que o servidor realizou
e que pode ser enquadrado na normativa. Conceitualmente, deve permitir
compreender:

- a descrição inicialmente lembrada;
- a natureza da atividade;
- o período estimado pelo servidor;
- o período efetivamente comprovado;
- a situação da comprovação;
- o eventual enquadramento normativo;
- a pontuação decorrente;
- os Documentos e Eventos Documentais relacionados.

Esses elementos descrevem necessidades do domínio, não campos técnicos. Uma
atividade pode começar como lembrança incompleta e ganhar precisão à medida que
fontes são localizadas e interpretadas.

### 6.3 Documento

Documento é o arquivo original utilizado como fonte. Portarias, boletins de
serviço, certificados, declarações, diplomas, atas, ofícios, termos e relatórios
são exemplos possíveis.

Um Documento pode conter várias pessoas, tratar de diversas atividades,
reproduzir informações anteriores e alterar somente parte de uma composição.
Trechos irrelevantes para o projeto atual permanecem parte íntegra do
documento, mas não precisam gerar Eventos Documentais.

### 6.4 Evento Documental

Evento Documental é a “informação relevante identificada em um documento e
utilizada para reconstruir a trajetória funcional do servidor”.

Designação, permanência, substituição, dispensa, encerramento, recondução,
conclusão de curso, participação registrada, alteração de composição e
definição de vigência são exemplos. Um Documento pode originar vários eventos,
inclusive associados a pessoas ou atividades diferentes.

Cada evento deve ser rastreável ao Documento e, quando aplicável, à página e ao
trecho de origem. O Evento Documental não se confunde com o documento completo
e não deve ser denominado “Ato Administrativo”, expressão que possui sentidos
jurídicos próprios e poderia gerar ambiguidade.

### 6.5 Período de Exercício

Período de Exercício é o intervalo temporal consolidado em que uma atividade
foi exercida. Pode resultar da combinação de:

- um evento inicial;
- eventos de continuidade;
- alterações que não afetam o servidor;
- um evento de encerramento;
- lacunas ou incertezas documentais.

A consolidação não deve presumir que cada novo documento inicia um novo
período. Também não deve inventar um encerramento quando a fonte apenas altera
outros integrantes. Períodos alegados, estimados e comprovados devem permanecer
distinguíveis.

### 6.6 Item Normativo

Item Normativo é um critério da normativa aplicável ao projeto. Conceitualmente,
deve permitir compreender sua descrição, categoria ou grupo, unidade de
cálculo, valor, limites, requisitos, documentação exigida e versão da
normativa.

Essas características não definem uma estrutura de armazenamento. Elas
registram o contexto necessário para interpretar e reproduzir um enquadramento.

### 6.7 Enquadramento Normativo

Enquadramento Normativo é a relação argumentada entre uma atividade comprovada
e um Item Normativo. Não é apenas a escolha de uma categoria: deve registrar a
justificativa da associação, as condições atendidas, as fontes utilizadas e as
ressalvas que exigem revisão.

Uma sugestão de enquadramento não equivale à sua confirmação. A decisão deve
permanecer revisável pelo servidor e sujeita à avaliação da banca.

### 6.8 Pontuação

Pontuação é o resultado calculado a partir do enquadramento. Deve preservar:

- a quantidade apurada;
- a regra aplicada;
- a memória de cálculo;
- os limites incidentes;
- o resultado anterior ao limite;
- o resultado posterior ao limite;
- a justificativa;
- a situação de revisão.

O cálculo ocorre depois que a atividade está suficientemente compreendida,
comprovada e enquadrada. A Pontuação não corrige incertezas documentais nem
substitui a validação humana.

### 6.9 Linha do Tempo

A Linha do Tempo representa cronologicamente as atividades consolidadas do
servidor. Ela deve destacar atividades e Períodos de Exercício, incluindo
sobreposições, lacunas e níveis de certeza.

Não deve ser apenas uma lista cronológica de documentos. Documentos e Eventos
Documentais aparecem como sustentação das atividades representadas.

### 6.10 Dossiê

O Dossiê organiza o material para apresentação e conferência pela banca. Deve
permitir compreender:

- qual atividade está sendo apresentada;
- qual período foi alegado;
- qual período foi comprovado;
- qual Item Normativo foi utilizado;
- como a Pontuação foi calculada;
- quais Documentos sustentam a conclusão.

Sua organização deve favorecer rastreabilidade e conferência sem alterar ou
duplicar desnecessariamente os arquivos originais.

### 6.11 Estado da Atividade

Um fluxo conceitual inicial pode incluir:

```text
lembrada
  → cadastrada
  → aguardando documentos
  → documentos localizados
  → eventos identificados
  → período em análise
  → período consolidado
  → aguardando enquadramento
  → enquadrada
  → pontuada
  → revisada
  → pronta para envio
```

Nem toda atividade necessariamente percorrerá os estados de maneira
estritamente linear. Retornos para revisão podem ocorrer quando novos
documentos ou divergências forem encontrados. Os estados ainda poderão ser
refinados antes da implementação e não constituem uma enumeração técnica
definitiva.

## 7. Relações entre os conceitos

```text
Projeto RSC
    contém Atividades Profissionais
    contém Documentos
    utiliza uma Normativa

Documento
    origina Eventos Documentais

Eventos Documentais
    sustentam Atividades Profissionais
    ajudam a formar Períodos de Exercício

Atividade Profissional
    possui um ou mais Períodos de Exercício
    recebe Enquadramento Normativo
    produz Pontuação

Atividades, Documentos, Enquadramentos e Pontuações
    formam o Dossiê

Atividades consolidadas
    formam a Linha do Tempo
```

As relações podem ser muitos-para-muitos no plano conceitual. Um Documento
pode produzir Eventos relacionados a várias Atividades. Uma Atividade pode
depender de Eventos originados em diversos Documentos. Um Evento pode ser
relevante para mais de uma atividade, desde que cada uso preserve seu contexto
e sua rastreabilidade.

Essas relações não determinam tabelas, identificadores ou estratégias de
persistência. Apenas expressam que a trajetória não pode ser representada
adequadamente por uma correspondência simples entre um documento e uma
atividade.

## 8. Fluxo conceitual do usuário

```text
Lembrança da atividade
    ↓
Cadastro inicial da atividade
    ↓
Busca e importação dos documentos
    ↓
Identificação dos eventos documentais
    ↓
Reconstrução dos períodos
    ↓
Consolidação da atividade comprovada
    ↓
Enquadramento normativo
    ↓
Cálculo da pontuação
    ↓
Revisão
    ↓
Organização do dossiê
    ↓
Exportação para avaliação
    ↓
Utilização externa das informações na elaboração do memorial
```

O fluxo parte da atividade lembrada, e não dos arquivos. Ele é iterativo:
novos documentos podem exigir revisão de eventos, períodos, enquadramentos e
pontuações anteriormente considerados.

## 9. Exemplo de consolidação documental

Considere três portarias fictícias:

1. a primeira designa Alexander Block e José Carlos como fiscais;
2. a segunda mantém Alexander, retira José e inclui Maria Teresa;
3. a terceira retira Alexander e inclui Rafael.

Para Alexander, a segunda portaria não inicia um novo exercício nem encerra o
anterior. A substituição de José por Maria altera a composição, mas não
interrompe a atividade de Alexander. Os três documentos precisam ser
interpretados em conjunto.

A primeira designação fornece o evento inicial. A manutenção ou ausência de
alteração de Alexander na segunda composição sustenta a continuidade. Sua
retirada na terceira portaria fornece o evento de encerramento. Deve ser
formado, portanto, um período contínuo desde a designação até a retirada de
Alexander, observadas as datas e vigências efetivamente declaradas.

Cada informação relevante constitui um Evento Documental próprio e permanece
rastreável à portaria correspondente. Os nomes utilizados são apenas exemplos
fictícios para explicar o domínio.

## 10. Incerteza, divergência e lacunas

O modelo deve admitir que a documentação disponível pode ser incompleta,
contraditória ou insuficiente. O sistema não deve inventar datas nem preencher
lacunas silenciosamente.

Princípios aplicáveis:

- **Data de início não localizada:** registrar que o início é desconhecido ou
  apenas estimado; não substituir a ausência por uma data presumida.
- **Data de encerramento não localizada:** manter o período em aberto ou com
  limite incerto, conforme a interpretação revisável.
- **Documentos contraditórios:** preservar as duas fontes, registrar a
  divergência e impedir que uma conclusão silenciosa esconda o conflito.
- **Período lembrado maior que o comprovado:** manter ambos distinguíveis e
  indicar a parcela ainda sem sustentação.
- **Documento parcialmente ilegível:** registrar a limitação e não apresentar
  como confirmada a informação que não pode ser conferida.
- **Alteração sem indicação explícita de manutenção:** avaliar o contexto e
  sinalizar eventual inferência de continuidade.
- **Possível duplicidade:** identificar a suspeita sem eliminar informações
  antes da revisão.
- **Sobreposição de períodos:** mostrar a sobreposição e verificar se decorre
  de atividades simultâneas, duplicidade ou divergência.
- **Comprovação parcial:** relacionar o documento somente à parte da atividade
  que ele efetivamente sustenta.

Toda incerteza relevante deve poder ser revisada por uma pessoa. Informação
extraída diretamente, interpretação, inferência e confirmação não devem ser
apresentadas como equivalentes.

## 11. Papel futuro da Inteligência Artificial

A Inteligência Artificial poderá auxiliar depois que as informações estiverem
organizadas em estruturas previsíveis e dentro de um contexto delimitado. Esta
possibilidade não integra a implementação atual.

### Possíveis papéis

- sugerir a identificação de documentos;
- localizar o servidor nos documentos;
- sugerir Eventos Documentais;
- extrair nomes, datas, funções, objetos e vigências;
- comparar documentos sucessivos;
- sugerir continuidade ou encerramento de períodos;
- localizar divergências ou lacunas;
- sugerir possíveis Enquadramentos Normativos;
- explicar uma sugestão de Pontuação;
- produzir resumos estruturados para revisão;
- auxiliar na criação de uma cronologia;
- gerar material de apoio para o servidor escrever externamente seu memorial.

### Limites obrigatórios

- a IA não é fonte documental;
- a IA não substitui o Documento original;
- a IA não deve criar eventos sem indicar sua origem;
- a IA não deve inventar datas;
- a IA não deve presumir continuidade sem sinalizar a inferência;
- a IA não deve confirmar definitivamente um enquadramento;
- a IA não deve validar definitivamente a Pontuação;
- toda sugestão deve poder ser revisada;
- resultados relevantes devem possuir rastreabilidade;
- o usuário deve distinguir claramente informação extraída, inferida e
  confirmada;
- o sistema deve continuar funcional sem IA;
- regras determinísticas devem ser preferidas para cálculos normativos;
- a decisão final pertence ao servidor e, posteriormente, à banca avaliadora.

> A IA auxilia na interpretação e na organização; o sistema preserva a
> estrutura, a rastreabilidade e as regras; a pessoa mantém a decisão.

A estruturação prévia reduz contexto desnecessário, custo de processamento,
respostas inconsistentes, risco de alucinação, necessidade de reenviar
documentos completos e dificuldade de auditoria.

Não são definidos neste documento fornecedor, modelo, API, comandos de
interação, preços, arquitetura de agentes, representações vetoriais, banco
vetorial ou processamento local ou remoto. Esses temas deverão ser tratados em
documento e sprint próprios.

## 12. Fora do escopo atual

Estão fora do escopo deste modelo conceitual:

- implementação de classes;
- banco de dados;
- telas;
- automação por Inteligência Artificial;
- OCR;
- extração automática;
- escrita automática do memorial;
- decisão da banca;
- validação jurídica definitiva;
- definição final das regras da normativa;
- integração com sistemas externos.

## 13. Questões em aberto

- Uma atividade pode possuir vários períodos descontínuos?
- Quando períodos semelhantes devem formar uma atividade única?
- Quando devem ser atividades distintas?
- Como tratar documentos que comprovam várias atividades?
- Como representar uma informação apenas inferida?
- Quem confirma um Evento Documental?
- Como registrar divergências entre documentos?
- Uma atividade pode ser enquadrada em mais de um Item Normativo?
- Como evitar dupla contagem?
- Como tratar limites globais e limites por categoria?
- Como representar versões diferentes da normativa?
- Como organizar os documentos no Dossiê sem duplicar arquivos?
- Quais informações poderão ser enviadas à IA?
- Quais dados pessoais devem ser minimizados ou ocultados?
- Quais etapas devem funcionar exclusivamente por regras determinísticas?

Essas perguntas deverão ser respondidas em etapas futuras, com base na
normativa, nos casos reais e nas necessidades de revisão e auditoria.

## 14. Síntese do modelo

```text
Atividade lembrada
    ↓
Documentos localizados
    ↓
Eventos documentais identificados
    ↓
Períodos reconstruídos
    ↓
Atividade comprovada
    ↓
Enquadramento normativo
    ↓
Pontuação rastreável
    ↓
Dossiê organizado
```

O ProcDoc RSC organiza a trajetória funcional. Os documentos são suas fontes
de comprovação.

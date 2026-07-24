# Workflow de um Projeto RSC

## 1. Objetivo do Workflow

Este documento descreve como um usuário constrói, revisa e conclui um projeto
de RSC no ProcDoc. O foco está no processo de negócio: como uma lembrança da
trajetória profissional se transforma gradualmente em atividades comprovadas,
períodos consolidados, enquadramentos justificáveis, pontuação auditável e um
dossiê organizado.

O modelo conceitual e o workflow cumprem papéis complementares. O
`domain-model.md` estabelece o vocabulário e as relações do domínio; este
documento apresenta a sequência de trabalho na qual esses conceitos são
utilizados.

O workflow deve orientar futuramente o detalhamento de jornadas, casos de uso,
automações e formas de apoio ao usuário. Ele não pressupõe que todos os projetos
percorram o processo de maneira estritamente linear. Novas evidências podem
exigir o retorno a etapas já revisadas.

## 2. Princípios

- **O trabalho começa pelas atividades lembradas.** A trajetória é organizada
  a partir do que o servidor realizou, e não da ordem em que os documentos são
  encontrados.
- **Documentos sustentam atividades.** Eles fornecem as fontes necessárias para
  confirmar, limitar ou corrigir aquilo que foi inicialmente lembrado.
- **Atividades evoluem gradualmente.** Uma atividade pode nascer com poucas
  informações e ganhar precisão durante a análise.
- **Informações incompletas são admissíveis.** A ausência de uma data ou de uma
  evidência não deve impedir o registro inicial, desde que a incerteza permaneça
  explícita.
- **Toda decisão deve ser rastreável.** Períodos, enquadramentos e pontuações
  precisam poder ser relacionados às fontes e justificativas que os sustentam.
- **A revisão humana permanece necessária.** Sugestões e resultados
  automatizados não substituem a conferência do servidor.
- **O processo é iterativo.** Uma descoberta posterior pode alterar eventos,
  períodos, enquadramentos ou cálculos anteriores.
- **O trabalho pode ser interrompido e retomado.** O projeto deve conservar seu
  progresso, suas pendências e suas decisões ao longo do tempo.
- **A pontuação vem depois da compreensão.** O cálculo não deve orientar
  prematuramente a interpretação da trajetória.
- **Incertezas não são resolvidas silenciosamente.** Lacunas, divergências e
  inferências permanecem visíveis até que possam ser revisadas.

## 3. Estados de um Projeto

O estado do projeto oferece uma visão geral de sua maturidade. Ele não substitui
os estados particulares das atividades e pode regredir quando uma revisão
revelar novas pendências.

```text
Novo
  ↓
Em construção
  ↓
Em revisão
  ↓
Pronto para envio
  ↓
Arquivado
```

### Novo

O projeto foi iniciado, mas ainda não possui conteúdo suficiente para
representar a trajetória que será avaliada. A normativa aplicável e o contexto
da avaliação podem ainda estar sendo confirmados.

### Em construção

O servidor está cadastrando atividades, reunindo documentos, identificando
eventos, reconstruindo períodos ou preparando enquadramentos. Pendências e
incertezas são esperadas nesse estado.

### Em revisão

O conteúdo principal já foi organizado e passa por conferência documental,
cronológica, normativa e de pontuação. Uma revisão pode devolver atividades à
construção quando encontrar lacunas, divergências ou associações inadequadas.

### Pronto para envio

As atividades selecionadas foram revisadas, os períodos e enquadramentos estão
justificados, os cálculos foram conferidos e o dossiê está organizado. Esse
estado indica prontidão do material, não aprovação pela banca.

### Arquivado

O ciclo de trabalho foi encerrado e o projeto é preservado para consulta,
auditoria ou referência futura. O arquivamento não altera as fontes nem as
conclusões registradas.

## 4. Fluxo Geral do Processo

O percurso principal é:

```text
Criar o Projeto RSC
    ↓
Registrar atividades lembradas
    ↓
Reunir e relacionar documentos
    ↓
Identificar Eventos Documentais
    ↓
Reconstruir e consolidar períodos
    ↓
Revisar a comprovação das atividades
    ↓
Realizar o enquadramento normativo
    ↓
Calcular a pontuação
    ↓
Revisar o projeto como um todo
    ↓
Organizar o dossiê
    ↓
Marcar como pronto para envio
    ↓
Arquivar após o encerramento do ciclo
```

O fluxo admite retornos. Por exemplo, uma inconsistência encontrada no cálculo
pode revelar um período incorreto; uma revisão cronológica pode exigir novos
documentos; e uma fonte localizada posteriormente pode modificar uma atividade
já enquadrada.

## 5. Cadastro de Atividades

Uma atividade nasce quando o servidor registra algo profissionalmente
relevante que se recorda de ter realizado. Nesse momento, não é necessário que
a comprovação já esteja disponível.

O cadastro inicial deve conter apenas informação suficiente para distinguir e
orientar a busca da atividade, como:

- descrição do que foi realizado;
- contexto ou natureza da atuação;
- período aproximado, quando lembrado;
- observações que ajudem a localizar fontes;
- indicação de incertezas conhecidas.

Essa descrição inicial é uma alegação de trabalho a investigar, não uma
conclusão comprovada. Ao longo do processo, a atividade pode:

- receber documentos relacionados;
- ser detalhada ou corrigida;
- ter Eventos Documentais associados;
- adquirir um ou mais períodos comprovados;
- ser separada em atividades distintas;
- ser reunida a outro registro inicialmente duplicado;
- permanecer parcialmente comprovada;
- receber enquadramento e pontuação;
- voltar à análise após uma revisão.

O período lembrado deve permanecer distinguível do período comprovado. A
evolução da atividade não deve apagar a hipótese original nem apresentar uma
inferência como fato documental.

## 6. Inclusão de Documentos

Os documentos são reunidos conforme o servidor identifica fontes
potencialmente relevantes para as atividades cadastradas. A inclusão deve
preservar o conteúdo original e as informações necessárias à sua localização e
conferência.

Um documento pode ser relacionado inicialmente a uma atividade e, durante a
análise, revelar utilidade para outras. Da mesma forma, parte de seu conteúdo
pode ser irrelevante para o servidor ou para o projeto atual.

O relacionamento entre documentos e atividades não exige que toda a
interpretação esteja pronta. Ele pode expressar diferentes situações:

- fonte ainda não analisada;
- fonte possivelmente relacionada;
- fonte da qual já foram identificados eventos;
- fonte confirmada como sustentação;
- fonte descartada para determinada atividade, com justificativa.

Um mesmo documento pode sustentar várias atividades sem que seu conteúdo seja
duplicado. Cada uso deve preservar a referência comum à fonte original.

## 7. Extração de Eventos Documentais

A análise documental identifica as informações relevantes para reconstruir a
trajetória. Cada informação selecionada dá origem a um Evento Documental
vinculado à sua fonte.

O trabalho de identificação envolve:

1. localizar a passagem relevante;
2. identificar as pessoas e atividades a que ela se refere;
3. compreender a natureza da informação, como início, continuidade, alteração
   ou encerramento;
4. registrar datas e vigências explicitamente apresentadas;
5. relacionar o evento às atividades pertinentes;
6. indicar dúvidas, ilegibilidade ou necessidade de confirmação;
7. revisar a interpretação antes de tratá-la como confirmada.

A rastreabilidade deve permitir retornar à origem da informação e compreender
por que ela foi utilizada. Quando aplicável, a localização inclui página e
trecho.

Um documento pode produzir vários eventos. Um evento também pode contribuir
para mais de uma atividade, desde que seu significado em cada relação seja
claro.

Versões futuras poderão sugerir eventos com auxílio de Inteligência Artificial.
Essas sugestões deverão continuar vinculadas à fonte e sujeitas à revisão
humana antes de influenciar uma consolidação.

## 8. Consolidação de Períodos

A consolidação temporal combina Eventos Documentais para determinar durante
quanto tempo uma atividade foi exercida. Ela ocorre depois que existem
informações suficientes para analisar início, continuidade, mudanças e
encerramento.

### Continuidade

Documentos sucessivos podem representar um único período contínuo. Uma
alteração que afeta outras pessoas, mas mantém o servidor na atividade, não deve
criar uma interrupção artificial. Quando a continuidade depender de
interpretação, essa inferência deve ser sinalizada.

### Interrupções

Uma interrupção deve estar sustentada por informação documental ou ser
apresentada como hipótese pendente. Encerramento, dispensa, substituição do
servidor ou término de vigência podem delimitar o período, conforme o contexto.

Uma mesma atividade poderá conter períodos descontínuos caso essa possibilidade
seja confirmada pelas decisões futuras do domínio. Enquanto essa questão
permanecer aberta, o projeto deve preservar os eventos sem forçar uma união.

### Sobreposições

Períodos sobrepostos podem indicar atividades simultâneas legítimas,
duplicidade de registro ou conflito entre interpretações. A sobreposição deve
ser exibida para revisão e não eliminada automaticamente.

### Incertezas

Quando uma data inicial ou final não estiver comprovada, o período deve
permanecer aberto, parcial ou estimado conforme o caso. O sistema não deve
inventar limites temporais. O resultado da consolidação deve mostrar:

- intervalo alegado;
- intervalo comprovado;
- eventos utilizados;
- lacunas existentes;
- inferências realizadas;
- situação de revisão.

## 9. Enquadramento Normativo

O enquadramento ocorre quando a atividade já está suficientemente compreendida
e possui comprovação adequada para ser comparada à normativa aplicável.

O usuário analisa:

- a natureza da atividade;
- os períodos comprovados;
- os requisitos do Item Normativo;
- a documentação exigida;
- a unidade de cálculo;
- os limites e condições aplicáveis.

O enquadramento deve registrar uma justificativa, e não apenas indicar um item.
Essa justificativa explica por que a atividade atende ao critério e quais
fontes sustentam a conclusão.

Antes da revisão, o enquadramento pode permanecer proposto ou incerto. Novos
documentos, alterações no período ou identificação de possível dupla contagem
podem exigir sua reavaliação.

## 10. Cálculo da Pontuação

A pontuação é calculada somente após a consolidação da informação necessária e
o enquadramento normativo. Ela utiliza regras determinísticas e deve poder ser
reproduzida por outra pessoa a partir dos mesmos dados.

O cálculo considera:

- quantidade comprovada;
- unidade prevista;
- valor aplicável;
- limites do item ou da categoria;
- regras de acumulação;
- resultado anterior e posterior aos limites.

Cada resultado conserva uma memória de cálculo com regra, valores utilizados,
justificativa e situação de revisão. Alterações em períodos ou enquadramentos
devem tornar visível a necessidade de recalcular e revisar os resultados
afetados.

A pontuação calculada é uma preparação para avaliação. Ela não representa a
decisão definitiva da banca.

## 11. Revisão do Projeto

A revisão verifica a coerência do conjunto antes da preparação final. Ela deve
ser conduzida em quatro perspectivas complementares.

### Revisão documental

Confere se as fontes estão íntegras, legíveis, corretamente relacionadas e
rastreáveis. Verifica se cada conclusão relevante pode ser localizada em sua
origem.

### Revisão cronológica

Confere inícios, continuidades, interrupções, encerramentos, lacunas,
duplicidades e sobreposições. Compara períodos lembrados e comprovados.

### Revisão normativa

Confere se cada enquadramento corresponde à natureza da atividade, atende aos
requisitos e utiliza a versão correta da normativa. Examina justificativas e
possíveis enquadramentos concorrentes.

### Revisão da pontuação

Confere quantidades, unidades, valores, limites, acumulações e memória de
cálculo. Também procura dupla contagem entre atividades ou itens.

Uma pendência encontrada em qualquer perspectiva pode devolver a atividade à
etapa apropriada. O projeto somente deve ser considerado pronto quando as
pendências relevantes estiverem resolvidas ou explicitamente registradas.

## 12. Dossiê Final

O dossiê organiza o material necessário à apresentação e à conferência. Sua
estrutura deve permitir compreender, para cada atividade:

- o que o servidor realizou;
- qual período foi alegado;
- qual período foi comprovado;
- quais eventos sustentam a consolidação;
- quais documentos servem de fonte;
- qual enquadramento foi adotado;
- qual justificativa foi registrada;
- como a pontuação foi calculada.

Além da visão por atividade, o dossiê deve oferecer uma cronologia coerente e
uma síntese das pontuações. A organização deve favorecer a conferência sem
alterar as fontes originais nem ocultar incertezas relevantes.

O material consolidado poderá subsidiar a elaboração externa do memorial pelo
servidor. A redação do memorial não faz parte deste workflow.

## 13. Interrupção e Retomada

Um projeto pode permanecer incompleto por semanas ou meses enquanto o servidor
localiza documentos, esclarece divergências ou aguarda informações.

Ao interromper o trabalho, devem permanecer preservados:

- atividades e descrições lembradas;
- documentos reunidos e suas relações;
- eventos identificados e sua situação de revisão;
- períodos estimados e comprovados;
- incertezas, divergências e pendências;
- enquadramentos propostos ou confirmados;
- memórias de cálculo;
- progresso da revisão;
- estado geral do projeto.

Na retomada, o usuário deve conseguir compreender o ponto alcançado, o que já
foi confirmado e quais ações continuam pendentes. A passagem do tempo não deve
transformar hipóteses em conclusões nem eliminar o histórico das decisões.

## 14. Considerações Futuras

Versões futuras poderão empregar Inteligência Artificial para auxiliar na
identificação de documentos, sugestão de eventos, comparação de fontes,
detecção de lacunas, reconstrução cronológica e proposta de enquadramentos.

Esse apoio não altera o papel central do ProcDoc como responsável por preservar
o estado do projeto, a rastreabilidade, as regras e as decisões confirmadas. A
Inteligência Artificial poderá sugerir; o usuário continuará responsável pela
revisão, e as fontes continuarão sendo a base da comprovação.

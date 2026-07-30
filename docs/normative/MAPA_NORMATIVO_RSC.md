# Mapa Normativo Oficial do Motor RSC

## 1. Escopo, fonte e método

Este relatório cataloga padrões computacionais observáveis no Decreto nº
13.048, de 3 de julho de 2026, sem promover qualquer interpretação jurídica.
A fonte normativa é o [texto oficial publicado pela Presidência da
República](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d13048.htm),
incluindo os Anexos I a VI.

Os arquivos estruturados já existentes em `docs/normative/` foram utilizados
somente como controle de cobertura e rastreabilidade. A classificação em
famílias, Measurements e perfis computacionais é uma descrição técnica para
planejamento do motor; ela não substitui o texto oficial nem torna automática
uma decisão atribuída à CRSC-PCCTAE.

Cobertura confirmada:

| Anexo | Requisito do art. 3º | Critérios |
|---|---|---:|
| I | Participação em grupos, comissões, comitês, núcleos e representações | 10 |
| II | Projetos institucionais, gestão e apoio a ensino, pesquisa, extensão, inovação e assistência | 11 |
| III | Premiação pública por projetos implementados | 3 |
| IV | Responsabilidades técnico-administrativas ou especializadas | 8 |
| V | Função, direção ou assessoramento institucional | 4 |
| VI | Produção, prospecção e difusão de conhecimento | 19 |
| **Total** | **Seis requisitos** | **55** |

## 2. Regras transversais do Decreto

Os critérios dos anexos não são executados isoladamente. O Decreto também
determina:

- comprovação documental para os critérios (art. 4º);
- pontuação mínima, número mínimo de critérios e requisitos obrigatórios por
  nível (art. 5º);
- acumulação de pontos e preservação de saldo (art. 5º, § 2º);
- uso único de cada atividade, com decisão fundamentada da Comissão quando
  houver sobreposição (art. 5º, § 3º);
- exclusão de desempenho exclusivamente ordinário do cargo sem demonstração
  dos elementos qualitativos previstos (art. 5º, § 4º);
- apreciação do memorial e dos requerimentos pela CRSC-PCCTAE (arts. 6º e
  8º);
- interstício de três anos, estágio probatório e requisitos de instrução
  processual (arts. 11 a 14);
- atestação fundamentada de saberes e competências diferenciados pela
  Comissão (art. 15);
- limite global de concessão e disponibilidade orçamentária (arts. 14, X, e
  19).

Consequentemente, o cálculo aritmético de pontos e a decisão final de
reconhecimento são problemas distintos.

## 3. Vocabulário da tabela mestre

Dependências comuns:

- **D1 — comprovação documental:** documentos compatíveis com o art. 4º;
- **D2 — unicidade:** uma atividade não pode atender simultaneamente a mais de
  um critério;
- **D3 — não ordinariedade e relevância:** aplicação dos arts. 5º, § 4º, e
  15;
- **D4 — revisão humana:** enquadramento e decisão fundamentada da
  CRSC-PCCTAE;
- **D5 — variante funcional:** seleção documentada entre titular e substituto
  no Anexo V.

Na coluna “Humano”, **Sim** significa que a qualificação do fato, a
comprovação, a exclusão de sobreposição ou a decisão final não decorrem apenas
da aritmética da tabela.

## 4. Tabela mestre dos 55 critérios

| Código | Descrição oficial | Unidade | Measurement | Família | Perfil atual | Valor | Limite/observação específica | Dependências | Humano |
|---|---|---|---|---|---|---|---|---|---|
| DEC13048-ANX-I-ITEM-01 | Exercício do mandato como membro de conselhos superiores e conselhos de unidades e órgãos colegiados da Instituição Federal de Ensino | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-02 | Coordenação ou presidência de núcleos, representações, grupos de trabalho ou similares, comissões ou comitês previstos no âmbito da administração pública, regularmente instituídos, ou reconhecidos pelo órgão ou pela entidade | Por designação | COUNT | Designação | CUSTOM_TEXT | 4,5 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-03 | Participação como membro de núcleos, representações, grupos de trabalho ou similares, comissões ou comitês previstos no âmbito da administração pública, regularmente instituídos | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-04 | Participação como defensor dativo ou como membro de equipe designada em processos de apuração de materialidade e responsabilidade, como sindicância, processo administrativo disciplinar e tomada de contas especial | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-05 | Atuação em atividades de organização, fiscalização, execução de exame de seleção, vestibular ou concursos | Por designação | COUNT | Designação | CUSTOM_TEXT | 4,5 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-06 | Atuação em atividades de elaboração, revisão e/ou correção de provas de exame de seleção, vestibular ou concursos | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-07 | Exercício de mandato em entidade sindical da categoria | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 1,5 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-08 | Participação como membro em programas ou projetos de políticas públicas externas à Instituição Federal de Ensino, desde que comprovada a obtenção de resultados institucionais relevantes | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | Resultado institucional relevante | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-09 | Representação legal da Instituição Federal de Ensino junto a órgãos e entidades do Poder Público ou responsabilidade técnica junto a órgãos de fiscalização, controle e regulação | Por designação | COUNT | Designação | CUSTOM_TEXT | 7,5 | — | D1–D4 | Sim |
| DEC13048-ANX-I-ITEM-10 | Atuação técnica externa, formalmente autorizada ou reconhecida pela Instituição Federal de Ensino de lotação, em órgãos estatais ou paraestatais, escolas de governo, agências reguladoras ou organismos internacionais, com contribuição ou repercussão institucional | Por produto | COUNT | Produção/Produto | CUSTOM_TEXT | 4,5 | Autorização ou reconhecimento e repercussão institucional | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-01 | Coordenação de projetos institucionais (ensino, pesquisa, extensão, gestão e inovação) | Por projeto | COUNT | Projeto | CUSTOM_TEXT | 7,5 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-02 | Participação em atividades técnicas e/ou especializadas em projetos, incluída a elaboração de projetos pedagógicos, programas e/ou ações institucionais (ensino, pesquisa, extensão, gestão e inovação) | Por projeto | COUNT | Projeto | CUSTOM_TEXT | 4,5 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-03 | Participação em comissão ou conselho editorial de livros, revistas ou publicações científicas ou outras publicações acadêmicas | Por mandato | COUNT | Mandato | CUSTOM_TEXT | 7,5 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-04 | Participação em atividade de Cooperação Técnica Interinstitucional em projetos institucionais | Por projeto | COUNT | Projeto | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-05 | Participação em atividades de orientação, tutoria, preceptoria ou supervisão | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-06 | Participação em atividades de produção ou reformulação de material acessível, ou técnico de referência (manuais, roteiros técnicos) | Por produto | COUNT | Produção/Produto | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-07 | Participação em atividade de avaliação de trabalho ou atuação como jurado em eventos acadêmicos, científicos, culturais, esportivos e técnicos | Por evento | COUNT | Evento | PER_EVENT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-08 | Participação em atividade institucional de produção audiovisual, artística, exposição, podcast ou outras formas de apresentação | Por projeto | COUNT | Projeto | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-09 | Participação em programas de formação continuada e/ou ações de desenvolvimento de competências, desde que não utilizada para fins de aceleração da promoção na carreira (carga horária mínima de dez horas) | Por capacitação | COUNT | Capacitação | CUSTOM_TEXT | 1 | Mínimo de 10 h; vedado uso para aceleração | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-10 | Desempenho de atividade técnica especializada, formalmente reconhecida pela Instituição Federal de Ensino, com demonstração de domínio técnico diferenciado e contribuição institucional relevante na área de atuação | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 1 | Reconhecimento formal, domínio diferenciado e contribuição relevante | D1–D4 | Sim |
| DEC13048-ANX-II-ITEM-11 | Participação em capacitação, fórum, oficina, workshop e congresso, com carga horária mínima de dez horas, vinculada aos interesses da Instituição Federal de Ensino | Por evento | COUNT | Evento | PER_EVENT | 1 | Mínimo de 10 h e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-III-ITEM-01 | Recebimento de premiação de âmbito internacional por projeto implementado na administração pública | Por prêmio | COUNT | Premiação | CUSTOM_TEXT | 20 | Âmbito internacional | D1–D4 | Sim |
| DEC13048-ANX-III-ITEM-02 | Recebimento de premiação de âmbito nacional por projeto implementado na administração pública | Por prêmio | COUNT | Premiação | CUSTOM_TEXT | 15 | Âmbito nacional | D1–D4 | Sim |
| DEC13048-ANX-III-ITEM-03 | Recebimento de premiação de âmbito local ou institucional, formalmente instituído, por projeto implementado na administração pública | Por prêmio | COUNT | Premiação | CUSTOM_TEXT | 7,5 | Âmbito local/institucional e instituição formal | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-01 | Atuação tecnicamente qualificada na operação, na implantação, no suporte ou no apoio a desenvolvimento, parametrização ou aperfeiçoamento de sistemas estruturantes da administração pública | Por sistema | COUNT | Sistema | CUSTOM_TEXT | 4,5 | Sistema estruturante e atuação qualificada | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-02 | Elaboração de projeto básico ou de termo de referência, ou participação como membro de equipe de planejamento de contratação | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-03 | Exercício de atividades de gestão ou fiscalização de contratos de aquisição, serviços, convênios e acordos ou instrumentos correlatos | Por designação | COUNT | Designação | CUSTOM_TEXT | 4,5 | — | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-04 | Exercício de atividades relacionadas à licitação e às suas excepcionalidades | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-05 | Participação em atividades de apoio técnico especializado em políticas, programas e ações de promoção na área de saúde humana, animal e ambiente, de acessibilidade ou diversidade, de interesse institucional | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 3 | Interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-06 | Atuação tecnicamente qualificada em ambientes ou processos que demandem condições especiais de segurança, cuidado ou conformidade com requisitos legais e regulatórios, desde que não receba adicional de periculosidade ou insalubridade em razão das mesmas condições | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 3 | Sem adicional pelas mesmas condições | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-07 | Atuação em sistemas e/ou processos de trabalho institucionais em ensino, pesquisa, extensão, gestão e inovação, desde que não constitua atividade habitual do cargo | Por designação | COUNT | Designação | CUSTOM_TEXT | 3 | Não pode constituir atividade habitual | D1–D4 | Sim |
| DEC13048-ANX-IV-ITEM-08 | Atuação como responsável por setor ou por unidade, formalmente designado, desde que a designação não gere pagamento de remuneração | Por ano ou fração acima de seis meses | DURATION | Temporal | PER_YEAR | 4,5 | Designação sem remuneração | D1–D4 | Sim |
| DEC13048-ANX-V-ITEM-01 | Exercício de cargo de direção (CD-02) ou equivalente | Por ano ou fração acima de seis meses | DURATION + ENUM | Temporal/Função | PER_YEAR + ROLE_VARIANT | Titular 9; substituto 4,5 | Seleção de papel | D1–D5 | Sim |
| DEC13048-ANX-V-ITEM-02 | Exercício de cargo de direção (CD-03 e 04) ou equivalente | Por ano ou fração acima de seis meses | DURATION + ENUM | Temporal/Função | PER_YEAR + ROLE_VARIANT | Titular 7,5; substituto 3 | Seleção de papel | D1–D5 | Sim |
| DEC13048-ANX-V-ITEM-03 | Exercício de função gratificada (FG-01 e 02) ou equivalente | Por ano ou fração acima de seis meses | DURATION + ENUM | Temporal/Função | PER_YEAR + ROLE_VARIANT | Titular 4,5; substituto 1,5 | Seleção de papel | D1–D5 | Sim |
| DEC13048-ANX-V-ITEM-04 | Exercício de função gratificada (a partir da FG-03) ou equivalente | Por ano ou fração acima de seis meses | DURATION + ENUM | Temporal/Função | PER_YEAR + ROLE_VARIANT | Titular 3; substituto 1 | Seleção de papel | D1–D5 | Sim |
| DEC13048-ANX-VI-ITEM-01 | Carta patente relacionada aos interesses institucionais | Por patente | COUNT | Patente | CUSTOM_TEXT | 30 | Interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-02 | Participação relevante no desenvolvimento de protótipos, depósitos e/ou registros de propriedade intelectual ou privilégio de invenção relacionada aos interesses institucionais | Por projeto | COUNT | Projeto/Inovação | CUSTOM_TEXT | 25 | Participação relevante e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-03 | Participação em transferência de tecnologia, licenciamento ou exploração de ativo tecnológico, como autor ou inventor relacionada aos interesses institucionais | Por produto | COUNT | Produção tecnológica | CUSTOM_TEXT | 20 | Autoria/invenção e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-04 | Conclusão de curso de educação formal superior ao exigido para o ingresso no cargo de que é titular e que não seja utilizado para percepção de Incentivo à Qualificação – IQ | Por curso | COUNT | Titulação | CUSTOM_TEXT | 15 | Superior à exigência de ingresso e não usado no IQ | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-05 | Participação relevante na implantação ou desenvolvimento de produto, projeto, processo, técnica ou tecnologia de interesse institucional | Por produto | COUNT | Produção tecnológica | CUSTOM_TEXT | 15 | Participação relevante e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-06 | Atuação em atividade de liderança ou vice-liderança de grupo de pesquisa ou extensão registrado em órgão ou sistema oficial de reconhecimento institucional | Por grupo de pesquisa | COUNT | Grupo de pesquisa | CUSTOM_TEXT | 7,5 | Registro oficial | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-07 | Participação como membro em grupo de pesquisa devidamente registrado em órgão ou sistema oficial de reconhecimento institucional | Por projeto | COUNT | Projeto/Pesquisa | CUSTOM_TEXT | 3 | Registro oficial | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-08 | Aprovação de projeto para a captação de recursos para a Instituição Federal de Ensino | Por projeto | COUNT | Projeto/Captação | CUSTOM_TEXT | 7,5 | Projeto aprovado | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-09 | Publicação ou organização de livro relacionado aos interesses institucionais (com ISBN e Conselho Editorial) | Por produto | COUNT | Produção bibliográfica | CUSTOM_TEXT | 20 | ISBN, conselho editorial e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-10 | Autoria ou coautoria de capítulo de livro, de artigo publicado em revista especializada, jornal científico ou periódico, relacionado aos interesses institucionais | Por publicação | COUNT | Produção bibliográfica | PER_PUBLICATION | 7,5 | Autoria/coautoria e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-11 | Apresentação de trabalho de interesse institucional em congresso, seminário ou outros eventos | Por produto | COUNT | Produção bibliográfica/técnica | CUSTOM_TEXT | 4,5 | Interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-12 | Produção de material técnico, científico, metodológico ou administrativo estruturado que visa à difusão do conhecimento | Por produto | COUNT | Produção técnica | CUSTOM_TEXT | 4,5 | Material estruturado para difusão | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-13 | Avaliação do projeto de ensino e/ou pesquisa e/ou extensão e/ou inovação | Por projeto | COUNT | Projeto/Avaliação | CUSTOM_TEXT | 4,5 | — | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-14 | Participação em atividade de difusão ou apoio à formação institucional (expositor, facilitador, colaborador) | Por evento | COUNT | Evento/Formação | PER_EVENT | 3 | — | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-15 | Atuação formalmente autorizada como instrutor, tutor, palestrante, autor de conteúdo técnico ou orientador em ação formativa estruturada de interesse institucional, prevista em plano ou programa de desenvolvimento de pessoas | Por curso | COUNT | Curso/Formação | CUSTOM_TEXT | 4,5 | Autorização formal, ação estruturada e interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-16 | Atuação na coordenação de congresso, simpósio ou seminário de interesse institucional | Por evento | COUNT | Evento/Coordenação | PER_EVENT | 3,5 | Interesse institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-17 | Exercício de atividade de coorientação de trabalho de conclusão de curso em diferentes modalidades de ensino | Por evento | COUNT | Evento/Orientação | PER_EVENT | 4,5 | — | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-18 | Autoria de obra artística ou cultural registrada com contribuição ou repercussão institucional comprovada | Por produto | COUNT | Produção artística | CUSTOM_TEXT | 3 | Registro e repercussão institucional | D1–D4 | Sim |
| DEC13048-ANX-VI-ITEM-19 | Atuação institucional no enfrentamento de situações de surto, epidemia e pandemia | Por mês | DURATION | Temporal mensal | PER_MONTH | 1 | Atuação institucional e período comprovado | D1–D4 | Sim |

## 5. Catálogo de unidades normativas

O Decreto usa 14 expressões distintas de unidade:

| Unidade oficial | Critérios | Measurement mínima | Operação aritmética potencial |
|---|---:|---|---|
| Por ano ou fração acima de seis meses | 11 | DURATION | anos computáveis × valor |
| Por mês | 1 | DURATION | meses completos × valor |
| Por designação | 11 | COUNT | designações válidas × valor |
| Por produto | 8 | COUNT | produtos válidos × valor |
| Por projeto | 8 | COUNT | projetos válidos × valor |
| Por evento | 5 | COUNT | eventos válidos × valor |
| Por prêmio | 3 | COUNT + ENUM de âmbito | prêmios válidos × valor do critério |
| Por curso | 2 | COUNT | cursos válidos × valor |
| Por mandato | 1 | COUNT | mandatos válidos × valor |
| Por capacitação | 1 | COUNT + HOURS/BOOLEAN auxiliar | capacitações válidas × valor |
| Por sistema | 1 | COUNT | sistemas válidos × valor |
| Por patente | 1 | COUNT | patentes válidas × valor |
| Por grupo de pesquisa | 1 | COUNT + BOOLEAN/CATALOG auxiliar | grupos válidos × valor |
| Por publicação | 1 | COUNT | publicações válidas × valor |

`HOURS`, `BOOLEAN`, `ENUM` e `CATALOG` aparecem como fatos auxiliares de
qualificação, não como operandos de pontuação autônomos nas tabelas.

## 6. Catálogo das Measurements

| Measurement | Papel no mapa | Compatível com | Incompatível com |
|---|---|---|---|
| DURATION | intervalo canônico fechado | PER_YEAR, PER_MONTH | regras unitárias por contagem |
| COUNT | quantidade inteira de ocorrências já qualificadas | evento, publicação, designação, produto, projeto, prêmio, curso, mandato, capacitação, sistema, patente, grupo | regras temporais |
| QUANTITY | quantidade numérica genérica; alternativa técnica quando a unidade for explicitamente preservada | perfis de contagem que aceitem unidade declarada | temporal sem intervalo; categorias textuais não qualificadas |
| HOURS | verificação auxiliar de carga horária mínima | critérios II-9 e II-11 como condição | operando direto de pontuação dos anexos |
| BOOLEAN | condição auxiliar comprovada, como registro oficial ou ausência de uso anterior | filtros objetivos explicitamente modelados | substituição da revisão qualitativa |
| ENUM | variante finita | papel titular/substituto no Anexo V; âmbito de prêmio quando modelado | duração ou contagem isoladamente |
| CATALOG | identidade/categoria controlada | tipo documental, tipo de curso, função, sistema, produto ou projeto | cálculo aritmético direto |
| TEXT | conteúdo explicativo ou condição não estruturada | justificativas e revisão humana | execução aritmética automática |

Não há unidade oficial cuja pontuação seja diretamente “por BOOLEAN”, “por
TEXT”, “por ENUM” ou “por CATALOG”. Esses tipos complementam a qualificação do
fato.

## 7. Catálogo das famílias computacionais

Foram identificadas **17 famílias semânticas principais**:

1. temporal anual;
2. temporal mensal;
3. função/direção com variante de papel;
4. evento;
5. publicação;
6. designação;
7. produção/produto;
8. projeto;
9. mandato;
10. premiação;
11. capacitação;
12. sistema;
13. patente;
14. grupo de pesquisa;
15. curso/titulação/formação;
16. produção bibliográfica, técnica, tecnológica ou artística;
17. coordenação/participação, usada como qualificador semântico transversal.

As famílias 16 e 17 especializam outras unidades e não criam necessariamente
nova aritmética. Elas são necessárias para compatibilidade documental,
explicabilidade e prevenção de enquadramento indevido.

## 8. Formas computacionais realmente distintas

Separando semântica de aritmética, existem **quatro formas de cálculo**:

| Forma | Critérios | Descrição |
|---|---:|---|
| COUNT × FIXED_VALUE | 43 | Contagem de objetos válidos por valor fixo |
| DURATION_YEAR_WITH_FRACTION × FIXED_VALUE | 7 | Anos e política de fração de seis meses |
| DURATION_YEAR_WITH_FRACTION × ROLE_VALUE | 4 | Mesma decomposição temporal, com valor por titular/substituto |
| DURATION_MONTH × FIXED_VALUE | 1 | Meses-calendário completos por valor |
| **Total** | **55** | Os 3 critérios de prêmio estão incluídos em COUNT × FIXED_VALUE por possuírem valores próprios por critério/âmbito |

Assim, há **quatro formas aritméticas** e **15 perfis operacionais de unidade**
(as 14 unidades oficiais, com a unidade anual dividida entre valor fixo e
variante de papel).

## 9. Mapa preliminar de compatibilidade

| Perfil | Measurement principal | Auxiliares | Compatibilidade proibida |
|---|---|---|---|
| PER_YEAR | DURATION | ENUM no Anexo V | COUNT sem intervalo |
| PER_MONTH | DURATION | — | COUNT sem intervalo |
| PER_EVENT | COUNT | CATALOG de tipo de evento | DURATION como quantidade |
| PER_PUBLICATION | COUNT | CATALOG documental/bibliográfico | DURATION |
| PER_DESIGNATION | COUNT | documento/ato e CATALOG de papel | DURATION |
| PER_PRODUCT | COUNT | CATALOG de produto | DURATION |
| PER_PROJECT | COUNT | CATALOG de projeto e papel | DURATION |
| PER_AWARD | COUNT | ENUM de âmbito | DURATION |
| PER_COURSE | COUNT | CATALOG de curso; HOURS quando aplicável | DURATION |
| PER_MANDATE | COUNT | intervalo apenas como evidência auxiliar | DURATION como operando |
| PER_TRAINING | COUNT | HOURS e condições de uso | DURATION como operando |
| PER_SYSTEM | COUNT | CATALOG de sistema | DURATION |
| PER_PATENT | COUNT | CATALOG/identidade registral | DURATION |
| PER_RESEARCH_GROUP | COUNT | BOOLEAN de registro e ENUM de papel | DURATION |

Essa matriz é preliminar. Ela descreve a forma dos dados; não autoriza a
criação automática de fatos nem substitui a qualificação documental.

## 10. Explicabilidade futura

Toda explicação de cálculo deverá conservar:

1. código, anexo, item e texto oficial do critério;
2. objeto factual qualificado e documentos utilizados;
3. unidade normativa oficial;
4. Measurement e fatos auxiliares;
5. quantidade bruta e quantidade aplicada;
6. valor ou variante selecionada;
7. fórmula e resultado em `Decimal`;
8. verificações de limites específicos;
9. decisão sobre unicidade/sobreposição;
10. pendências e decisões humanas;
11. rastreabilidade até o dispositivo legal.

Exemplos de fórmulas explicáveis:

- temporal: `anos computáveis × pontos por ano`;
- mensal: `meses completos × pontos por mês`;
- evento: `eventos válidos × pontos por evento`;
- variante: `anos computáveis × valor documentado do papel`;
- unidade contável: `objetos válidos × pontos por unidade`.

## 11. Decisões humanas e limites de automação

### 11.1 Aritmética automatizável

Depois que os fatos estiverem qualificados e as pendências resolvidas, as
quatro formas aritméticas são determinísticas.

### 11.2 Qualificação não integralmente computável

Todos os 55 critérios permanecem dependentes de ao menos comprovação
documental, unicidade da atividade e decisão institucional. Vários contêm
expressões que exigem avaliação material, como:

- “resultados institucionais relevantes”;
- “contribuição ou repercussão institucional”;
- “domínio técnico diferenciado”;
- “participação relevante”;
- “interesse institucional”;
- “tecnicamente qualificada”;
- “atividade habitual” ou desempenho ordinário;
- equivalência de cargo ou função.

Essas expressões não possuem limiares numéricos definidos nos anexos.

### 11.3 Resultado final necessariamente institucional

Ainda que a pontuação de cada critério seja calculável, o Decreto atribui à
CRSC-PCCTAE a apreciação do memorial, o tratamento fundamentado de
sobreposições e a decisão sobre saberes e competências diferenciados.
Portanto, **nenhum dos 55 critérios permite, isoladamente, automatizar a
concessão final**.

## 12. Regras futuras a implementar

### 12.1 Regras aritméticas

| Prioridade | Regra | Cobertura potencial | Situação observada |
|---|---|---:|---|
| 1 | PER_YEAR + FRACTION_ABOVE_SIX_MONTHS | 11 | núcleo temporal existente; variante de papel ainda separada |
| 2 | PER_MONTH | 1 | núcleo temporal existente |
| 3 | PER_EVENT | 5 | existente |
| 4 | PER_PUBLICATION | 1 | perfil reconhecido; validar cobertura final |
| 5 | PER_COUNT_FIXED | 37 | generalização dos perfis ainda classificados como CUSTOM_TEXT |
| 6 | ROLE_VARIANT_VALUE | 4 | seleção titular/substituto antes do cálculo |

Os 37 perfis `CUSTOM_TEXT` são quantitativos, mas ainda precisam ser
subdivididos pelas unidades oficiais para preservar compatibilidade,
explicabilidade e semântica documental.

### 12.2 Regras de qualificação

- validação de carga horária mínima;
- seleção documentada de variante;
- registro oficial;
- interesse, relevância e repercussão institucional;
- não utilização para outra finalidade;
- atividade não habitual ou não ordinária;
- ausência de adicional/remuneração quando exigida;
- exclusão de duplicidade e tratamento de sobreposição;
- compatibilidade documental do art. 4º.

Essas regras não devem ser misturadas ao Kernel aritmético.

## 13. Respostas consolidadas

- **Quantas famílias existem?** Dezessete famílias semânticas principais.
- **Quantas regras realmente diferentes existem?** Quatro formas aritméticas;
  quinze perfis operacionais quando a unidade e a variante são consideradas.
- **Quantos critérios reutilizam cada forma?** 43 usam contagem por valor
  fixo; 7 usam tempo anual com valor fixo; 4 usam tempo anual com variante de
  papel; 1 usa tempo mensal.
- **Quais regras ainda não possuem implementação consolidada?** A
  generalização das unidades contáveis hoje marcadas como `CUSTOM_TEXT`, a
  seleção de variante titular/substituto e as qualificações auxiliares
  listadas na seção 12.
- **Quais critérios jamais poderão ser totalmente automatizados?** A
  aritmética de todos pode ser determinística após qualificação; nenhum dos 55
  autoriza decisão final totalmente automática, pois comprovação,
  não-ordinariedade, sobreposição e decisão fundamentada permanecem no âmbito
  institucional.

## 14. Limitações deste mapa

- Não foi produzida interpretação jurídica.
- Não foram inventados tetos, arredondamentos, equivalências ou documentos.
- “Família”, “Measurement” e “perfil operacional” são classificações de
  engenharia, não termos do Decreto.
- Atos complementares previstos nos arts. 4º, VII, 19, § 1º, e 21 poderão
  acrescentar detalhes operacionais.
- O texto eletrônico informa que não substitui a publicação no Diário Oficial
  da União; divergências devem ser conferidas na publicação oficial.

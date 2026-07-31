# ProcDocOrganizer

## Visão do Produto

Versão: Beta 1.1

> **Nenhuma informação entra no sistema sem contexto, e nenhuma conclusão sai
> do sistema sem explicação.**

---

# Missão

O ProcDocOrganizer existe para transformar a preparação e a avaliação de
processos de Reconhecimento de Saberes e Competências (RSC) em um processo
organizado, transparente, rastreável e compreensível.

O sistema não substitui o julgamento humano.

Seu papel é organizar informações, preservar evidências e tornar a avaliação
mais clara e consistente.

---

# Problema

A preparação de um processo de RSC normalmente envolve:

- grande quantidade de documentos;
- múltiplas evidências;
- diversos critérios normativos;
- dificuldade para localizar documentos;
- dificuldade para compreender como a pontuação foi construída;
- baixa rastreabilidade;
- retrabalho.

O ProcDocOrganizer foi criado para eliminar essas dificuldades.

---

# Usuários

O produto possui dois usuários principais.

## Candidato

Deseja:

- organizar documentos;
- produzir evidências;
- acompanhar sua pontuação;
- identificar pendências;
- compreender a avaliação;
- preparar um processo consistente.

## Comissão Avaliadora

Deseja:

- compreender rapidamente o processo;
- localizar documentos;
- verificar rastreabilidade;
- revisar enquadramentos;
- confirmar pontuações;
- justificar decisões.

---

# O que o sistema faz

O ProcDocOrganizer organiza:

```text
Projeto
↓
Documentos
↓
Evidências
↓
ExecutionFacts
↓
ExecutionBindings
↓
Avaliação
↓
Resultados
↓
Relatórios
```

Sempre preservando a rastreabilidade completa.

---

# O que o sistema NÃO faz

O sistema NÃO:

- decide pelo avaliador;
- interpreta normas automaticamente;
- cria pontuação arbitrária;
- altera documentos;
- substitui o julgamento humano.

Toda decisão normativa permanece humana.

---

# Princípios Fundamentais

## 1. A decisão sempre pertence ao usuário

O sistema apoia. Nunca decide.

## 2. Toda pontuação deve ser explicável

Nenhum resultado pode existir sem rastreabilidade.

## 3. Todo documento deve possuir propósito

Sempre deve ser possível responder:

> Por que este documento está neste processo?

## 4. Toda evidência deve possuir origem verificável

Nenhuma informação perde sua rastreabilidade.

## 5. Avaliações podem ser parciais

Pendências operacionais não impedem o trabalho.

Princípio P-001 — Avaliação Progressiva.

## 6. Simplicidade é prioridade

Uma solução simples e compreensível é preferível a uma solução sofisticada e
difícil de manter.

## 7. O Core é estável

Mudanças no domínio exigem justificativa arquitetural e ADR.

---

# Filosofia da IA

A Inteligência Artificial é uma assistente. Nunca uma substituta.

Ela poderá:

- sugerir;
- localizar;
- resumir;
- identificar padrões;
- encontrar possíveis inconsistências.

Ela nunca deverá:

- decidir;
- enquadrar automaticamente;
- conceder pontuação;
- interpretar normas sem validação humana.

---

# Filosofia da Interface

O sistema deve responder rapidamente às seguintes perguntas:

- Como está meu processo?
- O que devo fazer agora?
- Onde está este documento?
- O que este documento comprova?
- Por que obtive esta pontuação?

O usuário nunca deve precisar procurar essas respostas em múltiplas telas.

---

# Critérios para novas funcionalidades

Uma nova funcionalidade somente deverá ser implementada quando atender pelo
menos um dos objetivos abaixo:

- reduzir o tempo de trabalho;
- aumentar a rastreabilidade;
- melhorar a compreensão da avaliação;
- reduzir erros operacionais;
- facilitar a navegação;
- preservar a simplicidade do sistema.

---

# O que não queremos nos tornar

O ProcDocOrganizer não pretende ser:

- GED corporativo;
- ERP;
- Sistema de RH;
- Plataforma de BI genérica;
- Framework de IA.

Seu foco continuará sendo o apoio à preparação e à avaliação de processos de
RSC.

---

# Visão de Longo Prazo

Ser a principal plataforma de organização, rastreabilidade e apoio à avaliação
de processos de Reconhecimento de Saberes e Competências, preservando a decisão
humana e oferecendo transparência completa em todas as etapas da avaliação.

---

# Estado da Beta 1.1

A Beta 1.1 conclui o ciclo de produtividade iniciado sobre o Core estabilizado
na Beta 1.0. A release entrega o shell produtivo integrado, Dashboard, Review,
Inspector de Resources, Insights, Coverage, navegação com histórico e
autoridade única da sessão ativa.

O próximo ciclo será definido por decisão de produto e arquitetura. Esta visão
não antecipa novas funcionalidades.

## Limitações conhecidas

- ExecutionFact ainda não possui projector e aparece como `UNAVAILABLE` no
  Resource Inspector.
- Evaluation, Results e Report devem ser regenerados após reabrir o Project.
- O banco legado `productive-shell.sqlite` não possui importação automática.

# Guia de Extensão do Pipeline Normativo

## 1. Princípio

Extensões devem entrar por dados, adapters ou componentes anteriores/posteriores
ao pipeline. Um estágio determinístico existente não deve ser modificado para
acomodar conteúdo específico de instituição ou decreto.

## 2. Matriz de extensibilidade

| Extensão | Sem modificar pipeline? | Condição |
|---|:---:|---|
| IA | sim, parcialmente | produzir metadata/propostas fora dos Engines |
| Novo decreto | sim, com ressalvas | adapter compatível e IDs não colidentes |
| Nova universidade | sim | fatos e políticas fora do núcleo |
| Novos critérios | sim | expostos pelo Modelo Normativo |
| Novas categorias documentais | sim | expostas pelo catálogo documental |
| Novo tipo de condição | não atualmente | enum e dispatch precisam mudar |

## 3. IA

Uma futura IA pode atuar como geradora de dados candidatos a revisão:

- sugerir `criterion_candidate_links`;
- preparar fatos para condições `ASSISTED`;
- redigir proposta preliminar.

Ela deve operar antes dos Engines determinísticos, marcar autoria/origem e
submeter toda saída a validação. Não deve:

- alterar condições `STRUCTURED`;
- preencher ausência como fato;
- produzir `HUMAN_ONLY`;
- mudar estados consolidados diretamente.

O pipeline não precisa mudar se a IA entregar o mesmo contrato factual.
Entretanto, os schemas de metadata devem ser tipados antes dessa integração.

## 4. Novo decreto

É tecnicamente possível fornecer outro adapter que implemente as capacidades
de critério, requisito, documento e condição.

Ressalvas:

- a documentação conceitual atual nomeia `Decree13048NormativeModel`;
- IDs precisam incluir namespace do documento;
- estados e operações estruturadas precisam ser compatíveis;
- `NormativeOrigin` já suporta `document_id` genérico;
- testes devem impedir mistura de requisitos de decretos diferentes.

## 5. Novas universidades

O núcleo não contém nome de universidade nem política local. Dados
institucionais podem entrar no `EvaluationContext`.

Atos complementares locais precisam de origem própria e não podem ser
misturados silenciosamente com o decreto. Recomenda-se namespace institucional
e adapter normativo composto.

## 6. Novos critérios

Podem ser adicionados sem alterar os Engines quando:

- possuem ID estável;
- apontam para requisito existente;
- fornecem origem normativa;
- vínculos factuais usam o schema esperado.

Nenhum switch por criterion ID foi encontrado.

## 7. Novas categorias documentais

Podem ser adicionadas pelo Modelo Normativo sem modificar o Evidence
Qualification Engine. O Engine consulta por ID e não possui lista fixa.

O Candidate Engine também consulta categorias hoje; essa duplicação deve ser
removida antes de ampliar o catálogo.

## 8. Novos tipos de condição

Classificações novas exigem modificação de:

- `ConditionClassification`;
- dispatch de `_verify`;
- estados e consolidação, conforme o caso;
- testes e documentação.

Operações `STRUCTURED` novas também exigem alterar `STRUCTURED_OPERATIONS` e
`_apply`.

Recomendação futura: registry de operadores determinísticos com contratos
imutáveis e whitelist explícita. Isso melhora abertura para extensão sem
permitir execução arbitrária.

## 9. Checklist para extensões

1. Preserva origem normativa?
2. Introduz fato ou apenas projeção?
3. Mantém determinismo?
4. Exige revisão humana?
5. Usa namespace de IDs?
6. Mantém coleções imutáveis?
7. Acrescenta operação ou nova semântica?
8. Pode ser implementada por adapter?
9. Mantém estados sem significado de aprovação?
10. Possui teste de rastreabilidade ponta a ponta?

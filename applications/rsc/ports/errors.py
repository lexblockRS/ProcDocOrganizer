"""Erros estáveis dos contratos de persistência RSC."""


class DuplicateFunctionalAssignmentEvidenceError(ValueError):
    """Indica tentativa de inserir uma atribuição com ID existente."""


class FunctionalAssignmentEvidencePersistenceError(RuntimeError):
    """Indica falha persistente independente do driver utilizado."""


class FunctionalExercisePersistenceError(RuntimeError):
    """Indica falha ao persistir ou reconstruir exercício funcional."""


class FunctionalExerciseAssignmentEvidenceNotFoundError(LookupError):
    """Indica proveniência que não existe no armazenamento do projeto."""


class ActivityPersistenceError(RuntimeError):
    """Indica falha ao persistir ou reconstruir uma atividade."""


class ActivityRelationNotFoundError(LookupError):
    """Indica relação da atividade ausente no armazenamento do projeto."""

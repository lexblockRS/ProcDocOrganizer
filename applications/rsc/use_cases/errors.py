"""Erros próprios da futura camada de casos de uso RSC."""


class RscUseCaseError(RuntimeError):
    """Erro esperado na coordenação de um caso de uso RSC."""


class InvalidCommandError(RscUseCaseError):
    """O comando não possui dados aceitáveis para o caso de uso."""


class ProcessNotFoundError(RscUseCaseError):
    """O processo solicitado não foi encontrado."""


class ActivityNotFoundError(RscUseCaseError):
    """A atividade solicitada não foi encontrada."""


class DocumentNotFoundError(RscUseCaseError):
    """O documento solicitado não foi encontrado."""


class EvidenceNotFoundError(RscUseCaseError):
    """A evidência solicitada não foi encontrada."""


class DuplicateEntityError(RscUseCaseError):
    """Uma entidade com a mesma identidade já existe."""


class DomainValidationError(RscUseCaseError):
    """Uma validação explícita do domínio impediu a operação."""


class SessionDisposedError(RscUseCaseError):
    """A operação tentou usar uma sessão já descartada."""

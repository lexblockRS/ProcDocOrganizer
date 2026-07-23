"""Exceções públicas do módulo Search."""


class SearchError(RuntimeError):
    """Base dos erros públicos de pesquisa."""


class InvalidSearchQueryError(SearchError, ValueError):
    """A consulta viola um contrato público de Search."""


class UnsupportedSearchFeatureError(SearchError):
    """O mecanismo não oferece uma capacidade solicitada."""


class SearchIndexUnavailableError(SearchError):
    """O índice não está disponível para consulta."""


class SearchIndexCorruptedError(SearchError):
    """O índice existe, mas sua estrutura ou conteúdo está corrompido."""


class SearchExecutionError(SearchError):
    """A consulta falhou sem caracterizar ausência ou corrupção do índice."""


class SearchIndexMaintenanceError(SearchError):
    """Base dos erros públicos de manutenção do índice."""


class InvalidIndexDocumentError(SearchIndexMaintenanceError, ValueError):
    """Um documento não atende ao contrato neutro de indexação."""


class SearchIndexWriteError(SearchIndexMaintenanceError):
    """Uma escrita atômica no índice falhou."""


class SearchIndexRebuildError(SearchIndexMaintenanceError):
    """A reconstrução integral falhou e preservou o índice anterior."""


class SearchIndexSourceError(SearchIndexMaintenanceError):
    """A fonte canônica não pôde produzir documentos indexáveis."""

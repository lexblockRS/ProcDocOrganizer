"""Coordenação entre o workspace visual e o SearchService."""

import logging

from contracts import DocumentNavigationRequest
from models import EvidenceSourceCandidate
from services.search import (
    InvalidSearchQueryError,
    SearchExecutionError,
    SearchIndexCorruptedError,
    SearchIndexUnavailableError,
    SearchOptions,
    SearchQuery,
    UnsupportedSearchFeatureError,
)


logger = logging.getLogger(__name__)


class SearchController:
    EMPTY_MESSAGE = "Informe um texto para pesquisar."
    NO_RESULTS_MESSAGE = "Nenhum resultado encontrado."
    ERROR_MESSAGE = "Não foi possível concluir a pesquisa. Tente novamente."
    INVALID_QUERY_MESSAGE = "A consulta informada é inválida."
    UNSUPPORTED_FEATURE_MESSAGE = (
        "Esta opção de pesquisa não é suportada."
    )
    INDEX_UNAVAILABLE_MESSAGE = "O índice de pesquisa não está disponível."
    INDEX_CORRUPTED_MESSAGE = "O índice de pesquisa está inválido ou corrompido."
    EXECUTION_ERROR_MESSAGE = "Não foi possível executar a pesquisa."

    NO_SELECTION_MESSAGE = "Selecione um resultado para criar uma evidência."
    INVALID_RESULT_MESSAGE = (
        "Este resultado não possui uma referência documental válida."
    )
    PREPARE_EVIDENCE_ERROR_MESSAGE = (
        "Não foi possível preparar a evidência a partir deste resultado."
    )
    NAVIGATION_ERROR_MESSAGE = (
        "Não foi possível abrir o documento selecionado."
    )

    def __init__(
        self,
        workspace,
        search_service=None,
        evidence_source_requested=None,
        document_navigation_requested=None,
    ):
        self.workspace = workspace
        self.search_service = search_service
        self.evidence_source_requested = evidence_source_requested
        self.document_navigation_requested = document_navigation_requested
        workspace.search_requested.connect(self.search)
        workspace.clear_requested.connect(self.clear)
        workspace.result_selected.connect(self.select_result)
        workspace.create_evidence_requested.connect(
            self.request_create_evidence_from_result
        )
        workspace.open_result_requested.connect(
            self.request_document_navigation
        )

    def set_search_service(self, search_service) -> None:
        self.search_service = search_service
        self.clear()

    def search(
        self, query: str, options: SearchOptions | None = None
    ) -> None:
        normalized = query.strip() if isinstance(query, str) else ""
        if not normalized:
            self.workspace.set_results(())
            self.workspace.show_message(self.EMPTY_MESSAGE)
            return
        if self.search_service is None:
            self.workspace.set_results(())
            self.workspace.show_message(self.ERROR_MESSAGE)
            return
        try:
            search_query = SearchQuery(
                text=normalized,
                options=options or SearchOptions(),
            )
            result_page = self.search_service.search(search_query)
        except InvalidSearchQueryError:
            self._show_search_error(self.INVALID_QUERY_MESSAGE)
            return
        except UnsupportedSearchFeatureError:
            self._show_search_error(self.UNSUPPORTED_FEATURE_MESSAGE)
            return
        except SearchIndexUnavailableError:
            self._show_search_error(self.INDEX_UNAVAILABLE_MESSAGE)
            return
        except SearchIndexCorruptedError:
            self._show_search_error(self.INDEX_CORRUPTED_MESSAGE)
            return
        except SearchExecutionError:
            self._show_search_error(self.EXECUTION_ERROR_MESSAGE)
            return
        except Exception:
            logger.exception("Falha inesperada ao coordenar pesquisa.")
            self._show_search_error(self.ERROR_MESSAGE)
            return
        self.workspace.set_results(result_page)
        self.workspace.show_message(
            "" if result_page.hits else self.NO_RESULTS_MESSAGE
        )

    def _show_search_error(self, message: str) -> None:
        self.workspace.set_results(())
        self.workspace.show_message(message)

    def clear(self) -> None:
        self.workspace.clear()

    def select_result(self, result) -> None:
        if result is not None:
            self.workspace.show_result(result)

    def set_evidence_source_requested(self, callback) -> None:
        self.evidence_source_requested = callback

    def set_document_navigation_requested(self, callback) -> None:
        self.document_navigation_requested = callback

    def request_document_navigation(self, hit) -> bool:
        if hit is None or self.document_navigation_requested is None:
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        try:
            request = DocumentNavigationRequest(
                document_identity=hit.document_identity,
                page_number=hit.page_number,
            )
            accepted = bool(self.document_navigation_requested(request))
        except (AttributeError, TypeError, ValueError):
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        except Exception:
            logger.exception(
                "Falha inesperada ao coordenar navegação documental."
            )
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        if accepted:
            self.workspace.show_message("")
        else:
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
        return accepted

    def request_create_evidence_from_selected_result(self) -> bool:
        return self.request_create_evidence_from_result(
            self.workspace.selected_result()
        )

    def request_create_evidence_from_result(self, result) -> bool:
        if result is None:
            self.workspace.show_message(self.NO_SELECTION_MESSAGE)
            return False
        try:
            candidate = EvidenceSourceCandidate.from_search_hit(result)
        except (TypeError, ValueError, AttributeError):
            self.workspace.show_message(self.INVALID_RESULT_MESSAGE)
            return False
        if self.evidence_source_requested is None:
            self.workspace.show_message(self.PREPARE_EVIDENCE_ERROR_MESSAGE)
            return False
        try:
            accepted = bool(self.evidence_source_requested(candidate))
        except Exception:
            logger.exception(
                "Falha inesperada ao coordenar criação de evidência da pesquisa."
            )
            self.workspace.show_message(self.PREPARE_EVIDENCE_ERROR_MESSAGE)
            return False
        if accepted:
            self.workspace.show_message("")
        return accepted

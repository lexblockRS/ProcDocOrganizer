"""View do acervo documental baseada no workspace documental existente."""

from .documents_workspace import DocumentsWorkspace


class DocumentsView(DocumentsWorkspace):
    """Expõe gestão do acervo preservando a navegação documental existente."""

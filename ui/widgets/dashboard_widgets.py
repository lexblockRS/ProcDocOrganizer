"""Widgets visuais reutilizáveis do Dashboard."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

CARD_MINIMUM_WIDTH = 150
CARD_MINIMUM_HEIGHT = 88
CONTENT_SPACING = 10
SECTION_SPACING = 8


def _scaled_font(widget, scale: float, *, bold=False):
    font = widget.font()
    point_size = font.pointSizeF()
    if point_size > 0:
        font.setPointSizeF(point_size * scale)
    font.setBold(bold)
    return font


class SummaryCard(QFrame):
    """Apresenta um único indicador, sem interpretar seu significado."""

    def __init__(self, title: str, value="0", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("summaryCard")
        self.setMinimumSize(
            CARD_MINIMUM_WIDTH, CARD_MINIMUM_HEIGHT
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.setAccessibleName(title)
        self.setAccessibleDescription(f"{title}: {value}")

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("summaryCardValue")
        self.value_label.setFont(
            _scaled_font(self.value_label, 1.7, bold=True)
        )
        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value) -> None:
        self.value_label.setText(str(value))
        self.setAccessibleDescription(
            f"{self.title_label.text()}: {value}"
        )


class DashboardSection(QFrame):
    """Agrupa conteúdo do Dashboard sob um título curto."""

    def __init__(self, title: str, content: QWidget, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.title_label = QLabel(title)
        self.title_label.setFont(
            _scaled_font(self.title_label, 1.15, bold=True)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SECTION_SPACING)
        layout.addWidget(self.title_label)
        layout.addWidget(content)


class DashboardHeader(QFrame):
    """Apresenta a identificação do projeto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_name_label = QLabel()
        self.project_name_label.setFont(
            _scaled_font(self.project_name_label, 1.7, bold=True)
        )
        self.application_label = QLabel()
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.created_label = QLabel()
        self.created_label.setWordWrap(True)
        self.last_opened_label = QLabel()
        self.last_opened_label.setWordWrap(True)

        metadata = QVBoxLayout()
        metadata.setSpacing(2)
        metadata.addWidget(self.created_label)
        metadata.addWidget(self.last_opened_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.project_name_label)
        layout.addWidget(self.application_label)
        layout.addWidget(self.path_label)
        layout.addLayout(metadata)

    def set_values(
        self,
        *,
        project_name: str,
        application_name: str,
        project_path: str,
        created_at: str,
        last_opened_at: str,
    ) -> None:
        self.project_name_label.setText(project_name)
        self.application_label.setText(
            f"Aplicação: {application_name}"
        )
        self.path_label.setText(f"Caminho: {project_path}")
        self.path_label.setToolTip(project_path)
        self.created_label.setText(f"Criação: {created_at}")
        self.last_opened_label.setText(
            f"Última abertura: {last_opened_at}"
        )


class ShortcutButton(QPushButton):
    """Botão genérico que expõe uma intenção de navegação."""

    requested = Signal()

    def __init__(self, text: str, tooltip: str, parent=None):
        super().__init__(text, parent)
        self.setToolTip(tooltip)
        self.setAccessibleName(text)
        self.setMinimumHeight(36)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.clicked.connect(self.requested)


class ResponsiveCardGrid(QWidget):
    """Reorganiza cartões conforme a largura disponível."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = []
        self._columns = 0
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(CONTENT_SPACING)
        self._layout.setVerticalSpacing(CONTENT_SPACING)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_cards(self, cards) -> None:
        self._cards = list(cards)
        for card in self._cards:
            if card.property("dashboardCardVisible") is None:
                card.setProperty("dashboardCardVisible", True)
        self._relayout(force=True)

    def set_card_visible(self, card, visible: bool) -> None:
        if card not in self._cards:
            raise ValueError("O widget não pertence a este grid.")
        card.setProperty("dashboardCardVisible", bool(visible))
        card.setVisible(bool(visible))
        self._relayout(force=True)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._relayout()

    def refresh_layout(self) -> None:
        self._relayout(force=True)

    def _relayout(self, force=False) -> None:
        margins = self._layout.contentsMargins()
        available = max(
            self.width() - margins.left() - margins.right(),
            CARD_MINIMUM_WIDTH,
        )
        columns = max(
            1,
            (available + CONTENT_SPACING)
            // (CARD_MINIMUM_WIDTH + CONTENT_SPACING),
        )
        if not force and columns == self._columns:
            return
        self._columns = columns
        for card in self._cards:
            self._layout.removeWidget(card)
        visible_cards = [
            card
            for card in self._cards
            if card.property("dashboardCardVisible") is not False
        ]
        for index, card in enumerate(visible_cards):
            self._layout.addWidget(
                card,
                index // columns,
                index % columns,
            )

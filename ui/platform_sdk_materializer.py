"""Materialização Qt interna dos componentes declarativos do SDK."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from platform_sdk import ApplicationView, DashboardCard, DashboardPanel
from ui.widgets import (
    DashboardSection,
    ResponsiveCardGrid,
    SummaryCard,
)


class _SdkDashboardCard(SummaryCard):
    def __init__(self, component: DashboardCard):
        super().__init__(component.title)
        self._component = component
        self.refresh_dashboard(None)

    def refresh_dashboard(self, session) -> bool:
        value = self._component.value
        self.set_value(value(session) if callable(value) else value)
        return True


class _SdkDashboardPanel(DashboardSection):
    def __init__(self, component: DashboardPanel):
        grid = ResponsiveCardGrid()
        self.cards = {
            card.key or str(index): _SdkDashboardCard(card)
            for index, card in enumerate(component.cards)
        }
        grid.set_cards(self.cards.values())
        super().__init__(component.title, grid)

    def refresh_dashboard(self, session) -> bool:
        for card in self.cards.values():
            card.refresh_dashboard(session)
        return True


def materialize_application_view(component: object) -> QWidget:
    if isinstance(component, QWidget):
        return component
    if not isinstance(component, ApplicationView):
        raise TypeError(
            "View factory deve retornar ApplicationView."
        )
    widget = QWidget()
    layout = QVBoxLayout(widget)
    title = QLabel(component.title)
    font = title.font()
    font.setBold(True)
    title.setFont(font)
    layout.addWidget(title)
    for line in component.content:
        label = QLabel(line)
        label.setWordWrap(True)
        layout.addWidget(label)
    layout.addStretch()
    return widget


def materialize_dashboard_component(component: object) -> QWidget:
    if isinstance(component, QWidget):
        return component
    if isinstance(component, DashboardCard):
        return _SdkDashboardCard(component)
    if isinstance(component, DashboardPanel):
        return _SdkDashboardPanel(component)
    raise TypeError(
        "Dashboard factory deve retornar DashboardCard ou DashboardPanel."
    )

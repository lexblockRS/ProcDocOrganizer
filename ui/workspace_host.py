"""Host visual mínimo para o Workspace lógico."""

from PySide6.QtWidgets import QStackedWidget, QWidget


class WorkspaceHost(QStackedWidget):
    """Recebe widgets sem incorporar regras de navegação."""

    @property
    def active_widget(self) -> QWidget | None:
        return self.currentWidget()

    def set_active_widget(self, widget: QWidget) -> None:
        if not isinstance(widget, QWidget):
            raise TypeError("widget deve ser QWidget.")
        if self.indexOf(widget) < 0:
            self.addWidget(widget)
        self.setCurrentWidget(widget)

    def replace_active_widget(self, widget: QWidget) -> None:
        if not isinstance(widget, QWidget):
            raise TypeError("widget deve ser QWidget.")
        current = self.currentWidget()
        if current is widget:
            return
        if current is not None:
            self.removeWidget(current)
            current.setParent(None)
            current.deleteLater()
        self.set_active_widget(widget)

    def release_active_widget(self) -> None:
        current = self.currentWidget()
        if current is None:
            return
        self.removeWidget(current)
        current.setParent(None)
        current.deleteLater()

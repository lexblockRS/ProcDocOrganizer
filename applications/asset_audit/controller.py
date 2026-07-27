"""Controller público e independente do Host."""

from .descriptor import MAIN_VIEW_ID, OPEN_HOME_COMMAND


class AssetAuditController:
    def __init__(self):
        self.executed_commands = []

    def execute(self, command_id, context=None):
        if command_id != OPEN_HOME_COMMAND:
            raise ValueError(
                f"Comando Asset Audit desconhecido: {command_id}."
            )
        self.executed_commands.append((command_id, context))
        return MAIN_VIEW_ID

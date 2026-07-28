"""Validações estruturais compartilhadas pelos casos de uso."""

from uuid import UUID

from .errors import InvalidCommandError


def require_command(command: object, expected_type: type) -> None:
    if command is None:
        raise InvalidCommandError("command é obrigatório.")
    if not isinstance(command, expected_type):
        raise InvalidCommandError(
            f"command deve ser {expected_type.__name__}."
        )


def require_uuid(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCommandError(f"{field} deve ser uma string UUID.")
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise InvalidCommandError(f"{field} deve ser um UUID válido.") from exc


def require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidCommandError(f"{field} é obrigatório.")
    return " ".join(value.split())

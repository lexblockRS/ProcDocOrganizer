"""Metadados estáticos e imutáveis de uma Application da plataforma."""

from dataclasses import dataclass
import re


_APPLICATION_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*$")
_CAPABILITY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9._-]*$")
_VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True, order=True, slots=True)
class Version:
    """Versão numérica comparável no formato major.minor.patch."""

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for name, value in (
            ("major", self.major),
            ("minor", self.minor),
            ("patch", self.patch),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} deve ser um inteiro.")
            if value < 0:
                raise ValueError(f"{name} não pode ser negativo.")

    @classmethod
    def parse(cls, value: str) -> "Version":
        if not isinstance(value, str):
            raise TypeError("version deve ser uma string.")
        match = _VERSION_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(
                "version deve usar o formato major.minor.patch."
            )
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True, slots=True)
class ApplicationDescriptor:
    """Descrição passiva da identidade e compatibilidade de uma Application."""

    application_id: str
    display_name: str
    version: Version
    minimum_platform_version: Version
    supported_project_schema_versions: tuple[int, ...] = ()
    required_capabilities: frozenset[str] = frozenset()
    provided_capabilities: frozenset[str] = frozenset()
    description: str = ""
    icon: str | None = None
    author: str = ""
    services: tuple[str, ...] = ()
    views: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.application_id, str):
            raise TypeError("application_id deve ser uma string.")
        if not _APPLICATION_ID_PATTERN.fullmatch(self.application_id):
            raise ValueError(
                "application_id deve ser um identificador estável."
            )
        if not isinstance(self.display_name, str):
            raise TypeError("display_name deve ser uma string.")
        if not self.display_name.strip():
            raise ValueError("display_name não pode ser vazio.")
        if not isinstance(self.version, Version):
            raise TypeError("version deve ser uma Version.")
        if not isinstance(self.minimum_platform_version, Version):
            raise TypeError(
                "minimum_platform_version deve ser uma Version."
            )
        if not isinstance(self.description, str):
            raise TypeError("description deve ser uma string.")
        if self.icon is not None and not isinstance(self.icon, str):
            raise TypeError("icon deve ser uma string ou None.")
        if not isinstance(self.author, str):
            raise TypeError("author deve ser uma string.")

        schemas = tuple(self.supported_project_schema_versions)
        if any(
            isinstance(item, bool)
            or not isinstance(item, int)
            or item < 1
            for item in schemas
        ):
            raise ValueError(
                "supported_project_schema_versions deve conter apenas "
                "inteiros positivos."
            )
        if len(schemas) != len(set(schemas)):
            raise ValueError(
                "supported_project_schema_versions não aceita duplicatas."
            )

        required = self._capabilities(
            self.required_capabilities,
            "required_capabilities",
        )
        provided = self._capabilities(
            self.provided_capabilities,
            "provided_capabilities",
        )

        object.__setattr__(self, "display_name", self.display_name.strip())
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(
            self,
            "icon",
            self.icon.strip() if self.icon and self.icon.strip() else None,
        )
        object.__setattr__(self, "author", self.author.strip())
        for field_name in ("services", "views", "commands"):
            object.__setattr__(
                self,
                field_name,
                self._identifiers(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "supported_project_schema_versions",
            tuple(sorted(schemas)),
        )
        object.__setattr__(self, "required_capabilities", required)
        object.__setattr__(self, "provided_capabilities", provided)

    @staticmethod
    def _capabilities(values, field_name: str) -> frozenset[str]:
        try:
            capabilities = frozenset(values)
        except TypeError as exc:
            raise TypeError(
                f"{field_name} deve ser uma coleção de strings."
            ) from exc
        if any(
            not isinstance(item, str)
            or not _CAPABILITY_ID_PATTERN.fullmatch(item)
            for item in capabilities
        ):
            raise ValueError(
                f"{field_name} deve conter identificadores válidos."
            )
        return capabilities

    @staticmethod
    def _identifiers(values, field_name: str) -> tuple[str, ...]:
        if not isinstance(values, tuple):
            raise TypeError(f"{field_name} deve ser uma tupla.")
        if any(
            not isinstance(item, str)
            or not _CAPABILITY_ID_PATTERN.fullmatch(item)
            for item in values
        ):
            raise ValueError(
                f"{field_name} deve conter identificadores válidos."
            )
        if len(values) != len(set(values)):
            raise ValueError(f"{field_name} não aceita duplicatas.")
        return values


def create_transitional_application_descriptor(
    *,
    application_id: str,
    display_name: str,
    version: Version | str | None = None,
    minimum_platform_version: Version | str | None = None,
    supported_project_schema_versions: tuple[int, ...] = (),
    required_capabilities=frozenset(),
    provided_capabilities=frozenset(),
    description: str = "",
    icon: str | None = None,
    author: str = "",
    services: tuple[str, ...] = (),
    views: tuple[str, ...] = (),
    commands: tuple[str, ...] = (),
) -> ApplicationDescriptor:
    """Cria o descriptor neutro de uma Application ainda legada."""

    return ApplicationDescriptor(
        application_id=application_id,
        display_name=display_name,
        version=_declared_or_unspecified_version(version),
        minimum_platform_version=_declared_or_unspecified_version(
            minimum_platform_version
        ),
        supported_project_schema_versions=(
            supported_project_schema_versions
        ),
        required_capabilities=required_capabilities,
        provided_capabilities=provided_capabilities,
        description=description,
        icon=icon,
        author=author,
        services=services,
        views=views,
        commands=commands,
    )


def _declared_or_unspecified_version(
    value: Version | str | None,
) -> Version:
    if value is None:
        return Version(0, 0, 0)
    if isinstance(value, Version):
        return value
    return Version.parse(value)

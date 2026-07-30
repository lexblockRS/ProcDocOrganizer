"""Catálogo normativo imutável do Decreto nº 13.048/2026."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from types import MappingProxyType


class NormativeCatalogError(ValueError):
    """O catálogo normativo possui uma definição inconsistente."""


def _require_text(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field_name} deve ser texto não vazio.")


def _require_text_tuple(value: object, field_name: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise TypeError(f"{field_name} deve ser uma tupla textual.")
    if len(value) != len(set(value)):
        raise NormativeCatalogError(
            f"{field_name} não pode conter duplicidades."
        )


class MeasurementType(str, Enum):
    DURATION = "DURATION"
    COUNT = "COUNT"
    QUANTITY = "QUANTITY"
    HOURS = "HOURS"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"
    CATALOG = "CATALOG"
    ENUM = "ENUM"


class ArithmeticEngine(str, Enum):
    PER_YEAR = "PER_YEAR"
    PER_MONTH = "PER_MONTH"
    PER_EVENT = "PER_EVENT"
    PER_PUBLICATION = "PER_PUBLICATION"
    CUSTOM_TEXT = "CUSTOM_TEXT"


class CompatibilityPolicyId(str, Enum):
    TEMPORAL = "TEMPORAL"
    QUANTITATIVE = "QUANTITATIVE"
    EVENT = "EVENT"
    PUBLICATION = "PUBLICATION"


class CriterionFamily(str, Enum):
    TEMPORAL = "TEMPORAL"
    TEMPORAL_MONTH = "TEMPORAL_MONTH"
    FUNCTION_ROLE = "FUNCTION_ROLE"
    DESIGNATION = "DESIGNATION"
    PRODUCTION = "PRODUCTION"
    PROJECT = "PROJECT"
    EVENT = "EVENT"
    AWARD = "AWARD"
    COURSE = "COURSE"
    MANDATE = "MANDATE"
    TRAINING = "TRAINING"
    SYSTEM = "SYSTEM"
    PATENT = "PATENT"
    RESEARCH_GROUP = "RESEARCH_GROUP"
    PUBLICATION = "PUBLICATION"


@dataclass(frozen=True, slots=True)
class CompatibilityPolicy:
    policy_id: CompatibilityPolicyId
    allowed_measurements: tuple[MeasurementType, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not self.allowed_measurements:
            raise NormativeCatalogError(
                "Uma política deve aceitar ao menos uma Measurement."
            )
        if len(self.allowed_measurements) != len(
            set(self.allowed_measurements)
        ):
            raise NormativeCatalogError(
                "Uma política não pode repetir Measurements."
            )
        _require_text(self.explanation, "explanation")


COMPATIBILITY_POLICIES = MappingProxyType({
    CompatibilityPolicyId.TEMPORAL: CompatibilityPolicy(
        CompatibilityPolicyId.TEMPORAL,
        (MeasurementType.DURATION,),
        "A unidade normativa é derivada de intervalo temporal canônico.",
    ),
    CompatibilityPolicyId.QUANTITATIVE: CompatibilityPolicy(
        CompatibilityPolicyId.QUANTITATIVE,
        (
            MeasurementType.COUNT,
            MeasurementType.QUANTITY,
            MeasurementType.HOURS,
        ),
        "A unidade normativa exige medição quantitativa explícita.",
    ),
    CompatibilityPolicyId.EVENT: CompatibilityPolicy(
        CompatibilityPolicyId.EVENT,
        (
            MeasurementType.COUNT,
            MeasurementType.QUANTITY,
            MeasurementType.HOURS,
        ),
        "A quantidade de eventos deve estar materializada na Measurement.",
    ),
    CompatibilityPolicyId.PUBLICATION: CompatibilityPolicy(
        CompatibilityPolicyId.PUBLICATION,
        (MeasurementType.COUNT, MeasurementType.QUANTITY),
        "A quantidade representa publicações previamente qualificadas.",
    ),
})

ENGINE_COMPATIBILITY_POLICIES = MappingProxyType({
    ArithmeticEngine.PER_YEAR: CompatibilityPolicyId.TEMPORAL,
    ArithmeticEngine.PER_MONTH: CompatibilityPolicyId.TEMPORAL,
    ArithmeticEngine.PER_EVENT: CompatibilityPolicyId.EVENT,
    ArithmeticEngine.PER_PUBLICATION: CompatibilityPolicyId.PUBLICATION,
    ArithmeticEngine.CUSTOM_TEXT: CompatibilityPolicyId.QUANTITATIVE,
})


@dataclass(frozen=True, slots=True)
class NormativeValueVariant:
    selector: str
    value: Decimal

    def __post_init__(self) -> None:
        _require_text(self.selector, "selector")
        if not isinstance(self.value, Decimal):
            raise TypeError("value deve ser Decimal.")


@dataclass(frozen=True, slots=True)
class NormativeCriterionDefinition:
    code: str
    execution_rule_id: str
    requirement_id: str
    description: str
    annex: str
    item: str
    family: CriterionFamily
    normative_unit: str
    required_measurement: MeasurementType
    compatibility_policy: CompatibilityPolicyId
    arithmetic_engine: ArithmeticEngine
    normative_value: Decimal | None
    value_variants: tuple[NormativeValueVariant, ...]
    limits: tuple[str, ...]
    dependencies: tuple[str, ...]
    human_decision_required: bool
    explanation_template: str

    def __post_init__(self) -> None:
        for field_name in (
            "code",
            "execution_rule_id",
            "requirement_id",
            "description",
            "annex",
            "item",
            "normative_unit",
            "explanation_template",
        ):
            _require_text(getattr(self, field_name), field_name)
        if self.annex not in {"I", "II", "III", "IV", "V", "VI"}:
            raise NormativeCatalogError("Anexo normativo inválido.")
        if not isinstance(self.family, CriterionFamily):
            raise TypeError("family deve ser CriterionFamily.")
        if not isinstance(self.required_measurement, MeasurementType):
            raise TypeError("required_measurement deve ser MeasurementType.")
        if not isinstance(
            self.compatibility_policy,
            CompatibilityPolicyId,
        ):
            raise TypeError(
                "compatibility_policy deve ser CompatibilityPolicyId."
            )
        if not isinstance(self.arithmetic_engine, ArithmeticEngine):
            raise TypeError("arithmetic_engine deve ser ArithmeticEngine.")
        if self.normative_value is not None and not isinstance(
            self.normative_value,
            Decimal,
        ):
            raise TypeError("normative_value deve ser Decimal ou None.")
        if not isinstance(self.value_variants, tuple) or any(
            not isinstance(item, NormativeValueVariant)
            for item in self.value_variants
        ):
            raise TypeError(
                "value_variants deve ser uma tupla de variantes."
            )
        if (self.normative_value is None) == (not self.value_variants):
            raise NormativeCatalogError(
                "Defina exatamente um valor fixo ou variantes."
            )
        _require_text_tuple(self.limits, "limits")
        _require_text_tuple(self.dependencies, "dependencies")
        policy = COMPATIBILITY_POLICIES[self.compatibility_policy]
        if self.required_measurement not in policy.allowed_measurements:
            raise NormativeCatalogError(
                f"{self.required_measurement.value} é incompatível com "
                f"{self.compatibility_policy.value}."
            )
        expected_policy = ENGINE_COMPATIBILITY_POLICIES[
            self.arithmetic_engine
        ]
        if self.compatibility_policy is not expected_policy:
            raise NormativeCatalogError(
                f"{self.arithmetic_engine.value} exige a política "
                f"{expected_policy.value}."
            )


@dataclass(frozen=True, slots=True)
class NormativeCriterionCatalog:
    criteria: tuple[NormativeCriterionDefinition, ...]
    _index: Mapping[str, NormativeCriterionDefinition] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.criteria, tuple) or any(
            not isinstance(item, NormativeCriterionDefinition)
            for item in self.criteria
        ):
            raise TypeError(
                "criteria deve ser uma tupla de definições normativas."
            )
        for attribute in ("code", "execution_rule_id"):
            values = tuple(
                getattr(item, attribute) for item in self.criteria
            )
            if len(values) != len(set(values)):
                raise NormativeCatalogError(
                    f"O catálogo contém {attribute} duplicado."
                )
        object.__setattr__(
            self,
            "_index",
            MappingProxyType({
                item.code: item for item in self.criteria
            }),
        )

    def __iter__(self) -> Iterator[NormativeCriterionDefinition]:
        return iter(self.criteria)

    def __len__(self) -> int:
        return len(self.criteria)

    def find(
        self,
        criterion_code: str,
    ) -> NormativeCriterionDefinition | None:
        return self._index.get(criterion_code)


_COMMON_DEPENDENCIES = (
    "DOCUMENTARY_PROOF",
    "SINGLE_USE_NO_OVERLAP",
    "NON_ORDINARY_RELEVANT_ACTIVITY",
    "HUMAN_COMMISSION_REVIEW",
)


def _criterion(
    code: str,
    annex: str,
    item: str,
    description: str,
    family: CriterionFamily,
    unit: str,
    measurement: MeasurementType,
    policy: CompatibilityPolicyId,
    engine: ArithmeticEngine,
    value: Decimal | None,
    variants: tuple[tuple[str, Decimal], ...],
    limits: tuple[str, ...],
    rule_id: str,
    requirement_id: str,
) -> NormativeCriterionDefinition:
    return NormativeCriterionDefinition(
        code=code,
        execution_rule_id=rule_id,
        requirement_id=requirement_id,
        description=description,
        annex=annex,
        item=item,
        family=family,
        normative_unit=unit,
        required_measurement=measurement,
        compatibility_policy=policy,
        arithmetic_engine=engine,
        normative_value=value,
        value_variants=tuple(
            NormativeValueVariant(selector, variant_value)
            for selector, variant_value in variants
        ),
        limits=limits,
        dependencies=_COMMON_DEPENDENCIES,
        human_decision_required=True,
        explanation_template=(
            "{criterion_code}: {quantity} "
            f"{unit} × {{normative_value}} = {{score}}; "
            "preservar documentos, limites e decisão humana."
        ),
    )


_CRITERIA = (
    _criterion("DEC13048-ANX-I-ITEM-01", "I", "1",
        "Exercício do mandato como membro de conselhos superiores e conselhos de unidades e órgãos colegiados da Instituição Federal de Ensino",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("3"), (), (),
        "DEC13048-RULE-ANX-I-ITEM-01", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-02", "I", "2",
        "Coordenação ou presidência de núcleos, representações, grupos de trabalho ou similares, comissões ou comitês previstos no âmbito da administração pública, regularmente instituídos, ou reconhecidos pelo órgão ou pela entidade",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-I-ITEM-02", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-03", "I", "3",
        "Participação como membro de núcleos, representações, grupos de trabalho ou similares, comissões ou comitês previstos no âmbito da administração pública, regularmente instituídos",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-I-ITEM-03", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-04", "I", "4",
        "Participação como defensor dativo ou como membro de equipe designada em processos de apuração de materialidade e responsabilidade, como sindicância, processo administrativo disciplinar e tomada de contas especial",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-I-ITEM-04", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-05", "I", "5",
        "Atuação em atividades de organização, fiscalização, execução de exame de seleção, vestibular ou concursos",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-I-ITEM-05", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-06", "I", "6",
        "Atuação em atividades de elaboração, revisão e/ou correção de provas de exame de seleção, vestibular ou concursos",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-I-ITEM-06", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-07", "I", "7",
        "Exercício de mandato em entidade sindical da categoria",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("1.5"), (), (),
        "DEC13048-RULE-ANX-I-ITEM-07", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-08", "I", "8",
        "Participação como membro em programas ou projetos de políticas públicas externas à Instituição Federal de Ensino, desde que comprovada a obtenção de resultados institucionais relevantes",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), ("RELEVANT_INSTITUTIONAL_RESULT",),
        "DEC13048-RULE-ANX-I-ITEM-08", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-09", "I", "9",
        "Representação legal da Instituição Federal de Ensino junto a órgãos e entidades do Poder Público ou responsabilidade técnica junto a órgãos de fiscalização, controle e regulação",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("7.5"), (), (), "DEC13048-RULE-ANX-I-ITEM-09", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-I-ITEM-10", "I", "10",
        "Atuação técnica externa, formalmente autorizada ou reconhecida pela Instituição Federal de Ensino de lotação, em órgãos estatais ou paraestatais, escolas de governo, agências reguladoras ou organismos internacionais, com contribuição ou repercussão institucional",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-I-ITEM-10", "DEC13048-ART3-I"),
    _criterion("DEC13048-ANX-II-ITEM-01", "II", "1",
        "Coordenação de projetos institucionais (ensino, pesquisa, extensão, gestão e inovação)",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("7.5"), (), (), "DEC13048-RULE-ANX-II-ITEM-01", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-02", "II", "2",
        "Participação em atividades técnicas e/ou especializadas em projetos, incluída a elaboração de projetos pedagógicos, programas e/ou ações institucionais (ensino, pesquisa, extensão, gestão e inovação)",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-II-ITEM-02", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-03", "II", "3",
        "Participação em comissão ou conselho editorial de livros, revistas ou publicações científicas ou outras publicações acadêmicas",
        CriterionFamily.MANDATE, "Por mandato", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("7.5"), (), (), "DEC13048-RULE-ANX-II-ITEM-03", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-04", "II", "4",
        "Participação em atividade de Cooperação Técnica Interinstitucional em projetos institucionais",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-II-ITEM-04", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-05", "II", "5",
        "Participação em atividades de orientação, tutoria, preceptoria ou supervisão",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-II-ITEM-05", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-06", "II", "6",
        "Participação em atividades de produção ou reformulação de material acessível, ou técnico de referência (manuais, roteiros técnicos)",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-II-ITEM-06", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-07", "II", "7",
        "Participação em atividade de avaliação de trabalho ou atuação como jurado em eventos acadêmicos, científicos, culturais, esportivos e técnicos",
        CriterionFamily.EVENT, "Por evento", MeasurementType.COUNT,
        CompatibilityPolicyId.EVENT, ArithmeticEngine.PER_EVENT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-II-ITEM-07", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-08", "II", "8",
        "Participação em atividade institucional de produção audiovisual, artística, exposição, podcast ou outras formas de apresentação",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-II-ITEM-08", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-09", "II", "9",
        "Participação em programas de formação continuada e/ou ações de desenvolvimento de competências, desde que não utilizada para fins de aceleração da promoção na carreira (carga horária mínima de dez horas)",
        CriterionFamily.TRAINING, "Por capacitação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("1"), (), ("MINIMUM_TEN_HOURS", "NOT_USED_FOR_CAREER_ACCELERATION"),
        "DEC13048-RULE-ANX-II-ITEM-09", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-10", "II", "10",
        "Desempenho de atividade técnica especializada, formalmente reconhecida pela Instituição Federal de Ensino, com demonstração de domínio técnico diferenciado e contribuição institucional relevante na área de atuação",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("1"), (), (
            "FORMAL_RECOGNITION", "RELEVANT_INSTITUTIONAL_CONTRIBUTION"),
        "DEC13048-RULE-ANX-II-ITEM-10", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-II-ITEM-11", "II", "11",
        "Participação em capacitação, fórum, oficina, workshop e congresso, com carga horária mínima de dez horas, vinculada aos interesses da Instituição Federal de Ensino",
        CriterionFamily.EVENT, "Por evento", MeasurementType.COUNT,
        CompatibilityPolicyId.EVENT, ArithmeticEngine.PER_EVENT,
        Decimal("1"), (), ("MINIMUM_TEN_HOURS", "INSTITUTIONAL_INTEREST"),
        "DEC13048-RULE-ANX-II-ITEM-11", "DEC13048-ART3-II"),
    _criterion("DEC13048-ANX-III-ITEM-01", "III", "1",
        "Recebimento de premiação de âmbito internacional por projeto implementado na administração pública",
        CriterionFamily.AWARD, "Por prêmio", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("20"), (), (), "DEC13048-RULE-ANX-III-ITEM-01",
        "DEC13048-ART3-III"),
    _criterion("DEC13048-ANX-III-ITEM-02", "III", "2",
        "Recebimento de premiação de âmbito nacional por projeto implementado na administração pública",
        CriterionFamily.AWARD, "Por prêmio", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("15"), (), (), "DEC13048-RULE-ANX-III-ITEM-02",
        "DEC13048-ART3-III"),
    _criterion("DEC13048-ANX-III-ITEM-03", "III", "3",
        "Recebimento de premiação de âmbito local ou institucional, formalmente instituído, por projeto implementado na administração pública",
        CriterionFamily.AWARD, "Por prêmio", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("7.5"), (), (), "DEC13048-RULE-ANX-III-ITEM-03",
        "DEC13048-ART3-III"),
    _criterion("DEC13048-ANX-IV-ITEM-01", "IV", "1",
        "Atuação tecnicamente qualificada na operação, na implantação, no suporte ou no apoio a desenvolvimento, parametrização ou aperfeiçoamento de sistemas estruturantes da administração pública",
        CriterionFamily.SYSTEM, "Por sistema", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-IV-ITEM-01",
        "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-02", "IV", "2",
        "Elaboração de projeto básico ou de termo de referência, ou participação como membro de equipe de planejamento de contratação",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-IV-ITEM-02",
        "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-03", "IV", "3",
        "Exercício de atividades de gestão ou fiscalização de contratos de aquisição, serviços, convênios e acordos ou instrumentos correlatos",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-IV-ITEM-03",
        "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-04", "IV", "4",
        "Exercício de atividades relacionadas à licitação e às suas excepcionalidades",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("3"), (), (),
        "DEC13048-RULE-ANX-IV-ITEM-04", "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-05", "IV", "5",
        "Participação em atividades de apoio técnico especializado em políticas, programas e ações de promoção na área de saúde humana, animal e ambiente, de acessibilidade ou diversidade, de interesse institucional",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("3"), (), (),
        "DEC13048-RULE-ANX-IV-ITEM-05", "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-06", "IV", "6",
        "Atuação tecnicamente qualificada em ambientes ou processos que demandem condições especiais de segurança, cuidado ou conformidade com requisitos legais e regulatórios, desde que não receba adicional de periculosidade ou insalubridade em razão das mesmas condições",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("3"), (), (
            "NO_HAZARD_OR_UNHEALTHY_WORK_PREMIUM_FOR_SAME_CONDITIONS",),
        "DEC13048-RULE-ANX-IV-ITEM-06", "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-07", "IV", "7",
        "Atuação em sistemas e/ou processos de trabalho institucionais em ensino, pesquisa, extensão, gestão e inovação, desde que não constitua atividade habitual do cargo",
        CriterionFamily.DESIGNATION, "Por designação", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), ("NOT_HABITUAL_DUTY",),
        "DEC13048-RULE-ANX-IV-ITEM-07", "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-IV-ITEM-08", "IV", "8",
        "Atuação como responsável por setor ou por unidade, formalmente designado, desde que a designação não gere pagamento de remuneração",
        CriterionFamily.TEMPORAL, "Por ano ou fração acima de seis meses",
        MeasurementType.DURATION, CompatibilityPolicyId.TEMPORAL,
        ArithmeticEngine.PER_YEAR, Decimal("4.5"), (), (
            "UNPAID_DESIGNATION",),
        "DEC13048-RULE-ANX-IV-ITEM-08", "DEC13048-ART3-IV"),
    _criterion("DEC13048-ANX-V-ITEM-01", "V", "1",
        "Exercício de cargo de direção (CD-02) ou equivalente",
        CriterionFamily.FUNCTION_ROLE,
        "Por ano ou fração acima de seis meses", MeasurementType.DURATION,
        CompatibilityPolicyId.TEMPORAL, ArithmeticEngine.PER_YEAR, None,
        (("titular", Decimal("9")), ("substituto", Decimal("4.5"))), (),
        "DEC13048-RULE-ANX-V-ITEM-01", "DEC13048-ART3-V"),
    _criterion("DEC13048-ANX-V-ITEM-02", "V", "2",
        "Exercício de cargo de direção (CD-03 e 04) ou equivalente",
        CriterionFamily.FUNCTION_ROLE,
        "Por ano ou fração acima de seis meses", MeasurementType.DURATION,
        CompatibilityPolicyId.TEMPORAL, ArithmeticEngine.PER_YEAR, None,
        (("titular", Decimal("7.5")), ("substituto", Decimal("3"))), (),
        "DEC13048-RULE-ANX-V-ITEM-02", "DEC13048-ART3-V"),
    _criterion("DEC13048-ANX-V-ITEM-03", "V", "3",
        "Exercício de função gratificada (FG-01 e 02) ou equivalente",
        CriterionFamily.FUNCTION_ROLE,
        "Por ano ou fração acima de seis meses", MeasurementType.DURATION,
        CompatibilityPolicyId.TEMPORAL, ArithmeticEngine.PER_YEAR, None,
        (("titular", Decimal("4.5")), ("substituto", Decimal("1.5"))), (),
        "DEC13048-RULE-ANX-V-ITEM-03", "DEC13048-ART3-V"),
    _criterion("DEC13048-ANX-V-ITEM-04", "V", "4",
        "Exercício de função gratificada (a partir da FG-03) ou equivalente",
        CriterionFamily.FUNCTION_ROLE,
        "Por ano ou fração acima de seis meses", MeasurementType.DURATION,
        CompatibilityPolicyId.TEMPORAL, ArithmeticEngine.PER_YEAR, None,
        (("titular", Decimal("3")), ("substituto", Decimal("1"))), (),
        "DEC13048-RULE-ANX-V-ITEM-04", "DEC13048-ART3-V"),
    _criterion("DEC13048-ANX-VI-ITEM-01", "VI", "1",
        "Carta patente relacionada aos interesses institucionais",
        CriterionFamily.PATENT, "Por patente", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("30"), (), (), "DEC13048-RULE-ANX-VI-ITEM-01",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-02", "VI", "2",
        "Participação relevante no desenvolvimento de protótipos, depósitos e/ou registros de propriedade intelectual ou privilégio de invenção relacionada aos interesses institucionais",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("25"), (), (), "DEC13048-RULE-ANX-VI-ITEM-02",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-03", "VI", "3",
        "Participação em transferência de tecnologia, licenciamento ou exploração de ativo tecnológico, como autor ou inventor relacionada aos interesses institucionais",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("20"), (), (), "DEC13048-RULE-ANX-VI-ITEM-03",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-04", "VI", "4",
        "Conclusão de curso de educação formal superior ao exigido para o ingresso no cargo de que é titular e que não seja utilizado para percepção de Incentivo à Qualificação – IQ",
        CriterionFamily.COURSE, "Por curso", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("15"), (), (
            "HIGHER_THAN_ENTRY_EDUCATION",
            "NOT_USED_FOR_QUALIFICATION_INCENTIVE",
        ), "DEC13048-RULE-ANX-VI-ITEM-04", "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-05", "VI", "5",
        "Participação relevante na implantação ou desenvolvimento de produto, projeto, processo, técnica ou tecnologia de interesse institucional",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("15"), (), (), "DEC13048-RULE-ANX-VI-ITEM-05",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-06", "VI", "6",
        "Atuação em atividade de liderança ou vice-liderança de grupo de pesquisa ou extensão registrado em órgão ou sistema oficial de reconhecimento institucional",
        CriterionFamily.RESEARCH_GROUP, "Por grupo de pesquisa",
        MeasurementType.COUNT, CompatibilityPolicyId.QUANTITATIVE,
        ArithmeticEngine.CUSTOM_TEXT, Decimal("7.5"), (), (
            "OFFICIAL_REGISTRATION",),
        "DEC13048-RULE-ANX-VI-ITEM-06", "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-07", "VI", "7",
        "Participação como membro em grupo de pesquisa devidamente registrado em órgão ou sistema oficial de reconhecimento institucional",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-VI-ITEM-07",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-08", "VI", "8",
        "Aprovação de projeto para a captação de recursos para a Instituição Federal de Ensino",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("7.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-08",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-09", "VI", "9",
        "Publicação ou organização de livro relacionado aos interesses institucionais (com ISBN e Conselho Editorial)",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("20"), (), ("ISBN_REQUIRED", "EDITORIAL_BOARD_REQUIRED"),
        "DEC13048-RULE-ANX-VI-ITEM-09", "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-10", "VI", "10",
        "Autoria ou coautoria de capítulo de livro, de artigo publicado em revista especializada, jornal científico ou periódico, relacionado aos interesses institucionais",
        CriterionFamily.PUBLICATION, "Por publicação", MeasurementType.COUNT,
        CompatibilityPolicyId.PUBLICATION, ArithmeticEngine.PER_PUBLICATION,
        Decimal("7.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-10",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-11", "VI", "11",
        "Apresentação de trabalho de interesse institucional em congresso, seminário ou outros eventos",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-11",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-12", "VI", "12",
        "Produção de material técnico, científico, metodológico ou administrativo estruturado que visa à difusão do conhecimento",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-12",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-13", "VI", "13",
        "Avaliação do projeto de ensino e/ou pesquisa e/ou extensão e/ou inovação",
        CriterionFamily.PROJECT, "Por projeto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-13",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-14", "VI", "14",
        "Participação em atividade de difusão ou apoio à formação institucional (expositor, facilitador, colaborador)",
        CriterionFamily.EVENT, "Por evento", MeasurementType.COUNT,
        CompatibilityPolicyId.EVENT, ArithmeticEngine.PER_EVENT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-VI-ITEM-14",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-15", "VI", "15",
        "Atuação formalmente autorizada como instrutor, tutor, palestrante, autor de conteúdo técnico ou orientador em ação formativa estruturada de interesse institucional, prevista em plano ou programa de desenvolvimento de pessoas",
        CriterionFamily.COURSE, "Por curso", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-15",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-16", "VI", "16",
        "Atuação na coordenação de congresso, simpósio ou seminário de interesse institucional",
        CriterionFamily.EVENT, "Por evento", MeasurementType.COUNT,
        CompatibilityPolicyId.EVENT, ArithmeticEngine.PER_EVENT,
        Decimal("3.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-16",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-17", "VI", "17",
        "Exercício de atividade de coorientação de trabalho de conclusão de curso em diferentes modalidades de ensino",
        CriterionFamily.EVENT, "Por evento", MeasurementType.COUNT,
        CompatibilityPolicyId.EVENT, ArithmeticEngine.PER_EVENT,
        Decimal("4.5"), (), (), "DEC13048-RULE-ANX-VI-ITEM-17",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-18", "VI", "18",
        "Autoria de obra artística ou cultural registrada com contribuição ou repercussão institucional comprovada",
        CriterionFamily.PRODUCTION, "Por produto", MeasurementType.COUNT,
        CompatibilityPolicyId.QUANTITATIVE, ArithmeticEngine.CUSTOM_TEXT,
        Decimal("3"), (), (), "DEC13048-RULE-ANX-VI-ITEM-18",
        "DEC13048-ART3-VI"),
    _criterion("DEC13048-ANX-VI-ITEM-19", "VI", "19",
        "Atuação institucional no enfrentamento de situações de surto, epidemia e pandemia",
        CriterionFamily.TEMPORAL_MONTH, "Por mês", MeasurementType.DURATION,
        CompatibilityPolicyId.TEMPORAL, ArithmeticEngine.PER_MONTH,
        Decimal("1"), (), (), "DEC13048-RULE-ANX-VI-ITEM-19",
        "DEC13048-ART3-VI"),
)

OFFICIAL_NORMATIVE_CATALOG = NormativeCriterionCatalog(_CRITERIA)


__all__ = [
    "ArithmeticEngine",
    "COMPATIBILITY_POLICIES",
    "ENGINE_COMPATIBILITY_POLICIES",
    "CompatibilityPolicy",
    "CompatibilityPolicyId",
    "CriterionFamily",
    "MeasurementType",
    "NormativeCatalogError",
    "NormativeCriterionCatalog",
    "NormativeCriterionDefinition",
    "NormativeValueVariant",
    "OFFICIAL_NORMATIVE_CATALOG",
]

"""Catálogo oficial transcrito exclusivamente dos Anexos I a VI."""

from decimal import Decimal
from types import MappingProxyType

from applications.rsc.domain import (
    CriterionScoreVariant,
    MeasurementUnit,
    RscCriterion,
    RscRequirement,
    criterion_id,
    requirement_id,
)

_TITLES = (
    "PARTICIPAÇÃO EM GRUPOS DE TRABALHO, COMISSÕES, COMITÊS, NÚCLEOS, "
    "REPRESENTAÇÕES OU SIMILARES, FORMALMENTE INSTITUÍDOS OU RECONHECIDOS "
    "PELO ÓRGÃO OU PELA ENTIDADE",
    "PARTICIPAÇÃO E ATUAÇÃO EM PROJETOS INSTITUCIONAIS, NA GESTÃO, NO "
    "APOIO AO ENSINO, À PESQUISA, À EXTENSÃO, DE INOVAÇÃO E ASSISTÊNCIA "
    "ESPECIALIZADA",
    "RECEBIMENTO DE PREMIAÇÃO EM EVENTO DE RECONHECIMENTO PÚBLICO POR "
    "PROJETOS IMPLEMENTADOS NA ADMINISTRAÇÃO PÚBLICA",
    "DESIGNAÇÃO PARA ASSUNÇÃO DE RESPONSABILIDADES TÉCNICO-ADMINISTRATIVAS "
    "OU ESPECIALIZADAS",
    "EXERCÍCIO DE FUNÇÃO OU CARGO DE DIREÇÃO OU DE ASSESSORAMENTO "
    "INSTITUCIONAL",
    "PRODUÇÃO, PROSPECÇÃO E DIFUSÃO DE CONHECIMENTO CIENTÍFICO OU TÉCNICO",
)

_REQUIREMENTS = tuple(
    RscRequirement(
        id=requirement_id(number),
        number=number,
        title=title,
        description=title,
        display_order=number,
    )
    for number, title in enumerate(_TITLES, 1)
)

Y = MeasurementUnit.YEAR_OR_FRACTION_OVER_SIX_MONTHS
D = MeasurementUnit.DESIGNATION
P = MeasurementUnit.PROJECT
PRODUCT = MeasurementUnit.PRODUCT
EVENT = MeasurementUnit.EVENT

_ROWS = (
    (1, 1, "Exercício do mandato como membro de conselhos superiores e conselhos de unidades e órgãos colegiados da Instituição Federal de Ensino", Y, "3"),
    (1, 2, "Coordenação ou presidência de núcleos, representações, grupos de trabalho ou similares, comissões ou comitês previstos no âmbito da administração pública, regularmente instituídos, ou reconhecidos pelo órgão ou pela entidade", D, "4.5"),
    (1, 3, "Participação como membro de núcleos, representações, grupos de trabalho ou similares, comissões ou comitês previstos no âmbito da administração pública, regularmente instituídos", D, "3"),
    (1, 4, "Participação como defensor dativo ou como membro de equipe designada em processos de apuração de materialidade e responsabilidade, como sindicância, processo administrativo disciplinar e tomada de contas especial", D, "3"),
    (1, 5, "Atuação em atividades de organização, fiscalização, execução de exame de seleção, vestibular ou concursos", D, "4.5"),
    (1, 6, "Atuação em atividades de elaboração, revisão e/ou correção de provas de exame de seleção, vestibular ou concursos", D, "3"),
    (1, 7, "Exercício de mandato em entidade sindical da categoria", Y, "1.5"),
    (1, 8, "Participação como membro em programas ou projetos de políticas públicas externas à Instituição Federal de Ensino, desde que comprovada a obtenção de resultados institucionais relevantes", D, "3"),
    (1, 9, "Representação legal da Instituição Federal de Ensino junto a órgãos e entidades do Poder Público ou responsabilidade técnica junto a órgãos de fiscalização, controle e regulação", D, "7.5"),
    (1, 10, "Atuação técnica externa, formalmente autorizada ou reconhecida pela Instituição Federal de Ensino de lotação, em órgãos estatais ou paraestatais, escolas de governo, agências reguladoras ou organismos internacionais, com contribuição ou repercussão institucional", PRODUCT, "4.5"),
    (2, 1, "Coordenação de projetos institucionais (ensino, pesquisa, extensão, gestão e inovação)", P, "7.5"),
    (2, 2, "Participação em atividades técnicas e/ou especializadas em projetos, incluída a elaboração de projetos pedagógicos, programas e/ou ações institucionais (ensino, pesquisa, extensão, gestão e inovação)", P, "4.5"),
    (2, 3, "Participação em comissão ou conselho editorial de livros, revistas ou publicações científicas ou outras publicações acadêmicas", MeasurementUnit.MANDATE, "7.5"),
    (2, 4, "Participação em atividade de Cooperação Técnica Interinstitucional em projetos institucionais", P, "3"),
    (2, 5, "Participação em atividades de orientação, tutoria, preceptoria ou supervisão", D, "3"),
    (2, 6, "Participação em atividades de produção ou reformulação de material acessível, ou técnico de referência (manuais, roteiros técnicos)", PRODUCT, "3"),
    (2, 7, "Participação em atividade de avaliação de trabalho ou atuação como jurado em eventos acadêmicos, científicos, culturais, esportivos e técnicos", EVENT, "3"),
    (2, 8, "Participação em atividade institucional de produção audiovisual, artística, exposição, podcast ou outras formas de apresentação", P, "3"),
    (2, 9, "Participação em programas de formação continuada e/ou ações de desenvolvimento de competências, desde que não utilizada para fins de aceleração da promoção na carreira (carga horária mínima de dez horas)", MeasurementUnit.TRAINING, "1"),
    (2, 10, "Desempenho de atividade técnica especializada, formalmente reconhecida pela Instituição Federal de Ensino, com demonstração de domínio técnico diferenciado e contribuição institucional relevante na área de atuação", Y, "1"),
    (2, 11, "Participação em capacitação, fórum, oficina, workshop e congresso, com carga horária mínima de dez horas, vinculada aos interesses da Instituição Federal de Ensino", EVENT, "1"),
    (3, 1, "Recebimento de premiação de âmbito internacional por projeto implementado na administração pública", MeasurementUnit.AWARD, "20"),
    (3, 2, "Recebimento de premiação de âmbito nacional por projeto implementado na administração pública", MeasurementUnit.AWARD, "15"),
    (3, 3, "Recebimento de premiação de âmbito local ou institucional, formalmente instituído, por projeto implementado na administração pública", MeasurementUnit.AWARD, "7.5"),
    (4, 1, "Atuação tecnicamente qualificada na operação, na implantação, no suporte ou no apoio a desenvolvimento, parametrização ou aperfeiçoamento de sistemas estruturantes da administração pública", MeasurementUnit.SYSTEM, "4.5"),
    (4, 2, "Elaboração de projeto básico ou de termo de referência, ou participação como membro de equipe de planejamento de contratação", D, "3"),
    (4, 3, "Exercício de atividades de gestão ou fiscalização de contratos de aquisição, serviços, convênios e acordos ou instrumentos correlatos", D, "4.5"),
    (4, 4, "Exercício de atividades relacionadas à licitação e às suas excepcionalidades", Y, "3"),
    (4, 5, "Participação em atividades de apoio técnico especializado em políticas, programas e ações de promoção na área de saúde humana, animal e ambiente, de acessibilidade ou diversidade, de interesse institucional", Y, "3"),
    (4, 6, "Atuação tecnicamente qualificada em ambientes ou processos que demandem condições especiais de segurança, cuidado ou conformidade com requisitos legais e regulatórios, desde que não receba adicional de periculosidade ou insalubridade em razão das mesmas condições", Y, "3"),
    (4, 7, "Atuação em sistemas e/ou processos de trabalho institucionais em ensino, pesquisa, extensão, gestão e inovação, desde que não constitua atividade habitual do cargo", D, "3"),
    (4, 8, "Atuação como responsável por setor ou por unidade, formalmente designado, desde que a designação não gere pagamento de remuneração", Y, "4.5"),
    (6, 1, "Carta patente relacionada aos interesses institucionais", MeasurementUnit.PATENT, "30"),
    (6, 2, "Participação relevante no desenvolvimento de protótipos, depósitos e/ou registros de propriedade intelectual ou privilégio de invenção relacionada aos interesses institucionais", P, "25"),
    (6, 3, "Participação em transferência de tecnologia, licenciamento ou exploração de ativo tecnológico, como autor ou inventor relacionada aos interesses institucionais", PRODUCT, "20"),
    (6, 4, "Conclusão de curso de educação formal superior ao exigido para o ingresso no cargo de que é titular e que não seja utilizado para percepção de Incentivo à Qualificação – IQ", MeasurementUnit.COURSE, "15"),
    (6, 5, "Participação relevante na implantação ou desenvolvimento de produto, projeto, processo, técnica ou tecnologia de interesse institucional", PRODUCT, "15"),
    (6, 6, "Atuação em atividade de liderança ou vice-liderança de grupo de pesquisa ou extensão registrado em órgão ou sistema oficial de reconhecimento institucional", MeasurementUnit.RESEARCH_GROUP, "7.5"),
    (6, 7, "Participação como membro em grupo de pesquisa devidamente registrado em órgão ou sistema oficial de reconhecimento institucional", P, "3"),
    (6, 8, "Aprovação de projeto para a captação de recursos para a Instituição Federal de Ensino", P, "7.5"),
    (6, 9, "Publicação ou organização de livro relacionado aos interesses institucionais (com ISBN e Conselho Editorial)", PRODUCT, "20"),
    (6, 10, "Autoria ou coautoria de capítulo de livro, de artigo publicado em revista especializada, jornal científico ou periódico, relacionado aos interesses institucionais", MeasurementUnit.PUBLICATION, "7.5"),
    (6, 11, "Apresentação de trabalho de interesse institucional em congresso, seminário ou outros eventos", PRODUCT, "4.5"),
    (6, 12, "Produção de material técnico, científico, metodológico ou administrativo estruturado que visa à difusão do conhecimento", PRODUCT, "4.5"),
    (6, 13, "Avaliação do projeto de ensino e/ou pesquisa e/ou extensão e/ou inovação", P, "4.5"),
    (6, 14, "Participação em atividade de difusão ou apoio à formação institucional (expositor, facilitador, colaborador)", EVENT, "3"),
    (6, 15, "Atuação formalmente autorizada como instrutor, tutor, palestrante, autor de conteúdo técnico ou orientador em ação formativa estruturada de interesse institucional, prevista em plano ou programa de desenvolvimento de pessoas", MeasurementUnit.COURSE, "4.5"),
    (6, 16, "Atuação na coordenação de congresso, simpósio ou seminário de interesse institucional", EVENT, "3.5"),
    (6, 17, "Exercício de atividade de coorientação de trabalho de conclusão de curso em diferentes modalidades de ensino", EVENT, "4.5"),
    (6, 18, "Autoria de obra artística ou cultural registrada com contribuição ou repercussão institucional comprovada", PRODUCT, "3"),
    (6, 19, "Atuação institucional no enfrentamento de situações de surto, epidemia e pandemia", MeasurementUnit.MONTH, "1"),
)

_VARIANT_ROWS = (
    (1, "Exercício de cargo de direção (CD-02) ou equivalente", "9", "4.5"),
    (2, "Exercício de cargo de direção (CD-03 e 04) ou equivalente", "7.5", "3"),
    (3, "Exercício de função gratificada (FG-01 e 02) ou equivalente", "4.5", "1.5"),
    (4, "Exercício de função gratificada (a partir da FG-03) ou equivalente", "3", "1"),
)


def _variant(criterion: str, role: str, points: str) -> CriterionScoreVariant:
    return CriterionScoreVariant(
        id=f"{criterion}.{role}",
        label=role.capitalize(),
        points_per_unit=Decimal(points),
        qualifiers={"role": role},
    )


_CRITERIA = tuple(
    RscCriterion(
        id=criterion_id(requirement, item),
        requirement_id=requirement_id(requirement),
        item_number=item,
        description=description,
        measurement_unit=unit,
        points_per_unit=Decimal(points),
        display_order=item,
    )
    for requirement, item, description, unit, points in _ROWS
) + tuple(
    RscCriterion(
        id=criterion_id(5, item),
        requirement_id=requirement_id(5),
        item_number=item,
        description=description,
        measurement_unit=Y,
        display_order=item,
        score_variants=(
            _variant(criterion_id(5, item), "titular", titular),
            _variant(criterion_id(5, item), "substituto", substituto),
        ),
    )
    for item, description, titular, substituto in _VARIANT_ROWS
)
_CRITERIA = tuple(
    sorted(
        _CRITERIA,
        key=lambda value: (
            int(value.requirement_id.rsplit(".", 1)[1]),
            value.display_order,
        ),
    )
)


class OfficialRscCatalog:
    """Snapshot imutável e determinístico dos Anexos I a VI."""

    def __init__(self) -> None:
        self._requirements = _REQUIREMENTS
        self._criteria = _CRITERIA
        self._requirements_by_id = MappingProxyType(
            {item.id: item for item in self._requirements}
        )
        self._criteria_by_id = MappingProxyType(
            {item.id: item for item in self._criteria}
        )
        if len(self._requirements) != 6 or len(self._criteria) != 55:
            raise RuntimeError("catálogo RSC oficial inconsistente.")

    def list_requirements(self) -> tuple[RscRequirement, ...]:
        return self._requirements

    def get_requirement(self, requirement: str) -> RscRequirement:
        try:
            return self._requirements_by_id[requirement]
        except KeyError as exc:
            raise KeyError(f"requisito inexistente: {requirement}") from exc

    def list_criteria(self) -> tuple[RscCriterion, ...]:
        return self._criteria

    def list_criteria_by_requirement(
        self, requirement: str
    ) -> tuple[RscCriterion, ...]:
        self.get_requirement(requirement)
        return tuple(
            item
            for item in self._criteria
            if item.requirement_id == requirement
        )

    def get_criterion(self, criterion: str) -> RscCriterion:
        try:
            return self._criteria_by_id[criterion]
        except KeyError as exc:
            raise KeyError(f"critério inexistente: {criterion}") from exc

    def count_criteria(self) -> int:
        return len(self._criteria)


OFFICIAL_RSC_CATALOG = OfficialRscCatalog()

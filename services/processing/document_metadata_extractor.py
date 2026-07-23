"""
Extração determinística de metadados do texto nativo de documentos.
"""

from datetime import date
import re

from models import DocumentType


class DocumentMetadataExtractor:
    """
    Extrai metadados estruturados exclusivamente das páginas já extraídas.
    """

    VERSION = 1

    DOCUMENT_TYPES = (
        (DocumentType.PORTARIA, r"\bPORTARIA\b"),
        (DocumentType.RESOLUCAO, r"\bRESOLU[CÇ][AÃ]O\b"),
        (DocumentType.OFICIO, r"\bOF[IÍ]CIO\b"),
        (DocumentType.MEMORANDO, r"\bMEMORANDO\b"),
        (DocumentType.DECLARACAO, r"\bDECLARA[CÇ][AÃ]O\b"),
        (DocumentType.CERTIFICADO, r"\bCERTIFICADO\b"),
        (DocumentType.EDITAL, r"\bEDITAL\b"),
    )

    MONTHS = {
        "janeiro": 1,
        "fevereiro": 2,
        "marco": 3,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    EXCLUDED_TITLE_HEADERS = re.compile(
        r"\b(?:SERVIÇO\s+PÚBLICO\s+FEDERAL|MINISTÉRIO|UNIVERSIDADE|"
        r"INSTITUTO\s+FEDERAL|PRÓ-REITORIA|SECRETARIA|GABINETE)\b",
        re.IGNORECASE,
    )

    # ------------------------------------------------------------------

    def extract(self, pages: list[dict]) -> dict:
        """
        Retorna os metadados identificados por regex e heurísticas simples.
        """

        page_texts = self._page_texts(pages)

        if not page_texts:
            return {}

        first_page = page_texts[0]
        first_page_lines = self._lines(first_page)
        full_text = "\n".join(page_texts)
        title_index, title = self._title(first_page_lines)
        document_type = self._document_type(full_text)
        document_number = self._document_number(first_page, full_text)

        return {
            "title": title,
            "document_type": document_type.value,
            "document_number": document_number,
            "document_date": self._document_date(
                page_texts,
                title_index,
                document_number,
            ),
            "issuing_organization": self._issuing_organization(first_page),
            "sei_process_number": self._first_match(
                r"\b\d{5}\.\d{6}/\d{4}-\d{2}\b",
                full_text,
            ),
            "sei_code": self._sei_code(full_text),
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _page_texts(pages: list[dict]) -> list[str]:
        return [
            page["text"]
            for page in pages
            if isinstance(page, dict)
            and isinstance(page.get("text"), str)
            and page["text"].strip()
        ]

    # ------------------------------------------------------------------

    @staticmethod
    def _lines(text: str) -> list[str]:
        return [
            normalized
            for line in text.replace("\r", "").splitlines()
            if (normalized := DocumentMetadataExtractor._normalize(line))
        ]

    # ------------------------------------------------------------------

    def _document_type(self, text: str) -> DocumentType:
        for document_type, pattern in self.DOCUMENT_TYPES:
            if re.search(pattern, text, re.IGNORECASE):
                return document_type

        return DocumentType.UNKNOWN

    # ------------------------------------------------------------------

    @staticmethod
    def _document_number(first_page: str, full_text: str) -> str | None:
        pattern = (
            r"\b(?:N[.º°]|N[Oº°]?\.?|NÚMERO)\s*"
            r"(?:[A-Z]{1,12}[-/]\s*)?(\d{1,7}(?:/\d{2,4})?)\b"
        )

        return (
            DocumentMetadataExtractor._first_match(pattern, first_page)
            or DocumentMetadataExtractor._first_match(pattern, full_text)
        )

    # ------------------------------------------------------------------

    def _title(self, lines: list[str]) -> tuple[int | None, str | None]:
        for index, line in enumerate(lines[:20]):
            if (
                self._document_type(line) != DocumentType.UNKNOWN
                and self._document_number(line, line) is not None
            ):
                return index, line

        for index, line in enumerate(lines[:15]):
            if len(line) < 8 or len(line) > 180:
                continue

            if line.upper() != line:
                continue

            if self.EXCLUDED_TITLE_HEADERS.search(line):
                continue

            return index, line

        return None, None

    # ------------------------------------------------------------------

    def _document_date(
        self,
        page_texts: list[str],
        title_index: int | None,
        document_number: str | None,
    ) -> str | None:
        candidates = []

        for page_index, page_text in enumerate(page_texts):
            for line_index, line in enumerate(self._lines(page_text)):
                parsed_date = self._date_from_line(line)

                if parsed_date is None or self._is_non_document_date(line):
                    continue

                score = self._date_score(
                    page_index,
                    line_index,
                    title_index,
                    document_number,
                    line,
                )
                candidates.append((score, -page_index, -line_index, parsed_date))

        if not candidates:
            return None

        return max(candidates)[3]

    # ------------------------------------------------------------------

    @staticmethod
    def _is_non_document_date(line: str) -> bool:
        return bool(
            re.search(
                r"\b(?:publicad[oa]|boletim\s+de\s+serviço|vigência|"
                r"vigorar|revoga[dr]?)\b",
                line,
                re.IGNORECASE,
            )
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _date_score(
        page_index: int,
        line_index: int,
        title_index: int | None,
        document_number: str | None,
        line: str,
    ) -> int:
        if page_index == 0 and title_index is not None:
            if line_index == title_index:
                return 1000

            if line_index == title_index + 1:
                return 900

            if abs(line_index - title_index) <= 3:
                return 800 - abs(line_index - title_index)

        if re.search(
            r"\b(?:gabinete|reitoria|cidade|sede|assinado|reitor[ae]?)\b|"
            r",\s*\d{1,2}",
            line,
            re.IGNORECASE,
        ):
            return 700

        if page_index == 0:
            return 500

        if document_number and document_number in line:
            return 400

        return 100

    # ------------------------------------------------------------------

    def _date_from_line(self, line: str) -> str | None:
        written_match = re.search(
            r"\b(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})\b",
            line,
            re.IGNORECASE,
        )

        if written_match:
            day, month_name, year = written_match.groups()
            month = self.MONTHS.get(month_name.casefold())

            if month is not None:
                return self._iso_date(year, month, day)

        numeric_match = re.search(
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
            line,
        )

        if numeric_match:
            day, month, year = numeric_match.groups()
            return self._iso_date(year, month, day)

        return None

    # ------------------------------------------------------------------

    @staticmethod
    def _iso_date(year: str, month: int | str, day: str) -> str | None:
        try:
            return date(int(year), int(month), int(day)).isoformat()
        except ValueError:
            return None

    # ------------------------------------------------------------------

    def _issuing_organization(self, first_page: str) -> str | None:
        patterns = (
            r"\b(?:PRÓ-REITORIA|SECRETARIA|GABINETE(?:\s+DA\s+REITORIA)?|"
            r"REITORIA)\b[^\n]{0,100}",
            r"\b(?:UNIVERSIDADE(?:\s+FEDERAL)?|INSTITUTO\s+FEDERAL)\b"
            r"[^\n]{0,100}",
            r"\bMINISTÉRIO\b[^\n]{0,100}",
        )

        for pattern in patterns:
            organization = self._first_match(pattern, first_page)

            if organization is not None:
                return organization

        return None

    # ------------------------------------------------------------------

    def _sei_code(self, text: str) -> str | None:
        number_marker = r"(?:n[º°o]\.?|n\.)"
        separator = rf"(?:{number_marker}\s*|[:#-]\s*)?"
        patterns = (
            rf"\bcódigo\s+(?:SEI|verificador)\s*{separator}(\d{{5,}})\b",
            r"\bSEI\s*/\s*UNIPAMPA\s*[-:]\s*(\d{5,})\b",
            rf"\bDocumento\s+SEI\s*{separator}(\d{{5,}})\b",
        )

        for pattern in patterns:
            sei_code = self._first_match(pattern, text)

            if sei_code is not None:
                return sei_code

        return None

    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None

        return " ".join(value.replace("\r", "").split())

    # ------------------------------------------------------------------

    @staticmethod
    def _first_match(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)

        if match is None:
            return None

        return DocumentMetadataExtractor._normalize(
            match.group(1) if match.lastindex else match.group(0)
        )

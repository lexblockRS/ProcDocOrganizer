"""
Testes unitários das heurísticas de metadados documentais.
"""

import unittest

from services.processing.document_metadata_extractor import (
    DocumentMetadataExtractor,
)
from services.processing.processing_result import ProcessingResult


class DocumentMetadataExtractorTest(unittest.TestCase):
    """
    Valida regras determinísticas sem interface ou arquivos PDF.
    """

    def setUp(self):
        self.extractor = DocumentMetadataExtractor()

    # ------------------------------------------------------------------

    def extract(self, text: str) -> dict:
        return self.extractor.extract([{"page": 1, "text": text}])

    # ------------------------------------------------------------------

    def test_portaria_com_numero_e_data_por_extenso(self):
        metadata = self.extract(
            "PORTARIA Nº 42/2025\n"
            "Gabinete da Reitoria, 15 de março de 2025."
        )

        self.assertEqual(metadata["document_type"], "portaria")
        self.assertEqual(metadata["document_number"], "42/2025")
        self.assertEqual(metadata["document_date"], "2025-03-15")

    def test_resolucao_com_numero_no_formato_ano(self):
        metadata = self.extract("RESOLUÇÃO Nº 123/2025")

        self.assertEqual(metadata["document_type"], "resolucao")
        self.assertEqual(metadata["document_number"], "123/2025")

    def test_oficio_com_data_numerica(self):
        metadata = self.extract(
            "OFÍCIO N. 77/2024\n"
            "Bagé, 03/08/2024"
        )

        self.assertEqual(metadata["document_type"], "oficio")
        self.assertEqual(metadata["document_date"], "2024-08-03")

    def test_data_contextual_tem_prioridade_sobre_data_generica(self):
        metadata = self.extract(
            "PORTARIA Nº 10/2025\n"
            "Publicado em 01/01/2025.\n"
            "Gabinete da Reitoria, 20 de fevereiro de 2025.\n"
            "Prazo final: 30/12/2025."
        )

        self.assertEqual(metadata["document_date"], "2025-02-20")

    def test_documento_sem_numero_retorna_null(self):
        metadata = self.extract("DECLARAÇÃO\nBagé, 10/01/2025")

        self.assertIsNone(metadata["document_number"])

    def test_documento_sem_data_retorna_null(self):
        metadata = self.extract("CERTIFICADO Nº 100")

        self.assertIsNone(metadata["document_date"])

    def test_processo_sei_no_formato_esperado(self):
        metadata = self.extract("Processo SEI 23100.000123/2025-45")

        self.assertEqual(
            metadata["sei_process_number"],
            "23100.000123/2025-45",
        )

    def test_codigo_sei_com_rotulo_explicito(self):
        metadata = self.extract("Código SEI: 1234567")

        self.assertEqual(metadata["sei_code"], "1234567")

    def test_numero_proximo_a_sei_nao_e_codigo_sei(self):
        metadata = self.extract("Processo SEI nº 987654")

        self.assertIsNone(metadata["sei_code"])

    def test_variacoes_de_rotulo_explicito_identificam_codigo_sei(self):
        cases = (
            ("Código SEI: 1234567", "1234567"),
            ("Código SEI nº 2345678", "2345678"),
            ("Documento SEI n. 3456789", "3456789"),
            ("Documento SEI - 4567890", "4567890"),
            ("Código verificador 5678901", "5678901"),
        )

        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.extract(text)["sei_code"], expected)

    def test_numero_perto_de_sei_sem_rotulo_semantico_nao_e_codigo(self):
        cases = (
            "Referência SEI nº 987654",
            "SEI relacionado ao documento 876543",
            "Consulte o SEI: 765432",
        )

        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(self.extract(text)["sei_code"])

    def test_processo_e_codigo_sei_coexistem_sem_confusao(self):
        metadata = self.extract(
            "Processo SEI 23100.000123/2025-45\n"
            "Documento SEI nº 1234567"
        )

        self.assertEqual(
            metadata["sei_process_number"], "23100.000123/2025-45"
        )
        self.assertEqual(metadata["sei_code"], "1234567")

    def test_numero_do_processo_nao_e_codigo_do_documento(self):
        metadata = self.extract("Processo SEI 23100.000123/2025-45")

        self.assertEqual(
            metadata["sei_process_number"], "23100.000123/2025-45"
        )
        self.assertIsNone(metadata["sei_code"])

    def test_cabecalho_institucional_nao_substitui_titulo(self):
        metadata = self.extract(
            "UNIVERSIDADE FEDERAL DO PAMPA\n"
            "PORTARIA Nº 8/2025\n"
            "Bagé, 01/02/2025"
        )

        self.assertEqual(metadata["title"], "PORTARIA Nº 8/2025")
        self.assertEqual(
            metadata["issuing_organization"],
            "UNIVERSIDADE FEDERAL DO PAMPA",
        )

    def test_documento_sem_tipo_reconhecido_retorna_unknown(self):
        metadata = self.extract("COMUNICADO INTERNO\nBagé, 01/02/2025")

        self.assertEqual(metadata["document_type"], "unknown")

    def test_texto_vazio_retorna_metadados_vazios(self):
        metadata = self.extract("")

        self.assertEqual(metadata, {})

    def test_campos_ausentes_retorna_null(self):
        metadata = self.extract("COMUNICADO INTERNO")

        self.assertIsNone(metadata["document_number"])
        self.assertIsNone(metadata["document_date"])
        self.assertIsNone(metadata["issuing_organization"])
        self.assertIsNone(metadata["sei_process_number"])
        self.assertIsNone(metadata["sei_code"])

    def test_data_impossivel_nao_e_aceita(self):
        metadata = self.extract("PORTARIA Nº 1\nBagé, 31/02/2025")

        self.assertIsNone(metadata["document_date"])

    def test_processing_result_antigo_sem_metadata_permanece_compativel(self):
        result = ProcessingResult.from_dict(
            {
                "document_sha256": "abc",
                "processed_at": "2025-01-01T00:00:00",
                "status": "processed",
                "page_count": 1,
                "pages": [{"page": 1, "text": "Texto"}],
                "error": None,
            }
        )

        self.assertEqual(result.metadata, {})
        self.assertIsNone(result.metadata_extractor_version)

    def test_caso_a_prioriza_titulo_e_data_do_ato(self):
        metadata = self.extract(
            "SERVIÇO PÚBLICO FEDERAL\n"
            "PORTARIA Nº 1646, DE 16 DE NOVEMBRO DE 2021\n"
            "Publicada no Boletim de Serviço em 20/11/2021.\n"
            "A Portaria nº 30, de 10 de janeiro de 2020, fica revogada."
        )

        self.assertEqual(
            metadata["title"],
            "PORTARIA Nº 1646, DE 16 DE NOVEMBRO DE 2021",
        )
        self.assertEqual(metadata["document_date"], "2021-11-16")

    def test_caso_b_prioriza_unidade_e_codigo_verificador(self):
        metadata = self.extract(
            "PRÓ-REITORIA DE ADMINISTRAÇÃO - PROAD\n"
            "PORTARIA Nº 183, DE 25 DE NOVEMBRO DE 2022\n"
            "CONSIDERANDO Documento SEI 0994022\n"
            "código verificador 0994214\n"
            "SEI nº 0994214"
        )

        self.assertEqual(
            metadata["title"],
            "PORTARIA Nº 183, DE 25 DE NOVEMBRO DE 2022",
        )
        self.assertEqual(
            metadata["issuing_organization"],
            "PRÓ-REITORIA DE ADMINISTRAÇÃO - PROAD",
        )
        self.assertEqual(metadata["sei_code"], "0994214")

    def test_caso_c_prioriza_gabinete_sobre_ministerio(self):
        metadata = self.extract(
            "SERVIÇO PÚBLICO FEDERAL\n"
            "MINISTÉRIO DA EDUCAÇÃO\n"
            "Universidade Federal do Pampa\n"
            "GABINETE DA REITORIA\n"
            "PORTARIA Nº 1036, DE 07 DE JULHO DE 2021"
        )

        self.assertEqual(
            metadata["title"],
            "PORTARIA Nº 1036, DE 07 DE JULHO DE 2021",
        )
        self.assertEqual(
            metadata["issuing_organization"],
            "GABINETE DA REITORIA",
        )


if __name__ == "__main__":
    unittest.main()

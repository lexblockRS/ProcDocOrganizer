"""Combina texto nativo e OCR sem expor sua origem aos consumidores."""

from .ocr_result import MergedTextResult, OCRResult


class TextMerger:
    def merge(
        self,
        native_pages: list[dict],
        ocr_results: dict[int, OCRResult],
    ) -> MergedTextResult:
        pages = []
        sources = set()
        errors = []

        for page in native_pages:
            page_number = page["page"]
            native_text = page["text"]
            ocr_result = ocr_results.get(page_number)

            if ocr_result is None:
                final_text = native_text
                if final_text.strip():
                    sources.add("native")
            elif ocr_result.success:
                final_text = ocr_result.text
                if final_text.strip():
                    sources.add("ocr")
            else:
                final_text = native_text
                if final_text.strip():
                    sources.add("native")
                errors.append(
                    f"Página {page_number}: "
                    f"{ocr_result.error or 'falha desconhecida no OCR'}"
                )

            pages.append({"page": page_number, "text": final_text})

        if sources == {"native", "ocr"}:
            text_source = "mixed"
        elif "ocr" in sources or (ocr_results and not sources):
            text_source = "ocr"
        else:
            text_source = "native"

        return MergedTextResult(
            pages=pages,
            text_source=text_source,
            ocr_used=bool(ocr_results),
            ocr_errors=errors,
        )


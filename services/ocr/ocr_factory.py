from services.ocr.tesseract_ocr import extract_text as tesseract_extract
from services.ocr.ollama_vision_ocr import extract_text as ollama_vision_extract


def extract_text_from_image(uploaded_file, provider, base_url=None, model_name=None, timeout_seconds=180):

    if provider == "tesseract":
        return tesseract_extract(uploaded_file)

    if provider == "ollama_vision":
        return ollama_vision_extract(
            uploaded_file,
            base_url or "http://localhost:11434",
            model_name or "qwen2.5vl:3b",
            timeout_seconds=timeout_seconds,
        )

    return "OCR provider not implemented yet."

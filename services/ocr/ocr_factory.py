from services.ocr.tesseract_ocr import extract_text as tesseract_extract


def extract_text_from_image(uploaded_file, provider):

    if provider == "tesseract":
        return tesseract_extract(uploaded_file)

    return "OCR provider not implemented yet."
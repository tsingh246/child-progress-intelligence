from PIL import Image
import pytesseract


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(uploaded_file):
    image = Image.open(uploaded_file)

    extracted_text = pytesseract.image_to_string(image)

    return extracted_text
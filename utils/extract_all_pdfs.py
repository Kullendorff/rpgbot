import os
import fitz  # pymupdf
import pytesseract
from pdf2image import convert_from_path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


PDF_FOLDER = "source_pdfs"
OUTPUT_FILE = "full_knowledge.txt"

def extract_text_from_pdfs(pdf_folder, output_file):
    """Extraherar text från alla PDF-filer, inklusive OCR för bilder."""
    all_text = ""

    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            doc = fitz.open(pdf_path)
            text = "\n".join([page.get_text("text") for page in doc])

            # 🔹 Om texten är tom, använd OCR
            if not text.strip():
                print(f"🛠️ OCR krävs för {pdf_file}, kör bildskanning...")
                images = convert_from_path(pdf_path)
                text = "\n".join([pytesseract.image_to_string(img) for img in images])

            all_text += f"\n### {pdf_file} ###\n{text}\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"✅ All PDF-text har extraherats till {output_file}")

extract_text_from_pdfs(PDF_FOLDER, OUTPUT_FILE)

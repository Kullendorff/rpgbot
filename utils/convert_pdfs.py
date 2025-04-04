import os
import fitz  # pymupdf

PDF_FOLDER = "source_pdfs"  # Nytt namn
TEXT_FOLDER = "knowledge_base"  # Här sparas textfilerna

if not os.path.exists(TEXT_FOLDER):
    os.makedirs(TEXT_FOLDER)

def convert_pdf_to_text(pdf_path, text_path):
    """Konverterar en PDF till en textfil"""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

# Konvertera alla PDF-filer
for pdf_file in os.listdir(PDF_FOLDER):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        text_path = os.path.join(TEXT_FOLDER, os.path.splitext(pdf_file)[0] + ".txt")
        convert_pdf_to_text(pdf_path, text_path)
        print(f"Konverterade {pdf_file} -> {text_path}")

print("Alla PDF-filer har konverterats till textfiler.")

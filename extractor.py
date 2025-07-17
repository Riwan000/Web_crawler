import os
import json
import fitz  # PyMuPDF
import hashlib
import string
import re
from pathlib import Path
from datetime import datetime
from pdf2image import convert_from_path
import pytesseract
import re
from PIL import Image, ImageFilter, ImageOps
from ebooklib import epub
from bs4 import BeautifulSoup
import langid
from langdetect import detect, DetectorFactory

JSON_DIR = "json"
os.makedirs(JSON_DIR, exist_ok=True)

def compute_sha256(file_path):
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def extract_pdf_metadata(file_path):
    try:
        doc = fitz.open(file_path)
        metadata = doc.metadata
        title = metadata.get("title") or Path(file_path).stem
        author = metadata.get("author") or "Unknown"
        date_raw = metadata.get("creationDate", "")

        pub_year = None
        if date_raw.startswith("D:"):
            try:
                pub_year = datetime.strptime(date_raw[2:10], "%Y%m%d").date().isoformat()
            except:
                pass

        return {
            "title": title.strip(),
            "authors": [author.strip()],
            "pub_year": pub_year,
            "language": "Unknown"
        }
    except Exception as e:
        print(f"[X] Metadata failed for {file_path}: {e}")
        return {
            "title": Path(file_path).stem,
            "authors": [],
            "pub_year": None,
            "language": "Unknown"
        }

def enhance_image(img):
    img = ImageOps.grayscale(img)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.point(lambda x: 0 if x < 180 else 255, '1')
    return img

def extract_text_from_pdf(file_path):
    try:
        print(f"\n[→] Extracting PDF: {file_path}")
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            text = page.get_text().strip()
            full_text += text + "\n"

        if len(full_text.strip()) > 50:
            print(f"[✓] PDF Embedded text found.")
            return full_text.strip()

        print(f"[⚠] No embedded text. Using OCR...")
        images = convert_from_path(file_path, dpi=300)
        ocr_text = ""
        for img in images:
            processed = enhance_image(img)
            ocr_text += pytesseract.image_to_string(processed)

        return ocr_text.strip() if len(ocr_text.strip()) > 20 else None

    except Exception as e:
        print(f"[X] PDF extraction failed: {e}")
        return None

def extract_text_from_epub(file_path):
    try:
        print(f"\n[→] Extracting EPUB: {file_path}")
        book = epub.read_epub(file_path)
        text = ""
        for item in book.get_items():
            if item.get_type() == epub.EpubHtml:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text += soup.get_text()
        return text.strip() if len(text.strip()) > 20 else None
    except Exception as e:
        print(f"[X] EPUB extraction failed: {e}")
        return None

def extract_text_from_html(file_path):
    try:
        print(f"\n[→] Extracting HTML: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        text = soup.get_text()
        return text.strip() if len(text.strip()) > 20 else None
    except Exception as e:
        print(f"[X] HTML extraction failed: {e}")
        return None

def clean_text(text):
    if not text:
        return None

    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)

    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        words = line.strip().split()
        if len(words) >= 3:
            clean_lines.append(line.strip())

    cleaned = '\n'.join(clean_lines).strip()
    return cleaned if len(cleaned) > 50 else None

def remove_garbage(text: str) -> str:
    # Define what characters are allowed: English + common punctuation + some Indian characters
    allowed_chars = string.ascii_letters + string.digits + string.whitespace + string.punctuation + "।॥‘’“”—"
    return ''.join(c for c in text if c in allowed_chars)

DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    try:
        sample = text[:5000]
        sample = remove_garbage(sample)

        if len(sample.strip()) < 100:
            return "unknown"

        # Try langdetect first
        return detect(sample)
    except Exception as e:
        print(f"[!] langdetect failed: {e}, falling back to langid...")
        try:
            return langid.classify(sample)[0]
        except Exception as e:
            print(f"[X] langid also failed: {e}")
            return "unknown"

def process_downloaded_files():
    for root, _, files in os.walk("downloads"):
        for file in files:
            if not file.lower().endswith((".pdf", ".epub", ".html", ".htm")):
                continue

            file_path = os.path.join(root, file)
            domain = Path(root).name
            download_url = f"https://{domain}/{file}"
            checksum = compute_sha256(file_path)

            out_filename = file.replace(" ", "_") + ".json"
            out_path = os.path.join(JSON_DIR, out_filename)

            # --- Δ Delta Detection ---
            if os.path.exists(out_path):
                try:
                    with open(out_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                        if existing.get("checksum") == checksum:
                            print(f"[→] Skipping (No changes): {file}")
                            continue
                except Exception as e:
                    print(f"[!] Failed to read existing JSON: {e}")

            # --- Extract Metadata ---
            if file.lower().endswith(".pdf"):
                meta = extract_pdf_metadata(file_path)
                raw_text = extract_text_from_pdf(file_path)
            elif file.lower().endswith(".epub"):
                meta = {
                    "title": Path(file).stem,
                    "authors": [],
                    "pub_year": None,
                    "language": "Unknown"
                }
                raw_text = extract_text_from_epub(file_path)
            elif file.lower().endswith((".html", ".htm")):
                meta = {
                    "title": Path(file).stem,
                    "authors": [],
                    "pub_year": None,
                    "language": "Unknown"
                }
                raw_text = extract_text_from_html(file_path)
            else:
                continue

            full_text = clean_text(raw_text)
            if not full_text:
                print(f"[X] Cleaned content too short: {file}")
                continue

            lang = detect_language(full_text)
            meta["language"] = lang

            record = {
                "site": domain,
                "document_id": file.replace(" ", "_"),
                "title": meta["title"],
                "authors": meta["authors"],
                "pub_year": meta["pub_year"],
                "language": meta["language"],
                "download_url": download_url,
                "checksum": checksum,
                "scraped_at": datetime.utcnow().isoformat() + "Z",
                "content": full_text
            }

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

            print(f"[✓] JSON saved with content: {record['document_id']}")


if __name__ == "__main__":
    process_downloaded_files()

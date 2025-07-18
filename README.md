# 📚 Document Scraper & Extractor

This project crawls and processes document files (PDFs, EPUBs, HTML) from Indian cultural archives, extracts metadata and text content, performs OCR when needed, detects document language, and outputs structured JSON files for downstream usage like search indexing or LLM ingestion.

---

## ✅ Features Implemented

### 📁 File Types Supported:
- PDF (embedded text + OCR fallback)
- EPUB
- HTML

### ⚙️ Processing Features:
- ✅ **Metadata Extraction** (title, author, pub year)
- ✅ **Text Extraction**
  - PDFs: Embedded text or OCR via Tesseract
  - EPUBs: Raw HTML to cleaned text using BeautifulSoup
  - HTMLs: Full page text using BeautifulSoup
- ✅ **Text Cleaning** (removes artifacts, reconstructs paragraphs)
- ✅ **OCR Enhancements** for scanned PDFs (grayscale, sharpen, binarize)
- ✅ **Language Detection** using `langdetect` with fallback to `langid`
- ✅ **Delta Detection** (uses SHA256 checksums to skip unchanged files)
- ✅ **Structured JSON Output** with validation-ready schema

---

## 📦 Output JSON Schema

Each extracted JSON file (saved in `/json/`) follows this structure:

```json
{
  "site": "archive.org",
  "document_id": "somefile.pdf",
  "title": "Mahabharata Vol. 1",
  "authors": ["Vyasa"],
  "pub_year": "1921-01-01",
  "language": "hi",
  "download_url": "https://archive.org/somefile.pdf",
  "checksum": "abc123...",
  "scraped_at": "2025-07-18T12:34:56Z",
  "content": "Cleaned document text here..."
}
```

---

## 🗂 Directory Structure

```
.
├── downloads/           # Contains downloaded documents from various sources
├── json/                # Processed structured JSON output
├── extractor.py         # Main processing script
├── crawler.py
├── main.py
├── processed_checksums.json
├── schema.json
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## 🚀 How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

> Make sure `poppler` and `Tesseract OCR` are installed on your system and accessible via PATH.

2. Include the required links for crawling in seed_urls in main.py.

```
seed_urls = [
    "https://archive.org/details/TFIC_ASI_Books/ACatalogueOfTheSamskritManuscriptsInTheAdyarLibraryPt.1/"
]
```

3. Run the main.py file:

```bash
python main.py
```

Output will be saved in the `json/` folder.

---

## 🧠 Next Steps (Planned)

- [ ] Automatic crawler for known domains
- [ ] EPUB metadata extraction (title, authors, year)
- [ ] Language mapping (ISO to human-readable)
- [ ] JSON Schema validation integration
- [ ] SQLite or Elasticsearch indexing
- [ ] FastAPI + UI interface for viewing parsed documents

---

## 🤝 Contributions

PRs welcome! Please create issues for bugs, features, or enhancements.

---

## 📜 License

MIT License — feel free to use, extend, and attribute.

---

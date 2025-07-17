# main.py

from crawler import crawl
from extractor import process_downloaded_files

seed_urls = [
    "https://archive.org/details/TFIC_ASI_Books/ACatalogueOfTheSamskritManuscriptsInTheAdyarLibraryPt.1/"
]

if __name__ == "__main__":
    print("\n🔍 Starting Crawler...\n")
    for url in seed_urls:
        crawl(url, depth=2)

    print("\n📄 Extracting Metadata...\n")
    process_downloaded_files()

    print("\n✅ Done. All files processed.\n")

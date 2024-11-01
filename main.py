from scrapers.table_scraper import scrape_annuity
from scrapers.pdf_parsering import process_all_pdfs

if __name__ == '__main__':
    # Run the Transamerica scraper
    scrape_annuity()
    # process_all_pdfs()
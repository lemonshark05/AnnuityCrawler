import pdfplumber
from utils.selenium_setup import initialize_driver
from utils.error_handler import send_alert_to_admin
import requests
import csv
import hashlib
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

MAX_WAIT_TIME = 120

def get_file_hash(file_path):
    """
    Calculate the MD5 hash of a file to determine if it matches another file.

    Args:
        file_path (str): Path to the file whose hash is to be calculated.

    Returns:
        str: The MD5 hash of the file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_pdf(response, pdf_save_path):
    """
    Save the downloaded PDF content to a file, appending the current date to avoid overwriting.

    Args:
        response (requests.Response): The response object containing PDF content.
        pdf_save_path (str): The original path to save the downloaded PDF file.
    """
    # Add current date to the filename and move to history folder
    current_date = datetime.now().strftime("%Y-%m-%d")
    base_name, ext = os.path.splitext(os.path.basename(pdf_save_path))
    pdf_save_path = os.path.join("history", f"{base_name}_{current_date}{ext}")

    # Ensure the history directory exists
    os.makedirs(os.path.dirname(pdf_save_path), exist_ok=True)

    with open(pdf_save_path, "wb") as file:
        file.write(response.content)
    print(f"PDF downloaded and saved to {pdf_save_path}")


def download_pdf_directly(base_url, pdf_save_path):
    """
    Directly download the PDF from a given URL and save it if it is different.

    Args:
        base_url (str): The URL of the PDF file.
        pdf_save_path (str): Path to save the downloaded PDF file.
    """
    response = requests.get(base_url)
    if response.status_code == 200:
        new_file_hash = hashlib.md5(response.content).hexdigest()

        # Check if the file already exists and compare hashes
        if os.path.exists(pdf_save_path):
            existing_file_hash = get_file_hash(pdf_save_path)
            if new_file_hash == existing_file_hash:
                print(f"PDF at {pdf_save_path} is already up-to-date. Skipping download.")
                return

        save_pdf(response, pdf_save_path)
    else:
        raise Exception(f"Failed to download PDF from {base_url}")


def download_pdf_via_selenium(driver, base_url, link_text, pdf_save_path, link_by):
    """
    Use Selenium to find and download a PDF link from a web page.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        base_url (str): The URL of the page to access.
        link_text (str): The value of either the `title` attribute or the text within the `<a>` tag.
        pdf_save_path (str): Path to save the downloaded PDF file.
        link_by (str): Method to locate the link, either by 'title', 'text'.
    """
    driver.get(base_url)
    wait = WebDriverWait(driver, MAX_WAIT_TIME)

    if link_by == "title":
        pdf_link_element = wait.until(EC.presence_of_element_located((By.XPATH, f'//a[@title="{link_text}"]')))
    elif link_by == "text":
        if '##' in link_text:
            parts = link_text.split('##')
            if len(parts) == 2:
                part_1 = parts[0].strip()
                part_2 = parts[1].strip()
                pdf_link_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, f'//a[contains(., "{part_1}") and contains(., "{part_2}")]')))
            else:
                raise ValueError("Invalid link_text format, expected exactly two parts separated by '##'.")
        else:
            pdf_link_element = wait.until(
                EC.presence_of_element_located((By.XPATH, f'//a[contains(., "{link_text}")]')))
    else:
        raise ValueError("Invalid link_by value. Use 'title', 'text', or 'pdf'.")

    pdf_link = pdf_link_element.get_attribute('href')
    response = requests.get(pdf_link)
    if response.status_code == 200:
        new_file_hash = hashlib.md5(response.content).hexdigest()

        # Check if the file already exists and compare hashes
        if os.path.exists(pdf_save_path):
            existing_file_hash = get_file_hash(pdf_save_path)
            if new_file_hash == existing_file_hash:
                print(f"PDF at {pdf_save_path} is already up-to-date. Skipping download.")
                return

        save_pdf(response, pdf_save_path)
    else:
        raise Exception(f"Failed to download PDF from {pdf_link}")


def fetch_pdf_from_page(base_url, link_text, pdf_save_path, link_by="title"):
    """
    Fetch and download PDF files from a specified page based on `title`, `text`, or direct `pdf` URL.

    Args:
        base_url (str): The URL of the page to access or a direct PDF link.
        link_text (str): The value of either the `title` attribute or the text within the `<a>` tag, or a substring of the text if using `text`.
        pdf_save_path (str): Path to save the downloaded PDF file.
        link_by (str): Method to locate the link, either by 'title', 'text', or direct 'pdf' URL.
    """
    driver = None
    try:
        if link_by == "pdf":
            download_pdf_directly(base_url, pdf_save_path)
        else:
            driver = initialize_driver(headless=False)
            download_pdf_via_selenium(driver, base_url, link_text, pdf_save_path, link_by)
    except Exception as e:
        send_alert_to_admin(f"Error in fetch_pdf_from_page: {str(e)}")
    finally:
        if driver:
            driver.quit()


def fetch_all_pdfs_from_csv(csv_path):
    """
    Reads configuration from CSV and downloads each specified PDF file.

    Args:
        csv_path (str): Path to the CSV configuration file.
    """
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            base_url = row['base_url']
            link_text = row['link_text']
            link_by = row['link_by']
            pdf_path = row['pdf_path']

            # Call the fetch_pdf_from_page function with parameters from CSV
            fetch_pdf_from_page(base_url, link_text, pdf_path, link_by)
            print(f"Processed URL: {base_url}")


def scrape_annuity():
    """
    Uses the fetch_pdf_from_page function to download a PDF from the Transamerica page and extract its contents into a CSV file.
    """
    fetch_all_pdfs_from_csv('table/sites_config.csv')
    # # Step 2: Extract data from the PDF and save it to CSV
    # csv_path = './annuity_data_transamerica.csv'
    # header_path = './table/header.txt'
    # target_index = "S&P 500®"
    # extract_table_and_convert_to_csv(pdf_path, csv_path, header_path, target_index)



def extract_table_and_convert_to_csv(pdf_path, csv_path, header_path, target_index):
    """
    Extract tables from the PDF, map the headers and data into CSV format for saving.
    """
    # Load custom header from the file
    with open(header_path, 'r', encoding='utf-8') as file:
        custom_header = file.readline().strip().split('|')

    company_name = "Transamerica"
    annuity_type = "RILA"
    product_name = "Transamerica Structured Index Advantage Annuity"
    term = "6 Years"

    # Open CSV file to write with the new header
    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(custom_header)

        # Process the PDF to extract relevant data
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()

                if tables:
                    for table in tables:
                        # Locate the index of columns we need
                        header_row = table[1]  # Assuming the second row is the header

                        # Only process data related to the specified target index and 6-year term
                        if target_index not in header_row:
                            continue

                        buffer_idx = header_row.index('Buffer') if 'Buffer' in header_row else None
                        index_idx = header_row.index(target_index) if target_index in header_row else None

                        if buffer_idx is None or index_idx is None:
                            print(f"{target_index} or Buffer not found in the header.")
                            continue

                        # Iterate over the rows starting from the third row to capture relevant data
                        for row in table[3:]:
                            if '6-year' in row:
                                buffer_value = row[buffer_idx]
                                index_value = row[index_idx]

                                # Write the extracted row into the CSV file
                                writer.writerow([
                                    company_name,
                                    annuity_type,
                                    product_name,
                                    term,
                                    target_index.replace('®', '').strip(),
                                    "0",  # Assuming fee is 0
                                    buffer_value,
                                    "N/A",  # Assuming Cap Rate is N/A for participation rate records
                                    index_value.replace('Participation Rate', '').strip()
                                ])

        print(f"Table extracted and saved to {csv_path}")
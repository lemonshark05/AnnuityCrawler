import os
import requests
import pdfplumber
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_pdf(pdf_url, output_path):
    """
    Download the PDF file and save it locally.
    """
    response = requests.get(pdf_url)
    with open(output_path, "wb") as file:
        file.write(response.content)
    print(f"PDF downloaded successfully and saved to {output_path}")

def extract_table_and_convert_to_csv(pdf_path, csv_path, header_path, target_index):
    """
    Extract tables from the PDF and map the headers and data into CSV format for saving.
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
            for page_num, page in enumerate(pdf.pages):
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

                        for row in table[3:]:  # Read data from the third row onward
                            # Filtering data for 6-year term only
                            if '6-year' in row:
                                buffer_value = row[buffer_idx]
                                index_value = row[index_idx]

                                # Write extracted row to CSV
                                writer.writerow([
                                    company_name,
                                    annuity_type,
                                    product_name,
                                    term,
                                    target_index.replace('®', '').strip(),
                                    "0",  # Assuming fee is 0 for most of the data
                                    buffer_value,
                                    "N/A",  # Assuming Cap Rate is N/A for participation rate records
                                    index_value.replace('Participation Rate', '').strip()
                                ])

        print(f"Table extracted and saved to {csv_path}")

if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')  # Uncomment to enable headless mode if needed
    options.add_argument('--disable-gpu')
    options.add_argument('--no-zygote')

    # Path to the manually installed ChromeDriver
    chrome_driver_path = "/usr/local/bin/chromedriver"
    os.environ["webdriver.chrome.driver"] = chrome_driver_path

    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Navigate to the target website
        driver.get('https://www.transamerica.com/annuities/transamerica-structured-index-advantage-annuity')

        # Wait until the <a> tag with title="Current Rates" appears, and get it using XPath
        wait = WebDriverWait(driver, 10)
        current_rates_link = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//a[@title="Current Rates"]')
        ))

        # Get the href attribute
        link_url = current_rates_link.get_attribute('href')
        print("The link to 'Current Rates' is:", link_url)

        # Download PDF
        output_pdf_path = "./Transamerica_Rate_Change_Flyer.pdf"
        download_pdf(link_url, output_pdf_path)

        # Specify the output CSV file path and header path
        csv_path = "annuity_data.csv"
        header_path = "../table/header.txt"  # File containing the custom header

        # Extract table and convert to CSV for the target index (S&P 500®)
        target_index = "S&P 500®"
        extract_table_and_convert_to_csv(output_pdf_path, csv_path, header_path, target_index)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()
import os
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')  # Uncomment this line to enable headless mode
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
        driver.get('https://www.allianzlife.com/what-we-offer/annuities/registered-index-linked-annuities/index-advantage-plus-nf/rates')

        # Wait until the table containing "Index Performance Strategy 6-Year Term" is present
        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//table[.//div[contains(text(), "Index Performance Strategy 6-Year Term")]]')
        ))

        # Extract the correct column headers (skip extra title rows)
        headers = ["Index", "Cap", "Buffer", "Participation Rate"]

        # Extract table rows
        rows = table.find_elements(By.XPATH, './/tbody/tr')
        data = []
        for row in rows:
            cols = row.find_elements(By.XPATH, './/td')
            if len(cols) >= 4:
                # Extract text from each column and append to data
                data.append([col.text for col in cols])

        # Filter data to only include rows containing "S&P 500"
        filtered_data = [row for row in data if "S&P 500" in row[0]]

        # Prepare the new headers and default values
        new_headers = ["Company", "Annuity Type", "Product Name", "Term", "Index", "Fee", "Buffer", "Cap Rate", "Participation Rate"]
        default_values = [
            "Allianz",  # Company
            "RILA",  # Annuity Type
            "Allianz Index Advantage+ NF® Variable Annuity",  # Product Name
            "6 Years",  # Term
            "S&P 500",  # Index
            "0"  # Fee
        ]

        # Construct new data with default values and values from filtered data
        new_data = []
        for row in filtered_data:
            if len(row) >= 4:
                # Extract "Cap", "Buffer", and "Participation Rate" values from the filtered row
                cap_rate = row[1]
                buffer = row[2]
                participation_rate = row[3]
                # Combine default values with the extracted values
                new_row = default_values + [buffer, cap_rate, participation_rate]
                new_data.append(new_row)

        # Save to the new CSV file
        csv_file_path = 'annuity_data.csv'
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the new headers
            writer.writerow(new_headers)
            # Write the new data
            writer.writerows(new_data)

        print(f"Filtered data extracted and saved to {csv_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()

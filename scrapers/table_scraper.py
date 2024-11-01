import pdfkit
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
import time
import base64

MAX_WAIT_TIME = 90

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
    elif link_by == "button":
        # 等待页面完全加载
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print("Page fully loaded.")

        # 使用CSV中的link_text直接作为XPath
        button_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//button[{link_text}]'))
        )
        driver.execute_script("arguments[0].click();", button_element)
        print("Button clicked successfully.")

        # 等待页面跳转到blob格式的URL
        time.sleep(5)  # 根据需要调整等待时间
        original_window = driver.current_window_handle
        all_windows = driver.window_handles
        for window in all_windows:
            if window != original_window:
                driver.switch_to.window(window)
                break

        # 获取新窗口的URL
        blob_url = driver.current_url
        print(f"New URL detected: {blob_url}")

        if "blob:" in blob_url:
            print("Detected blob URL. Starting PDF download...")

            # 执行 JavaScript 脚本获取 Blob 数据并保存
            pdf_content = driver.execute_script("""
                    return fetch(arguments[0]).then(response => response.blob()).then(blob => {
                        return new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onload = () => resolve(reader.result.split(',')[1]);  // 读取Base64数据
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);  // 将Blob转换为DataURL
                        });
                    });
                """, blob_url)

            # 将Base64解码并写入PDF文件
            with open(pdf_save_path, "wb") as file:
                file.write(base64.b64decode(pdf_content))
            print(f"PDF downloaded and saved to {pdf_save_path}")
        else:
            raise Exception("Expected blob URL, but did not find one.")
        return
    elif link_by == "div":
        # Locate the <a> tag within a <div> containing specific text
        get_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, f'//{link_text}')))
        div_element = get_element.find_element(By.XPATH, './ancestor::div[contains(@class, "pcr-rates-title-row")]')
        pdf_link_element = div_element.find_element(By.XPATH, './/a[contains(@href, "http")]')
        pdf_link = pdf_link_element.get_attribute('href')
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
            send_alert_to_admin(f"Error in fetch_pdf_from_page: {str(e)}"
                                f"Fullstacktrace: {e.__traceback__}")
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
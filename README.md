Annuity Crawling Project

## Overview

This project is a collection of Python scripts used for scraping annuity data from different websites. Each website has its own folder, which contains the relevant Python scripts used to gather information such as PDFs and extract tables from those documents. The tools used in this project include `Selenium` for interacting with websites and `pdfplumber` for extracting data from downloaded PDF files.

Annuities are a popular financial product, but comparing options is difficult due to the lack of a centralized, easy-to-use resource. This project aims to create an annuity database that makes searching and comparing offerings simple, starting with a focused Minimum Viable Product (MVP).

## Long-Term Vision

The ultimate goal of this project is to create a comprehensive database encompassing:
- All states
- All annuity providers within each state
- All annuity types
- All products within each annuity type
- All relevant indices and associated data points

This data will be structured for easy access and comparison.

## Scope

For the initial MVP, we focus on:
- **State**: California
- **Annuity Type**: Registered Index-Linked Annuities (RILAs)
- **Companies**: Transamerica, Allianz
- **Index**: S&P 500
- **Term**: 6 years
- **Key Metrics**: Buffer, Cap, Participation Rate, and complete Fee Structure

Data will be updated bi-weekly to maintain accuracy. The extracted data will be stored as a CSV file or in other suitable database formats.

## Installation Instructions

### Step 1: Install Dependencies

This project requires Python 3.10 and several Python packages, which are listed in `requirements.txt`. Use the following command to install them:

```sh
pip3 install -r requirements.txt
```

Ensure that you are using Python 3.10, as this project has been tested with that version.

### Step 2: Install Google Chrome and ChromeDriver

Make sure you have Google Chrome installed. To install Chrome, use the following command:

```sh
brew install --cask google-chrome
```

To install ChromeDriver, it is recommended to download the corresponding version directly from the [official ChromeDriver site](https://sites.google.com/chromium.org/driver/), then unzip the downloaded file and move it to a directory in your system path. Here are the steps:

1. Download ChromeDriver from the [official ChromeDriver site](https://sites.google.com/chromium.org/driver/) that matches your Chrome version.
2. Unzip the downloaded file:
   ```sh
   unzip chromedriver_mac_arm64.zip
   ```
3. Navigate to the unzipped ChromeDriver directory:
   ```sh
   cd chromedriver-mac-arm64
   ```
Move the `chromedriver` binary to a directory in your system path, such as `/usr/local/bin`:
   ```sh
   mv chromedriver /usr/local/bin/
   ```
4. Ensure that ChromeDriver is installed correctly by checking the version:
   ```sh
   chromedriver --version
   ```

Make sure that the ChromeDriver version matches your installed Chrome version. You can check your Chrome version by going to **Chrome > About Google Chrome**.

To verify your ChromeDriver version, use the following command:

```sh
chromedriver --version
```

Example output:
```
ChromeDriver 130.0.6723.58 (3a50e012e4c9b8a410a4e2b12bf577e69ee8f755-refs/branch-heads/6723@{#1353})
```

## Folder Structure

Each website is stored in a separate folder. Each folder contains the following:

- **`<website-name>` folder**: Contains the Python scripts for scraping data from that specific website.
- **Python script**: The script typically does the following:
  1. Opens the website using Selenium.
  2. Navigates and downloads the required data (e.g., PDFs).
  3. Uses `pdfplumber` to extract table data and save it as a CSV.

### Example Folder

```
project-root/
    ├── Transamerica/
    │   └── transamerica_scraper.py
    ├── table/
    │   └── header.txt
    ├── Allianz/
    │   └── allianz_scraper.py
    └── requirements.txt
```

## Usage Instructions

Each folder represents a different website. You can navigate to the respective folder and run the scraper script. Below is an example of how to run a scraper for a specific website.

1. Navigate to the appropriate folder:

   ```sh
   cd Transamerica
   ```

2. Run the script using Python:

   ```sh
   python3 transamerica_scraper.py
   ```

### Example Script Explained

The script provided in the repository works as follows:

1. **Download PDF**: The script uses Selenium to navigate the target website and locate the link to the PDF file. The `download_pdf()` function is then used to download and save the PDF locally.

2. **Extract Table and Save to CSV**: Once the PDF is downloaded, `pdfplumber` is used to extract tables, which are then saved to a CSV file using the `extract_table_and_convert_to_csv()` function.

### Expected Data Format
| Company  | Annuity Type | Product Name                                | Term    | Index   | Fee | Buffer  | Cap Rate  | Participation Rate |
|----------|--------------|--------------------------------------------|---------|---------|-----|---------|-----------|--------------------|
| Allianz  | RILA         | Allianz Index Advantage+ NF® Variable Annuity | 6 Years | S&P 500 | 0   | 10.00%  | Uncapped  | 100.00%            |
| Allianz  | RILA         | Allianz Index Advantage+ NF® Variable Annuity | 6 Years | S&P 500 | 0   | 20.00%  | 125.00%   | 100.00%            |

## Requirements File

The `requirements.txt` file is auto-generated and contains the necessary dependencies for running the scrapers:

- `requests`: Used to download files (such as PDFs).
- `pdfplumber`: Used for extracting table data from PDF files.
- `selenium`: Used to interact with and automate browser tasks.

Ensure that all versions are compatible with Python 3.10.

## Additional Notes

- **Headless Mode**: You can uncomment the line with `options.add_argument('--headless')` to run the browser in headless mode, which means Chrome will not open a visible window.
- **Error Handling**: If an error occurs, the browser will close, and the error will be printed to the terminal.

## Data Sources

- **Transamerica**: [Transamerica Structured Index Advantage Annuity](https://www.transamerica.com/annuities/transamerica-structured-index-advantage-annuity)
- **Allianz**: [Allianz Index Advantage+ NF® Rates](https://www.allianzlife.com/what-we-offer/annuities/registered-index-linked-annuities/index-advantage-plus-nf/rates)
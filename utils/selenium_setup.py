from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

def initialize_driver(chrome_driver_path="/usr/local/bin/chromedriver", headless=True):
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-zygote')
    os.environ["webdriver.chrome.driver"] = chrome_driver_path

    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    return driver
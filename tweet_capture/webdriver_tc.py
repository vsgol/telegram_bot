import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from os.path import exists
from os import environ
from math import ceil

from .exceptions_tc import WebdriverExceptionTC
from .logger_config import get_logger

logger = get_logger(__name__)

async def get_driver(driver_path=None, gui=False, scale=1.0):
    logger.info("Started launching the driver")
    chrome_options = Options()
    if scale < 1.0:
        scale = 1.0
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={ceil(1024*scale)},{ceil(1024*scale)}")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )

    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # driver_path argument : priority 2
    driver_path = "/usr/local/bin/chromedriver"
    chrome_options.binary_location = "/usr/local/bin/chrome"
    
    try:
        driver = webdriver.Chrome(
            service=Service(executable_path=driver_path), options=chrome_options
        )
        logger.info("Driver is running")
        return driver
    except Exception as e:
        logger.error(f"driver_path argument error: {e}")
        pass

    logger.error(f"Webdriver cannot be initialized")
    raise WebdriverExceptionTC("Webdriver cannot be initialized")

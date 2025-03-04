import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .exceptions_tc import TimeoutExceptionTC
from .logger_config import get_logger

logger = get_logger(__name__)

download_endpoint = "https://twtube.app/en/"


def get_videos(driver, url, media_path, wait_time=15):
    f"""
    Downloads gifs and videos from a tweet using the {download_endpoint} site

    The url to the tweet must be using twitter.com, not x.com, as otherwise the site doesn't work

    If the site doesn't respond for longer than {wait_time}, an exception is thrown.
    """
    driver.get(download_endpoint)
    try:
        driver.find_element(
                By.XPATH,
                "//html/body//button[@class='fc-button fc-cta-manage-options fc-secondary-button']"
            ).click()
        logger.info("Selecting options for the cookie")
        driver.find_element(
                By.XPATH,
                "//html/body//button[@class='fc-button fc-confirm-choices fc-primary-button' and @aria-label='Confirm choices']"
            ).click()
    except NoSuchElementException:
        logger.info("No cookie choice window???")

    entry_field = driver.find_element(
                By.XPATH,
                "//html/body//input[@id='url' and @name='url']"
            )
    entry_field.send_keys(url)
    entry_field.send_keys(Keys.ENTER)
    try:
        logger.info(f"Send link to wed service")
        download_buttons = WebDriverWait(driver, 2 * wait_time).until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//span[@class='align-middle'][text() = ' Download Video ' or text() = ' Download GIF ']",
                )
            )
        )
    except TimeoutException as err:
        raise TimeoutExceptionTC(
            f"The video upload site didn't process the tweet in {2*wait_time} seconds", download_endpoint
        ) from err
    logger.info(f"Started downloading videos")
    for i, button in enumerate(download_buttons):
        if "gif" in button.text.lower():
            extension = "gif"
        else: 
            extension = "mp4"
            
        video_url = button.find_element(By.XPATH, "..").get_attribute("href")

        with requests.get(video_url, stream=True) as response:
            with open(f"{media_path}/video_{i}.{extension}", "wb") as video:
                for chunk in response.iter_content(chunk_size=8 * 1024):
                    video.write(chunk)

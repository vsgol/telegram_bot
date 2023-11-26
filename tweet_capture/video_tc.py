import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tweet_capture.data_file import twtube_cookie
from tweet_capture.exceptions_tc import TimeoutExceptionTC

download_endpoint = "https://twtube.app/en/"


def get_videos(driver, url, media_path, wait_time=15):
    f"""
    Downloads gifs and videos from a tweet using the {download_endpoint} site

    The url to the tweet must be using twitter.com, not x.com, as otherwise the site doesn't work

    If the site doesn't respond for longer than {wait_time}, an exception is thrown.
    """
    driver.get(download_endpoint)
    driver.add_cookie(twtube_cookie)
    driver.get(download_endpoint)

    entry_field = driver.switch_to.active_element
    entry_field.send_keys(url)
    entry_field.send_keys(Keys.ENTER)
    try:
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
            f"The video upload site didn't process the tweet in {2*wait_time} seconds"
        ) from err
    for i, button in enumerate(download_buttons):
        video_url = button.find_element(By.XPATH, "..").get_attribute("href")

        with requests.get(video_url, stream=True) as response:
            with open(f"{media_path}/video_{i}.mp4", "wb") as video:
                for chunk in response.iter_content(chunk_size=8 * 1024):
                    video.write(chunk)

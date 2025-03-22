import asyncio
import re
import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, WebDriverException

from .exceptions_tc import BasicExceptionTC, TimeoutExceptionTC

from .video_tc import get_videos
from .webdriver_tc import get_driver


class TweetCapture:
    driver = None
    driver_path = None

    def __init__(self, mode=3, night_mode=0, wait_time = 15):
        self.set_mode(mode)
        self.set_night_mode(night_mode)
        self.set_wait_time(wait_time)

    async def capture(self, url, path, media_path, mode=None, night_mode=None, only_screenshot=False, only_media=False):
        if self.driver is None or not self.__driver_alive(self.driver):
            self.driver = await get_driver(self.driver_path)
        driver = self.driver
        tweet_info = []
        try:
            driver.get(url)
            driver.add_cookie(
                {
                    "name": "night_mode",
                    "value": str(self.night_mode if night_mode is None else night_mode),
                }
            )
            driver.get(url)

            try:
                tweet = WebDriverWait(driver, self.wait_time).until(
                    EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']"))
                )

                self.__init_scale_css(driver)

                self.__hide_global_items(driver)
                driver.execute_script(
                    "!!document.activeElement ? document.activeElement.blur() : 0"
                )

            except TimeoutException as err:
                raise TimeoutExceptionTC(
                    f"Tweet wasn't uploaded in {self.wait_time} seconds", url=url
                ) from err
            self.__code_main_footer_items_new(
                tweet, self.mode if mode is None else mode
            )
            self.__margin_tweet(self.mode if mode is None else mode, tweet)
            driver.execute_script("window.scrollTo(0, 0);")
            if tweet.find_elements(By.CSS_SELECTOR, "svg[data-testid='icon-verified']"):
                tweet_info.append("TB")

            if not only_media:
                tweet.screenshot(f"{path}/screenshot.png")            
            
            tweet_media = tweet.find_elements(By.XPATH, "//article//div[@data-testid='tweetPhoto' and not(ancestor::div[@role='link'])]/img")
            tweet_video = tweet.find_elements(By.XPATH, "//article//div[@data-testid='videoComponent' and not(ancestor::div[@role='link'])]")
            
            if not only_screenshot and (len(tweet_media) > 0 or len(tweet_video) > 0):
                self.__get_photos(tweet_media, media_path)
                
                if len(tweet_video) > 0:
                    get_videos(driver, url, media_path, self.wait_time)

        except BasicExceptionTC as err:
            raise err
        except Exception as err:
            raise BasicExceptionTC() from err
        return tweet_info

    def __driver_alive(self, driver):
        try:
            driver.title
            return True
        except (InvalidSessionIdException, WebDriverException):
            return False

    def __get_photos(self, tweet_media, media_path):
        for i, el in enumerate(tweet_media):
            src = el.get_attribute("src")
            src = re.sub("(?<=&name=)small", "large", src)
            img_data = requests.get(src).content
            with open(f"{media_path}/image_{i}.png", "wb") as image:
                image.write(img_data)

    def set_wait_time(self, time):
        if 1.0 <= time <= 30.0:
            self.wait_time = time

    def set_night_mode(self, night_mode):
        if 0 <= night_mode <= 2:
            self.night_mode = night_mode

    def set_mode(self, mode):
        self.mode = mode

    def set_webdriver_path(self, path):
        self.driver_path = path

    def __init_scale_css(self, driver):  # .r-rthrr5 { width: 100% !important; } idk twitter removed it
        driver.execute_script(
            """
            var style = document.createElement('style');
            style.innerHTML = ".r-1ye8kvj { max-width: 40rem !important; } body { scale: 1 !important; transform-origin: 0 0 !important; }";
            document.head.appendChild(style);
        """
        )

    def __hide_global_items(self, driver):
        HIDE_ITEMS_XPATH = [
            "/html/body/div/div/div/div[1]",
            "/html/body/div/div/div/div[2]/header",
            "/html/body/div/div/div/div[2]/main/div/div/div/div/div/div[1]",
            "//div[@data-testid='BottomBar' and contains(@style,'transition-property')]",
            "(//ancestor::div[@dir = 'ltr'])"
            "//article[@data-testid='tweet']//button[contains(@aria-label,'Grok')]",
            "//article[@data-testid='tweet']//a[@data-testid='logged_out_read_replies_pivot']",
        ]
        for item in HIDE_ITEMS_XPATH:
            try:
                element = driver.find_element(By.XPATH, item)
                driver.execute_script(
                    """
                arguments[0].style.display="none";
                """,
                    element,
                )
            except:
                continue

    def __margin_tweet(self, mode, base):
        if mode == 0 or mode == 1:
            try:
                base.parent.execute_script(
                    """arguments[0].childNodes[0].style.paddingBottom = '35px';""",
                    base.find_element(By.TAG_NAME, "article"),
                )
            except:
                pass

    def __code_main_footer_items_new(self, element, mode):
        XPATHS = [
            "((//ancestor::time)/..)[contains(@aria-describedby, 'id__')]",  # date
            "//div[contains(@role, 'group')][not(contains(@id, 'id__'))]",  # date 2????
            "//div[contains(@role, 'group')][contains(@id, 'id__')]",  # likes/replies/reply
        ]
        hides = []
        if mode == 0:
            hides = [0, 1, 2]
        elif mode == 1:
            hides = [0, 2]
        elif mode == 2:
            hides = [2]
        elif mode == 3:
            hides = []

        for i in hides:
            els = element.find_elements(By.XPATH, XPATHS[i])
            if len(els) > 0:
                for el in els:
                    element.parent.execute_script(
                        """
                    arguments[0].style.display="none";
                    """,
                        el,
                    )


    def quit(self):
        if self.driver is not None:
            self.driver.quit()

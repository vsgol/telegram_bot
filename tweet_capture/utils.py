from re import match
import os



def get_chromedriver_default_path():
    chrome_driver_env = os.getenv("CHROME_DRIVER")
    if chrome_driver_env is not None:
        return chrome_driver_env
    elif os.name == "nt":
        return "C:/bin/chromedriver.exe"
    else:
        return "/usr/local/bin/chromedriver"

class BasicExceptionTC(Exception):
    """Base tweet_capture exception"""
    
    def __str__(self) -> str:
        return "Some error in the code when uploading the tweet, please report the problem to @galloDest"


class TimeoutExceptionTC(BasicExceptionTC):
    """Thrown when a site does not response in enough time."""

    def __init__(self, reason, url):
        self.reason = reason
        self.url = url

    def __str__(self) -> str:
        return self.reason


class WebdriverExceptionTC(BasicExceptionTC):
    """Thrown when can't initialize a webdriver"""

    def __init__(self, reason):
        self.reason = reason

    def __str__(self) -> str:
        return self.reason

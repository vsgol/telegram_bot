import os
import logging
from logging.handlers import TimedRotatingFileHandler

def get_logger(name):
    # Logger setup
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        logger_handler = TimedRotatingFileHandler(
            filename=f"{os.getcwd()}/telegram_bot.log", when="W4"
        )
        logger_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s — %(name)s — %(levelname)s — %(message)s", datefmt="%d/%m %H:%M:%S"
            )
        )
        logger.addHandler(logger_handler)
    return logger

import logging
from rich.logging import RichHandler

def get_logger(name, level=logging.INFO, console=True, file=""):
    logger = logging.getLogger(name)
    
    logger.setLevel(level)

    if console:
        console_handler = RichHandler(
            show_time = False,
            show_path = False,
            markup = True
        )
        logger.addHandler(console_handler)
    
    if file:
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(funcName)s %(message)s"
        ))
        logger.addHandler(file_handler)
    
    return logger

logger = get_logger(__name__, file="log.txt")

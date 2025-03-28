import logging


def setup_logger():
    logger = logging.getLogger('faria_logger')
    logger.setLevel(logging.INFO)
    if logger.handlers:
        logger.handlers.clear()
    file_handler = logging.FileHandler("faria.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

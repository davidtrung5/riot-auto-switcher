import logging

def setup_logger():
    log_format = '%(asctime)s - [%(levelname)s] - %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler("automation.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("RiotAutoSwitcher")

logger = setup_logger()
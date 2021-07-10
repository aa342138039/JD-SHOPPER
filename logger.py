import logging
import logging.handlers
'''
日志模块
'''
LOG_FILENAME = 'JD_SHOPPER.log'
logger = logging.getLogger()


def set_logger():
    logger.setLevel(logging.INFO)
    fmt = '[%(asctime)s] (%(module)s.%(funcName)s): <%(levelname)s> %(message)s'
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=10485760, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

set_logger()
import os
import logging
import logging.handlers
from Config.settings import config

# 从config中查询所需数据
path = config.path() + config.settings("Logger", "FILE_PATH")
filename = config.path() + config.settings("Logger", "FILE_PATH") + config.settings("Logger", "FILE_NAME")
maxBytes = config.settings("Logger", "MAX_BYTES")
backupCount = config.settings("Logger", "AMOUNT")
clearUp = config.settings("Logger", "CLEAR_UP")

# 创建一个logger，创建一个列表存放logger数据
logger = logging.getLogger()
logger_records = []

class CustomFilter(logging.Filter):
    def filter(self, record):
        # logger_records.append(record.msg)
        return record.msg

def clearUpLogFile():
    if not os.path.exists(path):
        os.mkdir(path)
    with open(filename, "w") as file:
        file.seek(0)
        file.truncate()  # 清空文件

def logger_init():
    # 清理log文件
    if clearUp:
        clearUpLogFile()

    # 设置logger输出级别
    logger.setLevel(logging.INFO)
    filter = CustomFilter()
    logger.addFilter(filter)

    # 设置logger输出格式
    # fmt = logging.Formatter('%(asctime)s - %(process)d-%(threadName)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    fmt = '[%(asctime)s] (%(module)s.%(funcName)s): <%(levelname)s> %(message)s'
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # 定义一个console_handler，用于输出到控制台
    console_handler = logging.StreamHandler()

    # 定义一个console_handler，用于输出到控制台
    file_handler = logging.handlers.RotatingFileHandler(
        filename, maxBytes=maxBytes, backupCount=backupCount, encoding="utf-8")

    # 给handler添加formatter
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 把初始化完毕的handler对象添加到logger对象中
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


logger_init()




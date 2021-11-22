from Core.core import main
from Logger.logger import logger
from Scheduler.scheduler import Timer
from Config.settings import config
from Server.server import server
from threading import Thread
from GUI.gui import gui
from concurrent.futures import ProcessPoolExecutor

PROCESS_MODEL = config.settings("Server", "PROCESS_MODEL")
SCHEDULER = config.settings("Scheduler", "START_USING")
SERVER = config.settings("Server", "START_USING")
GUI = config.settings("GUI", "START_USING")


def running():
    if not SCHEDULER:
        thread_main = Thread(target=main)
        thread_main.start()
    else:  # 调度器开启后main函数将被scheduler调度器代理，开启定时执行main
        startTime = config.settings("Scheduler", "START_TIME")
        skipWeekend = config.settings("Scheduler", "SKIP_WEEKEND")
        scheduler = Timer(task=main, startTime=startTime, skipWeekend=skipWeekend)
        thread_scheduler = Thread(target=scheduler.schedule)
        thread_scheduler.start()
    if SERVER:
        if PROCESS_MODEL:
            work_count = config.settings("Server", "PROCESS_COUNT")
            server_process(work_count)
        else:
            thread_server = Thread(target=server)
            thread_server.start()
    if GUI:
        gui()


def server_process(work_count=4):
    with ProcessPoolExecutor(work_count) as pool:
        for i in range(work_count):
            pool.submit(server())


if __name__ == "__main__":
    DEBUG = config.settings("Debug", "DEBUG")
    if DEBUG:
        logger.info("\n===== DEBUG MODE =====")
        main()
    else:
        running()

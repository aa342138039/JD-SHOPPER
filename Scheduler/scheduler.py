import datetime
import time
from Logger.logger import logger


class Timer(object):

    def __init__(self, task, startTime, skipWeekend):
        '''初始化'''
        self.task = task
        self.start_time = startTime
        self.skip_weekend = skipWeekend

    def schedule(self):
        '''调度执行上下文'''
        while True:  # 一个循环为一天时间
            self._schedule()  # 进入今天的循环
            self.sleepToTomorrow()  # 今天的任务结束，休眠到下一天

    def _schedule(self):
        '''调度执行'''

        logger.info("Daily Task Initialized Successfully")

        if self.skip_weekend and not self.isTodayWorkday():
            # 今天不是工作日，结束今天的任务
            return False

        elif self.isTimePass():
            # 今天的任务时间已经过了，结束今天的任务
            return False

        else:
            self.execute()
            return True

    def execute(self):
        real_datetime = self.realDate()  # 当前的时间（日期）
        real_mstime = self.dateMSTime(real_datetime)  # 当前的时间（毫秒）
        today_task_datetime = self.todayTaskTime()  # 今天任务时间（日期）
        today_task_mstime = self.dateMSTime(today_task_datetime)  # 今天任务时间（毫秒）
        wait_time = today_task_mstime - real_mstime  # 获取当前时间与任务的时间差
        logger.info("Waiting to Start Mission -> {}".format(today_task_datetime))
        time.sleep(wait_time)  # 线程休眠阻塞任务
        self.task()  # 阻塞结束执行
        logger.info("Today's Mission Completed")


    def realDate(self):
        '''
        获取当前的日期与时间
        return: date "%Y-%m-%d %H:%M:%S"
        '''
        localtime = time.localtime(time.time())
        date = \
            localtime.tm_year.__str__() + '-' + \
            localtime.tm_mon.__str__() + '-' + \
            localtime.tm_mday.__str__() + ' ' + \
            localtime.tm_hour.__str__() + ':' + \
            localtime.tm_min.__str__() + ':' + \
            localtime.tm_sec.__str__()
        return date

    def realMSTime(self):
        '''
        获取当前的毫秒时间
        return: 毫秒时间
        '''
        return time.time()

    def tomorrowMSTime(self):
        '''
        获取明天的00:00:00毫秒时间
        return: 毫秒时间
        '''
        localtime = time.localtime(time.time())
        # 今天00:00:00的日期时间
        today_start_date = \
            localtime.tm_year.__str__() + '-' + \
            localtime.tm_mon.__str__() + '-' + \
            localtime.tm_mday.__str__() + ' ' + \
            '00:00:00'
        today_start_time = self.dateMSTime(today_start_date)
        tomorrow_start_time = today_start_time + 60 * 60 * 24
        return tomorrow_start_time

    def isTodayWorkday(self):
        '''
        该日期是否为工作日
        params:
            date "%Y-%m-%d %H:%M:%S"
        return:
            工作日: True
            休息日: False
        '''
        localtime = time.localtime(time.time())
        week = localtime.tm_wday.__str__()
        if week in (5, 6):
            # 如果是休息日
            logger.info("Over The Weekend")
            return False
        else:
            # 如果是工作日
            logger.info("Working Day")
            return True

    def sleepToTomorrow(self):
        '''休眠到下一天'''
        real_datetime = self.realDate()  # 当前的时间（日期）
        real_mstime = self.dateMSTime(real_datetime)  # 当前的时间（毫秒）
        tomorrow_mstime = self.tomorrowMSTime()  # 明天0点的时间（毫秒）
        diff_time = tomorrow_mstime - real_mstime  # 现在到明天0点的毫秒时间
        logger.info("Sleeping to tomorrow -> {} Seconds".format(diff_time))
        time.sleep(diff_time)

    def isTimePass(self):
        '''
        确认当前时间是否超过今天执行时间
        return：
            True：超时
            False：没超时
        '''
        real_datetime = self.realDate()  # 当前的时间（日期）
        real_mstime = self.dateMSTime(real_datetime)  # 当前的时间（毫秒）
        today_task_datetime = self.todayTaskTime()  # 今天任务时间（日期）
        today_task_mstime = self.dateMSTime(today_task_datetime)  # 今天任务时间（毫秒）
        if real_mstime > today_task_mstime:
            logger.info("Time Pass - Now Time: {} TaskTime: {}".format(real_datetime, today_task_datetime))
            return True
        else:
            logger.info("Time Waiting - RealTime: {}".format(real_datetime))
            return False

    def dateMSTime(self, date):
        '''
        获取该日期对应的毫秒时间
        params:
            date 格式为"%Y-%m-%d %H:%M:%S"
        return:
            ms_time 毫秒时间
        '''
        date_time = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        ms_time = int(time.mktime(date_time.timetuple()) + date_time.microsecond)
        return ms_time

    def todayTaskTime(self):
        '''
        获取今天的任务日期
        return: today_date "%Y-%m-%d %H:%M:%S"
        '''
        localtime = time.localtime(time.time())
        today_date = \
            localtime.tm_year.__str__() + '-' + \
            localtime.tm_mon.__str__() + '-' + \
            localtime.tm_mday.__str__() + ' ' + \
            self.start_time
        return today_date

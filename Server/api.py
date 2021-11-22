import copy
from Config.settings import config
from Core.spider import Waiter
from threading import Thread
class Global(object):

    def __init__(self):
        self.waiter = None
        self.login = None
        self.thread= None

    def update(self):
        self.login = self.waiter.qrlogin.is_login

glo = Global()

def log(request):
    file_path = config.path() + config.settings("Logger", "FILE_PATH") + \
        config.settings("Logger", "FILE_NAME")
    file_page_file = open(file_path, 'r', encoding="utf-8")
    return str(file_page_file.read())


def serverConfig(request):
    appConfig = copy.deepcopy(config._config._sections)
    for model in appConfig:
        for item in appConfig[model]:
            appConfig[model][item] = eval(appConfig[model][item])
            value = appConfig[model][item]
            # DEBUG print(model, item, value, type(value))
    return appConfig


def jdShopper(request):
    mode = request['mode']
    date = request['date']
    skuids = request['skuid']
    area = request['area']
    eid = request['eid']
    fp = request['fp']
    count = request['count']
    retry = request['retry']
    work_count = request['work_count']
    timeout = request['timeout']
    if mode == '1':
        glo.waiter = Waiter(skuids=skuids, area=area, eid=eid, fp=fp, count=count,
                    retry=retry, work_count=work_count, timeout=timeout)
        glo.thread = Thread(target=glo.waiter.waitForSell)
        glo.thread.start()
    elif mode == '2':
        date = date.replace("T", " ")
        date = date.replace("Z", "")
        glo.waiter = Waiter(skuids=skuids, area=area, eid=eid, fp=fp, count=count,
                    retry=retry, work_count=work_count, timeout=timeout, date=date)
        glo.thread = Thread(target=glo.waiter.waitTimeForSell)
        glo.thread.start()
    glo.update()
    print(glo.login)
    return glo.login

def loginStatus(request):
    try:
        glo.update()
    except:
        pass
    return glo.login

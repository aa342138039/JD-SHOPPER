import copy
import psutil

from Config.settings import config

def log(request):
    file_path = config.path() + config.settings("Logger", "FILE_PATH") + config.settings("Logger", "FILE_NAME")
    file_page_file = open(file_path, 'r')
    return str(file_page_file.read())

def systemInfo(request):
    info = {}
    info['cpu_count'] = psutil.cpu_count()  # CPU逻辑数量
    info['cpu_percent'] = psutil.cpu_percent(interval=1)  # CPU使用率
    info['cpu_times'] = psutil.cpu_times()  # CPU的用户／系统／空闲时间
    info['virtual_memory'] = psutil.virtual_memory()  # 物理内存
    info['swap_memory'] = psutil.swap_memory()  # 交换内存
    info['disk_partitions'] = psutil.disk_partitions() # 磁盘分区信息
    info['disk_partitions'] = psutil.disk_usage('/') # 磁盘使用情况
    info['disk_partitions'] = psutil.disk_io_counters() # 磁盘IO
    info['disk_partitions'] = psutil.net_io_counters() # 获取网络读写字节／包的个数
    info['disk_partitions'] = psutil.net_if_addrs() # 获取网络接口信息
    info['disk_partitions'] = psutil.net_if_stats() # 获取网络接口状态
    # need sudo: info['disk_partitions'] = psutil.net_connections() # 获取当前网络连接信息
    return info

def serverConfig(request):
    appConfig = copy.deepcopy(config._config._sections)
    for model in appConfig:
        for item in appConfig[model]:
            appConfig[model][item] = eval(appConfig[model][item])
            value = appConfig[model][item]
            # DEBUG print(model, item, value, type(value))
    return appConfig

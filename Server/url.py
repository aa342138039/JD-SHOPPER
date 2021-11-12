from Server.api import log, systemInfo, serverConfig

def urls(url, request):
    if (url == "/log"): return log(request)
    elif (url == "/system-info"): return systemInfo(request)
    elif (url == "/config"): return serverConfig(request)
    else: return "No Response"
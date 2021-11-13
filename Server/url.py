from Server.api import log, serverConfig, jdShopper, loginStatus

def urls(url, request):
    if (url == "/log"): return log(request)
    elif (url == "/config"): return serverConfig(request)
    elif (url == "/jd-shopper"): return jdShopper(request)
    elif (url == "/jd-login-status"): return loginStatus(request)
    else: return "No Response"
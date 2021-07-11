import json
import requests

from logger import logger
from config import global_config

def sendMessage(message):
    enabled = global_config.getRaw("messenger", "enable")
    if not enabled:
        return
    mode = global_config.getRaw("messenger", "mode")
    if mode == "group":
        groupid = global_config.getRaw("messenger", "group_id")
        sendGroupMessage(message, groupid)
    else:
        userid = global_config.getRaw("messenger", "user_id")
        sendFriendMessage(message, userid)

def sendFriendMessage(message, userid):
    URL = global_config.getRaw("messenger", "server_address")
    path = "sendFriendMessage"
    try:
        URL = "http://{}/{}".format(URL, path)
        body = {
            "sessionKey": "YourSession",
            "target": userid,
            "messageChain": [
                {"type": "Plain", "text": message}
            ]
        }

        # sender = requests.post(URL, params = params, data=json.dumps(body))
        sender = requests.post(URL, data=json.dumps(body))

        mes = message.replace("\n", " ")
        if len(mes) > 10:
            mes = mes[:10] + "···"
        logger.info("Send {}".format(mes))


        # print(sender.request.url)
        # sender.raise_for_status()
        # print(sender.text)
        return True
    except:
        logger.error("Message Send Failed")
        return False


def sendGroupMessage(message, groupid):
    URL = global_config.getRaw("messenger", "server_address")
    path = "sendGroupMessage"
    try:
        URL = "http://{}/{}".format(URL, path)

        body = {
            "sessionKey": "YourSession",
            "target": groupid,
            "messageChain": [
                {"type": "Plain", "text": message}
            ]
        }

        # sender = requests.post(URL, params = params, data=json.dumps(body))
        sender = requests.post(URL, data=json.dumps(body))
        mes = message.replace("\n", " ")
        if len(mes) > 10:
            mes = mes[:10] + "···"
        logger.info("Send {}".format(mes))

        # print(sender.request.url)
        # sender.raise_for_status()
        # print(sender.text)
        return True
    except:
        logger.error("Message Send Failed")
        return False

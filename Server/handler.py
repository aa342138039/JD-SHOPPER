import os, json, urllib, time

from Logger.logger import logger
from http.server import BaseHTTPRequestHandler
from Config.settings import config
from Server.url import urls


# Document https://docs.python.org/3.9/library/http.server.html

class RequestHandler(BaseHTTPRequestHandler):
    """处理请求并返回页面"""

    # 处理一个GET请求
    def do_GET(self):
        self.rootPath = config.path() + "/Static"
        url = self.requestline[4:-9]
        # print(url)
        request_data = {}  # 存放GET请求数据
        try:
            if url.find('?') != -1:
                req = url.split('?', 1)[1]
                url = url.split('?', 1)[0]
                parameters = req.split('&')
                for i in parameters:
                    key, val = i.split('=', 1)
                    request_data[key] = val
            # request_data['body'] = self.rfile.read()
        except:
            logger.error("URL Format Error")
        if (url == "/"):
            self.home()
        elif (url == ""):
            self.noFound()
        elif ("/api" in url):
            self.api(url[4:], request_data)
        else:
            self.file(url)

    def do_POST(self):
        LOCAL_HOST = config.settings("Server", "LOCAL_HOST")
        PORT = config.settings("Server", "PORT")
        hostLen = len(f'/{LOCAL_HOST}:{PORT}') + 5
        self.rootPath = config.path() + "/Static"
        url = self.requestline[hostLen:-9]
        request_data = json.loads(self.rfile.read(int(self.headers['content-length'])).decode())
        if (url == "/"):
            self.home()
        elif (url == ""):
            self.noFound()
        elif ("/api" in url):
            self.api(url[4:], request_data)
        else:
            self.file(url)

    def log_message(self, format, *args):
        SERVER_LOGGER = config.settings("Logger", "SERVER_LOGGER")
        if SERVER_LOGGER:
            logger.info(format % args)
        else:
            pass

    def home(self):

        file_path = self.rootPath + "/index.html"
        home_page_file = open(file_path, 'r', encoding="utf-8")
        content = str(home_page_file.read())

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content.encode())

    def file(self, url):
        file_name = url.split("/")[-1]
        file_sys_path = self.rootPath + url[:-len(file_name)]
        file_path = ""
        for root, dirs, files in os.walk(file_sys_path):
            for file in files:
                if file == file_name:
                    file_path = os.path.join(root, file)
                else:
                    continue
        if file_path != "":
            self.send_response(200)
        if file_path == "":
            # file_path = self.rootPath + "/404.html" # Hard Code
            self.noFound()
        elif file_name[-5:] == ".html":
            self.send_header("Content-Type", "text/html")
        elif file_name[-4:] == ".css":
            self.send_header("Content-Type", "text/css")
        elif file_name[-3:] == ".js":
            self.send_header("Content-Type", "application/javascript")
        elif file_name[-4:] == ".png":  # 二进制文件
            self.send_header("Content-Type", "img/png")
            file_page_file = open(file_path, 'rb')
            self.end_headers()
            self.wfile.write(file_page_file.read())
            return
        elif file_name[-4:] == ".jpg":  # 二进制文件
            self.send_header("Content-Type", "img/jpg")
            file_page_file = open(file_path, 'rb')
            self.end_headers()
            self.wfile.write(file_page_file.read())
            return
        elif file_name[-4:] == ".ico":  # 二进制文件
            self.send_header("Content-Type", "img/ico")
            file_page_file = open(file_path, 'rb')
            self.end_headers()
            self.wfile.write(file_page_file.read())
            return
        elif file_name[-5:] == ".woff":  # 二进制文件
            self.send_header("Content-Type", "img/ico")
            file_page_file = open(file_path, 'rb')
            self.end_headers()
            self.wfile.write(file_page_file.read())
            return
        file_page_file = open(file_path, 'r', encoding="utf-8")
        content = str(file_page_file.read())
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content.encode())

    def api(self, url, request_data):
        # ----------------------------------------------------------------
        # 此处写API
        content = urls(url, request_data)
        # ----------------------------------------------------------------
        localtime = time.localtime(time.time())
        date = \
            localtime.tm_year.__str__() + '-' + \
            localtime.tm_mon.__str__() + '-' + \
            localtime.tm_mday.__str__() + ' ' + \
            localtime.tm_hour.__str__() + ':' + \
            localtime.tm_min.__str__() + ':' + \
            localtime.tm_sec.__str__()
        jsondict = {}
        jsondict["data"] = content
        jsondict["time"] = date
        res = json.dumps(jsondict)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res.encode())

    def noFound(self):
        self.file("/404.html")

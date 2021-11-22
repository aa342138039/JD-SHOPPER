

from Config.settings import config

PROJECT = config.settings("Information", "PROJECT")
SERVER_HOST = config.settings("Server", "SERVER_HOST")
PORT = config.settings("Server", "PORT")

def gui():
    url = "http://{}:{}/".format(SERVER_HOST, PORT)

    # import webview
    # webview.create_window(PROJECT,
    #                       url=url,
    #                       js_api=None,
    #                       width=900,
    #                       height=800,
    #                       resizable=True,
    #                       fullscreen=False,
    #                       min_size=(200, 200),
    #                       background_color='#FFF',
    #                       text_select=False)
    # webview.start()

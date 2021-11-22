import os

RPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = RPATH.replace("\\", "/")


def run(*commands):
    for command in commands:
        print(command)
        os.system(command)

pack = f'pyinstaller --noconfirm --onedir --windowed \
--icon "{PATH}/Static/favicon.ico" \
--name "jd-shopper" --add-data "{PATH}/Config;Config/" \
--add-data "{PATH}/cookies;cookies/" \
--add-data "{PATH}/Core;Core/" \
--add-data "{PATH}/Docs;Docs/" \
--add-data "{PATH}/GUI;GUI/" \
--add-data "{PATH}/Logger;Logger/" \
--add-data "{PATH}/Message;Message/" \
--add-data "{PATH}/Scheduler;Scheduler/" \
--add-data "{PATH}/Server;Server/" \
--add-data "{PATH}/Static;Static/" \
--add-data "{PATH}/TEST;TEST/"  \
"{PATH}/runserver.py" \
'

if __name__ == '__main__':
    run(pack)

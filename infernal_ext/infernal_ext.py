import asyncio
import json
import logging
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime

import pyautogui
import pygetwindow
import telegram
from PIL import ImageGrab

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

ip = config["connection"]["ip"]
port = config["connection"]["port"]
user = config["connection"]["user"]
test_path = pathlib.Path(config["folder"]["test"])
screen_path = pathlib.Path(config["folder"]["screenshot"])
auto_focus = config["extended"]["auto_focus"]
editor_exe = config["extended"]["editor_exe"]
delete_screenshot = config["delete"]["screenshot"]
delete_test = config["delete"]["test"]
token = config["telegram"]["token"]
chat_id = config["telegram"]["chat_id"]
topic_id = config["telegram"]["topic_id"]

if not topic_id:
    topic_id = None

server = socket.socket()

test_path.mkdir(parents=True, exist_ok=True)
screen_path.mkdir(parents=True, exist_ok=True)


def connect():
    global server
    try:
        logging.info("Connecting...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((ip, port))
    except socket.error as e:
        logging.error(f"Connection error: {e}")
        server = None
        any_key_to_exit()
    else:
        logging.info("Connected")


def get_data(sock, timeout=2):
    sock.setblocking(False)
    total_data = list()
    begin = time.time()

    while True:
        if total_data and (time.time() - begin) > timeout:
            break
        elif (time.time() - begin) > (timeout * 2):
            break

        try:
            data = sock.recv(1024 * 8)
            if data:
                total_data.append(data)
                begin = time.time()
            else:
                time.sleep(0.1)
        except BlockingIOError:
            pass

    return b"".join(total_data)


def get_non_exist(name):
    file_path = test_path / name
    if not file_path.is_file():
        return file_path.open("wb")

    i = 2
    while True:
        newname = f"{name[:-4]} ({i}){name[-4:]}"
        new_file_path = test_path / newname
        if not new_file_path.is_file():
            return new_file_path.open("wb")
        i += 1


def download_tests():
    global server, task_count

    file_name = None
    try:
        server.sendall(b"GETLIST\r\n")
        server.sendall(bytes(user, "utf-8") + b"\r\n")
        data = get_data(server, 1)
        if data == b"NO\r\n":
            logging.warning("Haven't tests")
            server.sendall(b"QUIT\r\n")
            server.close()
            any_key_to_exit()

        directories = data.split(b"\r\n")[2:-1:2]

        for directory in directories:
            server.sendall(b"GETTEST\r\n")
            server.sendall(bytes(user, "utf-8") + b"\r\n")
            server.sendall(directory + b"\r\n")

            file_name = pathlib.Path(directory.decode("utf-8")).name

            with get_non_exist(file_name) as f:
                data = get_data(server, 5)
                content_start = data.find(b"\n", data.find(b"\n", data.find(b"\n", data.find(b"\n") + 1)) + 1) + 1
                f.write(data[content_start:])

            server.sendall(b"QUIT\r\n")
            server.close()

        logging.info("All tests downloaded")
        test_directory = test_path / file_name
        logging.info("Open MyTestX test editor")
        subprocess.Popen([editor_exe, str(test_directory)])

        task_count = int(input("Enter the count of tasks: "))

        if auto_focus:
            logging.info("Auto focus on MyTestEditor")
            pygetwindow.getWindowsWithTitle("MyTestEditor")[0].activate()

        time.sleep(1)
        screen_puller(task_count)

        if delete_screenshot:
            logging.info("Deleting screenshots folder...")
            shutil.rmtree(screen_path)

        if delete_test:
            logging.info("Deleting tests folder...")
            shutil.rmtree(test_path)

    except socket.error as e:
        logging.error(f"Socket error: {e}")
        any_key_to_exit()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        any_key_to_exit()


def screen_puller(screenshots_count):
    logging.info("Starting screenshot capture")

    window = next((w for w in pygetwindow.getWindowsWithTitle("Редактор") if w.title), None)
    left, top, right, bottom = window.left, window.top, window.right, window.bottom

    for i in range(screenshots_count):
        time.sleep(0.4)
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        screenshot.save(screen_path / f"{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.press("down")

    logging.info("Starting telegram sending")

    asyncio.run(start_sending())


async def start_sending():
    bot = telegram.Bot(token=token)

    logging.info("Start sending")
    for filename in os.listdir(screen_path):
        file_path = os.path.join(screen_path, filename)
        with open(file_path, "rb") as file:
            await bot.send_photo(
                chat_id=chat_id,
                message_thread_id=topic_id,
                photo=file,
                read_timeout=20,
                connect_timeout=20,
            )


def any_key_to_exit():
    print()
    os.system("pause")
    sys.exit()


if __name__ == "__main__":
    print(
        r"""                                                         
           (                             (                  )    
 (         )\ )    (   (              )  )\     (     )  ( /(    
 )\   (   (()/(   ))\  )(    (     ( /( ((_)   ))\ ( /(  )\())   
((_)  )\ ) /(_)) /((_)(()\   )\ )  )(_)) _    /((_))\())(_))/    
 (_) _(_/((_) _|(_))   ((_) _(_/( ((_)_ | |  (_)) ((_)\ | |_     
 | || ' \))|  _|/ -_) | '_|| ' \))/ _` || |  / -_)\ \ / |  _| _  
 |_||_||_| |_|  \___| |_|  |_||_| \__,_||_|  \___|/_\_\  \__|(_)                         

                                     infernal extended v0.9
                                     by Plak.I.A

    """
    )
    connect()
    if server:
        logging.info("The connection from the servers was successfully established")
        logging.info("Downloading tests...")
        download_tests()

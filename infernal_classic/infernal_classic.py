import logging
import os
import pathlib
import socket
import subprocess
import sys
import time

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

ip = "localhost"
port = 5005
user = "infernaler"
server = socket.socket()

test_path = pathlib.Path("tests")
test_path.mkdir(parents=True, exist_ok=True)


def connect():
    global server
    try:
        logging.info("Connecting...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((ip, port))
    except socket.error as e:
        logging.error(f"Connection error: {e}")
        any_key_to_exit()
    else:
        logging.info("Successful connection")


def recv_timeout(sock, timeout=2):
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
    global server

    file_name = None
    try:
        server.sendall(b"GETLIST\r\n")
        server.sendall(bytes(user, "utf-8") + b"\r\n")
        data = recv_timeout(server, 1)
        if data == b"NO\r\n":
            logging.warning("Haven't tests")
            any_key_to_exit()

        directories = data.split(b"\r\n")[2:-1:2]
        server.sendall(b"QUIT\r\n")
        server.close()

        for directory in directories:
            connect()
            server.sendall(b"GETTEST\r\n")
            server.sendall(bytes(user, "utf-8") + b"\r\n")
            server.sendall(directory + b"\r\n")

            file_name = directory[directory.rfind(b"\\") + 1:].decode("utf-8")
            with get_non_exist(file_name) as f:
                data = recv_timeout(server, 5)
                content_start = data.find(b"\n", data.find(b"\n", data.find(b"\n", data.find(b"\n") + 1)) + 1) + 1
                f.write(data[content_start:])

            server.sendall(b"QUIT\r\n")
            server.close()

        logging.info("All tests downloaded")
        test_directory = test_path / file_name
        logging.info("Open MyTestX test editor")
        subprocess.Popen(["MTE.exe", str(test_directory)])

    except socket.error as e:
        logging.error(f"Socket error: {e}")
        any_key_to_exit()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        any_key_to_exit()


def any_key_to_exit():
    print()
    os.system("pause")
    sys.exit()


if __name__ == "__main__":
    print(
        r"""                                                         

 ▄█  ███▄▄▄▄      ▄████████    ▄████████    ▄████████ ███▄▄▄▄      ▄████████  ▄█       
███  ███▀▀▀██▄   ███    ███   ███    ███   ███    ███ ███▀▀▀██▄   ███    ███ ███       
███▌ ███   ███   ███    █▀    ███    █▀    ███    ███ ███   ███   ███    ███ ███       
███▌ ███   ███  ▄███▄▄▄      ▄███▄▄▄      ▄███▄▄▄▄██▀ ███   ███   ███    ███ ███       
███▌ ███   ███ ▀▀███▀▀▀     ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   ███   ███ ▀███████████ ███       
███  ███   ███   ███          ███    █▄  ▀███████████ ███   ███   ███    ███ ███       
███  ███   ███   ███          ███    ███   ███    ███ ███   ███   ███    ███ ███▌    ▄ 
█▀    ▀█   █▀    ███          ██████████   ███    ███  ▀█   █▀    ███    █▀  █████▄▄██ 
                                           ███    ███                        ▀                             

                                                            infernal classic v1.1
                                                            by Plaksin

    """
    )
    connect()
    if server:
        logging.info("The connection from the servers was successfully established")
        logging.info("Downloading tests...")
        download_tests()
        sys.exit()

from flask import Flask, render_template
import socket
import threading
import json
import time
import datetime
import copy


class socket_conn():
    def __init__(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.bind(('127.0.0.1', 8998))
        self.buffer = dict()
        self.buffer_lock = threading.RLock()

    def start(self):
        threading.Thread(target=self.runner).start()

    def runner(self):
        self.conn.listen(1)
        sock, ip = self.conn.accept()
        while True:
            compile_msg = b""
            while b"://{}" not in compile_msg:
                compile_msg += sock.recv(1024)
            self.store(compile_msg.decode().replace("://{}", ""))

    def store(self, data):
        self.buffer_lock.acquire()
        parsed_json = json.loads(data)
        self.buffer = dict()
        for key, item in parsed_json.items():
            item = map(str, item)
            cords = ",".join(item)
            timestamp = time.time()
            self.buffer[key] = {
                "pos": cords,
                "timestamp": timestamp,
                "timeread": datetime.datetime.now()
            }
        self.buffer_lock.release()

    def get(self):
        self.buffer_lock.acquire()
        temp_buff = self.buffer
        self.buffer_lock.release()
        return temp_buff


class coord_manager(object):
    def __init__(self, players, update_time):
        self.update_time = update_time
        self.players = players
        self.connection = socket_conn()
        self.connection.start()
        self.time_left = 0
        self.time_of_update = 0
        self.data_live = dict(
            map(
                lambda x: (
                    x,
                    {
                        "pos": [0, 0, 0],
                        "timestamp": time.time(),
                        "timeread": datetime.datetime.now()
                    }
                ),
                players
            )
        )
        self.data_published = copy.deepcopy(self.data_live)
        self.data_lock = threading.RLock()

    def start(self):
        threading.Thread(target=self.runner).start()

    def runner(self):
        while 1:
            time.sleep(1)
            sock_data = self.connection.get()
            players_data = {}
            self.data_lock.acquire()
            if time.time()-self.time_of_update > self.update_time:
                self.data_published = copy.deepcopy(self.data_live)
                self.time_of_update = time.time()

            for player in self.players:
                print(player)
                player_data = sock_data.get(player, None)
                old_player_data = self.data_live.get(player, None)
                if player_data is not None and old_player_data is not None:
                    if player_data["timestamp"] > old_player_data["timestamp"]:
                        self.data_live[player]["pos"] = player_data["pos"]
                        self.data_live[player]["timeread"] = player_data["timeread"]
                        self.data_live[player]["timestamp"] = player_data["timestamp"]

            self.time_left = self.update_time-(time.time()-self.time_of_update)
            self.data_lock.release()

    def get(self):
        self.data_lock.acquire()
        temp_buffer = self.data_published
        self.data_lock.release()
        return temp_buffer


app = Flask(__name__)


@app.route('/', methods=['get'])
def home():
    print([connection.get(), connection.time_left])
    return render_template('home.html', pos=connection.get(), time_left=connection.time_left)


if __name__ == "__main__":

    connection = coord_manager(["ditrames", "Jellyonion64", "Stickman_Lord"], 60)
    connection.start()
    app.run(port=8080)

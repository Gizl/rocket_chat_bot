import websocket
import threading
import time
import queue
from typing import List
from rocketchat_API.rocketchat import RocketChat
import settings
import traceback
import json
from pprint import pprint


class Message:
    def __init__(self, channel_id: str, message: str):
        self.__channel_id = channel_id
        self.__message = message

    def get_channel_id(self) -> str:
        return self.__channel_id

    def get_message(self) -> str:
        return self.__message


class RocketChatReader(threading.Thread):

    def __init__(self, server: str, channel_names: List[str]):
        """Attribute: server - Server name. Example: open.rocket.chat"""
        threading.Thread.__init__(self, daemon=True)
        self.__rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
        self.__ws = websocket.WebSocket()
        self.__server = server
        self.__is_closed = True
        self.__is_started = False
        self.__messages_queue = queue.Queue()
        self.__channels = dict()
        self.__channels = {name: self.__get_channel_id(name) for name in channel_names}

    def connect(self) -> None:
        try:
            self.__ws.connect("wss://%s/websocket" % self.__server)

            connect_message = {"msg": "connect", "version": "1", "support": ["1"]}
            self.__ws.send(json.dumps(connect_message))

            login_message = {
                "msg": "method",
                "method": "login",
                "id": "42",
                "params": [
                    {"resume": settings.ROCKET_TOKEN}
                ]
            }
            self.__ws.send(json.dumps(login_message))

            for channel_id in self.__channels.values():
                self.__subscribe(channel_id)

            if not self.__is_started:
                self.start()
                self.__is_started = True

            self.__is_closed = False

            print("RocketChatReader has started")
        except:
            # print(traceback.format_exc())
            time.sleep(1)
            self.connect()

    def close_connection(self) -> None:
        self.__is_closed = True
        self.__ws.close()

    def get_messages_queue(self) -> queue:
        return self.__messages_queue

    def add_channels(self, channel_names: List[str]) -> None:
        for name in channel_names:
            if name not in self.__channels:
                channel_id = self.__get_channel_id(name)
                self.__subscribe(channel_id)
                self.__channels[name] = channel_id

    def delete_channels(self, channel_names: List[str]) -> None:
        [self.__unsubscribe(name) for name in channel_names]

    def __get_channel_id(self, channel_name) -> str:
        return self.__rocket.rooms_info(room_name=channel_name).json().get('room').get('_id')

    def __subscribe(self, channel_id) -> None:
        subscribe_message = {
            "msg": "sub",
            "id": channel_id,
            "name": "stream-room-messages",
            "params": [
                channel_id,
                False
            ]
        }
        self.__ws.send(json.dumps(subscribe_message))

    def __unsubscribe(self, channel_name):
        unsubscribe_message = {
            "msg": "unsub",
            "id": self.__channels.get(channel_name)
        }
        self.__ws.send(json.dumps(unsubscribe_message))
        del self.__channels[channel_name]

    def run(self):
        while True:
            try:
                data = self.__ws.recv()
                data = json.loads(data)
            except:
                # print(traceback.format_exc())
                if not self.__is_closed:
                    print("Connection lost")
                    self.__ws.close()
                    self.connect()
                    time.sleep(1)
                else:
                    break
            else:
                if data.get("msg") == "ping":
                    self.__ws.send(json.dumps({"msg": "pong"}))
                elif data.get("msg") == "changed" and data.get("collection") == "stream-room-messages":
                    self.__messages_queue.put(Message(data.get("fields").get("args")[0].get("rid"),
                                                      data.get("fields").get("args")[0].get("msg")))


if __name__ == "__main__":
    names: List[str] = list()
    reader = RocketChatReader("open.rocket.chat", names)
    reader.connect()
    while True:
        print(reader.get_messages_queue().get())
